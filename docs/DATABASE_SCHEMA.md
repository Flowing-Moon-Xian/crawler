# CS2 商品数据统计系统 - 数据库设计文档

## 概述

本数据库设计用于存储 CS2（Counter-Strike 2）游戏商品的统计数据和市场信息，支持从多个数据源（CSQAQ、SteamDT、Buff、UUYP、Steam）采集数据。

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
| obtain_method | TEXT | 获取途径（注释字段，如：稀有、常规、绝版等） |
| created_at | TIMESTAMPTZ | 创建时间 |
| updated_at | TIMESTAMPTZ | 更新时间 |

**索引**：
- `idx_boxes_name` - 箱子名称
- `idx_boxes_qaq_id` - CSQAQ ID
- `idx_boxes_return_rate` - 回报率
- `idx_boxes_obtain_method` - 获取途径

#### `knife_gloves` - 刀皮和手套表
存储刀皮和手套的基本信息。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| qaq_id | BIGINT | CSQAQ 网站的商品ID（唯一） |
| qaq_url | TEXT | CSQAQ 网站的商品URL（方便爬虫） |
| name | VARCHAR(255) | 名称 |
| item_type | VARCHAR(50) | 类型：'knife' 或 'glove' |
| rarity | rarity_type | 稀有度（枚举） |
| wear_condition | wear_condition | 磨损度（CSQAQ 将不同磨损度当作不同商品） |
| skin_series | VARCHAR(255) | 皮肤系列/Collection |
| is_tradable | BOOLEAN | 是否可交易（默认 true） |
| min_float | DECIMAL(10,8) | 最小磨损值 |
| max_float | DECIMAL(10,8) | 最大磨损值 |
| created_at | TIMESTAMPTZ | 创建时间 |
| updated_at | TIMESTAMPTZ | 更新时间 |

**注意**：CSQAQ 将不同磨损度当作不同商品，因此同一名称和类型的商品可以有多个磨损度记录。

**索引**：
- `idx_knife_gloves_name` - 名称
- `idx_knife_gloves_qaq_id` - CSQAQ ID
- `idx_knife_gloves_rarity` - 稀有度
- `idx_knife_gloves_item_type` - 类型
- `idx_knife_gloves_wear_condition` - 磨损度
- `idx_knife_gloves_name_item_type_wear_condition` - 复合索引

#### `gun_skins` - 枪皮表
存储枪皮的基本信息。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| qaq_id | BIGINT | CSQAQ 网站的商品ID（唯一） |
| qaq_url | TEXT | CSQAQ 网站的商品URL（方便爬虫） |
| name | VARCHAR(255) | 枪皮名称 |
| weapon_type | VARCHAR(100) | 武器类型（如 "AK-47", "M4A4", "AWP" 等） |
| rarity | rarity_type | 稀有度（枚举） |
| wear_condition | wear_condition | 磨损度（CSQAQ 将不同磨损度当作不同商品） |
| skin_series | VARCHAR(255) | 皮肤系列/Collection |
| is_tradable | BOOLEAN | 是否可交易（默认 true） |
| min_float | DECIMAL(10,8) | 最小磨损值 |
| max_float | DECIMAL(10,8) | 最大磨损值 |
| created_at | TIMESTAMPTZ | 创建时间 |
| updated_at | TIMESTAMPTZ | 更新时间 |

**注意**：CSQAQ 将不同磨损度当作不同商品，因此同一名称的枪皮可以有多个磨损度记录。

**索引**：
- `idx_gun_skins_name` - 名称
- `idx_gun_skins_qaq_id` - CSQAQ ID
- `idx_gun_skins_rarity` - 稀有度
- `idx_gun_skins_weapon_type` - 武器类型
- `idx_gun_skins_wear_condition` - 磨损度
- `idx_gun_skins_name_wear_condition` - 复合索引

### 2. 关系表

#### `box_knife_glove_relations` - 箱子-刀皮手套关系表
表示箱子与刀皮/手套的多对多关系（一款刀皮/手套可能同时存在多个箱子）。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| box_id | BIGINT | 箱子ID（外键） |
| knife_glove_id | BIGINT | 刀皮/手套ID（外键） |
| created_at | TIMESTAMPTZ | 创建时间 |

