"""
商品 K 线数据爬虫

从 steamdt.com API 获取「具体商品」的 K 线数据，并写入 Supabase 的 kline_data 表。

逻辑：
- 通过 type_val（SteamDT 的商品 ID / 分类 ID）去 item_statistics 表查找 steamdt_id 对应的 item_statistics.id
- 调用 SteamDT 的商品 K 线接口获取 K 线数据
- 将数据解析为 KlineData 模型，写入 kline_data 表，填充 item_statistics_id

API 示例（参考）：
https://api.steamdt.com/user/steam/category/v1/kline?timestamp=1764749084910&type=2&maxTime=1756828800&typeVal=24721&platform=ALL&specialStyle=

请求方式：GET
URL 参数：
- timestamp: 毫秒时间戳（整数）
- type: 1=时K, 2=日K, 3=周K
- maxTime: 秒时间戳（限制最大时间）
- typeVal: SteamDT 的 ID（这里用于匹配 item_statistics.steamdt_id）
- platform: "ALL"
- specialStyle: ""
"""

import requests
import time
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from decimal import Decimal
import logging
from crawler.config.config import Config
from crawler.database.supabase_client import SupabaseManager
from crawler.database.models import KlineData, KlinePeriod


class ItemKlineCrawler:
    """具体商品 K 线数据爬虫"""

    TYPE_TO_PERIOD = {
        1: KlinePeriod.HOURLY,
        2: KlinePeriod.DAILY,
        3: KlinePeriod.WEEKLY,
    }

    def __init__(self, config: Optional[Config] = None):
        """
        初始化商品 K 线爬虫

        Args:
            config: 配置对象，如果为 None 则从环境变量加载
        """
        self.config = config or Config.from_env()
        self.logger = logging.getLogger(self.__class__.__name__)

        # 通过 Config 初始化 Supabase（如果配置存在）
        if self.config.supabase:
            self.supabase = SupabaseManager(
                url=self.config.supabase.url,
                key=self.config.supabase.key,
            )
        else:
            # 如果 Config 中没有 Supabase 配置，尝试从环境变量初始化
            self.supabase = SupabaseManager()

        self.api_url = "https://api.steamdt.com/user/steam/category/v1/kline"

        # 初始化 requests session
        self.session = requests.Session()

        # 配置代理（如果提供）
        if self.config.crawler.proxy:
            self.session.proxies = {
                "http": self.config.crawler.proxy,
                "https": self.config.crawler.proxy,
            }

        # 设置请求头
        self.session.headers.update(
            {
                "User-Agent": self.config.csqaq.user_agent,
                "Accept": "application/json",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Content-Type": "application/json",
            }
        )

    # ==============================
    # 辅助方法
    # ==============================

    def _get_item_statistics_id_by_steamdt(self, steamdt_id: int) -> Optional[int]:
        """
        根据 steamdt_id 从 item_statistics 表中查找 item_statistics.id
        """
        try:
            result = (
                self.supabase.client.table("item_statistics")
                .select("id")
                .eq("steamdt_id", steamdt_id)
                .limit(1)
                .execute()
            )
            rows = result.data or []
            if not rows:
                self.logger.warning(f"在 item_statistics 中未找到 steamdt_id={steamdt_id} 的记录")
                return None
            return rows[0].get("id")
        except Exception as e:
            self.logger.error(f"查询 item_statistics 失败 (steamdt_id={steamdt_id}): {e}")
            return None

    # ==============================
    # API 请求
    # ==============================

    def fetch_kline_data(
        self,
        kline_type: int,
        type_val: int,
        timestamp: Optional[int] = None,
        max_time: Optional[int] = None,
        platform: str = "ALL",
        special_style: str = "",
    ) -> Optional[List[List[Any]]]:
        """
        从 API 获取商品 K 线数据（GET 请求）

        Args:
            kline_type: K 线类型，1=时K，2=日K，3=周K
            type_val: SteamDT 商品 / 分类 ID（用于 API 查询）
            timestamp: 毫秒时间戳（整数），用于分页；不提供则使用当前时间
            max_time: 最大时间戳（秒），用于限制数据范围
            platform: 平台，默认为 "ALL"
            special_style: 特殊样式，默认为空字符串
        """
        if timestamp is None:
            timestamp = int(time.time() * 1000)

        # GET 请求，参数放在 URL 中
        params = {
            "timestamp": timestamp,
            "type": kline_type,
            "typeVal": type_val,
            "platform": platform,
            "specialStyle": special_style,
        }
        
        if max_time:
            params["maxTime"] = max_time

        try:
            time.sleep(self.config.crawler.delay)

            response = self.session.get(
                self.api_url,
                params=params,
                timeout=self.config.crawler.timeout,
            )
            response.raise_for_status()

            data = response.json()

            if not data.get("success"):
                error_msg = data.get('errorMsg', '未知错误')
                self.logger.error(f"API 返回失败: {error_msg}")
                raise Exception(f"API Error: {error_msg}")

            kline_data = data.get("data", [])
            # 如果 kline_data 为 None，设为空列表
            if kline_data is None:
                kline_data = []

            if not kline_data:
                self.logger.info("API 返回数据为空")
                return []

            self.logger.info(f"成功获取 {len(kline_data)} 条 K 线数据 (type={kline_type}, typeVal={type_val})")
            return kline_data

        except requests.RequestException as e:
            self.logger.error(f"API 请求失败: {e}")
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_data = e.response.json()
                    self.logger.error(f"错误详情: {error_data}")
                except Exception:
                    self.logger.error(f"响应内容: {e.response.text[:500]}")
            raise
        except Exception as e:
            self.logger.error(f"获取 K 线数据失败: {e}")
            raise

    # ==============================
    # 解析与保存
    # ==============================

    def parse_kline_item(
        self, item: List[Any], period: KlinePeriod, item_statistics_id: int
    ) -> Optional[KlineData]:
        """
        解析单条商品 K 线数据为 KlineData 模型

        item: [timestamp, open, close, high, low, volume, turnover]
        """
        try:
            if len(item) < 7:
                self.logger.warning(f"数据格式不正确，期望 7 个字段，实际 {len(item)} 个: {item}")
                return None

            timestamp_str = str(item[0])
            # 安全处理可能为 None 的字段
            open_price = float(item[1]) if item[1] is not None else None
            close_price = float(item[2]) if item[2] is not None else None
            high_price = float(item[3]) if item[3] is not None else None
            low_price = float(item[4]) if item[4] is not None else None
            volume_val = item[5]
            turnover = float(item[6]) if item[6] is not None else None

            # 将时间戳（秒）转换为 datetime (UTC)
            timestamp_seconds = int(timestamp_str)
            # 必须使用 UTC 以确保是 offset-aware，与数据库取出的时间兼容
            timestamp_dt = datetime.fromtimestamp(timestamp_seconds, timezone.utc)

            volume = int(volume_val) if volume_val is not None else None

            return KlineData(
                item_statistics_id=item_statistics_id,
                period=period,
                timestamp=timestamp_dt,
                open_price=Decimal(str(open_price)) if open_price is not None else None,
                close_price=Decimal(str(close_price)) if close_price is not None else None,
                high_price=Decimal(str(high_price)) if high_price is not None else None,
                low_price=Decimal(str(low_price)) if low_price is not None else None,
                volume=volume,
                turnover=Decimal(str(turnover)) if turnover is not None else None,
            )
        except (ValueError, IndexError, TypeError) as e:
            self.logger.error(f"解析 K 线数据失败: {e}, 数据: {item}")
            return None

    def save_kline_data(
        self,
        item_statistics_id: int,
        kline_data: List[List[Any]],
        kline_type: int,
        batch_size: int = 100,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> int:
        """
        保存商品 K 线数据到 kline_data 表
        
        Args:
            start_time: 开始时间，只保存 >= 此时间的数据
            end_time: 结束时间，只保存 <= 此时间的数据
        """
        period_enum = self.TYPE_TO_PERIOD.get(kline_type)
        if not period_enum:
            self.logger.error(f"不支持的 K 线类型: {kline_type}")
            return 0

        # 解析为模型并过滤时间范围
        models: List[KlineData] = []
        filtered_count = 0
        
        for item in kline_data:
            parsed = self.parse_kline_item(item, period_enum, item_statistics_id)
            if parsed:
                # 时间段过滤
                if start_time and parsed.timestamp < start_time:
                    filtered_count += 1
                    continue
                if end_time and parsed.timestamp > end_time:
                    filtered_count += 1
                    continue

                # 数据有效性过滤：过滤掉 volume 或 turnover 为空的无效数据
                if parsed.volume is None or parsed.volume == 0:
                    filtered_count += 1
                    continue
                if parsed.turnover is None or parsed.turnover == 0:
                    filtered_count += 1
                    continue

                models.append(parsed)
        
        if filtered_count > 0:
            self.logger.info(f"过滤掉 {filtered_count} 条数据（时间范围外或无效数据：volume/turnover为空）")

        if not models:
            self.logger.info("没有有效的数据可保存")
            return 0
        
        # 优化：先查询数据库中已存在的记录，避免后面批量插入报错
        try:
            min_ts = min(m.timestamp for m in models)
            max_ts = max(m.timestamp for m in models)
            
            # 查询范围内的现有记录
            existing_query = (
                self.supabase.client.table("kline_data")
                .select("timestamp")
                .eq("item_statistics_id", item_statistics_id)
                .eq("period", period_enum.value)
                .gte("timestamp", min_ts.isoformat())
                .lte("timestamp", max_ts.isoformat())
                .execute()
            )
            
            existing_timestamps = set()
            if existing_query.data:
                # 注意：Supabase 返回的时间字符串可能带不同格式，统一解析处理
                # 这里假设返回的是 ISO 格式，将其转换为 datetime 或者直接对比字符串
                # 为保险起见，我们把数据库查出来的也不转了，因为本地 models 的 timestamps 是 datetime
                # 我们可以把本地的转成 string set，或者把远程的转成 timestamp
                # 简单起见，转成 ISO string 前缀匹配 (去掉毫秒等微小差异)
                # 或者，直接用 datetime 比较。Supabase-py usually returns strings.
                for row in existing_query.data:
                     # 数据库里的 timestamp 字符串
                     ts_str = row.get("timestamp")
                     if ts_str:
                         # 转换为 Python datetime 对象 (带时区)
                         try:
                             # 处理可能的 Z 结尾
                             if ts_str.endswith("Z"):
                                 ts_str = ts_str[:-1] + "+00:00"
                             dt = datetime.fromisoformat(ts_str)
                             existing_timestamps.add(dt)
                         except ValueError:
                             pass
            
            # 过滤掉已存在的
            new_models = []
            for m in models:
                # 简单的存在性检查 (注意时区比较)
                # 如果 m.timestamp 在 existing_timestamps 里
                # 由于浮点数/微秒可能不一致，可以允许微小误差吗？
                # K线数据通常是整点或整天，应该精准匹配。
                found = False
                for existing_ts in existing_timestamps:
                    if abs((m.timestamp - existing_ts).total_seconds()) < 1.0:
                        found = True
                        break
                
                if not found:
                    new_models.append(m)
            
            if len(models) - len(new_models) > 0:
                self.logger.info(f"预先过滤掉 {len(models) - len(new_models)} 条已存在的 K 线记录")
            
            models = new_models
            
            if not models:
                self.logger.info("所有数据均已存在，无需插入")
                return 0
                
        except Exception as e:
            self.logger.warning(f"预查询现有记录失败，回退到直接插入尝试: {e}")

        rows = [m.to_dict() for m in models]
        self.logger.info(f"准备保存 {len(rows)} 条 K 线数据到 kline_data 表 (item_statistics_id={item_statistics_id}, period={period_enum.value})")

        total_inserted = 0
        skipped_count = 0

        for i in range(0, len(rows), batch_size):
            batch = rows[i : i + batch_size]
            try:
                result = self.supabase.insert_batch("kline_data", batch)
                inserted_count = len(result) if result else 0
                total_inserted += inserted_count
                self.logger.debug(
                    f"批量插入 {inserted_count} 条数据 "
                    f"(进度: {min(i + batch_size, len(rows))}/{len(rows)})"
                )
            except Exception as e:
                # 如果还是出错 (比如并发写入)，则回退到逐条
                self.logger.warning(f"批量插入失败: {e}，改为逐条插入...")
                for item in batch:
                    try:
                        self.supabase.insert_data("kline_data", item)
                        total_inserted += 1
                    except Exception as single_e:
                        # 忽略重复错误，记录其他错误
                        if "unique" in str(single_e).lower() or "duplicate" in str(single_e).lower():
                             skipped_count += 1
                        else:
                             self.logger.error(f"插入单条数据失败: {single_e}")
                             skipped_count += 1

        self.logger.info(
            f"成功保存 {total_inserted} 条商品 K 线数据到 kline_data 表"
        )
        return total_inserted

    # ==============================
    # 对外入口
    # ==============================

    def crawl_and_save(
        self,
        kline_type: int,
        type_val: int,
        timestamp: Optional[int] = None,
        max_time: Optional[int] = None,
        platform: str = "ALL",
        special_style: str = "",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> int:
        """
        爬取并保存「单个商品」的 K 线数据

        - 根据 type_val（SteamDT ID）去 item_statistics 表找 item_statistics_id
        - 拉取该商品的 K 线数据
        - 写入 kline_data 表
        
        Args:
            start_time: 开始时间，只保存 >= 此时间的数据
            end_time: 结束时间，只保存 <= 此时间的数据
        """
        # 1. 查 item_statistics_id
        item_statistics_id = self._get_item_statistics_id_by_steamdt(type_val)
        if not item_statistics_id:
            self.logger.warning(f"未找到 steamdt_id={type_val} 对应的 item_statistics 记录，终止。")
            return 0

        # 2. 拉取 K 线数据
        kline_data = self.fetch_kline_data(
            kline_type=kline_type,
            type_val=type_val,
            timestamp=timestamp,
            max_time=max_time,
            platform=platform,
            special_style=special_style,
        )
        if not kline_data:
            return 0

        # 3. 保存到 kline_data 表（传入时间范围过滤）
        return self.save_kline_data(
            item_statistics_id=item_statistics_id,
            kline_data=kline_data,
            kline_type=kline_type,
            start_time=start_time,
            end_time=end_time,
        )


def main():
    """命令行入口示例"""
    import argparse

    parser = argparse.ArgumentParser(description="商品 K 线数据爬虫（写入 kline_data）")
    parser.add_argument(
        "--kline-type",
        type=int,
        required=True,
        choices=[1, 2, 3],
        help="K线类型: 1=时K, 2=日K, 3=周K",
    )
    parser.add_argument(
        "--type-val",
        type=int,
        required=True,
        help="SteamDT 商品 / 分类 ID（对应 item_statistics.steamdt_id）",
    )
    parser.add_argument(
        "--timestamp",
        type=int,
        default=None,
        help="时间戳（毫秒），用于分页。如果不提供，将使用当前时间戳",
    )
    parser.add_argument(
        "--max-time",
        type=int,
        help="最大时间戳（秒），用于限制数据范围",
    )
    parser.add_argument(
        "--platform",
        type=str,
        default="ALL",
        help="平台，默认为 'ALL'",
    )
    parser.add_argument(
        "--special-style",
        type=str,
        default="",
        help="特殊样式，默认为空字符串",
    )

    args = parser.parse_args()

    crawler = ItemKlineCrawler()
    count = crawler.crawl_and_save(
        kline_type=args.kline_type,
        type_val=args.type_val,
        timestamp=args.timestamp,
        max_time=args.max_time,
        platform=args.platform,
        special_style=args.special_style,
    )

    print(f"\n完成！共保存 {count} 条商品 K 线数据到 kline_data 表")


if __name__ == "__main__":
    main()


