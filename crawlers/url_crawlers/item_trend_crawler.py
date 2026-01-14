"""
商品走势（trend_data）爬虫

从 steamdt.com API 获取「具体商品」的走势数据，并写入 Supabase 的 trend_data 表。

逻辑：
- 通过 itemId（SteamDT 商品 ID）去 item_statistics 表查找 steamdt_id 对应的 item_statistics.id
- 调用 SteamDT 的商品走势接口获取数据
- 将数据解析为 TrendData 模型，写入 trend_data 表，填充 item_statistics_id

API 示例（参考自搜索结果）：
https://api.steamdt.com/user/steam/type-trend/v2/item/details?timestamp=1764749386230

请求方式：POST
请求体 JSON：
- timestamp: "1764749386230"          # 毫秒字符串
- platform: "ALL"
- typeDay: "1"                         # 1近一月，2三个月，3六个月，4一年，5三年
- dateType: 3                          # 目前固定为 3
- specialStyle: ""
- itemId: "295893123"                  # SteamDT 商品 ID

返回 data 中每一条记录格式：
["1762189158", 5250, 1086, 5400, 262, 10647, 2, "24572"]
依次为：
- 时间戳（秒字符串）
- 价格 price
- 在售数量 items_for_sale
- 求购价格 buying_price
- 求购数量 buy_orders
- 成交额 turnover
- 成交量 transaction_volume
- 存世量 circulation
"""

import requests
import time
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from decimal import Decimal

import logging
from crawler.config.config import Config
from crawler.database.supabase_client import SupabaseManager
from crawler.database.models import TrendData, KlinePeriod


