"""
容器数据爬虫
爬取 CSQAQ 容器页面数据
"""
from typing import List, Dict, Any, Optional
from datetime import datetime

from crawler.core.browser_crawler import BrowserCrawler
from crawler.config.config import Config


class ContainerCrawler(BrowserCrawler):
    """容器数据爬虫"""
    
    def __init__(self, config: Config, name: str = "container"):
        """
        初始化容器爬虫
        
        Args:
            config: 全局配置对象
            name: 爬虫名称
        """
        page_url = f"{config.csqaq.base_url}{config.csqaq.page_container}"
        api_pattern = config.csqaq.api_container_data
        
        super().__init__(
            config=config,
            name=name,
            target_table="boxes",
            page_url=page_url,
            api_pattern=api_pattern,
            unique_key="qaq_id"
        )
    
    def transform_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        转换数据格式
        将 API 返回的数据转换为 boxes 表格式
        
        Args:
            raw_data: 原始数据列表
            
        Returns:
            转换后的数据列表
        """
        boxes_data = []
        
        for item in raw_data:
            if not isinstance(item, dict):
                self.logger.warning(f"跳过非字典类型的数据项: {type(item)}")
                continue
            
            # 映射字段：id -> qaq_id, name -> name, comment -> obtain_method, created_at -> created_at
            box_data = {
                'qaq_id': item.get('id'),
                'name': item.get('name'),
                'obtain_method': item.get('comment'),  # comment 字段映射到 obtain_method
                'created_at': item.get('created_at'),
            }
            
            # 验证必需字段
            if not box_data['name']:
                self.logger.warning(f"跳过缺少 name 字段的数据项: {item}")
                continue
            
            # 处理时间戳
            if box_data['created_at']:
                try:
                    # 如果是数字时间戳（毫秒）
                    if isinstance(box_data['created_at'], (int, float)):
                        if box_data['created_at'] > 1e10:  # 毫秒时间戳
                            box_data['created_at'] = datetime.fromtimestamp(
                                box_data['created_at'] / 1000
                            ).isoformat()
                        else:  # 秒时间戳
                            box_data['created_at'] = datetime.fromtimestamp(
                                box_data['created_at']
                            ).isoformat()
                    # 如果已经是字符串，保持原样
                    elif isinstance(box_data['created_at'], str):
                        pass
                except Exception as e:
                    self.logger.warning(f"解析 created_at 失败: {e}, 原始值: {box_data['created_at']}")
                    # 如果解析失败，使用当前时间
                    box_data['created_at'] = datetime.now().isoformat()
            else:
                # 如果没有 created_at，使用当前时间
                box_data['created_at'] = datetime.now().isoformat()
            
            boxes_data.append(box_data)
        
        self.logger.info(f"成功转换 {len(boxes_data)} 条容器数据")
        return boxes_data



