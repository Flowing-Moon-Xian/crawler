"""
爬虫管理器
统一管理所有爬虫的注册、运行和调度
"""
import logging
from typing import Dict, List, Optional, Type
from datetime import datetime

from crawler.config.config import Config
from crawler.core.base import BaseCrawler


class CrawlerManager:
    """爬虫管理器"""
    
    def __init__(self, config: Optional[Config] = None):
        """
        初始化爬虫管理器
        
        Args:
            config: 全局配置对象，如果为 None 则从环境变量加载
        """
        self.config = config or Config.from_env()
        self.crawlers: Dict[str, BaseCrawler] = {}
        self.logger = logging.getLogger("CrawlerManager")
        
        # 验证配置
        if not self.config.validate():
            self.logger.warning("配置验证失败，某些功能可能无法使用")
    
    def register(self, crawler: BaseCrawler) -> None:
        """
        注册爬虫
        
        Args:
            crawler: 爬虫实例
        """
        self.crawlers[crawler.name] = crawler
        self.logger.info(f"注册爬虫: {crawler.name}")
    
    def register_class(
        self,
        crawler_class: Type[BaseCrawler],
        name: Optional[str] = None,
        **kwargs
    ) -> BaseCrawler:
        """
        注册爬虫类（自动实例化）
        
        Args:
            crawler_class: 爬虫类
            name: 爬虫名称（如果为 None，使用类名）
            **kwargs: 传递给爬虫构造函数的参数
            
        Returns:
            爬虫实例
        """
        if name is None:
            name = crawler_class.__name__
        
        crawler = crawler_class(config=self.config, name=name, **kwargs)
        self.register(crawler)
        return crawler
    
    def get_crawler(self, name: str) -> Optional[BaseCrawler]:
        """
        获取爬虫实例
        
        Args:
            name: 爬虫名称
            
        Returns:
            爬虫实例，如果不存在返回 None
        """
        return self.crawlers.get(name)
    
    def list_crawlers(self) -> List[str]:
        """
        列出所有已注册的爬虫名称
        
        Returns:
            爬虫名称列表
        """
        return list(self.crawlers.keys())
    
    def run_crawler(self, name: str) -> Dict:
        """
        运行指定的爬虫
        
        Args:
            name: 爬虫名称
            
        Returns:
            运行结果字典
        """
        crawler = self.get_crawler(name)
        if not crawler:
            return {
                "success": False,
                "error": f"爬虫 '{name}' 未注册"
            }
        
        self.logger.info(f"运行爬虫: {name}")
        result = crawler.run()
        return result
    
    def run_all(self) -> Dict[str, Dict]:
        """
        运行所有已注册的爬虫
        
        Returns:
            所有爬虫的运行结果字典
        """
        results = {}
        
        self.logger.info(f"开始运行所有爬虫，共 {len(self.crawlers)} 个")
        
        for name in self.crawlers:
            results[name] = self.run_crawler(name)
        
        # 统计
        success_count = sum(1 for r in results.values() if r.get("success"))
        total_count = len(results)
        
        self.logger.info(f"所有爬虫运行完成: {success_count}/{total_count} 成功")
        
        return results
    
    def get_status(self) -> Dict:
        """
        获取管理器状态
        
        Returns:
            状态字典
        """
        return {
            "crawler_count": len(self.crawlers),
            "crawlers": list(self.crawlers.keys()),
            "config_valid": self.config.validate(),
            "supabase_configured": self.config.supabase is not None,
            "timestamp": datetime.now().isoformat()
        }



