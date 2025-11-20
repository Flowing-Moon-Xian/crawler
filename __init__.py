"""
爬虫模块 - 用于数据采集和存储到 Supabase
统一架构，支持浏览器自动化和直接 API 调用两种模式
"""

__version__ = "2.0.0"

# 导出主要类和函数
from crawler.config.config import Config, SupabaseConfig, CrawlerConfig, CSQAQConfig
from crawler.core.manager import CrawlerManager
from crawler.core.base import BaseCrawler
from crawler.core.browser_crawler import BrowserCrawler
from crawler.core.api_crawler import APICrawler
from crawler.database.supabase_client import SupabaseManager

__all__ = [
    "Config",
    "SupabaseConfig",
    "CrawlerConfig",
    "CSQAQConfig",
    "CrawlerManager",
    "BaseCrawler",
    "BrowserCrawler",
    "APICrawler",
    "SupabaseManager",
]

