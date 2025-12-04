"""
同步 item_statistics 表脚本

作用：
- 从 boxes / gun_skins / knife_gloves 三张表读取已有数据
- 把它们统一写入 item_statistics 表
- 只维护以下字段：
  - id（由数据库自动生成）
  - item_id
  - item_type
  - name
  - csqaq_id
  - steamdt_id（目前没有来源，先置为 NULL）
  - created_at（DB 默认）
  - updated_at（DB 触发器自动维护）
"""

"""
  TODO:自增更新尚未实现，当前仅同步第一次数据
"""

from typing import List, Dict, Any

from crawler.config.config import Config
from crawler.database.supabase_client import SupabaseManager
from crawler.database.models import ItemStatistics, ItemType


def fetch_all(supabase: SupabaseManager, table: str, page_size: int = 1000) -> List[Dict[str, Any]]:
    """
    简单封装：分页拉取整张表的数据
    Supabase 默认单次最多返回 1000 行，这里用 range 分页把全部数据取完
    """
    all_rows: List[Dict[str, Any]] = []
    offset = 0

    while True:
        start = offset
        end = offset + page_size - 1
        result = (
            supabase.client.table(table)
            .select("*")
            .range(start, end)
            .execute()
        )
        rows = result.data or []
        if not rows:
            break

        all_rows.extend(rows)
        if len(rows) < page_size:
            # 最后一页
            break

        offset += page_size

    return all_rows


def build_item_statistics_from_boxes(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """将 boxes 表数据转换为 item_statistics 记录"""
    items: List[Dict[str, Any]] = []
    for row in rows:
        box_id = row.get("id")
        name = row.get("name")
        if not box_id or not name:
            continue

        csqaq_id = row.get("qaq_id")
        steamdt_id = row.get("steamdt_id")

        model = ItemStatistics(
            item_id=box_id,
            item_type=ItemType.BOX,
            name=name,
            csqaq_id=csqaq_id,
            steamdt_id=steamdt_id,
        )
        items.append(model.to_dict())
    return items


def build_item_statistics_from_gun_skins(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """将 gun_skins 表数据转换为 item_statistics 记录"""
    items: List[Dict[str, Any]] = []
    for row in rows:
        gun_id = row.get("id")
        name = row.get("name")
        if not gun_id or not name:
            continue

        csqaq_id = row.get("qaq_id")
        steamdt_id = row.get("steamdt_id")

        model = ItemStatistics(
            item_id=gun_id,
            item_type=ItemType.GUN_SKIN,
            name=name,
            csqaq_id=csqaq_id,
            steamdt_id=steamdt_id,
        )
        items.append(model.to_dict())
    return items


def build_item_statistics_from_knife_gloves(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """将 knife_gloves 表数据转换为 item_statistics 记录"""
    items: List[Dict[str, Any]] = []
    for row in rows:
        kg_id = row.get("id")
        name = row.get("name")
        if not kg_id or not name:
            continue

        csqaq_id = row.get("qaq_id")
        steamdt_id = row.get("steamdt_id")

        model = ItemStatistics(
            item_id=kg_id,
            item_type=ItemType.KNIFE_GLOVE,
            name=name,
            csqaq_id=csqaq_id,
            steamdt_id=steamdt_id,
        )
        items.append(model.to_dict())
    return items


def sync_item_statistics() -> None:
    """主同步流程：整合 box / gun / knife 三张表到 item_statistics"""
    # 使用框架内统一的配置入口
    config = Config.from_env()
    if not config or not config.supabase:
        raise ValueError("Supabase 配置缺失，请在 config_local.py 或环境变量中配置 SUPABASE_URL / SUPABASE_KEY")

    supabase = SupabaseManager(
        url=config.supabase.url,
        key=config.supabase.key,
    )

    # 1. 拉取三张表的数据
    print("Fetching boxes ...")
    boxes = fetch_all(supabase, "boxes")
    print(f"  boxes: {len(boxes)} rows")

    print("Fetching gun_skins ...")
    gun_skins = fetch_all(supabase, "gun_skins")
    print(f"  gun_skins: {len(gun_skins)} rows")

    print("Fetching knife_gloves ...")
    knife_gloves = fetch_all(supabase, "knife_gloves")
    print(f"  knife_gloves: {len(knife_gloves)} rows")

    # 2. 转换为 item_statistics 记录
    box_items = build_item_statistics_from_boxes(boxes)
    gun_items = build_item_statistics_from_gun_skins(gun_skins)
    kg_items = build_item_statistics_from_knife_gloves(knife_gloves)

    all_items: List[Dict[str, Any]] = box_items + gun_items + kg_items
    if not all_items:
        print("No data to sync into item_statistics.")
        return

    print(f"\nPrepared {len(all_items)} item_statistics records. Upserting ...")

    # 3. 批量 upsert 到 item_statistics
    #    on_conflict 使用 (item_id, item_type)，与表上的 UNIQUE 约束一致
    try:
        result = supabase.client.table("item_statistics").upsert(
            all_items,
            on_conflict="item_id,item_type",
        ).execute()

        affected = len(result.data) if result.data else 0
        print(f"Upsert into item_statistics done. affected rows: {affected}")
    except Exception as e:
        print(f"Upsert into item_statistics failed: {e}")


def main():
    """命令行入口"""
    sync_item_statistics()


if __name__ == "__main__":
    main()


