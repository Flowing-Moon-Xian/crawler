"""
数据库使用示例
演示如何使用 SupabaseManager 和模型类进行数据操作
"""
from datetime import datetime
from decimal import Decimal
from crawler.database.supabase_client import SupabaseManager
from crawler.database.models import (
    Box, GunSkin, KnifeGlove,
    ItemStatistics, MarketData, KlineData,
    UUYPData, SteamData, BuffData, PriceSnapshot, DataSource,
    RarityType, WearCondition, ItemType, MarketType, KlinePeriod, BoxObtainMethod
)


def example_insert_box_and_gun_skin():
    """示例：插入箱子和枪皮数据"""
    supabase = SupabaseManager()
    
    # 1. 创建箱子
    box = Box(
        qaq_id=1272,
        name="武器箱 #1",
        return_rate=Decimal("0.0250"),
        obtain_method=BoxObtainMethod.REGULAR,
        current_price=Decimal("15.50"),
        discontinue_date=None  # 未绝版
    )
    box_result = supabase.insert_data("boxes", box.to_dict())
    print(f"插入箱子成功: {box_result}")
    box_id = box_result["id"]
    
    # 2. 创建枪皮
    gun_skin = GunSkin(
        qaq_id=1234,
        name="AK-47 | 火蛇",
        weapon_type="AK-47",
        rarity=RarityType.COVERT,
        skin_series="狂牙大行动",
        is_tradable=True,
        min_float=Decimal("0.00000000"),
        max_float=Decimal("1.00000000")
    )
    gun_skin_result = supabase.insert_data("gun_skins", gun_skin.to_dict())
    print(f"插入枪皮成功: {gun_skin_result}")
    gun_skin_id = gun_skin_result["id"]
    
    # 3. 建立关系
    from crawler.database.models import BoxGunSkinRelation
    relation = BoxGunSkinRelation(
        box_id=box_id,
        gun_skin_id=gun_skin_id
    )
    relation_result = supabase.insert_data("box_gun_skin_relations", relation.to_dict())
    print(f"建立关系成功: {relation_result}")
    
    return box_id, gun_skin_id


def example_insert_item_statistics(gun_skin_id: int):
    """示例：插入商品统计"""
    supabase = SupabaseManager()
    
    statistics = ItemStatistics(
        item_id=gun_skin_id,
        item_type=ItemType.GUN_SKIN,
        name="AK-47 | 火蛇",
        rarity=RarityType.COVERT,
        circulation=10000
    )
    result = supabase.insert_data("item_statistics", statistics.to_dict())
    print(f"插入商品统计成功: {result}")
    return result["id"]