**唯一约束**：`(box_id, knife_glove_id)`

#### `box_gun_skin_relations` - 箱子-枪皮关系表
表示箱子与枪皮的一对多关系（一个箱子有多种枪皮）。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| box_id | BIGINT | 箱子ID（外键） |
| gun_skin_id | BIGINT | 枪皮ID（外键） |
| created_at | TIMESTAMPTZ | 创建时间 |

**唯一约束**：`(box_id, gun_skin_id)`

#### `item_statistics_market_index_relations` - 商品-大盘关系表
表示商品与大盘的多对多关系（一个商品可以对应多个大盘）。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| item_statistics_id | BIGINT | 商品统计ID（外键，关联 item_statistics） |
| market_index_type | market_index_type | 大盘类型（枚举：total/qianzhan/agent） |
| created_at | TIMESTAMPTZ | 创建时间 |

**唯一约束**：`(item_statistics_id, market_index_type)`

**索引**：
- `idx_item_statistics_market_index_item_statistics_id` - 商品统计ID
- `idx_item_statistics_market_index_type` - 大盘类型

**说明**：此表用于将商品关联到对应的大盘。一个商品可以同时属于多个大盘（如同时属于大盘和千百战大盘）。

### 3. 统计表

#### `item_statistics` - 商品统计主表
存储商品的统计信息（存世量、名字、类型、稀有度），作为统一维度表，便于关联各种统计数据。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| item_id | BIGINT | 商品ID（关联 gun_skins 或 knife_gloves） |
| item_type | item_type | 商品类型（枚举：box/gun_skin/knife_glove） |
| name | VARCHAR(255) | 商品名称 |
| csqaq_id | BIGINT | CSQAQ 商品ID（可选，便于直接关联） |
| steamdt_id | BIGINT | SteamDT 商品ID（可选，便于直接关联） |
| rarity | rarity_type | 稀有度（枚举） |
| circulation | BIGINT | 存世量 |
| created_at | TIMESTAMPTZ | 创建时间 |
| updated_at | TIMESTAMPTZ | 更新时间 |

**唯一约束**：`(item_id, item_type)`

**索引**：
- `idx_item_statistics_item_id` - 商品ID
- `idx_item_statistics_item_type` - 商品类型
- `idx_item_statistics_rarity` - 稀有度
- `idx_item_statistics_name` - 名称
- `idx_item_statistics_csqaq_id` - CSQAQ ID
- `idx_item_statistics_steamdt_id` - SteamDT ID

**说明**：此表作为统一维度表，用于关联 K 线数据、走势数据、市场数据等。通过 `csqaq_id` 和 `steamdt_id` 可以直接关联不同数据源的 ID。

### 4. K线数据表

#### `kline_data` - 商品 K 线数据表
存储具体商品的 K 线数据（开盘价、收盘价、最高价、最低价、交易量、成交额）。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| item_statistics_id | BIGINT | 商品统计ID（外键，关联 item_statistics） |
| period | kline_period | K线周期（枚举：hourly/daily/weekly） |
| timestamp | TIMESTAMPTZ | 时间戳 |
| open_price | DECIMAL(12,2) | 开盘价 |
| close_price | DECIMAL(12,2) | 收盘价 |
| high_price | DECIMAL(12,2) | 最高价 |
| low_price | DECIMAL(12,2) | 最低价 |
| volume | BIGINT | 交易量 |
| turnover | DECIMAL(18,2) | 成交额 |
| created_at | TIMESTAMPTZ | 创建时间 |

**唯一约束**：`(item_statistics_id, period, timestamp)`

**索引**：
- `idx_kline_data_item_statistics_id` - 商品统计ID
- `idx_kline_data_period` - 周期
- `idx_kline_data_timestamp` - 时间戳
- `idx_kline_data_item_period_timestamp` - 复合索引

#### `total_kline_data` - 大盘 K 线数据表
存储整个市场的 K 线数据。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| period | kline_period | K线周期（枚举：hourly/daily/weekly） |
| timestamp | TIMESTAMPTZ | 时间戳 |
| open_price | DECIMAL(12,2) | 开盘价 |
| close_price | DECIMAL(12,2) | 收盘价 |
| high_price | DECIMAL(12,2) | 最高价 |
| low_price | DECIMAL(12,2) | 最低价 |
| volume | BIGINT | 交易量 |
| turnover | DECIMAL(18,2) | 成交额 |
| created_at | TIMESTAMPTZ | 创建时间 |

