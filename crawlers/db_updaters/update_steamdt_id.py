"""
更新 SteamDT ID 脚本
根据名字和磨损度的组合，从 SteamDT JSON 文件中查询 HALOSKINS 的 itemId，
然后存入数据库对应记录的 steamdt_id 字段
"""
import json
import logging
from pathlib import Path
from typing import Dict, Optional, List, Any, Tuple

from crawler.config.config import Config
from crawler.database.supabase_client import SupabaseManager
from crawler.database.models import WearCondition


class SteamDTIDUpdater:
    """SteamDT ID 更新器"""
    
    def __init__(self, config: Optional[Config] = None, json_dir: str = "data"):
        """
        初始化更新器
        
        Args:
            config: 配置对象，如果为 None 则从环境变量加载
            json_dir: JSON 文件目录，默认为 "data"
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
        self.logger = logging.getLogger("SteamDTIDUpdater")
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
    
    def extract_wear_condition_from_name(self, name: str) -> Optional[str]:
        """
        从商品名称中提取磨损度
        
        Args:
            name: 商品名称，如 "AWP | 响尾蛇 (略有磨损)"
            
        Returns:
            磨损度枚举值，如果无法提取则返回 None
        """
        for chinese_wear, enum_value in self.wear_condition_map.items():
            if chinese_wear in name:
                return enum_value
        return None
    
    def extract_base_name(self, name: str) -> str:
        """
        从商品名称中提取基础名称（去除磨损度）
        
        Args:
            name: 商品名称，如 "AWP | 响尾蛇 (略有磨损)"
            
        Returns:
            基础名称，如 "AWP | 响尾蛇"
        """
        # 移除磨损度部分
        for chinese_wear in self.wear_condition_map.keys():
            if chinese_wear in name:
                name = name.replace(f" ({chinese_wear})", "").replace(f"({chinese_wear})", "")
                break
        return name.strip()
    
    def load_steamdt_json(self) -> Dict[Tuple[str, str], str]:
        """
        加载 SteamDT JSON 文件，构建 (name, wear_condition) -> HALOSKINS itemId 的映射
        
        Returns:
            字典，key 为 (基础名称, 磨损度)，value 为 HALOSKINS itemId
        """
        # 查找所有 SteamDT JSON 文件
        json_files = list(self.json_dir.glob("*steamdt*.json"))
        
        if not json_files:
            self.logger.warning(f"在 {self.json_dir} 中未找到 SteamDT JSON 文件")
            return {}
        
        self.logger.info(f"找到 {len(json_files)} 个 SteamDT JSON 文件，开始加载...")
        
        name_wear_to_itemid = {}
        total_items = 0
        
        for json_file in json_files:
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # 检查响应格式
                if not data.get("success") or "data" not in data:
                    self.logger.warning(f"跳过无效响应文件: {json_file.name}")
                    continue
                
                # 提取数据列表
                data_list = data.get("data", [])
                if not isinstance(data_list, list):
                    self.logger.warning(f"跳过格式错误的文件: {json_file.name}")
                    continue
                
                # 构建映射
                for item in data_list:
                    name = item.get("name", "")
                    if not name:
                        continue
                    
                    # 提取磨损度
                    wear_condition = self.extract_wear_condition_from_name(name)
                    base_name = self.extract_base_name(name)
                    
                    # 查找 HALOSKINS 的 itemId
                    platform_list = item.get("platformList", [])
                    haloskins_itemid = None
                    
                    for platform in platform_list:
                        if platform.get("name") == "HALOSKINS":
                            haloskins_itemid = platform.get("itemId")
                            break
                    
                    if haloskins_itemid:
                        # 使用 (基础名称, 磨损度) 作为 key
                        key = (base_name, wear_condition) if wear_condition else (base_name, None)
                        name_wear_to_itemid[key] = haloskins_itemid
                        total_items += 1
                
            except Exception as e:
                self.logger.error(f"加载文件失败 {json_file.name}: {e}")
                continue
        
        self.logger.info(f"成功加载 {total_items} 个商品数据项，覆盖 {len(name_wear_to_itemid)} 个唯一 (name, wear_condition) 组合")
        return name_wear_to_itemid
    
    def fetch_all_item_statistics_with_wear(self, page_size: int = 1000) -> List[Dict[str, Any]]:
        """
        分页查询所有 item_statistics 记录，并关联获取 name 和 wear_condition
        优化：先批量查询所有 gun_skins 和 knife_gloves，然后在内存中建立映射
        
        Args:
            page_size: 每页大小，默认 1000
            
        Returns:
            所有记录的列表（包含 name 和 wear_condition）
        """
        self.logger.info("开始查询 item_statistics 记录...")
        
        # 1. 先批量查询所有 gun_skins 和 knife_gloves，建立 item_id -> wear_condition 映射
        self.logger.info("批量查询 gun_skins 和 knife_gloves 表...")
        item_id_to_wear = {}
        
        # 查询 gun_skins
        gun_offset = 0
        while True:
            start = gun_offset
            end = gun_offset + page_size - 1
            try:
                result = (
                    self.supabase.client.table("gun_skins")
                    .select("id,wear_condition")
                    .range(start, end)
                    .execute()
                )
                records = result.data if result.data else []
                if not records:
                    break
                
                for record in records:
                    item_id_to_wear[("gun_skin", record.get("id"))] = record.get("wear_condition")
                
                if len(records) < page_size:
                    break
                gun_offset += page_size
            except Exception as e:
                self.logger.error(f"查询 gun_skins 失败: {e}")
                break
        
        # 查询 knife_gloves
        knife_offset = 0
        while True:
            start = knife_offset
            end = knife_offset + page_size - 1
            try:
                result = (
                    self.supabase.client.table("knife_gloves")
                    .select("id,wear_condition")
                    .range(start, end)
                    .execute()
                )
                records = result.data if result.data else []
                if not records:
                    break
                
                for record in records:
                    item_id_to_wear[("knife_glove", record.get("id"))] = record.get("wear_condition")
                
                if len(records) < page_size:
                    break
                knife_offset += page_size
            except Exception as e:
                self.logger.error(f"查询 knife_gloves 失败: {e}")
                break
        
        self.logger.info(f"已建立 {len(item_id_to_wear)} 个 item_id -> wear_condition 映射")
        
        # 2. 分页查询所有 item_statistics 记录
        all_records = []
        offset = 0
        
        while True:
            start = offset
            end = offset + page_size - 1
            
            try:
                result = (
                    self.supabase.client.table("item_statistics")
                    .select("id,item_id,item_type,name,steamdt_id")
                    .range(start, end)
                    .execute()
                )
                
                records = result.data if result.data else []
                if not records:
                    break
                
                # 从内存映射中获取 wear_condition
                for record in records:
                    item_id = record.get("item_id")
                    item_type = record.get("item_type")
                    wear_condition = item_id_to_wear.get((item_type, item_id))
                    record["wear_condition"] = wear_condition
                
                all_records.extend(records)
                self.logger.debug(f"已获取 {len(all_records)} 条 item_statistics 记录")
                
                # 如果返回的记录数少于 page_size，说明已经是最后一页
                if len(records) < page_size:
                    break
                
                offset += page_size
                
            except Exception as e:
                self.logger.error(f"分页查询失败 (offset={offset}): {e}")
                break
        
        return all_records
    
    def update_item_statistics(self, name_wear_to_itemid: Dict[Tuple[str, str], str], batch_size: int = 100) -> Dict[str, int]:
        """
        更新 item_statistics 表的 steamdt_id 字段
        
        Args:
            name_wear_to_itemid: (基础名称, 磨损度) -> HALOSKINS itemId 的映射
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
        
        self.logger.info("开始更新 item_statistics 表...")
        
        try:
            # 分页查询所有 item_statistics 记录（包含 wear_condition）
            records = self.fetch_all_item_statistics_with_wear()
            stats["total"] = len(records)
            
            self.logger.info(f"找到 {stats['total']} 条 item_statistics 记录")
            
            if not records:
                return stats
            
            # 准备批量更新数据
            update_data_list = []
            
            for record in records:
                item_id = record.get("id")
                db_name = record.get("name", "")
                wear_condition = record.get("wear_condition")
                
                # 构建匹配 key
                base_name = self.extract_base_name(db_name)
                key = (base_name, wear_condition) if wear_condition else (base_name, None)
                
                # 查找 HALOSKINS itemId
                haloskins_itemid = name_wear_to_itemid.get(key)
                
                if not haloskins_itemid:
                    stats["not_found"] += 1
                    continue
                
                # 检查是否已经设置
                current_steamdt_id = record.get("steamdt_id")
                if current_steamdt_id and str(current_steamdt_id) == str(haloskins_itemid):
                    stats["already_set"] += 1
                    continue
                
                # 添加到更新列表
                update_data_list.append({
                    "id": item_id,
                    "steamdt_id": int(haloskins_itemid)
                })
            
            # 批量更新
            if update_data_list:
                self.logger.info(f"准备批量更新 {len(update_data_list)} 条记录...")
                
                # 分批更新
                for i in range(0, len(update_data_list), batch_size):
                    batch = update_data_list[i:i + batch_size]
                    batch_updated = 0
                    
                    # 逐条更新（因为 Supabase 的 update 不支持批量更新不同 id 的记录）
                    for item in batch:
                        try:
                            result = self.supabase.client.table("item_statistics").update({
                                "steamdt_id": item["steamdt_id"]
                            }).eq("id", item["id"]).execute()
                            
                            if result.data:
                                batch_updated += 1
                            else:
                                stats["failed"] += 1
                                
                        except Exception as e:
                            stats["failed"] += 1
                            self.logger.debug(f"更新 item_statistics id={item['id']} 失败: {e}")
                    
                    stats["updated"] += batch_updated
                    self.logger.info(f"批量更新成功: {batch_updated}/{len(batch)} 条 (进度: {min(i + batch_size, len(update_data_list))}/{len(update_data_list)})")
            
        except Exception as e:
            self.logger.error(f"更新 item_statistics 表失败: {e}")
            stats["failed"] = stats["total"]
        
        return stats
    
    def run(self) -> Dict[str, Any]:
        """
        运行更新流程
        
        Returns:
            结果字典
        """
        self.logger.info("=" * 60)
        self.logger.info("开始更新 SteamDT ID")
        self.logger.info("=" * 60)
        
        result = {
            "success": False,
            "stats": {},
            "error": None
        }
        
        try:
            # 1. 加载 SteamDT JSON 文件
            name_wear_to_itemid = self.load_steamdt_json()
            
            if not name_wear_to_itemid:
                result["error"] = "未找到任何 SteamDT JSON 数据"
                return result
            
            # 2. 更新 item_statistics 表
            stats = self.update_item_statistics(name_wear_to_itemid, batch_size=100)
            result["stats"] = stats
            
            result["success"] = True
            
            # 打印统计信息
            self.logger.info("=" * 60)
            self.logger.info("更新完成")
            self.logger.info("=" * 60)
            self.logger.info("item_statistics 表统计:")
            self.logger.info(f"  总计: {stats['total']}")
            self.logger.info(f"  成功更新: {stats['updated']}")
            self.logger.info(f"  未找到匹配: {stats['not_found']}")
            self.logger.info(f"  无磨损度信息: {stats['no_wear_condition']}")
            self.logger.info(f"  已设置: {stats['already_set']}")
            self.logger.info(f"  更新失败: {stats['failed']}")
            
        except Exception as e:
            result["error"] = str(e)
            self.logger.error(f"更新流程失败: {e}", exc_info=True)
        
        return result


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="更新数据库中的 SteamDT ID")
    parser.add_argument(
        "--json-dir",
        type=str,
        default="data",
        help="JSON 文件目录（默认: data）"
    )
    
    args = parser.parse_args()
    
    # 创建更新器并运行
    updater = SteamDTIDUpdater(json_dir=args.json_dir)
    result = updater.run()
    
    if result["success"]:
        print(f"\n成功！共更新 {result['stats']['updated']} 条记录")
    else:
        print(f"\n失败！错误: {result.get('error', '未知错误')}")


if __name__ == "__main__":
    main()

