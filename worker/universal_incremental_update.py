"""
通用增量更新 Worker

对 item_statistics_market_index_relations 表中的所有商品进行增量更新，
不区分市场类型，只要在表中就会进行更新。
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from crawler.crawlers.db_updaters.daily_kline_trend_scheduler import DailyKlineTrendScheduler


def main():
    """
    通用增量更新 Worker（低内存优化版本）
    
    对 item_statistics_market_index_relations 表中的所有商品进行增量更新
    适用于 2GB 内存环境
    """
    import gc
    import time
    
    print("=" * 60)
    print("通用增量更新 Worker（低内存优化）")
    print("对所有 item_statistics_market_index_relations 表中的商品进行增量更新")
    print("=" * 60)
    
    # 创建调度器，使用低内存配置
    scheduler = DailyKlineTrendScheduler(
        market_index_type=None,  # 不区分市场类型，处理所有商品
        kline_types=[2],         # 只爬取日K
        type_days=[1],           # 只爬取近一月走势
        delay=2.0,               # 增加延迟以降低内存压力
        batch_size=20            # 减小批量大小
    )
    
    # 获取所有需要处理的商品
    print("\n获取商品列表...")
    items = scheduler.fetch_items_to_crawl()
    total_items = len(items)
    
    if total_items == 0:
        print("未找到需要处理的商品")
        return
    
    print(f"找到 {total_items} 个商品")
    
    # 分批处理，每批 10 个商品
    BATCH_SIZE = 10
    num_batches = (total_items - 1) // BATCH_SIZE + 1
    
    print(f"将分 {num_batches} 批处理，每批 {BATCH_SIZE} 个商品\n")
    
    for batch_idx in range(num_batches):
        start_idx = batch_idx * BATCH_SIZE
        end_idx = min(start_idx + BATCH_SIZE, total_items)
        batch = items[start_idx:end_idx]
        
        print(f"\n{'='*60}")
        print(f"处理批次 {batch_idx + 1}/{num_batches} (商品 {start_idx + 1}-{end_idx}/{total_items})")
        print(f"{'='*60}")
        
        # 处理当前批次的商品
        for i, item in enumerate(batch):
            global_idx = start_idx + i + 1
            scheduler.crawl_single_item(item, global_idx, total_items)
        
        # 批次完成后，强制垃圾回收
        print(f"\n批次 {batch_idx + 1} 完成，执行垃圾回收...")
        gc.collect()
        
        # 批次间等待，让系统释放内存
        if batch_idx < num_batches - 1:
            print("等待 5 秒后继续下一批次...")
            time.sleep(5)
    
    print("\n" + "=" * 60)
    print("✅ 所有商品增量更新完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
