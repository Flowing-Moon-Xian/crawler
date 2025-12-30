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
                "ApiToken": self.token  # API 使用 ApiToken 头，不是 Authorization
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
                params={"id": qaq_id},  # API 使用 id 参数，不是 qaq_id
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
        
        规则：
        - 如果稀有度是"非凡"（exceptional），则是刀/手套，保存到 knife_gloves 表
        - 如果是枪皮，名字中"|"前面的是武器类型，保存到 gun_skins 表
        
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
            
            # 过滤掉箱子本身（名字包含"武器箱"或"收藏品"的项目）
            if "武器箱" in short_name or "收藏品" in short_name:
                self.logger.debug(f"跳过箱子本身: {short_name} (qaq_id={qaq_id})")
                continue
            
            # 只保存受限及以上品质，先快速过滤低品质（避免不必要的映射）
            # 允许的品质：受限、保密、隐秘、违禁、非凡
            low_quality_keywords = {"普通级", "普通", "消费级", "消费", "工业级", "工业", "军规级", "军规"}
            if rln in low_quality_keywords:
                # 低品质直接跳过，不记录日志（因为数量很多）
                continue
            
            # 构建 URL
            qaq_url = f"https://csqaq.com/goods/{qaq_id}"
            rarity = self._map_rarity(rln)  # 映射稀有度
            
            # 如果稀有度映射失败，跳过该项（避免保存失败）
            if rarity is None:
                self.logger.warning(f"跳过无法映射稀有度的数据项: {short_name} (rln={rln}, qaq_id={qaq_id})")
                continue
            
            # 再次确认只保存受限及以上品质（restricted, classified, covert, contraband, exceptional）
            allowed_rarities = {"restricted", "classified", "covert", "contraband", "exceptional"}
            if rarity not in allowed_rarities:
                # 理论上不应该到这里（因为前面已经过滤了），但为了安全起见保留检查
                continue
            
            # 判断是否为非凡品质（刀/手套）
            if rln == "非凡" or rarity == "exceptional":
                # 判断是刀还是手套
                item_type = self._determine_knife_or_glove(short_name)
                
                knife_glove_data = {
                    "qaq_id": qaq_id,
                    "qaq_url": qaq_url,
                    "name": short_name,
                    "item_type": item_type,
                    "rarity": rarity,
                }
                knife_gloves.append(knife_glove_data)
                # 关系数据（用于后续建立关系，但实际关系是在 save_to_database 中通过数据库 ID 建立的）
                knife_glove_relations.append({
                    "box_qaq_id": box_qaq_id,
                    "knife_glove_qaq_id": qaq_id
                })
            else:
                # 枪皮：从名字中提取武器类型（"|"前面的部分）
                weapon_type = self._extract_weapon_type(short_name)
                
                gun_skin_data = {
                    "qaq_id": qaq_id,
                    "qaq_url": qaq_url,
                    "name": short_name,
                    "weapon_type": weapon_type,
                    "rarity": rarity,
                }
                gun_skins.append(gun_skin_data)
                gun_skin_relations.append({
                    "box_qaq_id": box_qaq_id,
                    "gun_skin_qaq_id": qaq_id
                })
        
        return {
            "gun_skins": gun_skins,
            "knife_gloves": knife_gloves,
            "gun_skin_relations": gun_skin_relations,
            "knife_glove_relations": knife_glove_relations
        }
    
    def _determine_knife_or_glove(self, name: str) -> str:
        """
        判断是刀还是手套
        
        Args:
            name: 商品名称
            
        Returns:
            'knife' 或 'glove'
        """
        name_lower = name.lower()
        
        # 检查是否包含手套相关关键词
        glove_keywords = ["手套", "glove"]
        for keyword in glove_keywords:
            if keyword in name_lower:
                return "glove"
        
        # 默认是刀
        return "knife"
    
    def _extract_weapon_type(self, name: str) -> Optional[str]:
        """
        从名字中提取武器类型（"|"前面的部分）
        
        Args:
            name: 商品名称，格式如 "AK-47 | 红线"
            
        Returns:
            武器类型，如 "AK-47"，如果没有"|"则返回 None
        """
        if "|" in name:
            weapon_type = name.split("|")[0].strip()
            return weapon_type if weapon_type else None
        return None
    
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
            "普通级": "normal",
            "普通": "normal",
            "消费级": "consumer",
            "消费": "consumer",
            "工业级": "industrial",
            "工业": "industrial",
            "军规级": "mil_spec",
            "军规": "mil_spec",
            "受限": "restricted",
            "保密": "classified",
            "隐秘": "covert",
            "违禁": "contraband",
            "非凡": "exceptional",
            # 也支持英文（以防万一）
            "normal": "normal",
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
            self.logger.info(f"查询箱子信息: qaq_id={box_qaq_id}")
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
            self.logger.info(f"找到箱子: {box_name} (id={box_id})")
        except Exception as e:
            self.logger.error(f"查询箱子失败: {e}")
            stats["failed"] = 1
            return stats
        
        # 2. 批量保存枪皮（使用 upsert，避免唯一约束冲突）
        gun_skins_list = transformed_data.get("gun_skins", [])
        total_gun_skins = len(gun_skins_list)
        if total_gun_skins > 0:
            self.logger.info(f"开始批量保存 {total_gun_skins} 个枪皮...")
            try:
                # 使用 upsert，如果 qaq_id 已存在则更新，不存在则插入
                result = self.supabase.client.table("gun_skins").upsert(
                    gun_skins_list,
                    on_conflict="qaq_id"
                ).execute()
                
                if result.data:
                    stats["gun_skins"] = len(result.data)
                    self.logger.info(f"成功保存 {stats['gun_skins']} 个枪皮（插入或更新）")
                    
                    # 构建 qaq_id 到 id 的映射
                    qaq_id_to_id = {item["qaq_id"]: item["id"] for item in result.data}
                    
                    # 批量插入关系（使用 upsert 避免重复）
                    relations = [
                        {"box_id": box_id, "gun_skin_id": qaq_id_to_id[gun_skin["qaq_id"]]}
                        for gun_skin in gun_skins_list
                        if gun_skin["qaq_id"] in qaq_id_to_id
                    ]
                    
                    if relations:
                        relation_result = self.supabase.client.table("box_gun_skin_relations").upsert(
                            relations,
                            on_conflict="box_id,gun_skin_id"
                        ).execute()
                        stats["gun_skin_relations"] = len(relation_result.data) if relation_result.data else 0
                        self.logger.info(f"成功保存 {stats['gun_skin_relations']} 个枪皮关系")
                else:
                    self.logger.warning("枪皮 upsert 未返回数据")
                    stats["failed"] = total_gun_skins
                    
            except Exception as e:
                self.logger.error(f"批量保存枪皮失败: {e}")
                stats["failed"] = total_gun_skins
        
        # 3. 批量保存刀/手套（使用 upsert，避免唯一约束冲突）
        knife_gloves_list = transformed_data.get("knife_gloves", [])
        total_knife_gloves = len(knife_gloves_list)
        if total_knife_gloves > 0:
            self.logger.info(f"开始批量保存 {total_knife_gloves} 个刀/手套...")
            try:
                # 使用 upsert，如果 qaq_id 已存在则更新，不存在则插入
                result = self.supabase.client.table("knife_gloves").upsert(
                    knife_gloves_list,
                    on_conflict="qaq_id"
                ).execute()
                
                if result.data:
                    stats["knife_gloves"] = len(result.data)
                    self.logger.info(f"成功保存 {stats['knife_gloves']} 个刀/手套（插入或更新）")
                    
                    # 构建 qaq_id 到 id 的映射
                    qaq_id_to_id = {item["qaq_id"]: item["id"] for item in result.data}
                    
                    # 批量插入关系（使用 upsert 避免重复）
                    relations = [
                        {"box_id": box_id, "knife_glove_id": qaq_id_to_id[knife_glove["qaq_id"]]}
                        for knife_glove in knife_gloves_list
                        if knife_glove["qaq_id"] in qaq_id_to_id
                    ]
                    
                    if relations:
                        relation_result = self.supabase.client.table("box_knife_glove_relations").upsert(
                            relations,
                            on_conflict="box_id,knife_glove_id"
                        ).execute()
                        stats["knife_glove_relations"] = len(relation_result.data) if relation_result.data else 0
                        self.logger.info(f"成功保存 {stats['knife_glove_relations']} 个刀/手套关系")
                else:
                    self.logger.warning("刀/手套 upsert 未返回数据")
                    stats["failed"] = total_knife_gloves
                    
            except Exception as e:
                self.logger.error(f"批量保存刀/手套失败: {e}")
                stats["failed"] = total_knife_gloves
        
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
            self.logger.info(f"开始转换数据，原始数据项数: {len(raw_data)}")
            transformed_data = self.transform_data(raw_data, box_qaq_id)
            total_items = len(transformed_data.get("gun_skins", [])) + len(transformed_data.get("knife_gloves", []))
            gun_skins_count = len(transformed_data.get("gun_skins", []))
            knife_gloves_count = len(transformed_data.get("knife_gloves", []))
            result["data_count"] = total_items
            
            self.logger.info(f"数据转换完成: 枪皮 {gun_skins_count} 个, 刀/手套 {knife_gloves_count} 个, 总计 {total_items} 个")
            
            if total_items == 0:
                result["error"] = "转换后无有效数据"
                return result
            
            # 3. 保存到文件（如果启用）
            if self.config.crawler.save_to_file:
                self.save_to_file([transformed_data], f"container_detail_{box_qaq_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            
            # 4. 保存到数据库（如果启用）
            if self.config.crawler.save_to_db and self.supabase:
                self.logger.info("开始保存数据到数据库...")
                db_stats = self.save_to_database(transformed_data, box_qaq_id)
                result["saved_count"] = db_stats["gun_skins"] + db_stats["knife_gloves"]
                result["db_stats"] = db_stats
                self.logger.info(f"数据库保存完成: 新增枪皮 {db_stats['gun_skins']} 个, 新增刀/手套 {db_stats['knife_gloves']} 个, "
                               f"关系 {db_stats['gun_skin_relations'] + db_stats['knife_glove_relations']} 个, "
                               f"失败 {db_stats['failed']} 个")
            elif self.config.crawler.save_to_db and not self.supabase:
                self.logger.warning("数据库保存已启用但 Supabase 未初始化")
            
            result["success"] = True
            self.logger.info(f"爬虫运行完成: {self.name}, 获取 {result['data_count']} 条数据")
            
        except Exception as e:
            result["error"] = str(e)
            self.logger.error(f"爬虫运行失败: {self.name}, 错误: {e}", exc_info=True)
        
        return result

