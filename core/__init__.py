"""
核心爬虫模块
包含基础爬虫类、API爬虫、浏览器爬虫和管理器
"""
from crawler.core.base import BaseCrawler
from crawler.core.api_crawler import APICrawler
from crawler.core.browser_crawler import BrowserCrawler
from crawler.core.manager import CrawlerManager

__all__ = [
    "BaseCrawler",
    "APICrawler",
    "BrowserCrawler",
    "CrawlerManager",
]

