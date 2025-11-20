"""
数据库模型定义
用于类型提示和数据验证
"""
from typing import Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict
from decimal import Decimal


# ============================================
# 枚举类型
# ============================================

class RarityType(str, Enum):
    """稀有度枚举"""
    CONSUMER = "consumer"          # 消费
    INDUSTRIAL = "industrial"      # 工业
    MIL_SPEC = "mil_spec"          # 军规
    RESTRICTED = "restricted"      # 受限
    CLASSIFIED = "classified"      # 保密
    COVERT = "covert"              # 隐秘
    CONTRABAND = "contraband"      # 违禁
    EXCEPTIONAL = "exceptional"    # 非凡


class WearCondition(str, Enum):
    """磨损度枚举"""
    FACTORY_NEW = "factory_new"        # 崭新出场
    MINIMAL_WEAR = "minimal_wear"      # 略有磨损
    FIELD_TESTED = "field_tested"      # 久经沙场
    WELL_WORN = "well_worn"            # 战痕累累
    BATTLE_SCARRED = "battle_scarred"  # 破损不堪


class ItemType(str, Enum):
    """商品类型枚举"""
    BOX = "box"                    # 箱子
    GUN_SKIN = "gun_skin"          # 枪皮
    KNIFE_GLOVE = "knife_glove"    # 刀皮和手套


class MarketType(str, Enum):
    """市场类型枚举"""
    BUFF = "buff"
    UUYP = "uuyp"
    STEAM = "steam"


class KlinePeriod(str, Enum):
    """K线周期枚举"""
    HOURLY = "hourly"              # 时K
    DAILY = "daily"                # 日K


class BoxObtainMethod(str, Enum):
    """箱子获取途径枚举"""
    RARE = "rare"                  # 稀有
    REGULAR = "regular"            # 常规
    DISCONTINUED = "discontinued"  # 绝版


# ============================================
# 数据模型
# ============================================

@dataclass
class Box:
    """箱子模型"""
    name: str
    qaq_id: Optional[int] = None
    return_rate: Optional[Decimal] = None
    obtain_method: Optional[BoxObtainMethod] = None
    current_price: Optional[Decimal] = None
    discontinue_date: Optional[datetime] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """转换为字典，用于数据库插入"""
        data = asdict(self)
        # 移除 None 的 id 和时间戳字段（插入时不需要）
        if data.get("id") is None:
            data.pop("id", None)
        if data.get("created_at") is None:
            data.pop("created_at", None)
        if data.get("updated_at") is None:
            data.pop("updated_at", None)
        # 转换 Decimal 为 float（Supabase 需要）
        if data.get("return_rate") is not None:
            data["return_rate"] = float(data["return_rate"])
        if data.get("current_price") is not None:
            data["current_price"] = float(data["current_price"])
        # 转换枚举为字符串
        if isinstance(data.get("obtain_method"), Enum):
            data["obtain_method"] = data["obtain_method"].value
        # 转换 datetime 为日期字符串
        if isinstance(data.get("discontinue_date"), datetime):
            data["discontinue_date"] = data["discontinue_date"].date().isoformat()
        return data


@dataclass
class KnifeGlove:
    """刀皮和手套模型"""
    name: str
    item_type: str  # 'knife' 或 'glove'
    rarity: RarityType
    qaq_id: Optional[int] = None
    qaq_url: Optional[str] = None  # CSQAQ 网站的商品URL
    skin_series: Optional[str] = None
    is_tradable: bool = True
    min_float: Optional[Decimal] = None
    max_float: Optional[Decimal] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """转换为字典，用于数据库插入"""
        data = asdict(self)
        if data.get("id") is None:
            data.pop("id", None)
        if data.get("created_at") is None:
            data.pop("created_at", None)
        if data.get("updated_at") is None:
            data.pop("updated_at", None)
        # 转换枚举为字符串
        if isinstance(data.get("rarity"), Enum):
            data["rarity"] = data["rarity"].value
        # 转换 Decimal 为 float
        if data.get("min_float") is not None:
            data["min_float"] = float(data["min_float"])
        if data.get("max_float") is not None:
            data["max_float"] = float(data["max_float"])
        return data