def example_insert_market_data(item_statistics_id: int):
    """示例：插入市场数据"""
    supabase = SupabaseManager()
    
    # 插入 Buff 市场数据
    market_data = MarketData(
        item_statistics_id=item_statistics_id,
        market=MarketType.BUFF,
        wear_condition=WearCondition.FACTORY_NEW,
        selling_price=Decimal("1500.00"),
        buying_price=Decimal("1450.00"),
        transaction_price=Decimal("1475.00"),
        transaction_volume=50,
        items_for_sale=200,
        buy_orders=150,
        avg_price_7d=Decimal("1480.00"),
        avg_price_30d=Decimal("1520.00"),
        price_change_24h=Decimal("0.02"),
        price_change_7d=Decimal("-0.01"),
        liquidity_score=85,
        popularity_rank=10,
        timestamp=datetime.now()
    )
    result = supabase.insert_data("market_data", market_data.to_dict())
    print(f"插入 Buff 市场数据成功: {result}")
    
    # 插入 Buff 独有数据
    buff_data = BuffData(
        market_data_id=result["id"],
        buff_goods_id=123456,
        steam_price=Decimal("1600.00"),
        steam_price_cny=Decimal("11200.00"),
        sell_min_price=Decimal("1480.00"),
        buy_max_price=Decimal("1450.00"),
        timestamp=datetime.now()
    )
    buff_result = supabase.insert_data("buff_data", buff_data.to_dict())
    print(f"插入 Buff 独有数据成功: {buff_result}")
    
    # 插入 UUYP 市场数据
    uuyp_market_data = MarketData(
        item_statistics_id=item_statistics_id,
        market=MarketType.UUYP,
        wear_condition=WearCondition.FACTORY_NEW,
        selling_price=Decimal("1480.00"),
        buying_price=Decimal("1440.00"),
        transaction_price=Decimal("1460.00"),
        transaction_volume=30,
        items_for_sale=150,
        buy_orders=120,
        timestamp=datetime.now()
    )
    uuyp_result = supabase.insert_data("market_data", uuyp_market_data.to_dict())
    print(f"插入 UUYP 市场数据成功: {uuyp_result}")
    
    # 插入 UUYP 独有数据
    uuyp_data = UUYPData(
        market_data_id=uuyp_result["id"],
        long_rent_yield=Decimal("0.05"),
        short_rent_yield=Decimal("0.08"),
        long_rent_price=Decimal("100.00"),
        short_rent_price=Decimal("20.00"),
        rental_buyout=Decimal("1500.00"),
        timestamp=datetime.now()
    )
    uuyp_unique_result = supabase.insert_data("uuyp_data", uuyp_data.to_dict())
    print(f"插入 UUYP 独有数据成功: {uuyp_unique_result}")
    
    # 插入 Steam 市场数据
    steam_market_data = MarketData(
        item_statistics_id=item_statistics_id,
        market=MarketType.STEAM,
        wear_condition=WearCondition.FACTORY_NEW,
        selling_price=Decimal("1520.00"),
        buying_price=Decimal("1460.00"),
        transaction_price=Decimal("1490.00"),
        transaction_volume=40,
        items_for_sale=180,
        buy_orders=130,
        timestamp=datetime.now()
    )
    steam_result = supabase.insert_data("market_data", steam_market_data.to_dict())
    print(f"插入 Steam 市场数据成功: {steam_result}")
    
    # 插入 Steam 独有数据
    steam_data = SteamData(
        market_data_id=steam_result["id"],
        buy_order_overprice_ratio=Decimal("0.02"),
        sell_order_overprice_ratio=Decimal("0.03"),
        timestamp=datetime.now()
    )
    steam_unique_result = supabase.insert_data("steam_data", steam_data.to_dict())
    print(f"插入 Steam 独有数据成功: {steam_unique_result}")
    
    return result["id"], uuyp_result["id"], steam_result["id"]


def example_insert_kline_data(item_statistics_id: int):
    """示例：插入K线数据"""
    supabase = SupabaseManager()
    
    # 插入日K数据
    kline = KlineData(
        item_statistics_id=item_statistics_id,
        period=KlinePeriod.DAILY,
        timestamp=datetime.now(),
        open_price=Decimal("1450.00"),
        close_price=Decimal("1475.00"),
        high_price=Decimal("1500.00"),
        low_price=Decimal("1440.00"),
        volume=100
    )
    result = supabase.insert_data("kline_data", kline.to_dict())
    print(f"插入K线数据成功: {result}")
    return result["id"]


def example_query_data():
    """示例：查询数据"""
    supabase = SupabaseManager()
    
    # 查询所有箱子
    boxes = supabase.query_data("boxes")
    print(f"查询到 {len(boxes)} 个箱子")
    
    # 查询特定稀有度的枪皮
    gun_skins = supabase.query_data(
        "gun_skins",
        filters={"rarity": RarityType.COVERT.value}
    )
    print(f"查询到 {len(gun_skins)} 个隐秘级枪皮")
    
    # 查询某个商品的市场数据
    if gun_skins:
        # 先查询商品统计
        statistics = supabase.query_data(
            "item_statistics",
            filters={"item_id": gun_skins[0]["id"], "item_type": ItemType.GUN_SKIN.value}
        )
        if statistics:
            # 查询市场数据
            market_data = supabase.query_data(
                "market_data",
                filters={"item_statistics_id": statistics[0]["id"]}
            )
            print(f"查询到 {len(market_data)} 条市场数据")
            
            # 查询K线数据
            kline_data = supabase.query_data(
                "kline_data",
                filters={
                    "item_statistics_id": statistics[0]["id"],
                    "period": KlinePeriod.DAILY.value
                }
            )
            print(f"查询到 {len(kline_data)} 条K线数据")


