# CS2 商品数据统计系统 - 数据库设计文档

## 概述

本数据库设计用于存储 CS2（Counter-Strike 2）游戏商品的统计数据和市场信息，支持从三个市场（Buff、UUYP、Steam）采集数据。

## 数据库表结构

### 1. 核心商品表

#### `boxes` - 箱子表
存储箱子的基本信息。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| qaq_id | BIGINT | CSQAQ 网站的商品ID（唯一） |
| name | VARCHAR(255) | 箱子名称（唯一） |
| return_rate | DECIMAL(10,4) | 回报率（额外属性） |
| obtain_method | box_obtain_method | 获取途径（枚举：稀有/常规/绝版） |
| current_price | DECIMAL(12,2) | 箱子当前价格 |
| discontinue_date | DATE | 绝版日期（如果已绝版） |
| created_at | TIMESTAMPTZ | 创建时间 |
| updated_at | TIMESTAMPTZ | 更新时间 |

#### `knife_gloves` - 刀皮和手套表
存储刀皮和手套的基本信息。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| qaq_id | BIGINT | CSQAQ 网站的商品ID（唯一） |
| name | VARCHAR(255) | 名称 |
| item_type | VARCHAR(50) | 类型：'knife' 或 'glove' |
| rarity | rarity_type | 稀有度（枚举） |
| skin_series | VARCHAR(255) | 皮肤系列/Collection |
| is_tradable | BOOLEAN | 是否可交易（默认 true） |
| min_float | DECIMAL(10,8) | 最小磨损值 |
| max_float | DECIMAL(10,8) | 最大磨损值 |
| created_at | TIMESTAMPTZ | 创建时间 |
| updated_at | TIMESTAMPTZ | 更新时间 |

#### `gun_skins` - 枪皮表
存储枪皮的基本信息。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| qaq_id | BIGINT | CSQAQ 网站的商品ID（唯一） |
| name | VARCHAR(255) | 枪皮名称（唯一） |
| weapon_type | VARCHAR(100) | 武器类型（如 "AK-47", "M4A4", "AWP" 等） |
| rarity | rarity_type | 稀有度（枚举） |
| skin_series | VARCHAR(255) | 皮肤系列/Collection |
| is_tradable | BOOLEAN | 是否可交易（默认 true） |
| min_float | DECIMAL(10,8) | 最小磨损值 |
| max_float | DECIMAL(10,8) | 最大磨损值 |
| created_at | TIMESTAMPTZ | 创建时间 |
| updated_at | TIMESTAMPTZ | 更新时间 |

### 2. 关系表

#### `box_knife_glove_relations` - 箱子-刀皮手套关系表
表示箱子与刀皮/手套的多对多关系（一款刀皮/手套可能同时存在多个箱子）。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| box_id | BIGINT | 箱子ID（外键） |
| knife_glove_id | BIGINT | 刀皮/手套ID（外键） |
| created_at | TIMESTAMPTZ | 创建时间 |

#### `box_gun_skin_relations` - 箱子-枪皮关系表
表示箱子与枪皮的一对多关系（一个箱子有多种枪皮）。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| box_id | BIGINT | 箱子ID（外键） |
| gun_skin_id | BIGINT | 枪皮ID（外键） |
| created_at | TIMESTAMPTZ | 创建时间 |

### 3. 统计表

#### `item_statistics` - 商品统计主表
存储商品的统计信息（存世量、名字、类型、稀有度）。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| item_id | BIGINT | 商品ID（关联 gun_skins 或 knife_gloves） |
| item_type | item_type | 商品类型（枚举：box/gun_skin/knife_glove） |
| name | VARCHAR(255) | 商品名称 |
| rarity | rarity_type | 稀有度（枚举） |
| circulation | BIGINT | 存世量 |
| created_at | TIMESTAMPTZ | 创建时间 |
| updated_at | TIMESTAMPTZ | 更新时间 |

#### `kline_data` - K线数据表
存储商品的K线数据（开盘价、收盘价、最高价、最低价、交易量）。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| item_statistics_id | BIGINT | 商品统计ID（外键） |
| period | kline_period | K线周期（枚举：hourly/daily） |
| timestamp | TIMESTAMPTZ | 时间戳 |
| open_price | DECIMAL(12,2) | 开盘价 |
| close_price | DECIMAL(12,2) | 收盘价 |
| high_price | DECIMAL(12,2) | 最高价 |
| low_price | DECIMAL(12,2) | 最低价 |
| volume | BIGINT | 交易量 |
| created_at | TIMESTAMPTZ | 创建时间 |

### 4. 市场数据表

