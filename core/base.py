"""
基础爬虫抽象类
定义所有爬虫的通用接口和功能
"""
import logging
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime

from crawler.database.supabase_client import SupabaseManager
from crawler.config.config import Config


class BaseCrawler(ABC):
    """基础爬虫抽象类"""
    
    def __init__(
        self,
        config: Config,
        name: str,
        target_table: str,
        unique_key: str = "qaq_id"
    ):
        """
        初始化爬虫
        
        Args:
            config: 全局配置对象
            name: 爬虫名称（用于日志和标识）
            target_table: 目标数据库表名
            unique_key: 唯一键字段名（用于 upsert）
        """
        self.config = config
        self.name = name
        self.target_table = target_table
        self.unique_key = unique_key
        
        # 设置日志（必须在其他操作之前）
        self.logger = logging.getLogger(f"Crawler.{name}")
        
        # 初始化 Supabase 客户端
        self.supabase: Optional[SupabaseManager] = None
        if config.supabase:
            try:
                self.supabase = SupabaseManager(
                    url=config.supabase.url,
                    key=config.supabase.key
                )
            except Exception as e:
                self.logger.warning(f"Supabase 初始化失败: {e}")
    
    @abstractmethod
    def fetch_data(self) -> Optional[List[Dict[str, Any]]]:
        """
        获取数据（子类必须实现）
        
        Returns:
            原始数据列表，失败返回 None
        """
        pass
    
    @abstractmethod
    def transform_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        转换数据格式（子类必须实现）
        将原始数据转换为数据库表格式
        
        Args:
            raw_data: 原始数据列表
            
        Returns:
            转换后的数据列表
        """
        pass
    
    def validate_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        验证数据（可被子类重写）
        
        Args:
            data: 数据列表
            
        Returns:
            验证通过的数据列表
        """
        valid_data = []
        for item in data:
            # 基本验证：必须有唯一键
            if not item.get(self.unique_key):
                self.logger.warning(f"跳过缺少 {self.unique_key} 的数据项: {item}")
                continue
            valid_data.append(item)
        return valid_data
    
    def save_to_database(
        self,
        data: List[Dict[str, Any]],
        upsert: bool = True
    ) -> Dict[str, int]:
        """
        保存数据到数据库
        
        Args:
            data: 要保存的数据列表
            upsert: 是否使用 upsert
            
        Returns:
            统计信息字典
        """
        if not self.supabase:
            self.logger.error("Supabase 客户端未初始化，无法保存到数据库")
            return {"success": 0, "failed": len(data), "inserted": 0, "updated": 0}
        
        stats = {
            "success": 0,
            "failed": 0,
            "inserted": 0,
            "updated": 0
        }
        
        if not data:
            return stats
        
        self.logger.info(f"开始保存 {len(data)} 条数据到表 {self.target_table}")
        
        try:
            if upsert:
                # 使用批量 upsert
                result = self.supabase.client.table(self.target_table).upsert(
                    data,
                    on_conflict=self.unique_key
                ).execute()
                
                if result.data:
                    stats["success"] = len(result.data)
                    stats["inserted"] = stats["success"]  # upsert 无法区分插入和更新
                    self.logger.info(f"批量 upsert 成功: {stats['success']} 条")
                else:
                    stats["failed"] = len(data)
            else:
                # 只插入新数据
                result = self.supabase.insert_batch(self.target_table, data)
                if result:
                    stats["success"] = len(result)
                    stats["inserted"] = len(result)
                    stats["failed"] = len(data) - len(result)
                else:
                    stats["failed"] = len(data)
                    
        except Exception as e:
            self.logger.error(f"保存数据失败: {e}")
            stats["failed"] = len(data)
        
        return stats
    
    def save_to_file(
        self,
        data: List[Dict[str, Any]],
        filename: Optional[str] = None
    ) -> str:
        """
        保存数据到 JSON 文件
        
        Args:
            data: 要保存的数据列表
            filename: 文件名（如果为 None，使用默认名称）
            
        Returns:
            保存的文件路径
        """
        if filename is None:
            filename = f"{self.name}_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"数据已保存到文件: {filename}")
        return filename
    
    def run(self) -> Dict[str, Any]:
        """
        运行爬虫（主流程）
        
        Returns:
            运行结果字典
        """
        self.logger.info(f"开始运行爬虫: {self.name}")
        
        result = {
            "crawler_name": self.name,
            "success": False,
            "data_count": 0,
            "saved_count": 0,
            "error": None
        }
        
        try:
            # 1. 获取数据
            raw_data = self.fetch_data()
            if not raw_data:
                result["error"] = "未能获取数据"
                return result
            
            # 2. 转换数据
            transformed_data = self.transform_data(raw_data)
            if not transformed_data:
                result["error"] = "数据转换后为空"
                return result
            
            # 3. 验证数据
            valid_data = self.validate_data(transformed_data)
            if not valid_data:
                result["error"] = "验证后无有效数据"
                return result
            
            result["data_count"] = len(valid_data)
            
            # 4. 保存到文件（如果启用）
            if self.config.crawler.save_to_file:
                self.save_to_file(valid_data)
            
            # 5. 保存到数据库（如果启用）
            if self.config.crawler.save_to_db and self.supabase:
                db_stats = self.save_to_database(valid_data, upsert=True)
                result["saved_count"] = db_stats["success"]
                result["db_stats"] = db_stats
            elif self.config.crawler.save_to_db and not self.supabase:
                self.logger.warning("数据库保存已启用但 Supabase 未初始化")
            
            result["success"] = True
            self.logger.info(f"爬虫运行完成: {self.name}, 获取 {result['data_count']} 条数据")
            
        except Exception as e:
            result["error"] = str(e)
            self.logger.error(f"爬虫运行失败: {self.name}, 错误: {e}", exc_info=True)
        
        return result