**唯一约束**：`(period, timestamp)`

**索引**：
- `idx_dapan_kline_period` - 周期
- `idx_dapan_kline_timestamp` - 时间戳
- `idx_dapan_kline_period_timestamp` - 复合索引

#### `qianzhan_kline_data` - 千百战大盘 K 线数据表
存储千百战子市场的 K 线数据。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| period | kline_period | K线周期（枚举：hourly/daily/weekly） |
| timestamp | TIMESTAMPTZ | 时间戳 |
| open_price | DECIMAL(12,2) | 开盘价 |
| close_price | DECIMAL(12,2) | 收盘价 |
| high_price | DECIMAL(12,2) | 最高价 |
| low_price | DECIMAL(12,2) | 最低价 |
| volume | BIGINT | 交易量 |
| turnover | DECIMAL(18,2) | 成交额 |
| created_at | TIMESTAMPTZ | 创建时间 |

**唯一约束**：`(period, timestamp)`

**索引**：
- `idx_qbz_kline_period` - 周期
- `idx_qbz_kline_timestamp` - 时间戳
- `idx_qbz_kline_period_timestamp` - 复合索引

#### `agent_kline_data` - 探员大盘 K 线数据表
存储探员子市场的 K 线数据。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| period | kline_period | K线周期（枚举：hourly/daily/weekly） |
| timestamp | TIMESTAMPTZ | 时间戳 |
| open_price | DECIMAL(12,2) | 开盘价 |
| close_price | DECIMAL(12,2) | 收盘价 |
| high_price | DECIMAL(12,2) | 最高价 |
| low_price | DECIMAL(12,2) | 最低价 |
| volume | BIGINT | 交易量 |
| turnover | DECIMAL(18,2) | 成交额 |
| created_at | TIMESTAMPTZ | 创建时间 |

**唯一约束**：`(period, timestamp)`

**索引**：
- `idx_agent_kline_period` - 周期
- `idx_agent_kline_timestamp` - 时间戳
- `idx_agent_kline_period_timestamp` - 复合索引

### 5. 走势数据表

#### `trend_data` - 商品走势数据表
存储商品的市场趋势数据（价格、在售数量、求购价、求购数量、存世量、成交量、成交额），支持时K、日K、周K三种周期。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| item_statistics_id | BIGINT | 商品统计ID（外键，关联 item_statistics） |
| period | kline_period | 周期（枚举：hourly/daily/weekly） |
| timestamp | TIMESTAMPTZ | 时间戳 |
| price | DECIMAL(12,2) | 价格（成交价或平均价） |
| items_for_sale | INTEGER | 在售数量 |
| buying_price | DECIMAL(12,2) | 求购价 |
| buy_orders | INTEGER | 求购数量 |
| circulation | BIGINT | 存世量 |
| transaction_volume | BIGINT | 成交量 |
| turnover | DECIMAL(18,2) | 成交额 |
| created_at | TIMESTAMPTZ | 创建时间 |

**唯一约束**：`(item_statistics_id, period, timestamp)`

**索引**：
- `idx_trend_data_item_statistics_id` - 商品统计ID
- `idx_trend_data_period` - 周期
- `idx_trend_data_timestamp` - 时间戳
- `idx_trend_data_item_period_timestamp` - 复合索引

### 6. 市场数据表

#### `market_data` - 市场数据主表
存储三个市场（Buff、UUYP、Steam）的共有字段。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| item_statistics_id | BIGINT | 商品统计ID（外键，关联 item_statistics） |
| market | market_type | 市场类型（枚举：buff/uuyp/steam） |
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

**唯一约束**：`(item_statistics_id, market, timestamp)`

**注意**：`wear_condition` 字段已从 `market_data` 移除，磨损度信息现在存储在 `gun_skins` 和 `knife_gloves` 表中。

**索引**：
- `idx_market_data_item_statistics_id` - 商品统计ID
- `idx_market_data_market` - 市场类型
- `idx_market_data_timestamp` - 时间戳
- `idx_market_data_item_market_timestamp` - 复合索引
- `idx_market_data_liquidity_score` - 流动性评分
- `idx_market_data_popularity_rank` - 热度排名
- `idx_market_data_price_change_7d` - 7日价格变化

