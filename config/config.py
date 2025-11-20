"""
配置管理模块
统一管理爬虫配置、Supabase 连接等
"""
import os
from typing import Optional, Dict, Any
from dataclasses import dataclass

# 可选加载 .env（如果安装了 python-dotenv）
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# 可选：从 config_local 导入显式配置（不纳入版本控制）
try:
    from crawler.config.config_local import SUPABASE_URL as LOCAL_SUPABASE_URL, SUPABASE_KEY as LOCAL_SUPABASE_KEY
except ImportError:
    LOCAL_SUPABASE_URL = None
    LOCAL_SUPABASE_KEY = None


@dataclass
class SupabaseConfig:
    """Supabase 配置"""
    url: str
    key: str
    
    @classmethod
    def from_env(cls) -> Optional['SupabaseConfig']:
        """从环境变量或 config_local 加载配置"""
        # 优先使用 config_local
        if LOCAL_SUPABASE_URL and LOCAL_SUPABASE_KEY:
            return cls(url=LOCAL_SUPABASE_URL, key=LOCAL_SUPABASE_KEY)
        
        # 其次使用环境变量
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        
        if url and key:
            return cls(url=url, key=key)
        return None


@dataclass
class CrawlerConfig:
    """爬虫通用配置"""
    delay: float = 1.0  # 请求延迟（秒）
    timeout: int = 30  # 请求超时（秒）
    browser_timeout: int = 30000  # 浏览器超时（毫秒）
    headless: bool = True  # 浏览器无头模式
    save_to_file: bool = True  # 是否保存到文件
    save_to_db: bool = True  # 是否保存到数据库
    batch_size: int = 100  # 批量处理大小


@dataclass
class CSQAQConfig:
    """CSQAQ 网站配置"""
    base_url: str = "https://csqaq.com"
    user_agent: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
    
    # API 端点
    api_chart_all: str = "/proxies/api/v1/info/simple/chartAll"
    api_container_data: str = "/proxies/api/v1/info/container_data_info"
    
    # 页面路径
    page_container: str = "/container"
    page_goods: str = "/goods/{goods_id}"


class Config:
    """全局配置类"""
    
    def __init__(
        self,
        supabase_config: Optional[SupabaseConfig] = None,
        crawler_config: Optional[CrawlerConfig] = None,
        csqaq_config: Optional[CSQAQConfig] = None
    ):
        self.supabase = supabase_config or SupabaseConfig.from_env()
        self.crawler = crawler_config or CrawlerConfig()
        self.csqaq = csqaq_config or CSQAQConfig()
    
    @classmethod
    def from_env(cls) -> 'Config':
        """从环境变量创建配置"""
        return cls(
            supabase_config=SupabaseConfig.from_env(),
            crawler_config=CrawlerConfig(),
            csqaq_config=CSQAQConfig()
        )
    
    def validate(self) -> bool:
        """验证配置是否完整"""
        if self.crawler.save_to_db and not self.supabase:
            return False
        return True