class ItemTrendCrawler:
    """具体商品走势数据爬虫"""

    @staticmethod
    def determine_period(type_day: int) -> KlinePeriod:
        """
        根据 typeDay 参数确定数据粒度
        
        根据实际测试结果：
        - typeDay 1-2 (近一月、三个月): 返回小时级数据（每天 ~24 条）
        - typeDay 3-5 (六个月、一年、三年): 返回日级数据（每天 1 条）
        
        Args:
            type_day: 时间范围 (1=近一月, 2=三个月, 3=六个月, 4=一年, 5=三年)
            
        Returns:
            KlinePeriod.HOURLY 或 KlinePeriod.DAILY
        """
        if type_day in [1, 2]:
            return KlinePeriod.HOURLY
        else:
            return KlinePeriod.DAILY

    def __init__(self, config: Optional[Config] = None):
        """
        初始化商品走势爬虫

        Args:
            config: 配置对象，如果为 None 则从环境变量加载
        """
        self.config = config or Config.from_env()
        self.logger = logging.getLogger(self.__class__.__name__)

        # 初始化 Supabase
        if self.config.supabase:
            self.supabase = SupabaseManager(
                url=self.config.supabase.url,
                key=self.config.supabase.key,
            )
        else:
            self.supabase = SupabaseManager()

        self.api_url = "https://api.steamdt.com/user/steam/type-trend/v2/item/details"

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
            rows = result.data or []
            if not rows:
                self.logger.warning(f"在 item_statistics 中未找到 steamdt_id={steamdt_id} 的记录")
                return None
            return rows[0].get("id")
        except Exception as e:
            self.logger.error(f"查询 item_statistics 失败 (steamdt_id={steamdt_id}): {e}")
            return None
    
    def get_last_trend_timestamp(
        self,
        item_statistics_id: int,
        type_day: int
    ) -> Optional[datetime]:
        """
        获取指定商品和 type_day 的最后更新时间
        
        Args:
            item_statistics_id: 商品统计 ID
            type_day: 时间范围
            
        Returns:
            最后更新时间，如果没有数据则返回 None
        """
        period = self.determine_period(type_day)
        
        try:
            result = (
                self.supabase.client.table("trend_data")
                .select("timestamp")
                .eq("item_statistics_id", item_statistics_id)
                .eq("period", period.value)
                .order("timestamp", desc=True)
                .limit(1)
                .execute()
            )
            
            if result.data and len(result.data) > 0:
                timestamp_str = result.data[0]["timestamp"]
                # 处理时区信息
                if timestamp_str.endswith('Z'):
                    timestamp_str = timestamp_str.replace('Z', '+00:00')
                return datetime.fromisoformat(timestamp_str)
            
            
            return None
        except Exception as e:
            self.logger.error(f"查询最新趋势数据时间戳失败: {e}")
            return None

    # ==============================
    # API 请求
    # ==============================

    def fetch_trend_data(
        self,
        item_id: int,
        type_day: int = 1,
        timestamp: Optional[int] = None,
        date_type: int = 3,
        platform: str = "ALL",
        special_style: str = "",
    ) -> Optional[List[List[Any]]]:
        """
        从 API 获取商品走势数据（POST 请求）

        Args:
            item_id: SteamDT 商品 ID（用于 API 参数 itemId，同时用于匹配 steamdt_id）
            type_day: 1近一月，2三个月，3六个月，4一年，5三年
            timestamp: 毫秒时间戳（整数），不提供则使用当前时间
            date_type: 目前固定为 3
            platform: 平台，默认 "ALL"
            special_style: 特殊样式，默认为空字符串
        """
        if timestamp is None:
            timestamp = int(time.time() * 1000)

        json_data = {
            "timestamp": str(timestamp),
            "platform": platform,
            "typeDay": str(type_day),
            "dateType": date_type,
            "specialStyle": special_style,
            "itemId": str(item_id),
        }

        params = {
            "timestamp": timestamp,
        }

        try:
            time.sleep(self.config.crawler.delay)

            response = self.session.post(
                self.api_url,
                params=params,
                json=json_data,
                timeout=self.config.crawler.timeout,
            )
            response.raise_for_status()

            data = response.json()

            if not data.get("success"):
                error_msg = data.get('errorMsg', '未知错误')
                self.logger.error(f"API 返回失败: {error_msg}")
                raise Exception(f"API Error: {error_msg}")

            trend_data = data.get("data", [])
            # 如果 trend_data 为 None，设为空列表
            if trend_data is None:
                trend_data = []

            if not trend_data:
                self.logger.info("API 返回数据为空")
                return []

            self.logger.info(
                f"成功获取 {len(trend_data)} 条走势数据 "
                f"(itemId={item_id}, typeDay={type_day}, dateType={date_type})"
            )
            return trend_data

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
            self.logger.error(f"获取走势数据失败: {e}")
            raise

    # ==============================
    # 解析与保存
    # ==============================

    def parse_trend_item(
        self, item: List[Any], period: KlinePeriod, item_statistics_id: int
    ) -> Optional[TrendData]:
        """
        解析单条走势数据为 TrendData 模型

        item: ["timestamp", price, items_for_sale, buying_price, buy_orders, turnover, transaction_volume, circulation]
        """
        try:
            if len(item) < 8:
                self.logger.warning(f"数据格式不正确，期望 8 个字段，实际 {len(item)} 个: {item}")
                return None

            timestamp_str = str(item[0])
            price = float(item[1]) if item[1] is not None else None
            items_for_sale = int(item[2]) if item[2] is not None else None
            buying_price = float(item[3]) if item[3] is not None else None
            buy_orders = int(item[4]) if item[4] is not None else None
            turnover = float(item[5]) if item[5] is not None else None
            transaction_volume = int(item[6]) if item[6] is not None else None
            circulation_str = item[7]
            circulation = int(circulation_str) if circulation_str not in (None, "") else None

            # 将时间戳（秒）转换为 datetime (UTC)
            timestamp_seconds = int(timestamp_str)
            # 必须使用 UTC 以确保是 offset-aware，与数据库取出的时间兼容
            timestamp_dt = datetime.fromtimestamp(timestamp_seconds, timezone.utc)

            return TrendData(
                item_statistics_id=item_statistics_id,
                period=period,
                timestamp=timestamp_dt,
                price=Decimal(str(price)) if price is not None else None,
                items_for_sale=items_for_sale,
                buying_price=Decimal(str(buying_price)) if buying_price is not None else None,
                buy_orders=buy_orders,
                circulation=circulation,
                transaction_volume=transaction_volume,
                turnover=Decimal(str(turnover)) if turnover is not None else None,
            )
        except (ValueError, IndexError, TypeError) as e:
            self.logger.error(f"解析走势数据失败: {e}, 数据: {item}")
            return None

    def save_trend_data(
        self,
        item_statistics_id: int,
        trend_data: List[List[Any]],
        type_day: int,
        date_type: int = 3,
        batch_size: int = 100,
        min_timestamp: Optional[datetime] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> int:
        """
        保存走势数据到 trend_data 表

        根据 typeDay 参数动态确定 period：
        - typeDay 1-2: HOURLY（小时级数据）
        - typeDay 3-5: DAILY（日级数据）
        
        Args:
            min_timestamp: 最小时间戳，只保存大于此时间的数据（用于增量更新）
            start_time: 开始时间，只保存 >= 此时间的数据
            end_time: 结束时间，只保存 <= 此时间的数据
        """
        period = self.determine_period(type_day)

        models: List[TrendData] = []
        filtered_count = 0
        for item in trend_data:
            parsed = self.parse_trend_item(item, period, item_statistics_id)
            if parsed:
                # 增量更新过滤
                if min_timestamp is not None and parsed.timestamp <= min_timestamp:
                    filtered_count += 1
                    continue
                
                # 时间段过滤
                if start_time and parsed.timestamp < start_time:
                    filtered_count += 1
                    continue
                if end_time and parsed.timestamp > end_time:
                    filtered_count += 1
                    continue

                # 数据有效性过滤：过滤掉 transaction_volume 或 turnover 为空的无效数据
                if parsed.transaction_volume is None or parsed.transaction_volume == 0:
                    filtered_count += 1
                    continue
                if parsed.turnover is None or parsed.turnover == 0:
                    filtered_count += 1
                    continue

                models.append(parsed)

        if filtered_count > 0:
            if min_timestamp:
                self.logger.info(f"过滤掉 {filtered_count} 条数据（<= {min_timestamp} 或不在时间范围 [{start_time} ~ {end_time}] 内，或无效数据：transaction_volume/turnover为空）")
            else:
                self.logger.info(f"过滤掉 {filtered_count} 条数据（不在时间范围 [{start_time} ~ {end_time}] 内，或无效数据：transaction_volume/turnover为空）")
        
        if not models:
            self.logger.info("没有需要更新的走势数据")
            return 0

        rows = [m.to_dict() for m in models]
        self.logger.info(
            f"准备保存 {len(rows)} 条走势数据到 trend_data 表 "
            f"(item_statistics_id={item_statistics_id}, period={period.value}, typeDay={type_day}, dateType={date_type})"
        )

        total_inserted = 0
        skipped_count = 0

        for i in range(0, len(rows), batch_size):
            batch = rows[i : i + batch_size]
            try:
                result = self.supabase.insert_batch("trend_data", batch)
                inserted_count = len(result) if result else 0
                total_inserted += inserted_count
                skipped_count += len(batch) - inserted_count
                self.logger.debug(
                    f"批量插入 {inserted_count} 条数据 "
                    f"(进度: {min(i + batch_size, len(rows))}/{len(rows)})"
                )
            except Exception as e:
                error_msg = str(e).lower()
                # 唯一约束冲突：item_statistics_id + period + timestamp
                if "unique" in error_msg or "duplicate" in error_msg or "23505" in error_msg:
                    self.logger.warning("批量插入遇到唯一约束冲突，改为逐条插入（只保存不存在的记录）...")
                    for item in batch:
                        try:
                            self.supabase.insert_data("trend_data", item)
                            total_inserted += 1
                        except Exception as single_e:
                            single_error = str(single_e).lower()
                            if (
                                "unique" in single_error
                                or "duplicate" in single_error
                                or "23505" in single_error
                            ):
                                skipped_count += 1
                                continue
                            else:
                                self.logger.error(f"插入单条数据失败: {single_e}")
                                skipped_count += 1
                else:
                    self.logger.warning(f"批量插入失败: {e}，改为逐条插入...")
                    for item in batch:
                        try:
                            self.supabase.insert_data("trend_data", item)
                            total_inserted += 1
                        except Exception as single_e:
                            single_error = str(single_e).lower()
                            if (
                                "unique" in single_error
                                or "duplicate" in single_error
                                or "23505" in single_error
                            ):
                                skipped_count += 1
                                continue
                            else:
                                self.logger.error(f"插入单条数据失败: {single_e}")
                                skipped_count += 1

        self.logger.info(
            f"成功保存 {total_inserted} 条走势数据到 trend_data 表，"
            f"跳过 {skipped_count} 条已存在的记录"
        )
        return total_inserted

    # ==============================
    # 对外入口
    # ==============================

    def crawl_and_save(
        self,
        item_id: int,
        type_day: int = 1,
        timestamp: Optional[int] = None,
        date_type: int = 3,
        platform: str = "ALL",
        special_style: str = "",
        incremental: bool = True,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> int:
        """
        爬取并保存「单个商品」的走势数据

        - 根据 itemId（SteamDT ID）去 item_statistics 表找对应的 steamdt_id -> item_statistics_id
        - 拉取该商品的走势数据
        - 写入 trend_data 表
        
        Args:
            incremental: 是否启用增量更新（默认 True）
            start_time: 开始时间，只保存 >= 此时间的数据
            end_time: 结束时间，只保存 <= 此时间的数据
        """
        # 1. 查 item_statistics_id（使用 steamdt_id=itemId）
        item_statistics_id = self._get_item_statistics_id_by_steamdt(item_id)
        if not item_statistics_id:
            self.logger.warning(f"未找到 steamdt_id={item_id} 对应的 item_statistics 记录，终止。")
            return 0
        
        # 2. 获取最新时间戳（如果启用增量更新）
        min_timestamp = None
        if incremental:
            min_timestamp = self.get_last_trend_timestamp(item_statistics_id, type_day)
            if min_timestamp:
                self.logger.info(f"增量更新：只保存 {min_timestamp} 之后的数据")

        # 3. 拉取走势数据
        trend_data = self.fetch_trend_data(
            item_id=item_id,
            type_day=type_day,
            timestamp=timestamp,
            date_type=date_type,
            platform=platform,
            special_style=special_style,
        )
        if not trend_data:
            return 0

        # 4. 保存到 trend_data 表（传入 min_timestamp 和时间范围用于过滤）
        return self.save_trend_data(
            item_statistics_id=item_statistics_id,
            trend_data=trend_data,
            type_day=type_day,
            date_type=date_type,
            min_timestamp=min_timestamp,
            start_time=start_time,
            end_time=end_time,
        )


def main():
    """命令行入口示例"""
    import argparse

    parser = argparse.ArgumentParser(description="商品走势数据爬虫（写入 trend_data）")
    parser.add_argument(
        "--item-id",
        type=int,
        required=True,
        help="SteamDT 商品 ID（对应 item_statistics.steamdt_id）",
    )
    parser.add_argument(
        "--type-day",
        type=int,
        default=1,
        choices=[1, 2, 3, 4, 5],
        help="时间范围: 1=近一月, 2=三个月, 3=六个月, 4=一年, 5=三年（默认: 1）",
    )
    parser.add_argument(
        "--timestamp",
        type=int,
        default=None,
        help="时间戳（毫秒），用于 API 请求。如果不提供，将使用当前时间戳",
    )
    parser.add_argument(
        "--date-type",
        type=int,
        default=3,
        help="dateType 参数，默认为 3（按接口文档固定）",
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

    crawler = ItemTrendCrawler()
    count = crawler.crawl_and_save(
        item_id=args.item_id,
        type_day=args.type_day,
        timestamp=args.timestamp,
        date_type=args.date_type,
        platform=args.platform,
        special_style=args.special_style,
    )

    print(f"\n完成！共保存 {count} 条走势数据到 trend_data 表")


if __name__ == "__main__":
    main()


