"""
每日 K 线和趋势数据爬虫运行示例

演示如何使用 DailyKlineTrendScheduler 进行一次性执行或守护进程模式
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from crawler.crawlers.db_updaters.daily_kline_trend_scheduler import DailyKlineTrendScheduler
from crawler.database.models import MarketIndexType


def run_once_example():
    """一次性执行示例（用于测试）"""
    print("=" * 60)
    print("一次性执行模式 - 测试爬取前 5 个商品")
    print("=" * 60)
    
    # 创建调度器
    scheduler = DailyKlineTrendScheduler(
        market_index_type=None,  # 所有商品
        kline_types=[2],         # 只爬取日K
        type_days=[1],           # 只爬取近一月
        delay=1.0
    )
    
    # 执行一次，限制 5 个商品
    scheduler.run_crawl_job(limit=5)
    
    print("\n✅ 测试完成！")


def run_daemon_example():
    """守护进程模式示例（用于生产环境）"""
    print("=" * 60)
    print("守护进程模式 - 每天 00:00 自动执行")
    print("=" * 60)
    
    # 创建调度器
    scheduler = DailyKlineTrendScheduler(
        market_index_type=None,  # 所有商品
        kline_types=[2],         # 只爬取日K
        type_days=[3],           # 六个月日级数据（原为 [1] 近一月小时级）
        delay=1.0
    )
    
    # 启动调度器（每天 00:00 执行）
    scheduler.start_scheduler(cron_expression="0 0 * * *")


def run_qianzhan_example():
    """只爬取千百战大盘商品示例"""
    print("=" * 60)
    print("一次性执行模式 - 爬取千百战大盘商品")
    print("=" * 60)
    
    # 创建调度器
    scheduler = DailyKlineTrendScheduler(
        market_index_type=MarketIndexType.QIANZHAN,  # 只爬取千百战大盘
        kline_types=[2],                              # 只爬取日K
        type_days=[3],                                # 六个月日级数据
        delay=1.0
    )
    
    # 执行一次
    scheduler.run_crawl_job()
    
    print("\n✅ 完成！")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="每日 K 线和趋势数据爬虫示例")
    parser.add_argument(
        "--mode",
        type=str,
        default="once",
        choices=["once", "daemon", "qianzhan"],
        help="运行模式: once=一次性执行(测试), daemon=守护进程, qianzhan=千百战大盘"
    )
    
    args = parser.parse_args()
    
    if args.mode == "once":
        run_once_example()
    elif args.mode == "daemon":
        run_daemon_example()
    elif args.mode == "qianzhan":
        run_qianzhan_example()
