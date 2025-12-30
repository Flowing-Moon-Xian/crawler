"""
分页列表爬虫
获取分页数据并保存 JSON 到本地
"""
import json
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from crawler.core.api_crawler import APICrawler
from crawler.config.config import Config


class PageListCrawler(APICrawler):
    """分页列表爬虫"""
    
    def __init__(self, config: Config, name: str = "page_list", output_dir: str = "data"):
        """
        初始化分页列表爬虫
        
        Args:
            config: 全局配置对象
            name: 爬虫名称
            output_dir: 输出目录，默认为 "data"
        """
        api_url = "https://api.csqaq.com/api/v1/info/get_page_list"
        self.token = "AQPI91A7P5Z9J0U4O3P3N6T8"
        
        super().__init__(
            config=config,
            name=name,
            target_table="",  # 不保存到数据库，只保存文件
            api_url=api_url,
            unique_key="id",
            headers={
                "ApiToken": self.token,  # API 使用 ApiToken 头
                "Content-Type": "application/json"
            }
        )
        
        # 设置输出目录
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_data(self) -> Optional[List[Dict[str, Any]]]:
        """
        获取数据（实现抽象方法，但此爬虫不使用此方法）
        
        Returns:
            空列表
        """
        return []
    
    def transform_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        转换数据格式（实现抽象方法，但此爬虫不使用此方法）
        
        Args:
            raw_data: 原始数据列表
            
        Returns:
            转换后的数据列表
        """
        return raw_data
    
    def fetch_page(self, page_index: int, page_size: int = 500) -> Optional[Dict[str, Any]]:
        """
        获取指定页的数据
        
        Args:
            page_index: 页码（从1开始）
            page_size: 每页大小，默认 500
            
        Returns:
            API 返回的完整响应数据，如果失败返回 None
        """
        try:
            json_data = {
                "page_index": page_index,
                "page_size": page_size
            }
            
            self.logger.info(f"正在获取第 {page_index} 页数据 (page_size={page_size})...")
            
            # 添加延迟以避免请求过于频繁（429 错误）
            if page_index > 1:
                delay = self.config.crawler.delay if hasattr(self.config.crawler, 'delay') else 1.0
                time.sleep(delay)
            
            response = self.session.post(
                self.api_url,
                json=json_data,
                timeout=self.config.crawler.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            # 检查响应状态
            if data.get("code") != 200:
                self.logger.warning(f"API 返回错误: {data.get('msg')}, page_index={page_index}")
                return None
            
            # 返回完整的响应数据
            return data
            
        except Exception as e:
            self.logger.error(f"获取第 {page_index} 页数据失败: {e}")
            return None
    
    def save_page_json(self, data: Dict[str, Any], page_index: int) -> str:
        """
        保存单页数据到 JSON 文件
        
        Args:
            data: 要保存的数据
            page_index: 页码
            
        Returns:
            保存的文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"page_list_page_{page_index:04d}_{timestamp}.json"
        filepath = self.output_dir / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"第 {page_index} 页数据已保存到: {filepath}")
        return str(filepath)
    
    def get_total_pages(self, response_data: Dict[str, Any], page_size: int) -> Optional[int]:
        """
        从响应数据中获取总页数
        
        Args:
            response_data: API 响应数据
            page_size: 每页大小
            
        Returns:
            总页数，如果无法获取则返回 None
        """
        # 尝试多种可能的字段名
        total_count = None
        
        # 检查常见的总数字段
        if "total" in response_data:
            total_count = response_data["total"]
        elif "total_count" in response_data:
            total_count = response_data["total_count"]
        elif "totalCount" in response_data:
            total_count = response_data["totalCount"]
        elif "count" in response_data:
            total_count = response_data["count"]
        elif "data" in response_data and isinstance(response_data["data"], dict):
            data = response_data["data"]
            if "total" in data:
                total_count = data["total"]
            elif "total_count" in data:
                total_count = data["total_count"]
            elif "totalCount" in data:
                total_count = data["totalCount"]
        
        if total_count is None:
            self.logger.warning("无法从响应中获取总记录数")
            return None
        
        # 计算总页数
        total_pages = (total_count + page_size - 1) // page_size  # 向上取整
        self.logger.info(f"总记录数: {total_count}, 每页大小: {page_size}, 总页数: {total_pages}")
        return total_pages
    
    def crawl_all_pages(self, page_size: int = 500, start_page: int = 1) -> Dict[str, Any]:
        """
        循环拉取所有页的数据
        
        Args:
            page_size: 每页大小，默认 500
            start_page: 起始页码，默认 1
            
        Returns:
            结果字典，包含统计信息
        """
        result = {
            "success": False,
            "total_pages": 0,
            "fetched_pages": 0,
            "failed_pages": 0,
            "saved_files": [],
            "error": None
        }
        
        self.logger.info("=" * 60)
        self.logger.info("开始爬取分页数据")
        self.logger.info("=" * 60)
        
        # 先获取第一页，确定总页数
        first_page_data = self.fetch_page(start_page, page_size)
        if not first_page_data:
            result["error"] = "无法获取第一页数据"
            self.logger.error(result["error"])
            return result
        
        # 保存第一页
        filepath = self.save_page_json(first_page_data, start_page)
        result["saved_files"].append(filepath)
        result["fetched_pages"] = 1
        
        # 获取总页数
        total_pages = self.get_total_pages(first_page_data, page_size)
        
        if total_pages is None:
            # 如果无法获取总页数，尝试继续拉取直到返回空数据
            self.logger.warning("无法获取总页数，将尝试拉取直到返回空数据")
            current_page = start_page + 1
            
            while True:
                page_data = self.fetch_page(current_page, page_size)
                if not page_data:
                    self.logger.info(f"第 {current_page} 页获取失败，停止拉取")
                    break
                
                # 检查数据是否为空（响应格式：data.data 是数组）
                data_obj = page_data.get("data", {})
                if isinstance(data_obj, dict):
                    data_list = data_obj.get("data", [])
                else:
                    data_list = data_obj if isinstance(data_obj, list) else []
                
                if isinstance(data_list, list) and len(data_list) == 0:
                    self.logger.info(f"第 {current_page} 页数据为空，停止拉取")
                    break
                
                # 保存数据
                filepath = self.save_page_json(page_data, current_page)
                result["saved_files"].append(filepath)
                result["fetched_pages"] += 1
                
                current_page += 1
                
                # 安全限制：最多拉取 10000 页
                if current_page > start_page + 10000:
                    self.logger.warning("已达到最大页数限制（10000页），停止拉取")
                    break
        else:
            # 已知总页数，循环拉取
            result["total_pages"] = total_pages
            
            for page_index in range(start_page + 1, total_pages + 1):
                page_data = self.fetch_page(page_index, page_size)
                if not page_data:
                    result["failed_pages"] += 1
                    self.logger.warning(f"第 {page_index} 页获取失败，继续下一页")
                    continue
                
                # 保存数据
                filepath = self.save_page_json(page_data, page_index)
                result["saved_files"].append(filepath)
                result["fetched_pages"] += 1
        
        result["success"] = True
        self.logger.info("=" * 60)
        self.logger.info("爬取完成")
        self.logger.info("=" * 60)
        self.logger.info(f"总页数: {result['total_pages']}")
        self.logger.info(f"成功获取: {result['fetched_pages']} 页")
        self.logger.info(f"失败: {result['failed_pages']} 页")
        self.logger.info(f"保存文件数: {len(result['saved_files'])}")
        
        return result
    
    def run(self, page_size: int = 500, start_page: int = 1) -> Dict[str, Any]:
        """
        运行爬虫（主流程）
        
        Args:
            page_size: 每页大小，默认 500
            start_page: 起始页码，默认 1
            
        Returns:
            运行结果字典
        """
        self.logger.info(f"开始运行分页列表爬虫: page_size={page_size}, start_page={start_page}")
        
        result = {
            "crawler_name": self.name,
            "success": False,
            "error": None
        }
        
        try:
            crawl_result = self.crawl_all_pages(page_size, start_page)
            result.update(crawl_result)
            result["success"] = crawl_result["success"]
            
        except Exception as e:
            result["error"] = str(e)
            self.logger.error(f"爬虫运行失败: {self.name}, 错误: {e}", exc_info=True)
        
        return result


def main():
    """主函数：运行爬虫"""
    import argparse
    
    parser = argparse.ArgumentParser(description="分页列表爬虫")
    parser.add_argument(
        "--page-size",
        type=int,
        default=500,
        help="每页大小（默认: 500）"
    )
    parser.add_argument(
        "--start-page",
        type=int,
        default=1,
        help="起始页码（默认: 1）"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/page_list",
        help="输出目录（默认: data/page_list）"
    )
    
    args = parser.parse_args()
    
    # 创建配置
    config = Config.from_env()
    
    # 创建爬虫
    crawler = PageListCrawler(config=config, output_dir=args.output_dir)
    
    # 运行爬虫
    result = crawler.run(page_size=args.page_size, start_page=args.start_page)
    
    if result["success"]:
        print(f"\n成功！共获取 {result['fetched_pages']} 页数据")
        print(f"保存了 {len(result['saved_files'])} 个文件")
        if result.get("total_pages"):
            print(f"总页数: {result['total_pages']}")
    else:
        print(f"\n失败！错误: {result.get('error', '未知错误')}")


if __name__ == "__main__":
    main()