@dataclass
class GunSkin:
    """枪皮模型"""
    name: str
    rarity: RarityType
    qaq_id: Optional[int] = None
    qaq_url: Optional[str] = None  # CSQAQ 网站的商品URL
    weapon_type: Optional[str] = None
    skin_series: Optional[str] = None
    is_tradable: bool = True
    min_float: Optional[Decimal] = None
    max_float: Optional[Decimal] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """转换为字典，用于数据库插入"""
        data = asdict(self)
        if data.get("id") is None:
            data.pop("id", None)
        if data.get("created_at") is None:
            data.pop("created_at", None)
        if data.get("updated_at") is None:
            data.pop("updated_at", None)
        # 转换枚举为字符串
        if isinstance(data.get("rarity"), Enum):
            data["rarity"] = data["rarity"].value
        # 转换 Decimal 为 float
        if data.get("min_float") is not None:
            data["min_float"] = float(data["min_float"])
        if data.get("max_float") is not None:
            data["max_float"] = float(data["max_float"])
        return data


@dataclass
class BoxKnifeGloveRelation:
    """箱子-刀皮手套关系模型"""
    box_id: int
    knife_glove_id: int
    id: Optional[int] = None
    created_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """转换为字典，用于数据库插入"""
        data = asdict(self)
        if data.get("id") is None:
            data.pop("id", None)
        if data.get("created_at") is None:
            data.pop("created_at", None)
        return data


@dataclass
class BoxGunSkinRelation:
    """箱子-枪皮关系模型"""
    box_id: int
    gun_skin_id: int
    id: Optional[int] = None
    created_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """转换为字典，用于数据库插入"""
        data = asdict(self)
        if data.get("id") is None:
            data.pop("id", None)
        if data.get("created_at") is None:
            data.pop("created_at", None)
        return data


@dataclass
class ItemStatistics:
    """商品统计模型"""
    item_id: int
    item_type: ItemType
    name: str
    rarity: Optional[RarityType] = None
    circulation: Optional[int] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """转换为字典，用于数据库插入"""
        data = asdict(self)
        if data.get("id") is None:
            data.pop("id", None)
        if data.get("created_at") is None:
            data.pop("created_at", None)
        if data.get("updated_at") is None:
            data.pop("updated_at", None)
        # 转换枚举为字符串
        if isinstance(data.get("item_type"), Enum):
            data["item_type"] = data["item_type"].value
        if isinstance(data.get("rarity"), Enum):
            data["rarity"] = data["rarity"].value
        return data


@dataclass
class KlineData:
    """K线数据模型"""
    item_statistics_id: int
    period: KlinePeriod
    timestamp: datetime
    open_price: Optional[Decimal] = None
    close_price: Optional[Decimal] = None
    high_price: Optional[Decimal] = None
    low_price: Optional[Decimal] = None
    volume: Optional[int] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """转换为字典，用于数据库插入"""
        data = asdict(self)
        if data.get("id") is None:
            data.pop("id", None)
        if data.get("created_at") is None:
            data.pop("created_at", None)
        # 转换枚举为字符串
        if isinstance(data.get("period"), Enum):
            data["period"] = data["period"].value
        # 转换 Decimal 为 float
        for price_field in ["open_price", "close_price", "high_price", "low_price"]:
            if data.get(price_field) is not None:
                data[price_field] = float(data[price_field])
        # 转换 datetime 为 ISO 格式字符串
        if isinstance(data.get("timestamp"), datetime):
            data["timestamp"] = data["timestamp"].isoformat()
        return data


@dataclass
class MarketData:
    """市场数据模型"""
    item_statistics_id: int
    market: MarketType
    timestamp: datetime
    wear_condition: Optional[WearCondition] = None
    selling_price: Optional[Decimal] = None
    buying_price: Optional[Decimal] = None
    transaction_price: Optional[Decimal] = None
    transaction_volume: Optional[int] = None
    items_for_sale: Optional[int] = None
    buy_orders: Optional[int] = None
    avg_price_7d: Optional[Decimal] = None
    avg_price_30d: Optional[Decimal] = None
    price_change_24h: Optional[Decimal] = None
    price_change_7d: Optional[Decimal] = None
    liquidity_score: Optional[int] = None
    popularity_rank: Optional[int] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """转换为字典，用于数据库插入"""
        data = asdict(self)
        if data.get("id") is None:
            data.pop("id", None)
        if data.get("created_at") is None:
            data.pop("created_at", None)
        # 转换枚举为字符串
        if isinstance(data.get("market"), Enum):
            data["market"] = data["market"].value
        if isinstance(data.get("wear_condition"), Enum):
            data["wear_condition"] = data["wear_condition"].value
        # 转换 Decimal 为 float
        for price_field in ["selling_price", "buying_price", "transaction_price", 
                           "avg_price_7d", "avg_price_30d", "price_change_24h", "price_change_7d"]:
            if data.get(price_field) is not None:
                data[price_field] = float(data[price_field])
        # 转换 datetime 为 ISO 格式字符串
        if isinstance(data.get("timestamp"), datetime):
            data["timestamp"] = data["timestamp"].isoformat()
        return data


