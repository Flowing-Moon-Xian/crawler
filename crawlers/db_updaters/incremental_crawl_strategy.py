"""
增量更新策略：
每天 00:01 运行，只抓取前一天 00:00:00 的那一条数据。
逻辑：
1. 遍历所有商品
2. 请求 K线(日K) 和 走势(近一月)
3. 提取目标日期(昨天)的数据
4. 批量存入数据库 (buffer 200)
"""
import time
import logging
import argparse
import random
from datetime import datetime, timedelta, timezone, date
from typing import List, Dict, Any, Optional

from crawler.config.config import Config
from crawler.database.supabase_client import SupabaseManager
from crawler.database.models import MarketIndexType, KlinePeriod, KlineData, TrendData
from crawler.crawlers.url_crawlers.item_trend_crawler import ItemTrendCrawler
from crawler.crawlers.url_crawlers.item_kline_crawler import ItemKlineCrawler
from crawler.utils.timestamp_refresher import get_valid_timestamp
from crawler.database.models import MarketIndexType

class IncrementalCrawlStrategy:
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config.from_env()
        
        # 初始化 Supabase
        if self.config.supabase:
            self.supabase = SupabaseManager(
                url=self.config.supabase.url,
                key=self.config.supabase.key,
            )
        else:
            self.supabase = SupabaseManager()
            
        self.kline_crawler = ItemKlineCrawler(self.config)
        self.trend_crawler = ItemTrendCrawler(self.config)
        
        # 日志
        self.logger = logging.getLogger("IncrementalCrawl")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def get_market_items(self, market_index_type: MarketIndexType = None) -> List[Dict]:
        """
        获取需要爬取的商品列表。
        """
        self.logger.info(f"正在获取商品列表 (MarketType={market_index_type})...")
        page_size = 1000
        items = []
        seen_ids = set()
        offset = 0
        
        while True:
            try:
                # 如果指定了 market_index_type，我们需要更复杂的查询
                # 这里为了简化和性能，我们改用查询 relations 表作为主表 (如果指定了类型)
                # 或者在 join 中添加过滤
                
                if market_index_type:
                     # 主表: relations -> inner join item_statistics
                     query = (
                        self.supabase.client.table("item_statistics_market_index_relations")
                        .select("item_statistics!inner(id, steamdt_id)")
                        .eq("market_index_type", market_index_type.value)
                        .range(offset, offset + page_size - 1)
                     )
                else:
                    # 原逻辑: 只要在 relations 表里就行
                    query = (
                        self.supabase.client.table("item_statistics")
                        .select("id,steamdt_id, item_statistics_market_index_relations!inner(id)")
                        .not_.is_("steamdt_id", "null")
                        .range(offset, offset + page_size - 1)
                    )

                result = query.execute()
                records = result.data or []
                
                if not records:
                    break
                    
                for r in records:
                    # 根据查询主表的区别，提取 ID 的方式不同
                    if market_index_type:
                        # 结果结构: {'item_statistics': {'id': ..., 'steamdt_id': ...}}
                        item_data = r.get("item_statistics")
                        if item_data:
                            item_id = item_data["id"]
                            steamdt = item_data["steamdt_id"]
                        else:
                            continue
                    else:
                        # 原结构: {'id': ..., 'steamdt_id': ...}
                        item_id = r["id"]
                        steamdt = r["steamdt_id"]

                    if item_id not in seen_ids and steamdt:
                         items.append({
                            "item_statistics_id": item_id,
                            "steamdt_id": steamdt
                        })
                         seen_ids.add(item_id)
                
                if len(records) < page_size:
                    break
                offset += page_size
                self.logger.info(f"已加载 {len(items)} 个商品 (已去重)...")
            except Exception as e:
                self.logger.error(f"获取商品列表失败: {e}")
                break
                
        self.logger.info(f"共加载 {len(items)} 个商品")
        return items

    def run(self, 
            target_date_str: Optional[str] = None, 
            batch_size: int = 200, 
            delay: float = 1.0, 
            limit: int = None,
            kline_type: int = 2,
            trend_type_day: int = 4,
            market_type_val: Optional[str] = None
        ):
        """
        执行增量更新
        :param target_date_str: 目标日期字符串 "YYYY-MM-DD". 默认为昨天.
        """
        # 1. 确定目标日期
        if target_date_str:
            target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
        else:
            # 默认为昨天
            target_date = date.today() - timedelta(days=1)
            
        self.logger.info(f"目标日期: {target_date} (将只保存该日期的 00:00:00 记录)")
        self.logger.info(f"批次大小: {batch_size}, 延时: {delay}s")
        
        if market_type_val:
             try:
                 # Already imported at top-level or import here if avoiding circles? 
                 # We added import at top.
                 m_type = MarketIndexType(market_type_val.lower()) # Ensure lowercase
                 self.logger.info(f"筛选 MarketType: {m_type}")
             except Exception:
                 self.logger.warning(f"无效的 MarketType value: {market_type_val}, 将获取所有 Items")
                 m_type = None
        else:
            m_type = None

        # 2. 获取商品
        items = self.get_market_items(market_index_type=m_type)
        if limit:
            items = items[:limit]
            self.logger.info(f"测试模式：限制处理 {limit} 个商品")
            
        # 3. 准备缓冲区
        kline_buffer: List[KlineData] = []
        trend_buffer: List[TrendData] = []
        
        total_items = len(items)
        processed_count = 0
        
        # --- Timestamp Management ---
        current_timestamp = None
        token_start_time = 0
        TOKEN_VALIDITY_SECONDS = 230  # 4分钟=240s，留10s缓冲
        
        # 初次获取 timestamp
        current_timestamp = get_valid_timestamp()
        if not current_timestamp:
            self.logger.error("无法获取初始 timestamp，程序退出")
            return
        token_start_time = time.time()
        
        for i, item in enumerate(items, 1):
            # 检查 timestamp 是否过期
            if time.time() - token_start_time > TOKEN_VALIDITY_SECONDS:
                self.logger.info("Timestamp 即将过期，正在刷新...")
                new_ts = get_valid_timestamp()
                if new_ts:
                    current_timestamp = new_ts
                    token_start_time = time.time()
                else:
                    self.logger.warning("刷新 timestamp 失败，将在下一轮尝试或继续使用旧的(可能失效)")
            
            steamdt_id = item["steamdt_id"]
            stats_id = item["item_statistics_id"]
            
            self.logger.info(f"[{i}/{total_items}] 处理 steamdt_id={steamdt_id}")
            
            # --- Fetch Kline (Type 2 = Daily) ---
            try:
                # 传入 current_timestamp
                raw_klines = self.kline_crawler.fetch_kline_data(
                    kline_type=kline_type, # 使用参数
                    type_val=steamdt_id,
                    timestamp=current_timestamp, # 使用捕获的 timestamp
                    max_time=int(time.time()),
                    platform="ALL"
                )
                
                found_kline = False
                if raw_klines:
                    for raw in raw_klines:
                        parsed = self.kline_crawler.parse_kline_item(raw, KlinePeriod.DAILY, stats_id)
                        # 转换到北京时间进行比较，以匹配 SteamDT 的天
                        if parsed:
                            beijing_time = parsed.timestamp.astimezone(timezone(timedelta(hours=8)))
                            if beijing_time.date() == target_date:
                                kline_buffer.append(parsed)
                                found_kline = True
                                self.logger.info(f"  -> 找到日K: {parsed.timestamp} (BJ: {beijing_time})")
                                break 
                
                    if not found_kline:
                        self.logger.info(f"  -> 未找到 {target_date} 的日K数据")
                else:
                    # 如果 raw_klines 为空，可能是 API 限制，也可能是真没数据
                    # 但如果是 API 限制，fetch_kline_data 内部可能会报错 raise
                    pass

            except Exception as e:
                self.logger.error(f"  -> 获取日K失败: {e}")
                # 尝试刷新 timestamp 以挽救后续请求
                self.logger.warning("  -> 尝试刷新 timestamp...")
                new_ts = get_valid_timestamp()
                if new_ts:
                    current_timestamp = new_ts
                    self.logger.info(f"  -> Timestamp 刷新成功: {current_timestamp}")
                else:
                    self.logger.error("  -> Timestamp 刷新失败")
                
            # --- Fetch Trend (Type Day 1 = Recent month) ---
            try:
                # 传入 current_timestamp
                raw_trends = self.trend_crawler.fetch_trend_data(
                    item_id=steamdt_id,
                    type_day=trend_type_day, # 使用参数
                    timestamp=current_timestamp, # 使用捕获的 timestamp
                    platform="ALL"
                )
                
                found_trend = False
                if raw_trends:
                    for raw in raw_trends:
                        parsed = self.trend_crawler.parse_trend_item(raw, KlinePeriod.HOURLY, stats_id)
                        if parsed:
                            beijing_time = parsed.timestamp.astimezone(timezone(timedelta(hours=8)))
                            if beijing_time.date() == target_date:
                                # 只要是目标日期的即可，不强制要求 00:00
                                trend_buffer.append(parsed)
                                found_trend = True
                                self.logger.info(f"  -> 找到趋势: {parsed.timestamp} (BJ: {beijing_time})")
                                break
                            
                    if not found_trend:
                        self.logger.info(f"  -> 未找到 {target_date} 00:00:00 的趋势数据")

            except Exception as e:
                self.logger.error(f"  -> 获取趋势失败: {e}")
                # 尝试刷新 timestamp
                if not current_timestamp: # 避免重复刷新(如果上面已经刷新过)
                     pass 
                else:
                     # 简单起见，这里也尝试刷一下，或者判断一下错误类型
                     # 为防止频繁调用 Playwright (很慢)，可以加个简单的标记或者判断
                     # 但由于上一块代码是独立的，这里也加上保险
                     self.logger.warning("  -> 尝试刷新 timestamp (Trend)...")
                     new_ts = get_valid_timestamp()
                     if new_ts:
                         current_timestamp = new_ts
                         self.logger.info(f"  -> Timestamp 刷新成功: {current_timestamp}")

            processed_count += 1
            
            # --- Check Buffer & Flush ---
            if processed_count % batch_size == 0 or i == total_items:
                self._flush_buffers(kline_buffer, trend_buffer)
                kline_buffer.clear()
                trend_buffer.clear()
            
            # 随机延迟 [delay, delay + 1.0]
            time.sleep(random.uniform(delay, delay + 1.0))

    def _flush_buffers(self, klines: List[KlineData], trends: List[TrendData]):
        if not klines and not trends:
            return
            
        self.logger.info(f"正在保存缓冲区: {len(klines)} K线, {len(trends)} 趋势...")
        
        # Save K-Lines
        if klines:
            rows = [k.to_dict() for k in klines]
            try:
                self.supabase.insert_batch("kline_data", rows)
                self.logger.info(f"已保存 {len(rows)} 条 K线数据")
            except Exception as e:
                self.logger.error(f"保存 K线数据失败: {e}")
                
        # Save Trends
        if trends:
            rows = [t.to_dict() for t in trends]
            try:
                self.supabase.insert_batch("trend_data", rows)
                self.logger.info(f"已保存 {len(rows)} 条 趋势数据")
            except Exception as e:
                self.logger.error(f"保存 趋势数据失败: {e}")

def main():
    parser = argparse.ArgumentParser(description="增量每日爬取策略")
    parser.add_argument("--batch-size", type=int, default=200, help="批量保存大小")
    parser.add_argument("--delay", type=float, default=1.0, help="商品间间隔(秒)")
    parser.add_argument("--target-date", type=str, default=None, help="目标日期 YYYY-MM-DD (默认昨天)")
    parser.add_argument("--limit", type=int, default=None, help="测试限制数量")
    
    args = parser.parse_args()
    
    strategy = IncrementalCrawlStrategy()
    strategy.config.crawler.delay = 0.5 
    
    strategy.run(
        target_date_str=args.target_date,
        batch_size=args.batch_size,
        delay=args.delay,
        limit=args.limit
    )

if __name__ == "__main__":
    main()
