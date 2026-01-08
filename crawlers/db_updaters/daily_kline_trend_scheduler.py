"""
每日自动爬取 K 线和趋势数据的调度器

功能：
- 使用 APScheduler 在每天 00:00 自动运行
- 从 item_statistics_market_index_relations 表按 item_statistics_id 顺序获取商品
- 增量更新：只拉取缺失或过时的数据
- 支持守护进程模式和一次性执行模式
"""
import time
import logging
import signal
import sys
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from crawler.config.config import Config
from crawler.database.supabase_client import SupabaseManager
from crawler.database.models import MarketIndexType
from crawler.crawlers.url_crawlers.item_kline_crawler import ItemKlineCrawler
from crawler.crawlers.url_crawlers.item_trend_crawler import ItemTrendCrawler


class DailyKlineTrendScheduler:
    """每日 K 线和趋势数据自动爬取调度器"""
    
    def __init__(
        self,
        config: Optional[Config] = None,
        market_index_type: Optional[MarketIndexType] = None,
        kline_types: List[int] = [2],  # 默认只爬取日K
        type_days: List[int] = [1],    # 默认只爬取近一月
        delay: float = 1.0,
        batch_size: int = 100
    ):
        """
        初始化调度器
        
        Args:
            config: 配置对象，如果为 None 则从环境变量加载
            market_index_type: 大盘类型，None 表示所有商品
            kline_types: K 线类型列表，默认 [2]（日K）
            type_days: 走势时间范围列表，默认 [1]（近一月）
            delay: 每次请求之间的延迟（秒）
            batch_size: 每批处理的商品数量
        """
        self.config = config or Config.from_env()
        self.market_index_type = market_index_type
        self.kline_types = kline_types
        self.type_days = type_days
        self.delay = delay
        self.batch_size = batch_size
        
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
        
        # 设置日志
        self.logger = logging.getLogger("DailyKlineTrendScheduler")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        
        # 调度器
        self.scheduler = None
    
    def fetch_items_to_crawl(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        从数据库获取需要爬取的商品列表，按 item_statistics_id 排序
        
        Args:
            limit: 限制数量，None 表示获取所有
            
        Returns:
            商品列表，每个商品包含 item_statistics_id 和 steamdt_id
        """
        self.logger.info("开始获取需要爬取的商品列表...")
        
        items = []
        offset = 0
        page_size = 1000
        
        while True:
            start = offset
            end = offset + page_size - 1
            
            try:
                # 构建查询
                query = (
                    self.supabase.client.table("item_statistics_market_index_relations")
                    .select("item_statistics_id")
                )
                
                # 如果指定了大盘类型，添加过滤条件
                if self.market_index_type:
                    query = query.eq("market_index_type", self.market_index_type.value)
                
                # 按 item_statistics_id 排序并分页
                result = (
                    query
                    .order("item_statistics_id")
                    .range(start, end)
                    .execute()
                )
                
                records = result.data if result.data else []
                if not records:
                    break
                
                # 提取 item_statistics_id（去重）
                for record in records:
                    item_statistics_id = record.get("item_statistics_id")
                    if item_statistics_id and not any(
                        item["item_statistics_id"] == item_statistics_id for item in items
                    ):
                        items.append({"item_statistics_id": item_statistics_id})
                
                if len(records) < page_size:
                    break
                
                offset += page_size
                
                # 如果设置了限制且已达到，退出
                if limit and len(items) >= limit:
                    items = items[:limit]
                    break
                
            except Exception as e:
                self.logger.error(f"查询关系表失败 (offset={offset}): {e}")
                break
        
        self.logger.info(f"找到 {len(items)} 个商品关系记录")
        
        if not items:
            return []
        
        # 批量查询 item_statistics 表获取 steamdt_id 和商品名称
        item_statistics_ids = [item["item_statistics_id"] for item in items]
        items_with_steamdt = []
        offset = 0
        
        while offset < len(item_statistics_ids):
            batch_ids = item_statistics_ids[offset:offset + page_size]
            
            try:
                result = (
                    self.supabase.client.table("item_statistics")
                    .select("id,steamdt_id,name")
                    .in_("id", batch_ids)
                    .not_.is_("steamdt_id", "null")
                    .execute()
                )
                
                records = result.data if result.data else []
                
                for record in records:
                    item_statistics_id = record.get("id")
                    steamdt_id = record.get("steamdt_id")
                    name = record.get("name", "未知商品")
                    if item_statistics_id and steamdt_id:
                        items_with_steamdt.append({
                            "item_statistics_id": item_statistics_id,
                            "steamdt_id": steamdt_id,
                            "name": name
                        })
                
                offset += page_size
                
            except Exception as e:
                self.logger.error(f"查询 item_statistics 表失败 (offset={offset}): {e}")
                offset += page_size
        
        self.logger.info(f"找到 {len(items_with_steamdt)} 个有 steamdt_id 的商品")
        return items_with_steamdt
    
    def get_last_kline_timestamp(
        self,
        item_statistics_id: int,
        kline_type: int
    ) -> Optional[datetime]:
        """
        获取指定商品和 K 线类型的最后更新时间
        
        Args:
            item_statistics_id: 商品统计 ID
            kline_type: K 线类型（1=时K, 2=日K, 3=周K）
            
        Returns:
            最后更新时间，如果没有记录则返回 None
        """
        period_map = {1: "hourly", 2: "daily", 3: "weekly"}
        period = period_map.get(kline_type)
        
        if not period:
            return None
        
        try:
            result = (
                self.supabase.client.table("kline_data")
                .select("timestamp")
                .eq("item_statistics_id", item_statistics_id)
                .eq("period", period)
                .order("timestamp", desc=True)
                .limit(1)
                .execute()
            )
            
            records = result.data if result.data else []
            if records:
                timestamp_str = records[0].get("timestamp")
                if timestamp_str:
                    return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            
            return None
            
        except Exception as e:
            self.logger.error(
                f"查询最后 K 线时间戳失败 "
                f"(item_statistics_id={item_statistics_id}, period={period}): {e}"
            )
            return None
    
    def get_last_trend_timestamp(self, item_statistics_id: int) -> Optional[datetime]:
        """
        获取指定商品的最后走势数据更新时间
        
        Args:
            item_statistics_id: 商品统计 ID
            
        Returns:
            最后更新时间，如果没有记录则返回 None
        """
        try:
            result = (
                self.supabase.client.table("trend_data")
                .select("timestamp")
                .eq("item_statistics_id", item_statistics_id)
                .order("timestamp", desc=True)
                .limit(1)
                .execute()
            )
            
            records = result.data if result.data else []
            if records:
                timestamp_str = records[0].get("timestamp")
                if timestamp_str:
                    return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            
            return None
            
        except Exception as e:
            self.logger.error(
                f"查询最后走势时间戳失败 (item_statistics_id={item_statistics_id}): {e}"
            )
            return None
    
    def should_update_kline(
        self,
        item_statistics_id: int,
        kline_type: int
    ) -> tuple[bool, Optional[int]]:
        """
        判断是否需要更新 K 线数据，并返回应该使用的 max_time
        
        Args:
            item_statistics_id: 商品统计 ID
            kline_type: K 线类型
            
        Returns:
            (是否需要更新, max_time)
        """
        last_timestamp = self.get_last_kline_timestamp(item_statistics_id, kline_type)
        
        # 如果没有记录，需要全量更新
        if last_timestamp is None:
            self.logger.info(
                f"商品 {item_statistics_id} 的 K 线类型 {kline_type} 没有历史数据，需要全量更新"
            )
            return True, int(datetime.now(timezone.utc).timestamp())
        
        # 计算距离现在的时间差
        now = datetime.now(timezone.utc)
        time_diff = now - last_timestamp
        
        # 根据 K 线类型判断是否需要更新
        # 时K：超过 1 小时更新
        # 日K：超过 1 天更新
        # 周K：超过 7 天更新
        update_thresholds = {
            1: timedelta(hours=1),
            2: timedelta(days=1),
            3: timedelta(days=7)
        }
        
        threshold = update_thresholds.get(kline_type, timedelta(days=1))
        
        if time_diff > threshold:
            self.logger.info(
                f"商品 {item_statistics_id} 的 K 线类型 {kline_type} "
                f"最后更新时间为 {last_timestamp}，需要增量更新"
            )
            return True, int(now.timestamp())
        else:
            self.logger.info(
                f"商品 {item_statistics_id} 的 K 线类型 {kline_type} "
                f"最后更新时间为 {last_timestamp}，无需更新"
            )
            return False, None
    
    def should_update_trend(self, item_statistics_id: int) -> bool:
        """
        判断是否需要更新走势数据
        
        Args:
            item_statistics_id: 商品统计 ID
            
        Returns:
            是否需要更新
        """
        last_timestamp = self.get_last_trend_timestamp(item_statistics_id)
        
        # 如果没有记录，需要更新
        if last_timestamp is None:
            self.logger.info(f"商品 {item_statistics_id} 没有走势数据，需要更新")
            return True
        
        # 如果最后更新时间超过 1 天，需要更新
        now = datetime.now(timezone.utc)
        time_diff = now - last_timestamp
        
        if time_diff > timedelta(days=1):
            self.logger.info(
                f"商品 {item_statistics_id} 的走势数据最后更新时间为 {last_timestamp}，需要更新"
            )
            return True
        else:
            self.logger.info(
                f"商品 {item_statistics_id} 的走势数据最后更新时间为 {last_timestamp}，无需更新"
            )
            return False
    
    def crawl_single_item(
        self,
        item: Dict[str, Any],
        index: int,
        total: int
    ) -> Dict[str, Any]:
        """
        爬取单个商品的数据
        
        Args:
            item: 商品信息
            index: 当前索引
            total: 总数量
            
        Returns:
            统计信息
        """
        item_statistics_id = item["item_statistics_id"]
        steamdt_id = item["steamdt_id"]
        item_name = item.get("name", "未知商品")
        
        self.logger.info(
            f"\n[{index}/{total}] 处理商品: {item_name} "
            f"(item_id={item_statistics_id}, steamdt_id={steamdt_id})"
        )
        
        stats = {
            "kline_updated": 0,
            "kline_skipped": 0,
            "trend_updated": 0,
            "trend_skipped": 0,
            "errors": []
        }
        
        # 爬取 K 线数据
        for kline_type in self.kline_types:
            try:
                should_update, max_time = self.should_update_kline(
                    item_statistics_id, kline_type
                )
                
                if should_update:
                    count = self.kline_crawler.crawl_and_save(
                        kline_type=kline_type,
                        type_val=steamdt_id,
                        max_time=max_time,
                        platform="ALL",
                        special_style=""
                    )
                    
                    if count > 0:
                        stats["kline_updated"] += 1
                        self.logger.info(f"  ✅ K 线类型 {kline_type}: 保存 {count} 条数据")
                    else:
                        stats["kline_skipped"] += 1
                        self.logger.info(
                            f"  ⏭️  K 线类型 {kline_type}: 无新数据 "
                            f"[{item_name} | steamdt_id={steamdt_id}]"
                        )
                    
                    # 添加延迟
                    if self.delay > 0:
                        time.sleep(self.delay)
                else:
                    stats["kline_skipped"] += 1
                    self.logger.info(
                        f"  ⏭️  K 线类型 {kline_type}: 跳过（数据已是最新） "
                        f"[{item_name} | steamdt_id={steamdt_id}]"
                    )
                    
            except Exception as e:
                self.logger.error(
                    f"  ❌ K 线类型 {kline_type} 失败: {e} "
                    f"[{item_name} | item_id={item_statistics_id} | steamdt_id={steamdt_id}]"
                )
                stats["errors"].append(f"K线类型{kline_type}: {str(e)}")
        
        # 爬取走势数据
        for type_day in self.type_days:
            try:
                if self.should_update_trend(item_statistics_id):
                    count = self.trend_crawler.crawl_and_save(
                        item_id=steamdt_id,
                        type_day=type_day,
                        platform="ALL",
                        special_style="",
                        incremental=True  # 启用增量更新
                    )
                    
                    if count > 0:
                        stats["trend_updated"] += 1
                        self.logger.info(f"  ✅ 走势数据 type_day={type_day}: 保存 {count} 条数据")
                    else:
                        stats["trend_skipped"] += 1
                        self.logger.info(
                            f"  ⏭️  走势数据 type_day={type_day}: 无新数据 "
                            f"[{item_name} | steamdt_id={steamdt_id}]"
                        )
                    
                    # 添加延迟
                    if self.delay > 0:
                        time.sleep(self.delay)
                else:
                    stats["trend_skipped"] += 1
                    self.logger.info(
                        f"  ⏭️  走势数据 type_day={type_day}: 跳过（数据已是最新） "
                        f"[{item_name} | steamdt_id={steamdt_id}]"
                    )
                    
            except Exception as e:
                self.logger.error(
                    f"  ❌ 走势数据 type_day={type_day} 失败: {e} "
                    f"[{item_name} | item_id={item_statistics_id} | steamdt_id={steamdt_id}]"
                )
                stats["errors"].append(f"走势数据type_day{type_day}: {str(e)}")
        
        return stats
    
    def run_crawl_job(self, limit: Optional[int] = None):
        """
        执行一次完整的爬取任务
        
        Args:
            limit: 限制处理的商品数量，None 表示处理所有
        """
        self.logger.info("=" * 60)
        self.logger.info("开始执行每日 K 线和趋势数据爬取任务")
        self.logger.info(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if self.market_index_type:
            self.logger.info(f"大盘类型: {self.market_index_type.value}")
        else:
            self.logger.info("大盘类型: 所有商品")
        self.logger.info(f"K 线类型: {self.kline_types}")
        self.logger.info(f"走势时间范围: {self.type_days}")
        self.logger.info("=" * 60)
        
        # 获取商品列表
        items = self.fetch_items_to_crawl(limit=limit)
        
        if not items:
            self.logger.warning("未找到需要爬取的商品")
            return
        
        total_items = len(items)
        self.logger.info(f"准备处理 {total_items} 个商品\n")
        
        # 统计信息
        total_stats = {
            "kline_updated": 0,
            "kline_skipped": 0,
            "trend_updated": 0,
            "trend_skipped": 0,
            "item_errors": []
        }
        
        # 逐个处理商品
        for i, item in enumerate(items, 1):
            try:
                stats = self.crawl_single_item(item, i, total_items)
                
                total_stats["kline_updated"] += stats["kline_updated"]
                total_stats["kline_skipped"] += stats["kline_skipped"]
                total_stats["trend_updated"] += stats["trend_updated"]
                total_stats["trend_skipped"] += stats["trend_skipped"]
                
                if stats["errors"]:
                    total_stats["item_errors"].append({
                        "item_statistics_id": item["item_statistics_id"],
                        "steamdt_id": item["steamdt_id"],
                        "errors": stats["errors"]
                    })
                
            except Exception as e:
                self.logger.error(f"处理商品失败: {e}")
                total_stats["item_errors"].append({
                    "item_statistics_id": item["item_statistics_id"],
                    "steamdt_id": item["steamdt_id"],
                    "errors": [str(e)]
                })
            
            # 商品之间的延迟
            if i < total_items and self.delay > 0:
                time.sleep(self.delay)
        
        # 打印总结
        self.logger.info("\n" + "=" * 60)
        self.logger.info("每日爬取任务完成")
        self.logger.info("=" * 60)
        self.logger.info(f"总商品数: {total_items}")
        self.logger.info(f"\nK 线数据统计:")
        self.logger.info(f"  更新: {total_stats['kline_updated']}")
        self.logger.info(f"  跳过: {total_stats['kline_skipped']}")
        self.logger.info(f"\n走势数据统计:")
        self.logger.info(f"  更新: {total_stats['trend_updated']}")
        self.logger.info(f"  跳过: {total_stats['trend_skipped']}")
        
        if total_stats["item_errors"]:
            self.logger.warning(f"\n处理失败的商品数: {len(total_stats['item_errors'])}")
            self.logger.warning("失败商品示例（前5个）:")
            for error_item in total_stats["item_errors"][:5]:
                self.logger.warning(
                    f"  steamdt_id={error_item['steamdt_id']}: "
                    f"{'; '.join(error_item['errors'])}"
                )
        
        self.logger.info("=" * 60 + "\n")
    
    def start_scheduler(self, cron_expression: str = "0 0 * * *"):
        """
        启动调度器（守护进程模式）
        
        Args:
            cron_expression: Cron 表达式，默认 "0 0 * * *"（每天 00:00）
        """
        self.scheduler = BlockingScheduler()
        
        # 添加定时任务
        self.scheduler.add_job(
            self.run_crawl_job,
            CronTrigger.from_crontab(cron_expression),
            id="daily_kline_trend_crawl",
            name="每日 K 线和趋势数据爬取",
            replace_existing=True
        )
        
        self.logger.info(f"调度器已启动，Cron 表达式: {cron_expression}")
        self.logger.info("按 Ctrl+C 停止调度器")
        
        # 设置信号处理
        def signal_handler(signum, frame):
            self.logger.info("\n收到停止信号，正在关闭调度器...")
            if self.scheduler:
                self.scheduler.shutdown()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            self.logger.info("调度器已停止")


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="每日 K 线和趋势数据自动爬取调度器")
    parser.add_argument(
        "--market-type",
        type=str,
        default=None,
        choices=["total", "qianzhan", "agent", "baizhan"],
        help="大盘类型，不指定则爬取所有商品"
    )
    parser.add_argument(
        "--kline-types",
        type=int,
        nargs="+",
        default=[2],
        choices=[1, 2, 3],
        help="K 线类型列表（默认: 2，即日K）"
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
        "--schedule-time",
        type=str,
        default="0 0 * * *",
        help="Cron 表达式（默认: '0 0 * * *'，即每天 00:00）"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="只执行一次，不启动调度器"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="限制处理的商品数量（用于测试），不指定则处理所有"
    )
    
    args = parser.parse_args()
    
    # 转换大盘类型
    market_index_type = None
    if args.market_type:
        market_type_map = {
            "total": MarketIndexType.TOTAL,
            "qianzhan": MarketIndexType.QIANZHAN,
            "agent": MarketIndexType.AGENT,
            "baizhan": MarketIndexType.BAIZHAN
        }
        market_index_type = market_type_map[args.market_type]
    
    # 创建调度器
    scheduler = DailyKlineTrendScheduler(
        market_index_type=market_index_type,
        kline_types=args.kline_types,
        type_days=args.type_days,
        delay=args.delay
    )
    
    if args.once:
        # 一次性执行
        scheduler.run_crawl_job(limit=args.limit)
    else:
        # 启动调度器
        scheduler.start_scheduler(cron_expression=args.schedule_time)


if __name__ == "__main__":
    main()
