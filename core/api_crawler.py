"""
API 爬虫基类
用于可以直接调用 API 的爬虫
"""
import requests
import time
from typing import Optional, Dict, Any, List

from crawler.core.base import BaseCrawler
from crawler.config.config import Config


class APICrawler(BaseCrawler):
    """API 爬虫基类"""
    
    def __init__(
        self,
        config: Config,
        name: str,
        target_table: str,
        api_url: str,
        unique_key: str = "qaq_id",
        headers: Optional[Dict[str, str]] = None
    ):
        """
        初始化 API 爬虫
        
        Args:
            config: 全局配置对象
            name: 爬虫名称
            target_table: 目标数据库表名
            api_url: API 端点 URL
            unique_key: 唯一键字段名
            headers: 自定义请求头
        """
        super().__init__(config, name, target_table, unique_key)
        self.api_url = api_url
        
        # 初始化 requests session
        self.session = requests.Session()
        default_headers = {
            "User-Agent": config.csqaq.user_agent,
            "Accept": "application/json",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        if headers:
            default_headers.update(headers)
        self.session.headers.update(default_headers)
    
    def fetch_data(
        self,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        authorization: Optional[str] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        获取数据（API 爬虫的默认实现）
        
        Args:
            method: HTTP 方法
            params: URL 参数
            json_data: JSON 请求体
            authorization: 授权 token
            
        Returns:
            API 返回的数据列表
        """
        headers = {}
        if authorization:
            headers["authorization"] = authorization
        
        try:
            time.sleep(self.config.crawler.delay)
            
            if method.upper() == "GET":
                response = self.session.get(
                    self.api_url,
                    params=params,
                    headers=headers,
                    timeout=self.config.crawler.timeout
                )
            elif method.upper() == "POST":
                response = self.session.post(
                    self.api_url,
                    params=params,
                    json=json_data,
                    headers=headers,
                    timeout=self.config.crawler.timeout
                )
            else:
                raise ValueError(f"不支持的 HTTP 方法: {method}")
            
            response.raise_for_status()
            data = response.json()
            
            # 处理不同的响应格式
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                # 尝试常见的字段名
                for key in ['data', 'list', 'items', 'results']:
                    if key in data and isinstance(data[key], list):
                        return data[key]
                # 如果整个字典就是一条数据
                return [data]
            
            return None
            
        except requests.RequestException as e:
            self.logger.error(f"API 请求失败: {e}")
            return None
        except Exception as e:
            self.logger.error(f"获取数据失败: {e}")
            return None



