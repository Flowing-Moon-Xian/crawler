"""
更新磨损度字段脚本
根据数据库中的 qaq_id 查找 JSON 文件，补全数据库中对应字段的 wear_condition
"""
import json
import logging
from pathlib import Path
from typing import Dict, Optional, List, Any
from glob import glob

from crawler.config.config import Config
from crawler.database.supabase_client import SupabaseManager
from crawler.database.models import WearCondition


class WearConditionUpdater:
    """磨损度更新器"""
    
    def __init__(self, config: Optional[Config] = None, json_dir: str = "data/page_list"):
        """
        初始化更新器
        
        Args:
            config: 配置对象，如果为 None 则从环境变量加载
            json_dir: JSON 文件目录，默认为 "data/page_list"
        """
        self.config = config or Config.from_env()
        self.json_dir = Path(json_dir)
        
        # 初始化 Supabase 客户端
        if not self.config.supabase:
            raise ValueError("Supabase 配置未找到，无法连接数据库")
        
        self.supabase = SupabaseManager(
            url=self.config.supabase.url,
            key=self.config.supabase.key
        )
        
        # 设置日志
        self.logger = logging.getLogger("WearConditionUpdater")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        
        # 磨损度映射（中文 -> 数据库枚举值）
        self.wear_condition_map = {
            "崭新出厂": WearCondition.FACTORY_NEW.value,
            "略有磨损": WearCondition.MINIMAL_WEAR.value,
            "久经沙场": WearCondition.FIELD_TESTED.value,
            "战痕累累": WearCondition.WELL_WORN.value,
            "破损不堪": WearCondition.BATTLE_SCARRED.value,
        }
    
    def load_json_files(self) -> Dict[int, Dict]:
        """
        加载所有 JSON 文件，构建 qaq_id -> 数据项的映射
        
        Returns:
            字典，key 为 qaq_id，value 为数据项
        """
        json_files = list(self.json_dir.glob("page_list_page_*.json"))
        
        if not json_files:
            self.logger.warning(f"在 {self.json_dir} 中未找到 JSON 文件")
            return {}
        
        self.logger.info(f"找到 {len(json_files)} 个 JSON 文件，开始加载...")
        
        qaq_id_map = {}
        total_items = 0
        
        for json_file in json_files:
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # 检查响应格式
                if data.get("code") != 200:
                    self.logger.warning(f"跳过无效响应文件: {json_file.name}")
                    continue
                
                # 提取数据列表
                data_list = data.get("data", {}).get("data", [])
                if not isinstance(data_list, list):
                    self.logger.warning(f"跳过格式错误的文件: {json_file.name}")
                    continue
                
                # 构建映射
                for item in data_list:
                    qaq_id = item.get("id")
                    if qaq_id:
                        qaq_id_map[qaq_id] = item
                        total_items += 1
                
            except Exception as e:
                self.logger.error(f"加载文件失败 {json_file.name}: {e}")
                continue
        
        self.logger.info(f"成功加载 {total_items} 个商品数据项，覆盖 {len(qaq_id_map)} 个唯一 qaq_id")
        return qaq_id_map
    
    def map_wear_condition(self, exterior_name: Optional[str]) -> Optional[str]:
        """
        将中文磨损度映射到数据库枚举值
        
        Args:
            exterior_name: 中文磨损度名称（如 "崭新出厂"）
            
        Returns:
            数据库枚举值，如果无法映射则返回 None
        """
        if not exterior_name:
            return None
        
        return self.wear_condition_map.get(exterior_name)
    
    def fetch_all_records(self, table: str, page_size: int = 1000) -> List[Dict[str, Any]]:
        """
        分页查询所有 wear_condition 为 NULL 的记录
        
        Args:
            table: 表名
            page_size: 每页大小，默认 1000
            
        Returns:
            所有记录的列表
        """
        all_records = []
        offset = 0
        
        while True:
            start = offset
            end = offset + page_size - 1
            
            try:
                result = (
                    self.supabase.client.table(table)
                    .select("id,qaq_id,name,wear_condition")
                    .is_("wear_condition", "null")
                    .range(start, end)
                    .execute()
                )
                
                records = result.data if result.data else []
                if not records:
                    break
                
                all_records.extend(records)
                self.logger.debug(f"已获取 {len(all_records)} 条记录 (table={table})")
                
                # 如果返回的记录数少于 page_size，说明已经是最后一页
                if len(records) < page_size:
                    break
                
                offset += page_size
                
            except Exception as e:
                self.logger.error(f"分页查询失败 (table={table}, offset={offset}): {e}")
                break
        
        return all_records
    
    def update_gun_skins(self, qaq_id_map: Dict[int, Dict], batch_size: int = 100) -> Dict[str, int]:
        """
        更新 gun_skins 表的 wear_condition 字段（批量更新）
        
        Args:
            qaq_id_map: qaq_id -> 数据项的映射
            batch_size: 批量更新大小，默认 100
            
        Returns:
            统计信息字典
        """
        stats = {
            "total": 0,
            "updated": 0,
            "not_found": 0,
            "no_wear_condition": 0,
            "already_set": 0,
            "failed": 0
        }
        
        self.logger.info("开始更新 gun_skins 表...")
        
        try:
            # 分页查询所有 wear_condition 为 NULL 的记录
            records = self.fetch_all_records("gun_skins")
            stats["total"] = len(records)
            
            self.logger.info(f"找到 {stats['total']} 条需要更新的 gun_skins 记录")
            
            if not records:
                return stats
            
            # 准备批量更新数据
            update_data_list = []
            
            for record in records:
                qaq_id = record.get("qaq_id")
                if not qaq_id:
                    stats["not_found"] += 1
                    continue
                
                # 在 JSON 数据中查找
                json_item = qaq_id_map.get(qaq_id)
                if not json_item:
                    stats["not_found"] += 1
                    continue
                
                # 提取磨损度
                exterior_name = json_item.get("exterior_localized_name")
                wear_condition = self.map_wear_condition(exterior_name)
                
                if not wear_condition:
                    stats["no_wear_condition"] += 1
                    continue
                
                # 添加到更新列表
                update_data_list.append({
                    "id": record["id"],
                    "wear_condition": wear_condition
                })
            
            # 批量更新
            if update_data_list:
                self.logger.info(f"准备批量更新 {len(update_data_list)} 条记录...")
                
                # 分批更新（使用 update 方法，逐条更新但批量执行）
                for i in range(0, len(update_data_list), batch_size):
                    batch = update_data_list[i:i + batch_size]
                    batch_updated = 0
                    
                    # 逐条更新（因为 Supabase 的 update 不支持批量更新不同 id 的记录）
                    for item in batch:
                        try:
                            result = self.supabase.client.table("gun_skins").update({
                                "wear_condition": item["wear_condition"]
                            }).eq("id", item["id"]).execute()
                            
                            if result.data:
                                batch_updated += 1
                            else:
                                stats["failed"] += 1
                                
                        except Exception as e:
                            stats["failed"] += 1
                            self.logger.debug(f"更新 gun_skins id={item['id']} 失败: {e}")
                    
                    stats["updated"] += batch_updated
                    self.logger.info(f"批量更新成功: {batch_updated}/{len(batch)} 条 (进度: {min(i + batch_size, len(update_data_list))}/{len(update_data_list)})")
            
        except Exception as e:
            self.logger.error(f"更新 gun_skins 表失败: {e}")
            stats["failed"] = stats["total"]
        
        return stats
    
    def update_knife_gloves(self, qaq_id_map: Dict[int, Dict], batch_size: int = 100) -> Dict[str, int]:
        """
        更新 knife_gloves 表的 wear_condition 字段（批量更新）
        
        Args:
            qaq_id_map: qaq_id -> 数据项的映射
            batch_size: 批量更新大小，默认 100
            
        Returns:
            统计信息字典
        """
        stats = {
            "total": 0,
            "updated": 0,
            "not_found": 0,
            "no_wear_condition": 0,
            "already_set": 0,
            "failed": 0
        }
        
        self.logger.info("开始更新 knife_gloves 表...")
        
        try:
            # 分页查询所有 wear_condition 为 NULL 的记录
            records = self.fetch_all_records("knife_gloves")
            stats["total"] = len(records)
            
            self.logger.info(f"找到 {stats['total']} 条需要更新的 knife_gloves 记录")
            
            if not records:
                return stats
            
            # 准备批量更新数据
            update_data_list = []
            
            for record in records:
                qaq_id = record.get("qaq_id")
                if not qaq_id:
                    stats["not_found"] += 1
                    continue
                
                # 在 JSON 数据中查找
                json_item = qaq_id_map.get(qaq_id)
                if not json_item:
                    stats["not_found"] += 1
                    continue
                
                # 提取磨损度
                exterior_name = json_item.get("exterior_localized_name")
                wear_condition = self.map_wear_condition(exterior_name)
                
                if not wear_condition:
                    stats["no_wear_condition"] += 1
                    continue
                
                # 添加到更新列表
                update_data_list.append({
                    "id": record["id"],
                    "wear_condition": wear_condition
                })
            
            # 批量更新
            if update_data_list:
                self.logger.info(f"准备批量更新 {len(update_data_list)} 条记录...")
                
                # 分批更新（使用 update 方法，逐条更新但批量执行）
                for i in range(0, len(update_data_list), batch_size):
                    batch = update_data_list[i:i + batch_size]
                    batch_updated = 0
                    
                    # 逐条更新（因为 Supabase 的 update 不支持批量更新不同 id 的记录）
                    for item in batch:
                        try:
                            result = self.supabase.client.table("knife_gloves").update({
                                "wear_condition": item["wear_condition"]
                            }).eq("id", item["id"]).execute()
                            
                            if result.data:
                                batch_updated += 1
                            else:
                                stats["failed"] += 1
                                
                        except Exception as e:
                            stats["failed"] += 1
                            self.logger.debug(f"更新 knife_gloves id={item['id']} 失败: {e}")
                    
                    stats["updated"] += batch_updated
                    self.logger.info(f"批量更新成功: {batch_updated}/{len(batch)} 条 (进度: {min(i + batch_size, len(update_data_list))}/{len(update_data_list)})")
            
        except Exception as e:
            self.logger.error(f"更新 knife_gloves 表失败: {e}")
            stats["failed"] = stats["total"]
        
        return stats
    
    def run(self) -> Dict[str, any]:
        """
        运行更新流程
        
        Returns:
            结果字典
        """
        self.logger.info("=" * 60)
        self.logger.info("开始更新磨损度字段")
        self.logger.info("=" * 60)
        
        result = {
            "success": False,
            "gun_skins_stats": {},
            "knife_gloves_stats": {},
            "error": None
        }
        
        try:
            # 1. 加载 JSON 文件
            qaq_id_map = self.load_json_files()
            
            if not qaq_id_map:
                result["error"] = "未找到任何 JSON 数据"
                return result
            
            # 2. 更新 gun_skins 表（批量更新，每批 100 条）
            gun_skins_stats = self.update_gun_skins(qaq_id_map, batch_size=100)
            result["gun_skins_stats"] = gun_skins_stats
            
            # 3. 更新 knife_gloves 表（批量更新，每批 100 条）
            knife_gloves_stats = self.update_knife_gloves(qaq_id_map, batch_size=100)
            result["knife_gloves_stats"] = knife_gloves_stats
            
            result["success"] = True
            
            # 打印统计信息
            self.logger.info("=" * 60)
            self.logger.info("更新完成")
            self.logger.info("=" * 60)
            self.logger.info("gun_skins 表统计:")
            self.logger.info(f"  总计: {gun_skins_stats['total']}")
            self.logger.info(f"  成功更新: {gun_skins_stats['updated']}")
            self.logger.info(f"  未找到 JSON 数据: {gun_skins_stats['not_found']}")
            self.logger.info(f"  无磨损度信息: {gun_skins_stats['no_wear_condition']}")
            self.logger.info(f"  更新失败: {gun_skins_stats['failed']}")
            
            self.logger.info("knife_gloves 表统计:")
            self.logger.info(f"  总计: {knife_gloves_stats['total']}")
            self.logger.info(f"  成功更新: {knife_gloves_stats['updated']}")
            self.logger.info(f"  未找到 JSON 数据: {knife_gloves_stats['not_found']}")
            self.logger.info(f"  无磨损度信息: {knife_gloves_stats['no_wear_condition']}")
            self.logger.info(f"  更新失败: {knife_gloves_stats['failed']}")
            
        except Exception as e:
            result["error"] = str(e)
            self.logger.error(f"更新流程失败: {e}", exc_info=True)
        
        return result


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="更新数据库中的磨损度字段")
    parser.add_argument(
        "--json-dir",
        type=str,
        default="data/page_list",
        help="JSON 文件目录（默认: data/page_list）"
    )
    
    args = parser.parse_args()
    
    # 创建更新器并运行
    updater = WearConditionUpdater(json_dir=args.json_dir)
    result = updater.run()
    
    if result["success"]:
        total_updated = result["gun_skins_stats"]["updated"] + result["knife_gloves_stats"]["updated"]
        print(f"\n成功！共更新 {total_updated} 条记录")
    else:
        print(f"\n失败！错误: {result.get('error', '未知错误')}")


if __name__ == "__main__":
    main()

