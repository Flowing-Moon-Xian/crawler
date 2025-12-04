"""
子大盘 K 线数据爬虫
从 steamdt.com API 获取子大盘 K 线数据并存储到 Supabase
支持不同的 type（如 HOT）和 klineType（1=时K, 2=日K, 3=周K）
"""
import requests
import time
from datetime import datetime
from typing import Optional, List, Dict, Any

from crawler.config.config import Config
from crawler.database.supabase_client import SupabaseManager
from crawler.database.models import SubKlineData, KlinePeriod
from decimal import Decimal


class SubKlineCrawler:
    """子大盘 K 线数据爬虫"""
    
    # klineType 到 period 的映射
    KLINETYPE_TO_PERIOD = {
        1: "hourly",   # 时K
        2: "daily",    # 日K
        3: "weekly",   # 周K（数据库暂不支持，会跳过）
    }
    
    def __init__(self, config: Optional[Config] = None):
        """
        初始化子大盘 K 线爬虫
        
        Args:
            config: 配置对象，如果为 None 则从环境变量加载
        """
        self.config = config or Config.from_env()
        
        # 通过 Config 初始化 Supabase（如果配置存在）
        if self.config.supabase:
            self.supabase = SupabaseManager(
                url=self.config.supabase.url,
                key=self.config.supabase.key
            )
        else:
            # 如果 Config 中没有 Supabase 配置，尝试从环境变量初始化
            self.supabase = SupabaseManager()
        
        self.api_url = "https://api.steamdt.com/user/item/block/v1/kline"
        
        # 初始化 requests session
        self.session = requests.Session()
        
        # 配置代理（如果提供）
        if self.config.crawler.proxy:
            self.session.proxies = {
                "http": self.config.crawler.proxy,
                "https": self.config.crawler.proxy
            }
        
        # 设置请求头
        self.session.headers.update({
            "User-Agent": self.config.csqaq.user_agent,
            "Accept": "application/json",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Content-Type": "application/json",
        })
    
    def fetch_kline_data(
        self,
        type: str,
        kline_type: int,
        type_val: str,
        timestamp: Optional[str] = None,
        max_time: Optional[int] = None,
        platform: str = "ALL",
        special_style: str = ""
    ) -> Optional[List[List[Any]]]:
        """
        从 API 获取 K 线数据（POST 请求）
        
        Args:
            type: 类型，如 "HOT"
            kline_type: K 线类型，1=时K，2=日K，3=周K
            type_val: 类型值，如 "1402501509110038528"
            timestamp: 时间戳（毫秒字符串），用于分页
            max_time: 最大时间戳（秒），用于限制数据范围
            platform: 平台，默认为 "ALL"
            special_style: 特殊样式，默认为空字符串
            
        Returns:
            K 线数据列表，格式：[[timestamp, open, close, high, low, volume, turnover], ...]
        """
        # 构建请求体
        json_data = {
            "type": type,
            "klineType": kline_type,
            "typeVal": type_val,
            "platform": platform,
            "specialStyle": special_style
        }
        
        # 添加可选参数
        if timestamp:
            json_data["timestamp"] = timestamp
        else:
            # 如果没有提供 timestamp，使用当前时间戳（毫秒）
            json_data["timestamp"] = str(int(time.time() * 1000))
        
        if max_time:
            json_data["maxTime"] = max_time
        
        # 构建 URL 参数（如果有 timestamp）
        params = {}
        if timestamp:
            params["timestamp"] = timestamp
        
        try:
            time.sleep(self.config.crawler.delay)
            
            response = self.session.post(
                self.api_url,
                params=params,
                json=json_data,
                timeout=self.config.crawler.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get("success"):
                print(f"API 返回失败: {data.get('errorMsg', '未知错误')}")
                return None
            
            kline_data = data.get("data", [])
            if not kline_data:
                print("API 返回数据为空")
                return None
            
            print(f"成功获取 {len(kline_data)} 条 K 线数据 (type={type}, klineType={kline_type})")
            return kline_data
            
        except requests.RequestException as e:
            print(f"API 请求失败: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    print(f"错误详情: {error_data}")
                except:
                    print(f"响应内容: {e.response.text[:500]}")
            return None
        except Exception as e:
            print(f"获取 K 线数据失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def parse_kline_item(self, item: List[Any], period: str) -> Optional[SubKlineData]:
        """
        解析单条 K 线数据
        
        Args:
            item: API 返回的单条数据，格式：[timestamp, open, close, high, low, volume, turnover]
            period: K 线周期（hourly/daily/weekly）
            
        Returns:
            解析后的 SubKlineData 模型对象，如果解析失败返回 None
        """
        try:
            # 数据格式：[timestamp(字符串), open, close, high, low, volume(字符串), turnover]
            if len(item) < 7:
                print(f"数据格式不正确，期望 7 个字段，实际 {len(item)} 个: {item}")
                return None
            
            timestamp_str = str(item[0])
            open_price = float(item[1])
            close_price = float(item[2])
            high_price = float(item[3])
            low_price = float(item[4])
            volume_str = str(item[5])
            turnover = float(item[6])
            
            # 将时间戳（秒）转换为 datetime
            timestamp_seconds = int(timestamp_str)
            timestamp_dt = datetime.fromtimestamp(timestamp_seconds)
            
            # 转换 volume（字符串）为整数
            volume = int(volume_str) if volume_str else None
            
            # 转换 period 字符串为枚举
            period_enum = KlinePeriod(period) if period in ["hourly", "daily", "weekly"] else None
            if period_enum is None:
                print(f"不支持的 period: {period}")
                return None
            
            # 创建模型对象
            return SubKlineData(
                period=period_enum,
                timestamp=timestamp_dt,
                open_price=Decimal(str(open_price)) if open_price else None,
                close_price=Decimal(str(close_price)) if close_price else None,
                high_price=Decimal(str(high_price)) if high_price else None,
                low_price=Decimal(str(low_price)) if low_price else None,
                volume=volume,
                turnover=Decimal(str(turnover)) if turnover else None
            )
            
        except (ValueError, IndexError, TypeError) as e:
            print(f"解析 K 线数据失败: {e}, 数据: {item}")
            return None
    
    def save_kline_data(
        self,
        kline_data: List[List[Any]],
        kline_type: int,
        table_name: str = "qianzhan_kline_data",
        batch_size: int = 100
    ) -> int:
        """
        保存 K 线数据到数据库
        
        Args:
            kline_data: K 线数据列表
            kline_type: K 线类型（1=时K，2=日K，3=周K）
            table_name: 目标表名，默认为 "qianzhan_kline_data"
                        可选值: "qianzhan_kline_data", "agent_kline_data" 等
            batch_size: 批量插入大小
            
        Returns:
            成功插入的记录数
        """
        # 检查 period 是否支持
        period = self.KLINETYPE_TO_PERIOD.get(kline_type)
        if not period:
            print(f"不支持的 K 线类型: {kline_type}")
            return 0
        
        # 检查数据库是否支持该 period（weekly 暂不支持）
        if period == "weekly":
            print(f"警告: 数据库暂不支持周K (weekly)，跳过保存")
            return 0
        
        # 解析数据为模型对象
        parsed_models = []
        for item in kline_data:
            parsed = self.parse_kline_item(item, period)
            if parsed:
                parsed_models.append(parsed)
        
        if not parsed_models:
            print("没有有效的数据可保存")
            return 0
        
        # 转换为字典列表（用于数据库插入）
        parsed_data = [model.to_dict() for model in parsed_models]
        
        print(f"准备保存 {len(parsed_data)} 条数据到 {table_name} 表 (period={period})")
        
        # 批量插入
        total_inserted = 0
        skipped_count = 0
        
        for i in range(0, len(parsed_data), batch_size):
            batch = parsed_data[i:i + batch_size]
            try:
                result = self.supabase.insert_batch(table_name, batch)
                inserted_count = len(result) if result else 0
                total_inserted += inserted_count
                skipped_count += len(batch) - inserted_count
                print(f"批量插入 {inserted_count} 条数据 (进度: {min(i + batch_size, len(parsed_data))}/{len(parsed_data)})")
            except Exception as e:
                # 如果是唯一约束冲突，尝试逐条插入（只保存不存在的记录）
                error_msg = str(e).lower()
                if "unique" in error_msg or "duplicate" in error_msg or "23505" in error_msg:
                    print(f"批量插入遇到唯一约束冲突，改为逐条插入（只保存不存在的记录）...")
                    for item in batch:
                        try:
                            self.supabase.insert_data(table_name, item)
                            total_inserted += 1
                        except Exception as single_e:
                            single_error = str(single_e).lower()
                            if "unique" in single_error or "duplicate" in single_error or "23505" in single_error:
                                # 记录已存在，跳过
                                skipped_count += 1
                                continue
                            else:
                                print(f"插入单条数据失败: {single_e}")
                                skipped_count += 1
                else:
                    print(f"批量插入失败: {e}，改为逐条插入...")
                    # 对于其他错误，也尝试逐条插入
                    for item in batch:
                        try:
                            self.supabase.insert_data(table_name, item)
                            total_inserted += 1
                        except Exception as single_e:
                            single_error = str(single_e).lower()
                            if "unique" in single_error or "duplicate" in single_error or "23505" in single_error:
                                # 记录已存在，跳过
                                skipped_count += 1
                                continue
                            else:
                                print(f"插入单条数据失败: {single_e}")
                                skipped_count += 1
        
        print(f"成功保存 {total_inserted} 条 K 线数据到 {table_name} 表，跳过 {skipped_count} 条已存在的记录")
        return total_inserted
    
    def crawl_and_save(
        self,
        type: str,
        kline_type: int,
        type_val: str,
        table_name: str = "qianzhan_kline_data",
        timestamp: Optional[str] = None,
        max_time: Optional[int] = None,
        platform: str = "ALL",
        special_style: str = ""
    ) -> int:
        """
        爬取并保存 K 线数据（一步完成）
        
        Args:
            type: 类型，如 "HOT"
            kline_type: K 线类型，1=时K，2=日K，3=周K
            type_val: 类型值，如 "1402501509110038528"，用于区分不同的子大盘
            table_name: 目标表名，默认为 "qianzhan_kline_data"
                        可选值: "qianzhan_kline_data", "agent_kline_data" 等
            timestamp: 时间戳（毫秒字符串），用于分页
            max_time: 最大时间戳（秒），用于限制数据范围
            platform: 平台，默认为 "ALL"
            special_style: 特殊样式，默认为空字符串
            
        Returns:
            成功保存的记录数
        """
        # 获取数据
        kline_data = self.fetch_kline_data(
            type=type,
            kline_type=kline_type,
            type_val=type_val,
            timestamp=timestamp,
            max_time=max_time,
            platform=platform,
            special_style=special_style
        )
        if not kline_data:
            return 0
        
        # 保存数据
        return self.save_kline_data(kline_data, kline_type, table_name=table_name)


def main():
    """主函数：示例用法"""
    import argparse
    
    parser = argparse.ArgumentParser(description="子大盘 K 线数据爬虫")
    parser.add_argument(
        "--type",
        type=str,
        required=True,
        help="类型，如 'HOT'"
    )
    parser.add_argument(
        "--kline-type",
        type=int,
        required=True,
        choices=[1, 2, 3],
        help="K线类型: 1=时K, 2=日K, 3=周K"
    )
    parser.add_argument(
        "--type-val",
        type=str,
        required=True,
        help="类型值，如 '1402501509110038528'"
    )
    parser.add_argument(
        "--timestamp",
        type=str,
        default=None,
        help="时间戳（毫秒字符串），用于分页。如果不提供，将使用当前时间戳"
    )
    parser.add_argument(
        "--max-time",
        type=int,
        help="最大时间戳（秒），用于限制数据范围"
    )
    parser.add_argument(
        "--platform",
        type=str,
        default="ALL",
        help="平台，默认为 'ALL'"
    )
    parser.add_argument(
        "--special-style",
        type=str,
        default="",
        help="特殊样式，默认为空字符串"
    )
    parser.add_argument(
        "--table",
        type=str,
        default="qianzhan_kline_data",
        choices=["qianzhan_kline_data", "agent_kline_data"],
        help="目标表名，默认为 'qianzhan_kline_data'，可选: 'agent_kline_data'"
    )
    
    args = parser.parse_args()
    
    # 如果没有提供 timestamp，使用当前时间戳（毫秒字符串）
    timestamp = args.timestamp
    if timestamp is None:
        timestamp = str(int(time.time() * 1000))
        print(f"未提供 timestamp，使用当前时间戳（毫秒）: {timestamp}")
    
    # 创建爬虫
    crawler = SubKlineCrawler()
    
    # 爬取并保存数据
    count = crawler.crawl_and_save(
        type=args.type,
        kline_type=args.kline_type,
        type_val=args.type_val,
        table_name=args.table,
        timestamp=timestamp,
        max_time=args.max_time,
        platform=args.platform,
        special_style=args.special_style
    )
    
    print(f"\n完成！共保存 {count} 条数据")


if __name__ == "__main__":
    main()

