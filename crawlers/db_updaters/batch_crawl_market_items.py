"""
批量爬取大盘商品的 K 线和走势数据

功能：
- 从 item_statistics_market_index_relations 表读取指定大盘的商品
- 获取每个商品的 steamdt_id
- 批量调用 item_kline_crawler 和 item_trend_crawler 爬取数据
- 支持配置大盘类型和 max_time
"""
import time
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from crawler.config.config import Config
from crawler.database.supabase_client import SupabaseManager
from crawler.database.models import MarketIndexType
from crawler.crawlers.url_crawlers.item_kline_crawler import ItemKlineCrawler
from crawler.crawlers.url_crawlers.item_trend_crawler import ItemTrendCrawler
from crawler.utils.timestamp_refresher import get_valid_timestamp


class BatchCrawlMarketItems:
    """批量爬取大盘商品的 K 线和走势数据"""
    
    def __init__(self, config: Optional[Config] = None):
        """
        初始化批量爬虫
        
        Args:
            config: 配置对象，如果为 None 则从环境变量加载
        """
        self.config = config or Config.from_env()
        
        # 初始化 Supabase
        if self.config.supabase:
            self.supabase = SupabaseManager(
                url=self.config.supabase.url,
                key=self.config.supabase.key,
            )
        else:
            self.supabase = SupabaseManager()
        
        # 初始化爬虫
        self.kline_crawler = ItemKlineCrawler(self.config)
        self.trend_crawler = ItemTrendCrawler(self.config)
        
        # 当前有效的 timestamp (从 Playwright 获取)
        self.current_timestamp = None
        
        # 设置日志
        self.logger = logging.getLogger("BatchCrawlMarketItems")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def fetch_market_items(
        self,
        market_index_type: MarketIndexType,
        page_size: int = 1000,
        min_created_at: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        从数据库获取指定大盘的商品列表
        
        Args:
            market_index_type: 大盘类型（如 MarketIndexType.QIANZHAN）
            page_size: 每页大小，默认 1000
            
        Returns:
            商品列表，每个商品包含 item_statistics_id 和 steamdt_id
        """
        type_str = market_index_type.value if hasattr(market_index_type, "value") else str(market_index_type)
        if min_created_at:
            self.logger.info(f"开始查询大盘类型为 '{type_str}' 且创建时间 > {min_created_at} 的商品...")
        else:
            self.logger.info(f"开始查询大盘类型为 '{type_str}' 的商品...")
        
        # 第一步：查询关系表获取所有 item_statistics_id
        item_statistics_ids = []
        offset = 0
        
        while True:
            start = offset
            end = offset + page_size - 1
            
            try:
                query = (
                    self.supabase.client.table("item_statistics_market_index_relations")
                    .select("item_statistics_id")
                )
                
                # 如果不是 "all"，才进行过滤
                if market_index_type and str(market_index_type).lower() != "all" and str(market_index_type).lower() != "none":
                    if hasattr(market_index_type, "value"):
                         query = query.eq("market_index_type", market_index_type.value)
                    else:
                         query = query.eq("market_index_type", str(market_index_type))
                
                if min_created_at:
                    query = query.gt("created_at", min_created_at)
                    
                result = query.range(start, end).execute()
                
                records = result.data if result.data else []
                if not records:
                    break
                
                for record in records:
                    item_statistics_id = record.get("item_statistics_id")
                    if item_statistics_id:
                        item_statistics_ids.append(item_statistics_id)
                
                if len(records) < page_size:
                    break
                
                offset += page_size
                
            except Exception as e:
                self.logger.error(f"查询关系表失败 (offset={offset}): {e}")
                break
        
        self.logger.info(f"找到 {len(item_statistics_ids)} 个商品关系记录")
        
        if not item_statistics_ids:
            return []
        
        # 第二步：批量查询 item_statistics 表获取 steamdt_id
        items = []
        offset = 0
        
        while offset < len(item_statistics_ids):
            batch_ids = item_statistics_ids[offset:offset + page_size]
            
            try:
                # 使用 in_ 查询批量获取
                result = (
                    self.supabase.client.table("item_statistics")
                    .select("id,steamdt_id")
                    .in_("id", batch_ids)
                    .not_.is_("steamdt_id", "null")  # 只获取有 steamdt_id 的记录
                    .execute()
                )
                
                records = result.data if result.data else []
                
                for record in records:
                    item_statistics_id = record.get("id")
                    steamdt_id = record.get("steamdt_id")
                    if item_statistics_id and steamdt_id:
                        items.append({
                            "item_statistics_id": item_statistics_id,
                            "steamdt_id": steamdt_id
                        })
                
                offset += page_size
                
            except Exception as e:
                self.logger.error(f"查询 item_statistics 表失败 (offset={offset}): {e}")
                offset += page_size
        
        self.logger.info(f"找到 {len(items)} 个有 steamdt_id 的商品（大盘类型: {type_str}）")
        return items
    
    def crawl_item_kline(
        self,
        steamdt_id: int,
        max_time: int,
        kline_types: List[int] = [1, 2],  # 默认爬取时K和日K
        delay: float = 1.0,
        days: int = 365  # 需要获取的天数，默认365天（一年）
    ) -> Dict[str, int]:
        """
        爬取单个商品的 K 线数据（循环调用以获取指定天数的数据）
        
        Args:
            steamdt_id: SteamDT 商品 ID
            max_time: 最大时间戳（秒）
            kline_types: K 线类型列表，默认 [1, 2]（时K和日K）
            delay: 每次请求之间的延迟（秒）
            days: 需要获取的天数，默认365天（一年）。每次API调用最多返回3个月数据，需要循环调用
            
        Returns:
            统计信息字典
        """
        # 三个月约等于 90 天（秒）
        THREE_MONTHS_SECONDS = 90 * 24 * 60 * 60
        # 计算目标最小时间戳（从 max_time 往前推 days 天）
        target_min_time = max_time - (days * 24 * 60 * 60)
        
        stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "rounds": 0
        }
        
        for kline_type in kline_types:
            current_max_time = max_time
            round_num = 1
            
            self.logger.info(
                f"开始爬取 K 线数据: steamdt_id={steamdt_id}, "
                f"kline_type={kline_type} ({'时K' if kline_type == 1 else '日K' if kline_type == 2 else '周K'}), "
                f"目标时间范围: {days} 天 (从 {datetime.fromtimestamp(target_min_time).strftime('%Y-%m-%d')} 到 {datetime.fromtimestamp(max_time).strftime('%Y-%m-%d')})"
            )
            
            # 循环调用，每次获取三个月的数据
            while current_max_time > target_min_time:
                try:
                    self.logger.info(
                        f"  第 {round_num} 轮: max_time={current_max_time} "
                        f"({datetime.fromtimestamp(current_max_time).strftime('%Y-%m-%d %H:%M:%S')})"
                    )
                    
                    count = self.kline_crawler.crawl_and_save(
                        kline_type=kline_type,
                        type_val=steamdt_id,
                        max_time=current_max_time,
                        platform="ALL",
                        special_style="",
                        timestamp=self.current_timestamp
                    )
                    
                    stats["total"] += count
                    stats["rounds"] += 1
                    
                    if count > 0:
                        stats["success"] += 1
                    else:
                        stats["failed"] += 1
                    
                    # 向前推三个月
                    current_max_time -= THREE_MONTHS_SECONDS
                    
                    # 如果下一轮会超过目标时间，直接设置为目标时间
                    if current_max_time <= target_min_time:
                        # 最后一次，使用目标时间
                        if current_max_time < target_min_time:
                            self.logger.info(
                                f"  最后一轮: max_time={target_min_time} "
                                f"({datetime.fromtimestamp(target_min_time).strftime('%Y-%m-%d %H:%M:%S')})"
                            )
                            
                            count = self.kline_crawler.crawl_and_save(
                                kline_type=kline_type,
                                type_val=steamdt_id,
                                max_time=target_min_time,
                                platform="ALL",
                                special_style="",
                                timestamp=self.current_timestamp
                            )
                            
                            stats["total"] += count
                            stats["rounds"] += 1
                            
                            if count > 0:
                                stats["success"] += 1
                            else:
                                stats["failed"] += 1
                        break
                    
                    round_num += 1
                    
                    # 添加延迟
                    if delay > 0:
                        time.sleep(delay)
                        
                except Exception as e:
                    self.logger.error(f"爬取 K 线数据失败 (steamdt_id={steamdt_id}, kline_type={kline_type}, round={round_num}): {e}")
                    
                    # 失败后尝试获取新 timestamp
                    self.logger.warning("检测到失败，启动 Playwright 获取 timestamp...")
                    new_ts = get_valid_timestamp()
                    if new_ts:
                        self.current_timestamp = new_ts
                        self.logger.info(f"获取 timestamp 成功: {self.current_timestamp}")
                    else:
                        self.logger.warning("获取 timestamp 失败")
                    stats["failed"] += 1
                    # 即使失败也继续下一轮
                    current_max_time -= THREE_MONTHS_SECONDS
                    if current_max_time <= target_min_time:
                        break
                    round_num += 1
                    if delay > 0:
                        time.sleep(delay)
            
            self.logger.info(
                f"K 线数据爬取完成: steamdt_id={steamdt_id}, kline_type={kline_type}, "
                f"共 {stats['rounds']} 轮, 总记录数 {stats['total']}"
            )
            
            # K 线类型之间的延迟
            if delay > 0:
                time.sleep(delay)
        
        return stats
    
    def crawl_item_trend(
        self,
        steamdt_id: int,
        type_days: List[int] = [1],  # 默认只爬取近一月
        delay: float = 1.0
    ) -> Dict[str, int]:
        """
        爬取单个商品的走势数据
        
        Args:
            steamdt_id: SteamDT 商品 ID
            type_days: 时间范围列表，默认 [1]（近一月）
                       1=近一月，2=三个月，3=六个月，4=一年，5=三年
            delay: 每次请求之间的延迟（秒）
            
        Returns:
            统计信息字典
        """
        stats = {
            "total": 0,
            "success": 0,
            "failed": 0
        }
        
        for type_day in type_days:
            try:
                self.logger.info(
                    f"爬取走势数据: steamdt_id={steamdt_id}, "
                    f"type_day={type_day} ({'近一月' if type_day == 1 else '三个月' if type_day == 2 else '六个月' if type_day == 3 else '一年' if type_day == 4 else '三年'})"
                )
                
                count = self.trend_crawler.crawl_and_save(
                    item_id=steamdt_id,
                    type_day=type_day,
                    platform="ALL",
                    special_style="",
                    timestamp=self.current_timestamp
                )
                
                stats["total"] += count
                if count > 0:
                    stats["success"] += 1
                else:
                    stats["failed"] += 1
                
                # 添加延迟
                if delay > 0:
                    time.sleep(delay)
                    
            except Exception as e:
                self.logger.error(f"爬取走势数据失败 (steamdt_id={steamdt_id}, type_day={type_day}): {e}")
                
                 # 失败后尝试获取新 timestamp
                self.logger.warning("检测到失败，启动 Playwright 获取 timestamp...")
                new_ts = get_valid_timestamp()
                if new_ts:
                    self.current_timestamp = new_ts
                    self.logger.info(f"获取 timestamp 成功: {self.current_timestamp}")
                else:
                    self.logger.warning("获取 timestamp 失败")
                stats["failed"] += 1
        
        return stats
    
    def crawl_all_items(
        self,
        market_index_type: MarketIndexType = MarketIndexType.QIANZHAN,
        max_time: Optional[int] = None,
        max_date: str = "2025-12-03",
        kline_types: List[int] = [1, 2],
        type_days: List[int] = [1],
        delay: float = 1.0,

        limit: Optional[int] = None,
        min_created_at: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        批量爬取所有商品的 K 线和走势数据
        
        Args:
            market_index_type: 大盘类型，默认 QIANZHAN
            max_time: 最大时间戳（秒），如果不提供则使用 max_date 计算
            max_date: 最大日期字符串（格式：YYYY-MM-DD），默认 "2025-12-03"
            kline_types: K 线类型列表，默认 [1, 2]（时K和日K）
            type_days: 走势时间范围列表，默认 [1]（近一月）
            delay: 每次请求之间的延迟（秒）
            limit: 限制处理的商品数量（用于测试），None 表示处理所有
            
        Returns:
            统计信息字典
        """
        # 计算 max_time
        if max_time is None:
            try:
                max_date_dt = datetime.strptime(max_date, "%Y-%m-%d")
                max_time = int(max_date_dt.timestamp())
                self.logger.info(f"使用 max_date={max_date} 计算 max_time={max_time}")
            except ValueError as e:
                self.logger.error(f"日期格式错误: {max_date}, 错误: {e}")
                return {"success": False, "error": f"日期格式错误: {max_date}"}
        
        # 根据 type_days 计算需要的天数（用于 K 线数据）
        # type_day 映射：1=近一月(30天), 2=三个月(90天), 3=六个月(180天), 4=一年(365天), 5=三年(1095天)
        type_day_to_days = {
            1: 30,
            2: 90,
            3: 180,
            4: 365,
            5: 1095
        }
        # 取最大的天数，确保 K 线数据覆盖所有走势数据的时间范围
        kline_days = max([type_day_to_days.get(td, 365) for td in type_days]) if type_days else 365
        
        self.logger.info("=" * 60)
        self.logger.info("开始批量爬取大盘商品数据")
        type_str = market_index_type.value if hasattr(market_index_type, "value") else str(market_index_type)
        self.logger.info(f"大盘类型: {type_str}")
        self.logger.info(f"最大时间戳: {max_time} ({datetime.fromtimestamp(max_time).strftime('%Y-%m-%d %H:%M:%S')})")
        self.logger.info(f"K 线类型: {kline_types}")
        self.logger.info(f"走势时间范围: {type_days}")
        self.logger.info(f"K 线数据时间范围: {kline_days} 天（自动匹配走势数据范围）")
        self.logger.info("=" * 60)
        
        # 获取商品列表
        items = self.fetch_market_items(
            market_index_type=market_index_type, 
            min_created_at=min_created_at
        )
        
        if not items:
            self.logger.warning("未找到任何商品")
            return {
                "success": False,
                "error": "未找到任何商品",
                "total_items": 0
            }
        
        # 限制数量（如果指定）
        if limit and limit > 0:
            items = items[:limit]
            self.logger.info(f"限制处理数量为 {limit} 个商品")
        
        total_items = len(items)
        self.logger.info(f"准备处理 {total_items} 个商品\n")
        
        # 统计信息
        result = {
            "success": True,
            "total_items": total_items,
            "processed_items": 0,
            "kline_stats": {
                "total": 0,
                "success": 0,
                "failed": 0,
                "rounds": 0
            },
            "trend_stats": {
                "total": 0,
                "success": 0,
                "failed": 0
            },
            "item_errors": []
        }
        
        # 逐个处理商品
        for i, item in enumerate(items, 1):
            item_statistics_id = item["item_statistics_id"]
            steamdt_id = item["steamdt_id"]
            
            self.logger.info(f"\n[{i}/{total_items}] 处理商品: item_statistics_id={item_statistics_id}, steamdt_id={steamdt_id}")
            
            item_error = None
            
            # 爬取 K 线数据（循环调用以获取指定天数的数据）
            try:
                kline_stats = self.crawl_item_kline(
                    steamdt_id=steamdt_id,
                    max_time=max_time,
                    kline_types=kline_types,
                    delay=delay,
                    days=kline_days
                )
                result["kline_stats"]["total"] += kline_stats["total"]
                result["kline_stats"]["success"] += kline_stats["success"]
                result["kline_stats"]["failed"] += kline_stats["failed"]
                result["kline_stats"]["rounds"] += kline_stats.get("rounds", 0)
            except Exception as e:
                self.logger.error(f"处理 K 线数据失败: {e}")
                item_error = f"K线数据失败: {str(e)}"
                result["kline_stats"]["failed"] += len(kline_types)
            
            # 爬取走势数据
            try:
                trend_stats = self.crawl_item_trend(
                    steamdt_id=steamdt_id,
                    type_days=type_days,
                    delay=delay
                )
                result["trend_stats"]["total"] += trend_stats["total"]
                result["trend_stats"]["success"] += trend_stats["success"]
                result["trend_stats"]["failed"] += trend_stats["failed"]
            except Exception as e:
                self.logger.error(f"处理走势数据失败: {e}")
                if item_error:
                    item_error += f"; 走势数据失败: {str(e)}"
                else:
                    item_error = f"走势数据失败: {str(e)}"
                result["trend_stats"]["failed"] += len(type_days)
            
            if item_error:
                result["item_errors"].append({
                    "item_statistics_id": item_statistics_id,
                    "steamdt_id": steamdt_id,
                    "error": item_error
                })
            
            result["processed_items"] += 1
            
            # 商品之间的延迟
            if i < total_items and delay > 0:
                time.sleep(delay)
        
        # 打印总结
        self.logger.info("\n" + "=" * 60)
        self.logger.info("批量爬取完成")
        self.logger.info("=" * 60)
        self.logger.info(f"总商品数: {result['total_items']}")
        self.logger.info(f"已处理: {result['processed_items']}")
        self.logger.info(f"\nK 线数据统计:")
        self.logger.info(f"  总记录数: {result['kline_stats']['total']}")
        self.logger.info(f"  总轮数: {result['kline_stats'].get('rounds', 0)}")
        self.logger.info(f"  成功: {result['kline_stats']['success']}")
        self.logger.info(f"  失败: {result['kline_stats']['failed']}")
        self.logger.info(f"\n走势数据统计:")
        self.logger.info(f"  总记录数: {result['trend_stats']['total']}")
        self.logger.info(f"  成功: {result['trend_stats']['success']}")
        self.logger.info(f"  失败: {result['trend_stats']['failed']}")
        
        if result["item_errors"]:
            self.logger.warning(f"\n处理失败的商品数: {len(result['item_errors'])}")
            self.logger.warning("失败商品示例（前5个）:")
            for error_item in result["item_errors"][:5]:
                self.logger.warning(f"  steamdt_id={error_item['steamdt_id']}: {error_item['error']}")
        
        return result


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="批量爬取大盘商品的 K 线和走势数据")
    parser.add_argument(
        "--market-type",
        type=str,
        default="qianzhan",
        choices=["total", "qianzhan", "agent","baizhan", "all"],
        help="大盘类型（默认: qianzhan）"
    )
    parser.add_argument(
        "--max-date",
        type=str,
        default="2025-12-03",
        help="最大日期（格式：YYYY-MM-DD，默认: 2025-12-03）"
    )
    parser.add_argument(
        "--max-time",
        type=int,
        default=None,
        help="最大时间戳（秒），如果不提供则使用 --max-date 计算"
    )
    parser.add_argument(
        "--kline-types",
        type=int,
        nargs="+",
        default=[1, 2],
        choices=[1, 2, 3],
        help="K 线类型列表（默认: 1 2，即时K和日K）"
    )
    parser.add_argument(
        "--type-days",
        type=int,
        nargs="+",
        default=[1],
        choices=[1, 2, 3, 4, 5],
        help="走势时间范围列表（默认: 1，即近一月）"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="每次请求之间的延迟（秒，默认: 1.0）"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="限制处理的商品数量（用于测试），不指定则处理所有"
    )
    parser.add_argument(
        "--min-created-at",
        type=str,
        default=None,
        help="最小创建时间（格式: YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS），只爬取在此之后创建的关联关系"
    )
    
    args = parser.parse_args()
    
    # 转换大盘类型
    market_type_map = {
        "total": MarketIndexType.TOTAL,
        "qianzhan": MarketIndexType.QIANZHAN,
        "agent": MarketIndexType.AGENT,
        "baizhan": MarketIndexType.BAIZHAN,
        "all": "all"
    }
    market_index_type = market_type_map[args.market_type]
    
    # 创建批量爬虫
    batch_crawler = BatchCrawlMarketItems()
    
    # 执行爬取
    result = batch_crawler.crawl_all_items(
        market_index_type=market_index_type,
        max_time=args.max_time,
        max_date=args.max_date,
        kline_types=args.kline_types,
        type_days=args.type_days,

        delay=args.delay,
        limit=args.limit,
        min_created_at=args.min_created_at
    )
    
    if result["success"]:
        print(f"\n✅ 成功！")
        print(f"处理了 {result['processed_items']}/{result['total_items']} 个商品")
        print(f"K 线数据: {result['kline_stats']['total']} 条")
        print(f"走势数据: {result['trend_stats']['total']} 条")
    else:
        print(f"\n❌ 失败！错误: {result.get('error', '未知错误')}")


if __name__ == "__main__":
    main()