#### `market_data` - 市场数据主表
存储三个市场（Buff、UUYP、Steam）的共有字段。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| item_statistics_id | BIGINT | 商品统计ID（外键） |
| market | market_type | 市场类型（枚举：buff/uuyp/steam） |
| wear_condition | wear_condition | 磨损度（枚举） |
| selling_price | DECIMAL(12,2) | 出售价 |
| buying_price | DECIMAL(12,2) | 求购价 |
| transaction_price | DECIMAL(12,2) | 成交价 |
| transaction_volume | BIGINT | 成交量 |
| items_for_sale | INTEGER | 在售数 |
| buy_orders | INTEGER | 求购数 |
| avg_price_7d | DECIMAL(12,2) | 7日平均价格 |
| avg_price_30d | DECIMAL(12,2) | 30日平均价格 |
| price_change_24h | DECIMAL(10,4) | 24小时价格变化百分比 |
| price_change_7d | DECIMAL(10,4) | 7日价格变化百分比 |
| liquidity_score | INTEGER | 流动性评分（基于交易量） |
| popularity_rank | INTEGER | 热度排名 |
| timestamp | TIMESTAMPTZ | 数据采集时间 |
| created_at | TIMESTAMPTZ | 创建时间 |

#### `uuyp_data` - UUYP 市场独有数据表
存储 UUYP 市场的独有字段。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| market_data_id | BIGINT | 市场数据ID（外键） |
| long_rent_yield | DECIMAL(10,4) | 长租收益率 |
| short_rent_yield | DECIMAL(10,4) | 短租收益率 |
| long_rent_price | DECIMAL(12,2) | 长租价格 |
| short_rent_price | DECIMAL(12,2) | 短租价格 |
| rental_buyout | DECIMAL(12,2) | 租赁买断 |
| timestamp | TIMESTAMPTZ | 数据采集时间 |
| created_at | TIMESTAMPTZ | 创建时间 |

#### `steam_data` - Steam 市场独有数据表
存储 Steam 市场的独有字段。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| market_data_id | BIGINT | 市场数据ID（外键） |
| buy_order_overprice_ratio | DECIMAL(10,4) | 求购挂刀比 |
| sell_order_overprice_ratio | DECIMAL(10,4) | 在售挂刀比 |
| timestamp | TIMESTAMPTZ | 数据采集时间 |
| created_at | TIMESTAMPTZ | 创建时间 |

#### `buff_data` - Buff 市场独有数据表
存储 Buff 市场的独有字段。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| market_data_id | BIGINT | 市场数据ID（外键） |
| buff_goods_id | BIGINT | Buff 商品ID |
| steam_price | DECIMAL(12,2) | Steam 参考价格 |
| steam_price_cny | DECIMAL(12,2) | Steam 价格（人民币） |
| sell_min_price | DECIMAL(12,2) | 最低在售价 |
| buy_max_price | DECIMAL(12,2) | 最高求购价 |
| timestamp | TIMESTAMPTZ | 数据采集时间 |
| created_at | TIMESTAMPTZ | 创建时间 |

### 5. 价格历史快照表

#### `price_snapshots` - 价格历史快照表
用于详细的价格历史分析。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| item_statistics_id | BIGINT | 商品统计ID（外键） |
| market | market_type | 市场类型（枚举） |
| wear_condition | wear_condition | 磨损度（枚举） |
| snapshot_price | DECIMAL(12,2) | 快照时的价格 |
| snapshot_volume | INTEGER | 快照时的交易量 |
| snapshot_date | DATE | 快照日期 |
| created_at | TIMESTAMPTZ | 创建时间 |

### 6. 数据源追踪表

#### `data_sources` - 数据源追踪表
追踪数据来源和同步状态。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| source_name | VARCHAR(50) | 数据源名称（唯一：buff/uuyp/steam/csqaq） |
| api_endpoint | TEXT | API 端点 |
| last_sync_time | TIMESTAMPTZ | 最后同步时间 |
| sync_status | VARCHAR(20) | 同步状态（success/failed/syncing） |
| error_message | TEXT | 错误信息 |
| total_synced | INTEGER | 累计同步次数（默认 0） |
| created_at | TIMESTAMPTZ | 创建时间 |
| updated_at | TIMESTAMPTZ | 更新时间 |

## 枚举类型

### `rarity_type` - 稀有度
- `consumer` - 消费
- `industrial` - 工业
- `mil_spec` - 军规
- `restricted` - 受限
- `classified` - 保密
- `covert` - 隐秘
- `contraband` - 违禁

### `wear_condition` - 磨损度
- `factory_new` - 崭新出场
- `minimal_wear` - 略有磨损
- `field_tested` - 久经沙场
- `well_worn` - 战痕累累
- `battle_scarred` - 破损不堪

### `item_type` - 商品类型
- `box` - 箱子
- `gun_skin` - 枪皮
- `knife_glove` - 刀皮和手套

### `market_type` - 市场类型
- `buff`
- `uuyp`
- `steam`

### `kline_period` - K线周期
- `hourly` - 时K
- `daily` - 日K