#### `uuyp_data` - UUYP 市场独有数据表
存储 UUYP 市场的独有字段。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| market_data_id | BIGINT | 市场数据ID（外键，关联 market_data） |
| long_rent_yield | DECIMAL(10,4) | 长租收益率 |
| short_rent_yield | DECIMAL(10,4) | 短租收益率 |
| long_rent_price | DECIMAL(12,2) | 长租价格 |
| short_rent_price | DECIMAL(12,2) | 短租价格 |
| rental_buyout | DECIMAL(12,2) | 租赁买断 |
| timestamp | TIMESTAMPTZ | 数据采集时间 |
| created_at | TIMESTAMPTZ | 创建时间 |

**唯一约束**：`(market_data_id, timestamp)`

#### `steam_data` - Steam 市场独有数据表
存储 Steam 市场的独有字段。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| market_data_id | BIGINT | 市场数据ID（外键，关联 market_data） |
| buy_order_overprice_ratio | DECIMAL(10,4) | 求购挂刀比 |
| sell_order_overprice_ratio | DECIMAL(10,4) | 在售挂刀比 |
| timestamp | TIMESTAMPTZ | 数据采集时间 |
| created_at | TIMESTAMPTZ | 创建时间 |

**唯一约束**：`(market_data_id, timestamp)`

#### `buff_data` - Buff 市场独有数据表
存储 Buff 市场的独有字段。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| market_data_id | BIGINT | 市场数据ID（外键，关联 market_data） |
| buff_goods_id | BIGINT | Buff 商品ID |
| steam_price | DECIMAL(12,2) | Steam 参考价格 |
| steam_price_cny | DECIMAL(12,2) | Steam 价格（人民币） |
| sell_min_price | DECIMAL(12,2) | 最低在售价 |
| buy_max_price | DECIMAL(12,2) | 最高求购价 |
| timestamp | TIMESTAMPTZ | 数据采集时间 |
| created_at | TIMESTAMPTZ | 创建时间 |

**唯一约束**：`(market_data_id, timestamp)`

### 7. 价格历史快照表

#### `price_snapshots` - 价格历史快照表
用于详细的价格历史分析。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGSERIAL | 主键 |
| item_statistics_id | BIGINT | 商品统计ID（外键，关联 item_statistics） |
| market | market_type | 市场类型（枚举） |
| wear_condition | wear_condition | 磨损度（枚举） |
| snapshot_price | DECIMAL(12,2) | 快照时的价格 |
| snapshot_volume | INTEGER | 快照时的交易量 |
| snapshot_date | DATE | 快照日期 |
| created_at | TIMESTAMPTZ | 创建时间 |

**唯一约束**：`(item_statistics_id, market, wear_condition, snapshot_date)`

### 8. 数据源追踪表

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

**唯一约束**：`(source_name)`

## 枚举类型

### `rarity_type` - 稀有度
- `normal` - 普通级
- `consumer` - 消费
- `industrial` - 工业
- `mil_spec` - 军规
- `restricted` - 受限
- `classified` - 保密
- `covert` - 隐秘
- `contraband` - 违禁
- `exceptional` - 非凡

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
- `buff` - Buff 市场
- `uuyp` - UUYP 市场
- `steam` - Steam 市场

### `kline_period` - K线周期
- `hourly` - 时K
- `daily` - 日K
- `weekly` - 周K

### `market_index_type` - 大盘类型
- `total` - 大盘
- `qianzhan` - 千百战大盘
- `agent` - 探员大盘

## 视图

### `v_item_full_info` - 商品完整信息视图
包含商品统计信息和原始商品信息的联合视图。

### `v_market_full_data` - 市场数据完整视图
包含所有市场数据（包括共有字段和独有字段）的联合视图。

## 数据关系图

