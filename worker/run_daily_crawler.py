"""
每日自动增量爬取脚本 (适配 IncrementalCrawlStrategy)

功能:
1. 支持一次性运行 (mode=once)
2. 支持守护进程模式 (mode=daemon)，使用 cron 表达式调度
3. 自动适配 Docker 部署环境 (从环境变量读取配置)
"""
import os
import sys
import logging
import signal
import argparse
from datetime import datetime
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from crawler.crawlers.db_updaters.incremental_crawl_strategy import IncrementalCrawlStrategy

# 配置日志
today_str = datetime.now().strftime("%Y-%m-%d")
log_dir = Path("logs") / today_str
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_dir / "daily_crawler.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("DailyCrawlerRunner")

def run_job(batch_size: int = 200, delay: float = 1.0, limit: int = None, kline_type: int = 2, trend_type_day: int = 4, market_type: str = None):
    """执行爬取任务的工作函数"""
    logger.info(">>> 开始执行每日增量爬取任务")
    try:
        strategy = IncrementalCrawlStrategy()
        # 如果需要，可以在这里覆盖 config
        # strategy.config.crawler.delay = ... 
        
        # 默认爬取昨天的数据 (target_date=None)
        strategy.run(
            target_date_str=None, 
            batch_size=batch_size, 
            delay=delay, 
            limit=limit,
            kline_type=kline_type,
            trend_type_day=trend_type_day,
            market_type_val=market_type
        )
        logger.info("<<< 每日增量爬取任务完成")
    except Exception as e:
        logger.error(f"任务执行出错: {e}", exc_info=True)

def run_once_mode(args):
    """一次性运行模式"""
    logger.info("运行模式: ONCE (一次性执行)")
    run_job(
        batch_size=args.batch_size,
        delay=args.delay,
        limit=args.limit
    )

def run_daemon_mode(args):
    """守护进程模式"""
    cron_exp = os.getenv("CRON_EXPRESSION", "1 0 * * *") # 默认每天 00:01
    
    # 获取环境变量
    market_type_str = os.getenv("MARKET_TYPE", "")
    kline_type_str = os.getenv("KLINE_TYPES", "2")
    type_days_str = os.getenv("TYPE_DAYS", "4") # Default 4 (Year/Daily) based on last discussion
    crawl_limit_str = os.getenv("CRAWL_LIMIT", "") # Optional limit override
    crawl_delay_str = os.getenv("CRAWL_DELAY", "") # Optional delay override

    # Parse params
    if market_type_str and market_type_str.strip():
        market_type = market_type_str.strip() # Pass as string (e.g., "baizhan" or "BAIZHAN")
    else:
        market_type = None

    kline_type = int(kline_type_str) if kline_type_str.isdigit() else 2
    trend_type_day = int(type_days_str) if type_days_str.isdigit() else 4
    
    # Priority: Env > Args (Since we are in Docker)
    delay = float(crawl_delay_str) if crawl_delay_str else args.delay
    limit = int(crawl_limit_str) if crawl_limit_str and crawl_limit_str.isdigit() else args.limit

    logger.info("运行模式: DAEMON (守护进程)")
    logger.info(f"Cron 表达式: {cron_exp}")
    logger.info(f"配置参数: MarketType={market_type}, KlineType={kline_type}, TrendTypeDay={trend_type_day}")
    logger.info(f"批量保存大小: {args.batch_size}, Delay Base: {delay}s")
    
    scheduler = BlockingScheduler()
    
    # 添加任务
    scheduler.add_job(
        run_job,
        CronTrigger.from_crontab(cron_exp),
        kwargs={
            "batch_size": args.batch_size,
            "delay": delay,
            "limit": limit,
            "kline_type": kline_type,
            "trend_type_day": trend_type_day,
            "market_type": market_type
        },
        id="incremental_crawl_job",
        replace_existing=True
    )
    
    # 优雅退出处理
    def signal_handler(signum, frame):
        logger.info("收到停止信号，正在关闭...")
        scheduler.shutdown()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info(f"调度器准备启动...")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass

def main():
    parser = argparse.ArgumentParser(description="CS2 每日增量爬虫")
    
    # 运行模式
    parser.add_argument(
        "--mode", 
        choices=["once", "daemon"], 
        default="once",
        help="运行模式: once=立即运行一次, daemon=守护进程定时运行"
    )
    
    # 核心参数 (优先使用命令行参数，其次使用环境变量，最后默认值)
    parser.add_argument(
        "--batch-size", 
        type=int, 
        default=int(os.getenv("BATCH_SIZE", "200")),
        help="批量入库大小"
    )
    parser.add_argument(
        "--delay", 
        type=float, 
        default=float(os.getenv("CRAWL_DELAY", "1.0")),
        help="请求间隔(秒)"
    )
    # 安全解析 CRAWL_LIMIT 环境变量
    crawl_limit_env = os.getenv("CRAWL_LIMIT", "").strip()
    default_limit = int(crawl_limit_env) if crawl_limit_env.isdigit() else None
    
    parser.add_argument(
        "--limit", 
        type=int, 
        default=default_limit,
        help="限制处理数量(测试用)"
    )
    
    args = parser.parse_args()
    
    if args.mode == "once":
        run_once_mode(args)
    else:
        run_daemon_mode(args)

if __name__ == "__main__":
    main()
