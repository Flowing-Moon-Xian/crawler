"""
大盘商品关系爬虫（支持千百战、百战等）
从 SteamDT API 获取大盘包含的商品，并插入到 item_statistics_market_index_relations 表
支持通过参数指定不同的大盘类型和对应的 typeVal
"""
import time
from typing import Optional, Dict, Any, List
from datetime import datetime

from crawler.core.api_crawler import APICrawler
from crawler.config.config import Config
from crawler.database.supabase_client import SupabaseManager
from crawler.database.models import ItemStatisticsMarketIndexRelation, MarketIndexType, ItemStatistics, ItemType


class QianzhanMarketIndexCrawler(APICrawler):
    """大盘商品关系爬虫（支持千百战、百战等）"""
    
    # 预定义的大盘配置
    MARKET_CONFIGS = {
        MarketIndexType.QIANZHAN: {
            "type_val": "1402501509110038528",
            "name": "千百战大盘"
        },
        MarketIndexType.BAIZHAN: {
            "type_val": "1368024613355786240",
            "name": "百战大盘"
        },
        MarketIndexType.AGENT: {
            "type_val": "1368076160637956096",
            "name": "探员大盘"
        },
        MarketIndexType.STICKER: {
            "type_val": None,  # TODO: 需要提供贴纸大盘的 typeVal
            "name": "贴纸大盘"
        }
    }
    
    def __init__(
        self, 
        config: Config, 
        market_index_type: MarketIndexType = MarketIndexType.QIANZHAN,
        type_val: Optional[str] = None,
        name: Optional[str] = None
    ):
        """
        初始化爬虫
        
        Args:
            config: 全局配置对象
            market_index_type: 大盘类型，默认为千百战
            type_val: 类型值（typeVal），如果不提供则使用预定义的值
            name: 爬虫名称，如果不提供则根据大盘类型自动生成
        """
        api_url = "https://api.steamdt.com/user/item/block/v1/skin-list"
        
        # 确定大盘类型和类型值
        self.market_index_type = market_index_type
        
        # 如果提供了 type_val，使用提供的值；否则使用预定义的值
        if type_val is None:
            if market_index_type in self.MARKET_CONFIGS:
                config_type_val = self.MARKET_CONFIGS[market_index_type]["type_val"]
                if config_type_val is None:
                    raise ValueError(f"{market_index_type.value} 大盘的 typeVal 未配置，请通过 --type-val 参数提供")
                self.type_val = config_type_val
            else:
                raise ValueError(f"未找到 {market_index_type} 的预定义配置，请提供 type_val 参数")
        else:
            self.type_val = type_val
        
        # 生成爬虫名称
        if name is None:
            market_name = self.MARKET_CONFIGS.get(market_index_type, {}).get("name", market_index_type.value)
            name = f"{market_name.lower().replace('大盘', '')}_market_index"
        
        super().__init__(
            config=config,
            name=name,
            target_table="item_statistics_market_index_relations",
            api_url=api_url,
            unique_key="id",
            headers={
                "Content-Type": "application/json",
            }
        )
        
        # 初始化数据库管理器
        self.supabase = SupabaseManager()
    
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
    
    def _get_item_type_from_market_index_type(self) -> ItemType:
        """
        根据大盘类型推断商品类型
        
        Returns:
            ItemType 枚举值
        """
        # 根据大盘类型映射到商品类型
        market_to_item_type = {
            MarketIndexType.AGENT: ItemType.AGENT,
            MarketIndexType.STICKER: ItemType.STICKER,
        }
        # 如果大盘类型在映射中，返回对应的 item_type；否则默认使用 gun_skin
        return market_to_item_type.get(self.market_index_type, ItemType.GUN_SKIN)
    
    def _create_item_statistics(self, steamdt_id: int, name: str) -> Optional[int]:
        """
        创建新的 item_statistics 记录
        
        Args:
            steamdt_id: SteamDT 商品ID
            name: 商品名称
            
        Returns:
            item_statistics.id，如果创建失败则返回 None
        """
        try:
            # 推断 item_type
            item_type = self._get_item_type_from_market_index_type()
            
            # 创建 ItemStatistics 对象
            # 注意：item_id 字段是必需的，对于 agent/sticker 类型，使用 steamdt_id 作为 item_id
            # 因为 agent 和 sticker 可能没有对应的原始表（gun_skins/knife_gloves）
            item_statistics = ItemStatistics(
                item_id=steamdt_id,  # 使用 steamdt_id 作为 item_id（对于 agent/sticker 类型）
                item_type=item_type,
                name=name,
                steamdt_id=steamdt_id
            )
            
            # 转换为字典并插入数据库
            data = item_statistics.to_dict()
            
            # 插入数据库（使用 upsert，基于 item_id 和 item_type 的唯一约束）
            result = self.supabase.client.table("item_statistics").upsert(
                data,
                on_conflict="item_id,item_type"
            ).execute()
            
            if result.data and len(result.data) > 0:
                item_statistics_id = result.data[0].get("id")
                self.logger.info(f"成功创建 item_statistics 记录: id={item_statistics_id}, steamdt_id={steamdt_id}, name={name}, item_type={item_type.value}")
                return item_statistics_id
            else:
                self.logger.error(f"创建 item_statistics 记录失败: 未返回数据, steamdt_id={steamdt_id}")
                return None
                
        except Exception as e:
            self.logger.error(f"创建 item_statistics 记录失败 (steamdt_id={steamdt_id}, name={name}): {e}")
            return None
    
    def _get_item_statistics_id_by_steamdt(self, steamdt_id: int, item_name: Optional[str] = None) -> Optional[int]:
        """
        根据 steamdt_id 从 item_statistics 表中查找 item_statistics.id
        如果未找到，则创建新记录
        
        Args:
            steamdt_id: SteamDT 商品ID
            item_name: 商品名称（用于创建新记录时使用）
            
        Returns:
            item_statistics.id，如果查找和创建都失败则返回 None
        """
        try:
            result = (
                self.supabase.client.table("item_statistics")
                .select("id")
                .eq("steamdt_id", steamdt_id)
                .limit(1)
                .execute()
            )
            rows = result.data or []
            if rows:
                return rows[0].get("id")
            
            # 如果未找到记录，且提供了名称，则创建新记录
            if item_name:
                self.logger.info(f"未找到 steamdt_id={steamdt_id} 的记录，尝试创建新记录 (name={item_name})")
                return self._create_item_statistics(steamdt_id, item_name)
            else:
                self.logger.debug(f"在 item_statistics 中未找到 steamdt_id={steamdt_id} 的记录，且未提供名称，无法创建")
                return None
        except Exception as e:
            self.logger.error(f"查询 item_statistics 失败 (steamdt_id={steamdt_id}): {e}")
            return None
    
    def fetch_page(self, next_id: str = "", timestamp: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        获取指定页的数据
        
        Args:
            next_id: 下一页ID，用于分页查询
            timestamp: 时间戳，如果为 None 则使用当前时间戳
            
        Returns:
            API 返回的完整响应数据，如果失败返回 None
        """
        try:
            # 生成时间戳
            if timestamp is None:
                timestamp = str(int(time.time() * 1000))
            
            # 构建请求 URL（带时间戳参数）
            url = f"{self.api_url}?timestamp={timestamp}"
            
            # 构建请求负载
            json_data = {
                "type": "HOT",
                "level": "0",
                "typeVal": self.type_val,  # 使用实例变量中的 type_val
                "platform": "ALL",
                "pageSize": 20,
                "nextId": next_id,
                "dataField": "priceRate",
                "dataRange": "SEVEN_DAYS",
                "queryName": "",
                "sortType": "DESC",
                "timestamp": timestamp
            }
            
            self.logger.info(f"正在获取数据 (nextId={next_id or '初始'})...")
            
            # 添加延迟以避免请求过于频繁
            if next_id:
                delay = self.config.crawler.delay if hasattr(self.config.crawler, 'delay') else 1.0
                time.sleep(delay)
            
            response = self.session.post(
                url,
                json=json_data,
                timeout=self.config.crawler.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            # 打印响应数据以便调试
            self.logger.debug(f"API 响应: {data}")
            
            # 检查响应状态（有些 API 可能使用 success 字段而不是 code）
            if isinstance(data, dict):
                code = data.get("code")
                success = data.get("success")
                
                # 如果 code 存在且不等于 200，或者 success 存在且为 False
                if (code is not None and code != 200) or (success is not None and not success):
                    self.logger.warning(f"API 返回错误: code={code}, success={success}, msg={data.get('msg')}, nextId={next_id}")
                    self.logger.debug(f"完整响应数据: {data}")
                    return None
            
            # 返回完整的响应数据
            return data
            
        except Exception as e:
            self.logger.error(f"获取数据失败 (nextId={next_id}): {e}")
            return None
    
    def extract_items_from_response(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        从响应数据中提取商品列表
        
        Args:
            response_data: API 响应数据
            
        Returns:
            商品列表
        """
        items = []
        
        # 尝试多种可能的响应格式
        if "data" in response_data:
            data = response_data["data"]
            
            # 如果 data 是列表
            if isinstance(data, list):
                items = data
            # 如果 data 是字典，尝试查找列表字段
            elif isinstance(data, dict):
                if "list" in data and isinstance(data["list"], list):
                    items = data["list"]
                elif "data" in data and isinstance(data["data"], list):
                    items = data["data"]
                elif "items" in data and isinstance(data["items"], list):
                    items = data["items"]
                elif "results" in data and isinstance(data["results"], list):
                    items = data["results"]
        
        return items
    
    def get_next_id_from_response(self, response_data: Dict[str, Any]) -> Optional[str]:
        """
        从响应数据中获取下一页ID
        
        Args:
            response_data: API 响应数据
            
        Returns:
            下一页ID，如果没有下一页则返回 None
        """
        # 尝试多种可能的字段名
        if "data" in response_data:
            data = response_data["data"]
            if isinstance(data, dict):
                # 检查是否有下一页
                if "hasMore" in data and not data["hasMore"]:
                    return None
                if "has_more" in data and not data["has_more"]:
                    return None
                
                # 获取 nextId
                if "nextId" in data:
                    next_id = data["nextId"]
                    # 如果 nextId 为空字符串或 None，表示没有更多数据
                    if next_id is None or next_id == "":
                        return None
                    return str(next_id)
                if "next_id" in data:
                    next_id = data["next_id"]
                    if next_id is None or next_id == "":
                        return None
                    return str(next_id)
        
        # 如果响应中没有 nextId 字段，检查是否还有数据
        items = self.extract_items_from_response(response_data)
        # 如果返回的商品数量少于 pageSize，说明没有更多数据
        if len(items) < 20:  # pageSize 是 20
            return None
        
        # 如果有数据但没有明确的 nextId，尝试使用最后一项的ID
        # 但这里先返回 None，因为不确定 API 是否支持这种方式
        # 如果需要，可以根据实际 API 响应调整
        return None
    
    def insert_relations(self, item_statistics_ids: List[int]) -> Dict[str, int]:
        """
        批量插入商品-大盘关系
        
        Args:
            item_statistics_ids: item_statistics.id 列表
            
        Returns:
            统计信息字典
        """
        stats = {
            "total": len(item_statistics_ids),
            "inserted": 0,
            "skipped": 0,
            "errors": 0
        }
        
        if not item_statistics_ids:
            return stats
        
        relations = []
        for item_statistics_id in item_statistics_ids:
            relation = ItemStatisticsMarketIndexRelation(
                item_statistics_id=item_statistics_id,
                market_index_type=self.market_index_type
            )
            relations.append(relation.to_dict())
        
        # 批量插入（使用 upsert 避免重复）
        try:
            # 由于有 UNIQUE 约束，使用 upsert
            result = self.supabase.client.table(self.target_table).upsert(
                relations,
                on_conflict="item_statistics_id,market_index_type"
            ).execute()
            
            inserted_count = len(result.data) if result.data else 0
            stats["inserted"] = inserted_count
            stats["skipped"] = stats["total"] - inserted_count
            
            self.logger.info(f"成功插入 {inserted_count} 条关系记录")
            
        except Exception as e:
            self.logger.error(f"批量插入关系失败: {e}")
            stats["errors"] = stats["total"]
        
        return stats
    
    def crawl_all_pages(self, batch_size: int = 100) -> Dict[str, Any]:
        """
        循环拉取所有页的数据并插入数据库
        
        Args:
            batch_size: 批量插入的批次大小，默认 100 条
        
        Returns:
            结果字典，包含统计信息
        """
        result = {
            "success": False,
            "total_pages": 0,
            "total_items": 0,
            "total_relations_inserted": 0,
            "total_relations_skipped": 0,
            "total_relations_errors": 0,
            "items_not_found": 0,
            "error": None
        }
        
        market_name = self.MARKET_CONFIGS.get(self.market_index_type, {}).get("name", self.market_index_type.value)
        self.logger.info("=" * 60)
        self.logger.info(f"开始爬取{market_name}商品关系")
        self.logger.info(f"大盘类型: {self.market_index_type.value}, typeVal: {self.type_val}")
        self.logger.info(f"批量插入批次大小: {batch_size}")
        self.logger.info("=" * 60)
        
        next_id = ""
        page_count = 0
        all_item_statistics_ids = []
        pending_item_statistics_ids = []  # 待插入的批次
        items_not_found = []
        
        while True:
            page_count += 1
            
            # 获取当前页数据
            page_data = self.fetch_page(next_id)
            if not page_data:
                self.logger.warning(f"第 {page_count} 页获取失败，停止拉取")
                break
            
            # 提取商品列表
            items = self.extract_items_from_response(page_data)
            if not items:
                self.logger.info(f"第 {page_count} 页数据为空，停止拉取")
                break
            
            self.logger.info(f"第 {page_count} 页获取到 {len(items)} 个商品")
            result["total_items"] += len(items)
            
            # 处理每个商品，查找对应的 item_statistics_id
            page_item_statistics_ids = []
            for item in items:
                # 尝试多种可能的字段名来获取 steamdt_id
                # 根据 API 响应，商品ID在 typeVal 字段中
                steamdt_id = None
                if "typeVal" in item:
                    steamdt_id = item["typeVal"]
                elif "id" in item:
                    steamdt_id = item["id"]
                elif "steamdt_id" in item:
                    steamdt_id = item["steamdt_id"]
                elif "itemId" in item:
                    steamdt_id = item["itemId"]
                elif "item_id" in item:
                    steamdt_id = item["item_id"]
                
                if steamdt_id is None:
                    self.logger.warning(f"商品数据中未找到ID字段: {item}")
                    items_not_found.append(item)
                    continue
                
                # 确保 steamdt_id 是整数
                try:
                    steamdt_id = int(steamdt_id)
                except (ValueError, TypeError):
                    self.logger.warning(f"商品ID格式错误: {steamdt_id}, 商品: {item.get('name', 'Unknown')}")
                    items_not_found.append(item)
                    continue
                
                # 获取商品名称
                item_name = item.get("name") or item.get("itemName") or item.get("shortName") or "Unknown"
                
                # 查找对应的 item_statistics_id（如果不存在则自动创建）
                item_statistics_id = self._get_item_statistics_id_by_steamdt(steamdt_id, item_name=item_name)
                if item_statistics_id is None:
                    self.logger.warning(f"无法获取或创建 steamdt_id={steamdt_id} 对应的 item_statistics 记录 (商品: {item_name})")
                    items_not_found.append({"steamdt_id": steamdt_id, "item": item, "item_name": item_name})
                    continue
                
                page_item_statistics_ids.append(item_statistics_id)
            
            # 累积到待插入批次
            if page_item_statistics_ids:
                pending_item_statistics_ids.extend(page_item_statistics_ids)
                all_item_statistics_ids.extend(page_item_statistics_ids)
            
            # 当累积的数据达到批次大小时，批量插入
            if len(pending_item_statistics_ids) >= batch_size:
                batch_to_insert = pending_item_statistics_ids[:batch_size]
                pending_item_statistics_ids = pending_item_statistics_ids[batch_size:]
                
                stats = self.insert_relations(batch_to_insert)
                result["total_relations_inserted"] += stats["inserted"]
                result["total_relations_skipped"] += stats["skipped"]
                result["total_relations_errors"] += stats["errors"]
                self.logger.info(f"已累积插入 {result['total_relations_inserted']} 条关系")
            
            # 获取下一页ID
            next_id = self.get_next_id_from_response(page_data)
            if next_id is None:
                self.logger.info("没有更多数据，停止拉取")
                break
            
            # 如果 next_id 为空字符串，重置为空字符串继续查询（某些 API 可能使用空字符串表示第一页）
            if next_id == "":
                # 如果当前页返回的数据少于 pageSize，说明没有更多数据
                if len(items) < 20:
                    self.logger.info("返回数据少于 pageSize，停止拉取")
                    break
            
            # 安全限制：最多拉取 10000 页
            if page_count >= 10000:
                self.logger.warning("已达到最大页数限制（10000页），停止拉取")
                break
        
        # 插入剩余的数据
        if pending_item_statistics_ids:
            self.logger.info(f"插入剩余 {len(pending_item_statistics_ids)} 条关系")
            stats = self.insert_relations(pending_item_statistics_ids)
            result["total_relations_inserted"] += stats["inserted"]
            result["total_relations_skipped"] += stats["skipped"]
            result["total_relations_errors"] += stats["errors"]
        
        result["total_pages"] = page_count
        result["items_not_found"] = len(items_not_found)
        result["success"] = True
        
        self.logger.info("=" * 60)
        self.logger.info("爬取完成")
        self.logger.info("=" * 60)
        self.logger.info(f"总页数: {result['total_pages']}")
        self.logger.info(f"总商品数: {result['total_items']}")
        self.logger.info(f"成功插入关系: {result['total_relations_inserted']}")
        self.logger.info(f"跳过关系（已存在）: {result['total_relations_skipped']}")
        self.logger.info(f"错误关系: {result['total_relations_errors']}")
        self.logger.info(f"未找到 item_statistics 的商品数: {result['items_not_found']}")
        
        if items_not_found:
            self.logger.warning(f"未找到 item_statistics 的商品示例（前10个）:")
            for item in items_not_found[:10]:
                self.logger.warning(f"  {item}")
        
        return result
    
    def run(self, batch_size: int = 100) -> Dict[str, Any]:
        """
        运行爬虫（主流程）
        
        Args:
            batch_size: 批量插入的批次大小，默认 100 条
        
        Returns:
            运行结果字典
        """
        market_name = self.MARKET_CONFIGS.get(self.market_index_type, {}).get("name", self.market_index_type.value)
        self.logger.info(f"开始运行{market_name}商品关系爬虫")
        
        result = {
            "crawler_name": self.name,
            "success": False,
            "error": None
        }
        
        try:
            crawl_result = self.crawl_all_pages(batch_size=batch_size)
            result.update(crawl_result)
            result["success"] = crawl_result["success"]
            
        except Exception as e:
            result["error"] = str(e)
            self.logger.error(f"爬虫运行失败: {self.name}, 错误: {e}", exc_info=True)
        
        return result


def main():
    """主函数：运行爬虫"""
    import argparse
    
    parser = argparse.ArgumentParser(description="大盘商品关系爬虫（支持千百战、百战等）")
    parser.add_argument(
        "--market-type",
        type=str,
        default="qianzhan",
        choices=["qianzhan", "baizhan", "agent", "sticker"],
        help="大盘类型（默认: qianzhan），可选: qianzhan=千百战大盘, baizhan=百战大盘, agent=探员大盘, sticker=贴纸大盘"
    )
    parser.add_argument(
        "--type-val",
        type=str,
        default=None,
        help="类型值（typeVal），如果不提供则使用预定义的值"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="批量插入的批次大小（默认: 100）"
    )
    
    args = parser.parse_args()
    
    # 映射市场类型字符串到枚举
    market_type_map = {
        "qianzhan": MarketIndexType.QIANZHAN,
        "baizhan": MarketIndexType.BAIZHAN,
        "agent": MarketIndexType.AGENT,
        "sticker": MarketIndexType.STICKER
    }
    market_index_type = market_type_map[args.market_type]
    
    # 创建配置
    config = Config.from_env()
    
    # 创建爬虫
    crawler = QianzhanMarketIndexCrawler(
        config=config,
        market_index_type=market_index_type,
        type_val=args.type_val
    )
    
    # 运行爬虫
    result = crawler.run(batch_size=args.batch_size)
    
    if result["success"]:
        print(f"\n✅ 成功！")
        print(f"总页数: {result.get('total_pages', 0)}")
        print(f"总商品数: {result.get('total_items', 0)}")
        print(f"成功插入关系: {result.get('total_relations_inserted', 0)}")
        print(f"跳过关系（已存在）: {result.get('total_relations_skipped', 0)}")
        print(f"未找到 item_statistics 的商品数: {result.get('items_not_found', 0)}")
    else:
        print(f"\n❌ 失败！错误: {result.get('error', '未知错误')}")


if __name__ == "__main__":
    main()