```
boxes (箱子)
  ├── box_knife_glove_relations ──> knife_gloves (刀皮和手套)
  └── box_gun_skin_relations ──> gun_skins (枪皮)
                                    │
                                    └──> item_statistics (商品统计)
                                           ├──> kline_data (商品K线数据)
                                           ├──> trend_data (商品走势数据)
                                           ├──> price_snapshots (价格快照)
                                           └──> market_data (市场数据)
                                                  ├──> uuyp_data (UUYP独有)
                                                  ├──> steam_data (Steam独有)
                                                  └──> buff_data (Buff独有)

total_kline_data (大盘K线) - 独立表
qianzhan_kline_data (千百战大盘K线) - 独立表
agent_kline_data (探员大盘K线) - 独立表

data_sources (数据源追踪) - 独立表，记录各数据源同步状态
```

## 使用示例

### 1. 创建表结构

在 Supabase SQL Editor 中执行以下文件：
- `supabase_schema.sql` - 主表结构
- `supabase_kline.sql` - K线数据表结构

### 2. 插入数据示例

```python
from crawler.database.supabase_client import SupabaseManager

supabase = SupabaseManager()

# 插入箱子
box_data = {
    "qaq_id": 1272,
    "name": "武器箱 #1",
    "return_rate": 0.0250,
    "obtain_method": "常规"
}
box = supabase.insert_data("boxes", box_data)

# 插入枪皮
gun_skin_data = {
    "qaq_id": 1234,
    "name": "AK-47 | 火蛇",
    "rarity": "covert",
    "weapon_type": "AK-47"
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
    "csqaq_id": 1234,
    "steamdt_id": 24721,
    "rarity": "covert",
    "circulation": 10000
}
statistics = supabase.insert_data("item_statistics", statistics_data)

# 插入市场数据
market_data = {
    "item_statistics_id": statistics["id"],
    "market": "buff",
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

# 查询某个商品的走势数据
trend_data = supabase.query_data(
    "trend_data",
    filters={
        "item_statistics_id": statistics_id,
        "period": "daily"
    }
)

# 查询大盘K线数据
total_kline = supabase.query_data(
    "total_kline_data",
    filters={
        "period": "daily"
    }
)

# 使用视图查询完整信息
full_info = supabase.query_data(
    "v_item_full_info",
    filters={"item_type": "gun_skin"}
)
```

## 注意事项

1. **唯一性约束**：
   - 箱子名称唯一
   - 枪皮/刀皮手套的 `qaq_id` 唯一
   - 商品统计的 `(item_id, item_type)` 组合唯一
   - K线数据的 `(item_statistics_id, period, timestamp)` 或 `(period, timestamp)` 组合唯一
   - 走势数据的 `(item_statistics_id, period, timestamp)` 组合唯一
   - 市场数据的 `(item_statistics_id, market, timestamp)` 组合唯一

2. **外键约束**：
   - 所有外键都设置了 `ON DELETE CASCADE`，删除父记录时会自动删除子记录

3. **索引优化**：
   - 为常用查询字段创建了索引，提高查询性能
   - 复合索引用于优化多条件查询

4. **时间戳**：
   - 所有表都有 `created_at` 字段
   - 核心表还有 `updated_at` 字段，通过触发器自动更新
   - `timestamp` 字段用于记录数据采集时间，便于时间序列分析

5. **数据采集**：
   - `timestamp` 字段用于记录数据采集时间，便于时间序列分析
   - `created_at` 字段用于记录数据插入数据库的时间

6. **磨损度处理**：
   - `wear_condition` 字段已从 `market_data` 移除
   - 磨损度信息现在存储在 `gun_skins` 和 `knife_gloves` 表中
   - CSQAQ 将不同磨损度当作不同商品，因此同一名称的商品可以有多个磨损度记录

7. **商品统计表的作用**：
   - `item_statistics` 表作为统一维度表，用于关联各种统计数据
   - 通过 `csqaq_id` 和 `steamdt_id` 可以直接关联不同数据源的 ID
   - 便于统一查询和分析，避免多表关联

## 扩展建议

1. **分区表**：如果数据量很大，可以考虑对 `kline_data`、`trend_data` 和 `market_data` 表按时间分区

2. **归档策略**：定期归档历史数据，保持表的大小在合理范围内

3. **数据验证**：在应用层添加数据验证，确保数据的完整性和一致性

4. **监控告警**：设置监控，当数据采集异常时及时告警

5. **数据同步**：使用 `item_statistics_sync.py` 脚本定期同步 `item_statistics` 表的数据
