"""
Supabase 客户端配置和工具函数
"""

import os
from typing import Optional, Dict, Any, List

from supabase import create_client, Client

from crawler.config.config import SupabaseConfig


class SupabaseManager:
    """Supabase 数据库管理器"""

    def __init__(self, url: Optional[str] = None, key: Optional[str] = None):
        """
        初始化 Supabase 客户端

        Args:
            url: Supabase 项目 URL，如果为 None 则从配置/环境变量获取
            key: Supabase API Key，如果为 None 则从配置/环境变量获取
        """

        # 如果未显式传入，则尝试从 crawler 的配置模块中加载
        if url is None or key is None:
            cfg = SupabaseConfig.from_env()
        else:
            cfg = None

        # 优先级：显式参数 > config_local / 环境变量 > 直接读取环境变量
        self.url = url or (cfg.url if cfg else None) or os.getenv("SUPABASE_URL")
        self.key = key or (cfg.key if cfg else None) or os.getenv("SUPABASE_KEY")

        if not self.url or not self.key:
            raise ValueError(
                "Supabase URL 和 Key 必须提供，可以通过：\n"
                "- crawler/config/config_local.py 中的 SUPABASE_URL/SUPABASE_KEY，或\n"
                "- 环境变量 SUPABASE_URL / SUPABASE_KEY，或\n"
                "- 显式传入 url/key 参数 之一进行配置。"
            )

        self.client: Client = create_client(self.url, self.key)
    
    def insert_data(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        插入单条数据
        
        Args:
            table: 表名
            data: 要插入的数据字典
            
        Returns:
            插入后的数据
        """
        result = self.client.table(table).insert(data).execute()
        return result.data[0] if result.data else None
    
    def insert_batch(self, table: str, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量插入数据
        
        Args:
            table: 表名
            data: 要插入的数据列表
            
        Returns:
            插入后的数据列表
        """
        result = self.client.table(table).insert(data).execute()
        return result.data if result.data else []
    
    def query_data(
        self, 
        table: str, 
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        查询数据
        
        Args:
            table: 表名
            filters: 过滤条件字典，例如 {"column": "value"}
            limit: 限制返回数量
            
        Returns:
            查询结果列表
        """
        query = self.client.table(table).select("*")
        
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        
        if limit:
            query = query.limit(limit)
        
        result = query.execute()
        return result.data if result.data else []
    
    def update_data(
        self, 
        table: str, 
        filters: Dict[str, Any], 
        data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        更新数据
        
        Args:
            table: 表名
            filters: 过滤条件字典
            data: 要更新的数据
            
        Returns:
            更新后的数据列表
        """
        query = self.client.table(table).update(data)
        
        for key, value in filters.items():
            query = query.eq(key, value)
        
        result = query.execute()
        return result.data if result.data else []
    
    def delete_data(self, table: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        删除数据
        
        Args:
            table: 表名
            filters: 过滤条件字典
            
        Returns:
            删除的数据列表
        """
        query = self.client.table(table).delete()
        
        for key, value in filters.items():
            query = query.eq(key, value)
        
        result = query.execute()
        return result.data if result.data else []


