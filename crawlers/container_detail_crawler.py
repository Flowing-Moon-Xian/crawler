"""
箱子详情爬虫
获取箱子内的枪皮和刀/手套信息
"""
from typing import List, Dict, Any, Optional
from datetime import datetime

from crawler.core.api_crawler import APICrawler
from crawler.config.config import Config


class ContainerDetailCrawler(APICrawler):
    """箱子详情爬虫"""
    
    def __init__(self, config: Config, name: str = "container_detail"):
        """
        初始化箱子详情爬虫
        
        Args:
            config: 全局配置对象
            name: 爬虫名称
        """
        api_url = "https://api.csqaq.com/api/v1/info/good/container_detail"
        self.token = "AQPI91A7P5Z9J0U4O3P3N6T8"
        
        super().__init__(
            config=config,
            name=name,
            target_table="gun_skins",  # 默认表（实际会保存到多个表）
            api_url=api_url,
            unique_key="qaq_id",
            headers={
                "Authorization": f"Bearer {self.token}"
            }
        )
    
    def fetch_data(self, qaq_id: int) -> Optional[List[Dict[str, Any]]]:
        """
        获取指定箱子的详情数据
        
        Args:
            qaq_id: 箱子的 qaq_id
            
        Returns:
            API 返回的数据列表
        """
        try:
            response = self.session.get(
                self.api_url,
                params={"qaq_id": qaq_id},
                timeout=self.config.crawler.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            # 检查响应状态
            if data.get("code") != 200:
                self.logger.warning(f"API 返回错误: {data.get('msg')}, qaq_id={qaq_id}")
                return None
            
            # 提取 data 数组
            items = data.get("data", [])
            if not items:
                self.logger.warning(f"箱子 {qaq_id} 没有内容")
                return None
            
            return items
            
        except Exception as e:
            self.logger.error(f"获取箱子详情失败 qaq_id={qaq_id}: {e}")
            return None
    
    def transform_data(self, raw_data: List[Dict[str, Any]], box_qaq_id: int) -> Dict[str, Any]:
        """
        转换数据格式
        将 API 返回的数据转换为数据库表格式
        
        Args:
            raw_data: 原始数据列表
            box_qaq_id: 箱子的 qaq_id
            
        Returns:
            包含 gun_skins, knife_gloves, relations 的字典
        """
        gun_skins = []
        knife_gloves = []
        gun_skin_relations = []
        knife_glove_relations = []
        
        for item in raw_data:
            qaq_id = item.get("id")
            rln = item.get("rln")  # 稀有度（中文）
            short_name = item.get("short_name")  # 短名称
            
            if not qaq_id or not short_name:
                self.logger.warning(f"跳过缺少必要字段的数据项: {item}")
                continue
            
            # 构建 URL
            qaq_url = f"https://csqaq.com/goods/{qaq_id}"
            
            # 暂时都保存为枪皮（如果后续需要区分，可以根据名称或其他字段判断）
            # TODO: 根据实际需求添加类型判断逻辑
            gun_skin_data = {
                "qaq_id": qaq_id,
                "qaq_url": qaq_url,
                "name": short_name,
                "rarity": self._map_rarity(rln),  # rln 是中文，需要映射
            }
            gun_skins.append(gun_skin_data)
            gun_skin_relations.append({
                "box_qaq_id": box_qaq_id,
                "gun_skin_qaq_id": qaq_id
            })
        
        return {
            "gun_skins": gun_skins,
            "knife_gloves": knife_gloves,  # 暂时为空，后续如果需要可以添加
            "gun_skin_relations": gun_skin_relations,
            "knife_glove_relations": knife_glove_relations  # 暂时为空
        }
    
    def _map_rarity(self, rln: Optional[str]) -> Optional[str]:
        """
        映射稀有度（支持中文）
        将 API 返回的中文 rln 映射到数据库的 rarity_type
        
        Args:
            rln: API 返回的稀有度字符串（中文）
            
        Returns:
            数据库枚举值
        """
        if not rln:
            return None
        
        # API 返回的是中文，直接使用中文映射
        rarity_map = {
            "消费": "consumer",
            "工业": "industrial",
            "军规级": "mil_spec",
            "军规": "mil_spec",
            "受限": "restricted",
            "保密": "classified",
            "隐秘": "covert",
            "违禁": "contraband",
            "非凡": "exceptional",
            # 也支持英文（以防万一）
            "consumer": "consumer",
            "industrial": "industrial",
            "mil_spec": "mil_spec",
            "restricted": "restricted",
            "classified": "classified",
            "covert": "covert",
            "contraband": "contraband",
            "exceptional": "exceptional",
        }
        
        return rarity_map.get(rln)
    
    def get_filtered_boxes(self) -> List[Dict[str, Any]]:
        """
        获取符合条件的箱子列表（名字中包含"武器箱"或"收藏品"）
        
        Returns:
            箱子列表，包含 id 和 qaq_id
        """
        if not self.supabase:
            self.logger.error("Supabase 客户端未初始化")
            return []
        
        try:
            # 使用 Supabase 的 or 和 ilike 查询
            # 查询名字中包含"武器箱"或"收藏品"的箱子
            result = self.supabase.client.table("boxes").select("id,qaq_id,name").or_(
                "name.ilike.*武器箱*,name.ilike.*收藏品*"
            ).execute()
            
            boxes = result.data if result.data else []
            self.logger.info(f"找到 {len(boxes)} 个符合条件的箱子（包含'武器箱'或'收藏品'）")
            return boxes
            
        except Exception as e:
            self.logger.error(f"查询箱子列表失败: {e}")
            # 如果 or_ 语法不支持，尝试分别查询然后合并
            try:
                result1 = self.supabase.client.table("boxes").select("id,qaq_id,name").ilike("name", "%武器箱%").execute()
                result2 = self.supabase.client.table("boxes").select("id,qaq_id,name").ilike("name", "%收藏品%").execute()
                
                boxes1 = result1.data if result1.data else []
                boxes2 = result2.data if result2.data else []
                
                # 合并并去重（基于 qaq_id）
                seen = set()
                boxes = []
                for box in boxes1 + boxes2:
                    qaq_id = box.get("qaq_id")
                    if qaq_id and qaq_id not in seen:
                        seen.add(qaq_id)
                        boxes.append(box)
                
                self.logger.info(f"找到 {len(boxes)} 个符合条件的箱子（包含'武器箱'或'收藏品'）")
                return boxes
            except Exception as e2:
                self.logger.error(f"备用查询方法也失败: {e2}")
                return []
    
    def save_to_database(
        self,
        transformed_data: Dict[str, Any],
        box_qaq_id: int
    ) -> Dict[str, int]:
        """
        保存数据到数据库（保存到多个表）
        
        Args:
            transformed_data: 转换后的数据
            box_qaq_id: 箱子的 qaq_id
            
        Returns:
            统计信息字典
        """
        if not self.supabase:
            self.logger.error("Supabase 客户端未初始化，无法保存到数据库")
            return {"success": 0, "failed": 0, "gun_skins": 0, "knife_gloves": 0, "relations": 0}
        
        stats = {
            "gun_skins": 0,
            "knife_gloves": 0,
            "gun_skin_relations": 0,
            "knife_glove_relations": 0,
            "failed": 0
        }
        
        # 1. 获取 box_id（通过 qaq_id 查找，且名字必须包含"武器箱"或"收藏品"）
        try:
            # 先查询箱子是否存在
            box_result = self.supabase.query_data(
                table="boxes",
                filters={"qaq_id": box_qaq_id},
                limit=1
            )
            
            if not box_result:
                self.logger.error(f"未找到 qaq_id={box_qaq_id} 的箱子")
                stats["failed"] = 1
                return stats
            
            box = box_result[0]
            box_name = box.get("name", "")
            
            # 检查名字是否包含"武器箱"或"收藏品"
            if "武器箱" not in box_name and "收藏品" not in box_name:
                self.logger.warning(f"箱子 qaq_id={box_qaq_id} 名字不包含'武器箱'或'收藏品'，跳过: {box_name}")
                stats["failed"] = 1
                return stats
            
            box_id = box["id"]
        except Exception as e:
            self.logger.error(f"查询箱子失败: {e}")
            stats["failed"] = 1
            return stats
        
        # 2. 保存枪皮
        for gun_skin in transformed_data.get("gun_skins", []):
            try:
                # 检查是否已存在
                existing = self.supabase.query_data(
                    table="gun_skins",
                    filters={"qaq_id": gun_skin["qaq_id"]},
                    limit=1
                )
                
                if existing:
                    gun_skin_id = existing[0]["id"]
                else:
                    # 插入新枪皮
                    result = self.supabase.insert_data("gun_skins", gun_skin)
                    if result:
                        gun_skin_id = result["id"]
                        stats["gun_skins"] += 1
                    else:
                        stats["failed"] += 1
                        continue
                
                # 建立关系
                relation = {
                    "box_id": box_id,
                    "gun_skin_id": gun_skin_id
                }
                existing_relation = self.supabase.query_data(
                    table="box_gun_skin_relations",
                    filters={"box_id": box_id, "gun_skin_id": gun_skin_id},
                    limit=1
                )
                if not existing_relation:
                    self.supabase.insert_data("box_gun_skin_relations", relation)
                    stats["gun_skin_relations"] += 1
                    
            except Exception as e:
                self.logger.error(f"保存枪皮失败: {e}, data={gun_skin}")
                stats["failed"] += 1
        
        # 3. 保存刀/手套
        for knife_glove in transformed_data.get("knife_gloves", []):
            try:
                # 检查是否已存在
                existing = self.supabase.query_data(
                    table="knife_gloves",
                    filters={"qaq_id": knife_glove["qaq_id"]},
                    limit=1
                )
                
                if existing:
                    knife_glove_id = existing[0]["id"]
                else:
                    # 插入新刀/手套
                    result = self.supabase.insert_data("knife_gloves", knife_glove)
                    if result:
                        knife_glove_id = result["id"]
                        stats["knife_gloves"] += 1
                    else:
                        stats["failed"] += 1
                        continue
                
                # 建立关系
                relation = {
                    "box_id": box_id,
                    "knife_glove_id": knife_glove_id
                }
                existing_relation = self.supabase.query_data(
                    table="box_knife_glove_relations",
                    filters={"box_id": box_id, "knife_glove_id": knife_glove_id},
                    limit=1
                )
                if not existing_relation:
                    self.supabase.insert_data("box_knife_glove_relations", relation)
                    stats["knife_glove_relations"] += 1
                    
            except Exception as e:
                self.logger.error(f"保存刀/手套失败: {e}, data={knife_glove}")
                stats["failed"] += 1
        
        return stats
    
    def run(self, box_qaq_id: int) -> Dict[str, Any]:
        """
        运行爬虫（主流程）
        
        Args:
            box_qaq_id: 箱子的 qaq_id
            
        Returns:
            运行结果字典
        """
        self.logger.info(f"开始获取箱子详情: qaq_id={box_qaq_id}")
        
        result = {
            "crawler_name": self.name,
            "box_qaq_id": box_qaq_id,
            "success": False,
            "data_count": 0,
            "saved_count": 0,
            "error": None
        }
        
        try:
            # 1. 获取数据
            raw_data = self.fetch_data(box_qaq_id)
            if not raw_data:
                result["error"] = "未能获取数据"
                return result
            
            # 2. 转换数据
            transformed_data = self.transform_data(raw_data, box_qaq_id)
            total_items = len(transformed_data.get("gun_skins", [])) + len(transformed_data.get("knife_gloves", []))
            result["data_count"] = total_items
            
            if total_items == 0:
                result["error"] = "转换后无有效数据"
                return result
            
            # 3. 保存到文件（如果启用）
            if self.config.crawler.save_to_file:
                self.save_to_file([transformed_data], f"container_detail_{box_qaq_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            
            # 4. 保存到数据库（如果启用）
            if self.config.crawler.save_to_db and self.supabase:
                db_stats = self.save_to_database(transformed_data, box_qaq_id)
                result["saved_count"] = db_stats["gun_skins"] + db_stats["knife_gloves"]
                result["db_stats"] = db_stats
            elif self.config.crawler.save_to_db and not self.supabase:
                self.logger.warning("数据库保存已启用但 Supabase 未初始化")
            
            result["success"] = True
            self.logger.info(f"爬虫运行完成: {self.name}, 获取 {result['data_count']} 条数据")
            
        except Exception as e:
            result["error"] = str(e)
            self.logger.error(f"爬虫运行失败: {self.name}, 错误: {e}", exc_info=True)
        
        return result

