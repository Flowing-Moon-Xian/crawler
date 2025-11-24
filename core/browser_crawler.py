"""
浏览器爬虫基类
用于需要浏览器自动化拦截 API 的爬虫
"""
import logging
from typing import Optional, Dict, Any, List

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

from crawler.core.base import BaseCrawler
from crawler.config.config import Config


class BrowserCrawler(BaseCrawler):
    """浏览器爬虫基类"""
    
    def __init__(
        self,
        config: Config,
        name: str,
        target_table: str,
        page_url: str,
        api_pattern: str,
        unique_key: str = "qaq_id"
    ):
        """
        初始化浏览器爬虫
        
        Args:
            config: 全局配置对象
            name: 爬虫名称
            target_table: 目标数据库表名
            page_url: 要访问的页面 URL
            api_pattern: 要拦截的 API URL 模式（用于匹配）
            unique_key: 唯一键字段名
        """
        super().__init__(config, name, target_table, unique_key)
        self.page_url = page_url
        self.api_pattern = api_pattern
        
        if not PLAYWRIGHT_AVAILABLE:
            self.logger.warning("Playwright 未安装，浏览器爬虫将无法工作")
            self.logger.warning("安装方法: pip install playwright && playwright install chromium")
    
    def intercept_api(
        self,
        timeout: Optional[int] = None,
        wait_after_load: int = 2000
    ) -> Optional[Dict[str, Any]]:
        """
        使用浏览器拦截 API 响应
        
        Args:
            timeout: 超时时间（毫秒），如果为 None 使用配置中的值
            wait_after_load: 页面加载后等待时间（毫秒）
            
        Returns:
            API 响应数据，失败返回 None
        """
        if not PLAYWRIGHT_AVAILABLE:
            self.logger.error("Playwright 未安装，无法使用浏览器自动化")
            return None
        
        timeout = timeout or self.config.crawler.browser_timeout
        self.logger.info(f"使用浏览器访问页面并拦截 API: {self.page_url}")
        
        try:
            with sync_playwright() as p:
                # 配置浏览器启动选项
                launch_options = {"headless": self.config.crawler.headless}
                
                # 配置代理（如果提供）
                context_options = {
                    "user_agent": self.config.csqaq.user_agent
                }
                if self.config.crawler.proxy:
                    # 解析代理 URL
                    proxy_url = self.config.crawler.proxy
                    # 移除协议前缀
                    if proxy_url.startswith("http://"):
                        proxy_url = proxy_url[7:]
                    elif proxy_url.startswith("https://"):
                        proxy_url = proxy_url[8:]
                    
                    # 解析用户名密码（如果有）
                    if "@" in proxy_url:
                        auth_part, server_part = proxy_url.rsplit("@", 1)
                        if ":" in auth_part:
                            username, password = auth_part.split(":", 1)
                            context_options["proxy"] = {
                                "server": f"http://{server_part}",
                                "username": username,
                                "password": password
                            }
                        else:
                            context_options["proxy"] = {"server": f"http://{server_part}"}
                    else:
                        context_options["proxy"] = {"server": f"http://{proxy_url}"}
                    
                    self.logger.info(f"使用代理: {self.config.crawler.proxy}")
                
                browser = p.chromium.launch(**launch_options)
                context = browser.new_context(**context_options)
                page = context.new_page()
                
                captured_response = [None]
                response_received = [False]
                
                def handle_response(response):
                    """拦截响应"""
                    response_url = response.url
                    if self.api_pattern.lower() in response_url.lower():
                        self.logger.info(f"✅ 检测到目标 API: {response_url}")
                        
                        if response.status == 200:
                            try:
                                data = response.json()
                                captured_response[0] = data
                                response_received[0] = True
                                self.logger.info("✅ 成功拦截到 API 响应")
                            except Exception as e:
                                self.logger.warning(f"解析响应 JSON 失败: {e}")
                
                page.on("response", handle_response)
                
                # 访问页面
                try:
                    self.logger.info("正在加载页面...")
                    page.goto(self.page_url, wait_until="load", timeout=timeout)
                    self.logger.info("页面加载完成")
                    
                    # 等待 JavaScript 执行
                    page.wait_for_timeout(wait_after_load)
                    
                    # 等待 API 响应（如果支持）
                    if hasattr(page, 'wait_for_response'):
                        try:
                            self.logger.info("等待 API 响应...")
                            response = page.wait_for_response(
                                lambda r: self.api_pattern.lower() in r.url.lower() and r.status == 200,
                                timeout=20000
                            )
                            self.logger.info(f"✅ 获取到响应: {response.url}")
                            try:
                                data = response.json()
                                captured_response[0] = data
                                response_received[0] = True
                            except Exception as e:
                                self.logger.warning(f"解析响应失败: {e}")
                        except Exception as e:
                            self.logger.warning(f"等待响应超时: {e}")
                    
                    # 轮询等待
                    if not response_received[0]:
                        max_wait = 15
                        wait_interval = 200
                        waited = 0
                        
                        while not response_received[0] and waited < max_wait * 1000:
                            page.wait_for_timeout(wait_interval)
                            waited += wait_interval
                            if waited % 2000 == 0:
                                self.logger.info(f"等待中... ({waited/1000:.1f}s)")
                        
                        if not response_received[0]:
                            self.logger.warning("未能拦截到 API 响应")
                            # 尝试滚动页面
                            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                            page.wait_for_timeout(3000)
                            
                except PlaywrightTimeoutError:
                    self.logger.warning("页面加载超时，但可能已拦截到响应")
                except Exception as e:
                    self.logger.error(f"访问页面时出错: {e}")
                
                browser.close()
                
                if captured_response[0]:
                    return captured_response[0]
                else:
                    return None
                    
        except Exception as e:
            self.logger.error(f"浏览器自动化失败: {e}")
            return None
    
    def fetch_data(self) -> Optional[List[Dict[str, Any]]]:
        """
        获取数据（浏览器爬虫的默认实现）
        子类可以重写此方法以自定义行为
        """
        api_response = self.intercept_api()
        if api_response:
            # 如果响应是列表，直接返回
            if isinstance(api_response, list):
                return api_response
            # 如果响应是字典，尝试提取数据
            elif isinstance(api_response, dict):
                # 尝试常见的字段名
                for key in ['data', 'list', 'items', 'results']:
                    if key in api_response and isinstance(api_response[key], list):
                        return api_response[key]
                # 如果整个字典就是一条数据
                return [api_response]
        return None