def example_update_data():
    """示例：更新数据"""
    supabase = SupabaseManager()
    
    # 更新箱子的回报率
    boxes = supabase.query_data("boxes", limit=1)
    if boxes:
        result = supabase.update_data(
            "boxes",
            {"id": boxes[0]["id"]},
            {"return_rate": 0.0300}
        )
        print(f"更新箱子回报率成功: {result}")


def example_batch_insert():
    """示例：批量插入数据"""
    supabase = SupabaseManager()
    
    # 批量插入多个枪皮
    gun_skins = [
        GunSkin(
            qaq_id=1001, 
            name="M4A4 | 龙王", 
            weapon_type="M4A4",
            rarity=RarityType.COVERT,
            skin_series="炼狱大行动",
            min_float=Decimal("0.00000000"),
            max_float=Decimal("0.80000000")
        ).to_dict(),
        GunSkin(
            qaq_id=1002, 
            name="AWP | 龙狙", 
            weapon_type="AWP",
            rarity=RarityType.COVERT,
            skin_series="龙系列",
            min_float=Decimal("0.00000000"),
            max_float=Decimal("0.99000000")
        ).to_dict(),
        GunSkin(
            qaq_id=1003, 
            name="AK-47 | 二西莫夫", 
            weapon_type="AK-47",
            rarity=RarityType.CLASSIFIED,
            skin_series="凤凰大行动",
            min_float=Decimal("0.05000000"),
            max_float=Decimal("0.70000000")
        ).to_dict(),
    ]
    
    results = supabase.insert_batch("gun_skins", gun_skins)
    print(f"批量插入 {len(results)} 个枪皮成功")


def example_price_snapshot():
    """示例：插入价格快照数据"""
    supabase = SupabaseManager()
    
    # 假设我们有一个商品统计ID
    item_statistics_id = 1  # 这应该是一个真实的ID
    
    # 插入价格快照
    snapshot = PriceSnapshot(
        item_statistics_id=item_statistics_id,
        market=MarketType.BUFF,
        wear_condition=WearCondition.FACTORY_NEW,
        snapshot_price=Decimal("1500.00"),
        snapshot_volume=50,
        snapshot_date=datetime.now()
    )
    result = supabase.insert_data("price_snapshots", snapshot.to_dict())
    print(f"插入价格快照成功: {result}")


def example_data_source():
    """示例：管理数据源"""
    supabase = SupabaseManager()
    
    # 插入数据源记录
    data_source = DataSource(
        source_name="buff",
        api_endpoint="https://buff.163.com/api/market/goods",
        last_sync_time=datetime.now(),
        sync_status="success",
        total_synced=100
    )
    result = supabase.insert_data("data_sources", data_source.to_dict())
    print(f"插入数据源记录成功: {result}")
    
    # 更新同步状态
    supabase.update_data(
        "data_sources",
        {"source_name": "buff"},
        {
            "last_sync_time": datetime.now().isoformat(),
            "sync_status": "success",
            "total_synced": 101
        }
    )
    print("更新数据源同步状态成功")


def main():
    """主函数：运行所有示例"""
    print("=" * 50)
    print("数据库操作示例")
    print("=" * 50)
    
    try:
        # 示例1：插入箱子和枪皮
        print("\n1. 插入箱子和枪皮")
        box_id, gun_skin_id = example_insert_box_and_gun_skin()
        
        # 示例2：插入商品统计
        print("\n2. 插入商品统计")
        item_statistics_id = example_insert_item_statistics(gun_skin_id)
        
        # 示例3：插入市场数据
        print("\n3. 插入市场数据")
        example_insert_market_data(item_statistics_id)
        
        # 示例4：插入K线数据
        print("\n4. 插入K线数据")
        example_insert_kline_data(item_statistics_id)
        
        # 示例5：查询数据
        print("\n5. 查询数据")
        example_query_data()
        
        # 示例6：更新数据
        print("\n6. 更新数据")
        example_update_data()
        
        # 示例7：批量插入
        print("\n7. 批量插入")
        example_batch_insert()
        
        # 示例8：价格快照
        print("\n8. 价格快照")
        example_price_snapshot()
        
        # 示例9：数据源管理
        print("\n9. 数据源管理")
        example_data_source()
        
        print("\n" + "=" * 50)
        print("所有示例执行完成！")
        print("=" * 50)
        
    except Exception as e:
        print(f"执行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