### `box_obtain_method` - 箱子获取途径
- `rare` - 稀有
- `regular` - 常规
- `discontinued` - 绝版

## 视图

### `v_item_full_info` - 商品完整信息视图
包含商品统计信息和原始商品信息的联合视图。

### `v_market_full_data` - 市场数据完整视图
包含所有市场数据（包括共有字段和独有字段）的联合视图。

## 使用示例

### 1. 创建表结构

在 Supabase SQL Editor 中执行 `supabase_schema.sql` 文件。

### 2. 插入数据示例

```python
from crawler.supabase_client import SupabaseManager

supabase = SupabaseManager()

# 插入箱子
box_data = {
    "qaq_id": 1272,
    "name": "武器箱 #1",
    "return_rate": 0.0250,
    "obtain_method": "regular"
}
box = supabase.insert_data("boxes", box_data)

# 插入枪皮
gun_skin_data = {
    "qaq_id": 1234,
    "name": "AK-47 | 火蛇",
    "rarity": "covert"
}
gun_skin = supabase.insert_data("gun_skins", gun_skin_data)

# 建立关系
relation_data = {
    "box_id": box["id"],
    "gun_skin_id": gun_skin["id"]
}
supabase.insert_data("box_gun_skin_relations", relation_data)

# 插入商品统计
statistics_data = {
    "item_id": gun_skin["id"],
    "item_type": "gun_skin",
    "name": "AK-47 | 火蛇",
    "rarity": "covert",
    "circulation": 10000
}
statistics = supabase.insert_data("item_statistics", statistics_data)

# 插入市场数据
market_data = {
    "item_statistics_id": statistics["id"],
    "market": "buff",
    "wear_condition": "factory_new",
    "selling_price": 1500.00,
    "buying_price": 1450.00,
    "transaction_price": 1475.00,
    "transaction_volume": 50,
    "items_for_sale": 200,
    "buy_orders": 150,
    "timestamp": "2024-01-01T12:00:00Z"
}
market = supabase.insert_data("market_data", market_data)

# 如果是 UUYP 市场，插入独有数据
if market["market"] == "uuyp":
    uuyp_data = {
        "market_data_id": market["id"],
        "long_rent_yield": 0.05,
        "short_rent_yield": 0.08,
        "long_rent_price": 100.00,
        "short_rent_price": 20.00,
        "rental_buyout": 1500.00,
        "timestamp": "2024-01-01T12:00:00Z"
    }
    supabase.insert_data("uuyp_data", uuyp_data)
```

### 3. 查询数据示例

```python
# 查询某个商品的所有市场数据
market_data = supabase.query_data(
    "market_data",
    filters={"item_statistics_id": statistics_id}
)

# 查询某个商品的K线数据
kline_data = supabase.query_data(
    "kline_data",
    filters={
        "item_statistics_id": statistics_id,
        "period": "daily"
    }
)

# 使用视图查询完整信息
full_info = supabase.query_data(
    "v_item_full_info",
    filters={"item_type": "gun_skin"}
)
```

## 数据关系图

```
boxes (箱子)
  ├── box_knife_glove_relations ──> knife_gloves (刀皮和手套)
  └── box_gun_skin_relations ──> gun_skins (枪皮)
                                    │
                                    └──> item_statistics (商品统计)
                                           ├──> kline_data (K线数据)
                                           ├──> price_snapshots (价格快照)
                                           └──> market_data (市场数据)
                                                  ├──> uuyp_data (UUYP独有)
                                                  ├──> steam_data (Steam独有)
                                                  └──> buff_data (Buff独有)

data_sources (数据源追踪) - 独立表，记录各数据源同步状态
```

## 注意事项

1. **唯一性约束**：
   - 箱子名称唯一
   - 枪皮名称唯一
   - 刀皮/手套的 (name, item_type) 组合唯一
   - 商品统计的 (item_id, item_type) 组合唯一
   - K线数据的 (item_statistics_id, period, timestamp) 组合唯一
   - 市场数据的 (item_statistics_id, market, wear_condition, timestamp) 组合唯一

2. **外键约束**：
   - 所有外键都设置了 `ON DELETE CASCADE`，删除父记录时会自动删除子记录

3. **索引优化**：
   - 为常用查询字段创建了索引，提高查询性能

4. **时间戳**：
   - 所有表都有 `created_at` 字段
   - 核心表还有 `updated_at` 字段，通过触发器自动更新

5. **数据采集**：
   - `timestamp` 字段用于记录数据采集时间，便于时间序列分析
   - `created_at` 字段用于记录数据插入数据库的时间

## 扩展建议

1. **分区表**：如果数据量很大，可以考虑对 `kline_data` 和 `market_data` 表按时间分区
2. **归档策略**：定期归档历史数据，保持表的大小在合理范围内
3. **数据验证**：在应用层添加数据验证，确保数据的完整性和一致性
4. **监控告警**：设置监控，当数据采集异常时及时告警