@dataclass
class UUYPData:
    """UUYP 市场独有数据模型"""
    market_data_id: int
    timestamp: datetime
    long_rent_yield: Optional[Decimal] = None
    short_rent_yield: Optional[Decimal] = None
    long_rent_price: Optional[Decimal] = None
    short_rent_price: Optional[Decimal] = None
    rental_buyout: Optional[Decimal] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """转换为字典，用于数据库插入"""
        data = asdict(self)
        if data.get("id") is None:
            data.pop("id", None)
        if data.get("created_at") is None:
            data.pop("created_at", None)
        # 转换 Decimal 为 float
        for field in ["long_rent_yield", "short_rent_yield", "long_rent_price", 
                      "short_rent_price", "rental_buyout"]:
            if data.get(field) is not None:
                data[field] = float(data[field])
        # 转换 datetime 为 ISO 格式字符串
        if isinstance(data.get("timestamp"), datetime):
            data["timestamp"] = data["timestamp"].isoformat()
        return data


@dataclass
class SteamData:
    """Steam 市场独有数据模型"""
    market_data_id: int
    timestamp: datetime
    buy_order_overprice_ratio: Optional[Decimal] = None
    sell_order_overprice_ratio: Optional[Decimal] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """转换为字典，用于数据库插入"""
        data = asdict(self)
        if data.get("id") is None:
            data.pop("id", None)
        if data.get("created_at") is None:
            data.pop("created_at", None)
        # 转换 Decimal 为 float
        for field in ["buy_order_overprice_ratio", "sell_order_overprice_ratio"]:
            if data.get(field) is not None:
                data[field] = float(data[field])
        # 转换 datetime 为 ISO 格式字符串
        if isinstance(data.get("timestamp"), datetime):
            data["timestamp"] = data["timestamp"].isoformat()
        return data


@dataclass
class BuffData:
    """Buff 市场独有数据模型"""
    market_data_id: int
    timestamp: datetime
    buff_goods_id: Optional[int] = None
    steam_price: Optional[Decimal] = None
    steam_price_cny: Optional[Decimal] = None
    sell_min_price: Optional[Decimal] = None
    buy_max_price: Optional[Decimal] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """转换为字典，用于数据库插入"""
        data = asdict(self)
        if data.get("id") is None:
            data.pop("id", None)
        if data.get("created_at") is None:
            data.pop("created_at", None)
        # 转换 Decimal 为 float
        for field in ["steam_price", "steam_price_cny", "sell_min_price", "buy_max_price"]:
            if data.get(field) is not None:
                data[field] = float(data[field])
        # 转换 datetime 为 ISO 格式字符串
        if isinstance(data.get("timestamp"), datetime):
            data["timestamp"] = data["timestamp"].isoformat()
        return data


@dataclass
class PriceSnapshot:
    """价格历史快照模型"""
    item_statistics_id: int
    market: MarketType
    snapshot_date: datetime
    wear_condition: Optional[WearCondition] = None
    snapshot_price: Optional[Decimal] = None
    snapshot_volume: Optional[int] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """转换为字典，用于数据库插入"""
        data = asdict(self)
        if data.get("id") is None:
            data.pop("id", None)
        if data.get("created_at") is None:
            data.pop("created_at", None)
        # 转换枚举为字符串
        if isinstance(data.get("market"), Enum):
            data["market"] = data["market"].value
        if isinstance(data.get("wear_condition"), Enum):
            data["wear_condition"] = data["wear_condition"].value
        # 转换 Decimal 为 float
        if data.get("snapshot_price") is not None:
            data["snapshot_price"] = float(data["snapshot_price"])
        # 转换 datetime 为日期字符串
        if isinstance(data.get("snapshot_date"), datetime):
            data["snapshot_date"] = data["snapshot_date"].date().isoformat()
        return data


@dataclass
class DataSource:
    """数据源追踪模型"""
    source_name: str
    api_endpoint: Optional[str] = None
    last_sync_time: Optional[datetime] = None
    sync_status: Optional[str] = None
    error_message: Optional[str] = None
    total_synced: int = 0
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """转换为字典，用于数据库插入"""
        data = asdict(self)
        if data.get("id") is None:
            data.pop("id", None)
        if data.get("created_at") is None:
            data.pop("created_at", None)
        if data.get("updated_at") is None:
            data.pop("updated_at", None)
        # 转换 datetime 为 ISO 格式字符串
        if isinstance(data.get("last_sync_time"), datetime):
            data["last_sync_time"] = data["last_sync_time"].isoformat()
        return data

