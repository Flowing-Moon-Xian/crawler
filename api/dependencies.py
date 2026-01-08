"""
依赖注入

提供爬虫实例等共享资源
"""
from functools import lru_cache
from crawler.config.config import Config
from crawler.crawlers.url_crawlers.item_kline_crawler import ItemKlineCrawler
from crawler.crawlers.url_crawlers.item_trend_crawler import ItemTrendCrawler


@lru_cache()
def get_config() -> Config:
    """获取配置实例（单例）"""
    return Config.from_env()


@lru_cache()
def get_kline_crawler() -> ItemKlineCrawler:
    """获取 K线爬虫实例（单例）"""
    config = get_config()
    return ItemKlineCrawler(config)


@lru_cache()
def get_trend_crawler() -> ItemTrendCrawler:
    """获取走势爬虫实例（单例）"""
    config = get_config()
    return ItemTrendCrawler(config)
