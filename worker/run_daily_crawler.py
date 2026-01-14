"""
每日 K 线和趋势数据爬虫运行示例

演示如何使用 DailyKlineTrendScheduler 进行一次性执行或守护进程模式
支持通过环境变量配置参数
"""
import os
import sys
from pathlib import Path
from typing import List, Optional

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from crawler.crawlers.db_updaters.daily_kline_trend_scheduler import DailyKlineTrendScheduler
from crawler.database.models import MarketIndexType


def parse_int_list(value: str) -> List[int]:
    """
    解析逗号分隔的整数列表
    
    Args:
        value: 逗号分隔的整数字符串，例如 "1,2,3"
        
    Returns:
        整数列表
    """
    if not value:
        return []
    return [int(x.strip()) for x in value.split(",") if x.strip()]


def get_market_type_from_env() -> Optional[MarketIndexType]:
    """
    从环境变量获取大盘类型
    
    Returns:
        MarketIndexType 或 None
    """
    market_type_str = os.getenv("MARKET_TYPE", "").strip().lower()
    if not market_type_str:
        return None
    
    market_type_map = {
        "total": MarketIndexType.TOTAL,
        "qianzhan": MarketIndexType.QIANZHAN,
        "agent": MarketIndexType.AGENT,
        "baizhan": MarketIndexType.BAIZHAN
    }
    
    return market_type_map.get(market_type_str)


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
    """守护进程模式示例（用于生产环境）- 支持环境变量配置"""
    # 从环境变量读取配置
    cron_expression = os.getenv("CRON_EXPRESSION", "0 0 * * *")
    market_type = get_market_type_from_env()
    kline_types = parse_int_list(os.getenv("KLINE_TYPES", "2"))
    type_days = parse_int_list(os.getenv("TYPE_DAYS", "3"))
    delay = float(os.getenv("CRAWL_DELAY", "1.0"))
    limit_str = os.getenv("CRAWL_LIMIT", "").strip()
    limit = int(limit_str) if limit_str else None
    
    print("=" * 60)
    print("守护进程模式 - 从环境变量读取配置")
    print("=" * 60)
    print(f"Cron 表达式: {cron_expression}")
    print(f"大盘类型: {market_type.value if market_type else '所有商品'}")
    print(f"K 线类型: {kline_types}")
    print(f"走势时间范围: {type_days}")
    print(f"请求延迟: {delay}s")
    if limit:
        print(f"商品数量限制: {limit} (测试模式)")
    print("=" * 60)
    
    # 创建调度器
    scheduler = DailyKlineTrendScheduler(
        market_index_type=market_type,
        kline_types=kline_types,
        type_days=type_days,
        delay=delay
    )
    
    # 启动调度器
    scheduler.start_scheduler(cron_expression=cron_expression)


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
