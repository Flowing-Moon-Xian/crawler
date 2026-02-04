"""
通用增量更新 Worker (Legacy Entry Point)

该脚本已重构，内部调用新的 IncrementalCrawlStrategy。
推荐使用 crawler.worker.run_daily_crawler
"""
import sys
import logging
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from crawler.crawlers.db_updaters.incremental_crawl_strategy import IncrementalCrawlStrategy

def main():
    print("=" * 60)
    print("通用增量更新 Worker (调用 IncrementalCrawlStrategy)")
    print("=" * 60)
    
    # 默认配置
    strategy = IncrementalCrawlStrategy()
    strategy.run(batch_size=200, delay=1.0)

if __name__ == "__main__":
    main()
