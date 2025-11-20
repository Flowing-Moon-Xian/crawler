-- ============================================
-- CS2 商品数据统计系统 - Supabase 数据库表结构
-- ============================================

-- 1. 商品类型枚举表
-- ============================================

-- 稀有度枚举
CREATE TYPE rarity_type AS ENUM (
    'consumer',      -- 消费
    'industrial',    -- 工业
    'mil_spec',      -- 军规
    'restricted',    -- 受限
    'classified',    -- 保密
    'covert',        -- 隐秘
    'contraband',    -- 违禁
    'exceptional'    -- 非凡
);

-- 磨损度枚举
CREATE TYPE wear_condition AS ENUM (
    'factory_new',   -- 崭新出场
    'minimal_wear',  -- 略有磨损
    'field_tested',  -- 久经沙场
    'well_worn',     -- 战痕累累
    'battle_scarred' -- 破损不堪
);

-- 商品类型枚举
CREATE TYPE item_type AS ENUM (
    'box',           -- 箱子
    'gun_skin',      -- 枪皮
    'knife_glove'    -- 刀皮和手套
);

-- 市场类型枚举
CREATE TYPE market_type AS ENUM (
    'buff',
    'uuyp',
    'steam'
);

-- K线周期类型枚举
CREATE TYPE kline_period AS ENUM (
    'hourly',        -- 时K
    'daily'          -- 日K
);


-- ============================================
-- 2. 核心商品表
-- ============================================

-- 箱子表
CREATE TABLE boxes (
    id BIGSERIAL PRIMARY KEY,
    qaq_id BIGINT,                                 -- CSQAQ 网站的商品ID
    name VARCHAR(255) NOT NULL,                    -- 箱子名称
    return_rate DECIMAL(10, 4),                    -- 回报率（额外属性）
    obtain_method TEXT,                            -- 获取途径（注释字段，如：稀有、常规、绝版等）
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(name),
    UNIQUE(qaq_id)
);

-- 刀皮和手套表
CREATE TABLE knife_gloves (
    id BIGSERIAL PRIMARY KEY,
    qaq_id BIGINT,                                 -- CSQAQ 网站的商品ID
    qaq_url TEXT,                                  -- CSQAQ 网站的商品URL（方便爬虫）
    name VARCHAR(255) NOT NULL,                    -- 名称
    item_type VARCHAR(50) NOT NULL,                -- 'knife' 或 'glove'
    rarity rarity_type NOT NULL,                   -- 稀有度
    skin_series VARCHAR(255),                      -- 皮肤系列/Collection
    is_tradable BOOLEAN DEFAULT true,              -- 是否可交易
    min_float DECIMAL(10, 8),                      -- 最小磨损值
    max_float DECIMAL(10, 8),                      -- 最大磨损值
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(name, item_type),
    UNIQUE(qaq_id)
);

-- 枪皮表
CREATE TABLE gun_skins (
    id BIGSERIAL PRIMARY KEY,
    qaq_id BIGINT,                                 -- CSQAQ 网站的商品ID
    qaq_url TEXT,                                  -- CSQAQ 网站的商品URL（方便爬虫）
    name VARCHAR(255) NOT NULL,                    -- 枪皮名称
    weapon_type VARCHAR(100),                      -- 武器类型（如 "AK-47", "M4A4", "AWP" 等）
    rarity rarity_type NOT NULL,                   -- 稀有度
    skin_series VARCHAR(255),                      -- 皮肤系列/Collection
    is_tradable BOOLEAN DEFAULT true,              -- 是否可交易
    min_float DECIMAL(10, 8),                      -- 最小磨损值
    max_float DECIMAL(10, 8),                      -- 最大磨损值
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(name),
    UNIQUE(qaq_id)
);

-- ============================================
-- 3. 关系表
-- ============================================

-- 箱子-刀皮手套关系表（一对多：一款刀皮/手套可能同时存在多个箱子）
CREATE TABLE box_knife_glove_relations (
    id BIGSERIAL PRIMARY KEY,
    box_id BIGINT NOT NULL REFERENCES boxes(id) ON DELETE CASCADE,
    knife_glove_id BIGINT NOT NULL REFERENCES knife_gloves(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(box_id, knife_glove_id)
);

-- 箱子-枪皮关系表（一对多：一个箱子有多种枪皮）
CREATE TABLE box_gun_skin_relations (
    id BIGSERIAL PRIMARY KEY,
    box_id BIGINT NOT NULL REFERENCES boxes(id) ON DELETE CASCADE,
    gun_skin_id BIGINT NOT NULL REFERENCES gun_skins(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(box_id, gun_skin_id)
);

-- ============================================
-- 4. 商品统计表
-- ============================================

-- 商品统计主表（存世量、名字、类型、稀有度）
CREATE TABLE item_statistics (
    id BIGSERIAL PRIMARY KEY,
    item_id BIGINT NOT NULL,                       -- 商品ID（可能是 gun_skin_id 或 knife_glove_id）
    item_type item_type NOT NULL,                  -- 商品类型
    name VARCHAR(255) NOT NULL,                    -- 商品名称
    rarity rarity_type,                            -- 稀有度（枪皮和刀皮手套都有）
    circulation BIGINT,                            -- 存世量
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(item_id, item_type)
);

-- ============================================
-- 5. K线数据表
-- ============================================

-- K线数据表（开盘价、收盘价、最高价、最低价、交易量）
CREATE TABLE kline_data (
    id BIGSERIAL PRIMARY KEY,
    item_statistics_id BIGINT NOT NULL REFERENCES item_statistics(id) ON DELETE CASCADE,
    period kline_period NOT NULL,                  -- K线周期（时K或日K）
    timestamp TIMESTAMPTZ NOT NULL,                -- 时间戳
    open_price DECIMAL(12, 2),                     -- 开盘价
    close_price DECIMAL(12, 2),                    -- 收盘价
    high_price DECIMAL(12, 2),                     -- 最高价
    low_price DECIMAL(12, 2),                      -- 最低价
    volume BIGINT,                                 -- 交易量
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(item_statistics_id, period, timestamp)
);

-- ============================================
-- 6. 市场数据表
-- ============================================

-- 市场数据主表（三个市场共有字段）
CREATE TABLE market_data (
    id BIGSERIAL PRIMARY KEY,
    item_statistics_id BIGINT NOT NULL REFERENCES item_statistics(id) ON DELETE CASCADE,
    market market_type NOT NULL,                   -- 市场类型
    wear_condition wear_condition,                 -- 磨损度（枪皮和刀皮手套都有）
    selling_price DECIMAL(12, 2),                  -- 出售价
    buying_price DECIMAL(12, 2),                   -- 求购价
    transaction_price DECIMAL(12, 2),              -- 成交价
    transaction_volume BIGINT,                     -- 成交量
    items_for_sale INTEGER,                        -- 在售数
    buy_orders INTEGER,                            -- 求购数
    avg_price_7d DECIMAL(12, 2),                   -- 7日平均价格
    avg_price_30d DECIMAL(12, 2),                  -- 30日平均价格
    price_change_24h DECIMAL(10, 4),               -- 24小时价格变化百分比
    price_change_7d DECIMAL(10, 4),                -- 7日价格变化百分比
    liquidity_score INTEGER,                       -- 流动性评分（基于交易量）
    popularity_rank INTEGER,                       -- 热度排名
    timestamp TIMESTAMPTZ NOT NULL,                -- 数据采集时间
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(item_statistics_id, market, wear_condition, timestamp)
);

-- UUYP 市场独有数据表
CREATE TABLE uuyp_data (
    id BIGSERIAL PRIMARY KEY,
    market_data_id BIGINT NOT NULL REFERENCES market_data(id) ON DELETE CASCADE,
    long_rent_yield DECIMAL(10, 4),                -- 长租收益率
    short_rent_yield DECIMAL(10, 4),               -- 短租收益率
    long_rent_price DECIMAL(12, 2),                -- 长租价格
    short_rent_price DECIMAL(12, 2),               -- 短租价格
    rental_buyout DECIMAL(12, 2),                  -- 租赁买断
    timestamp TIMESTAMPTZ NOT NULL,                -- 数据采集时间
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(market_data_id, timestamp)
);

-- Steam 市场独有数据表
CREATE TABLE steam_data (
    id BIGSERIAL PRIMARY KEY,
    market_data_id BIGINT NOT NULL REFERENCES market_data(id) ON DELETE CASCADE,
    buy_order_overprice_ratio DECIMAL(10, 4),      -- 求购挂刀比
    sell_order_overprice_ratio DECIMAL(10, 4),     -- 在售挂刀比
    timestamp TIMESTAMPTZ NOT NULL,                -- 数据采集时间
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(market_data_id, timestamp)
);

-- Buff 市场独有数据表
CREATE TABLE buff_data (
    id BIGSERIAL PRIMARY KEY,
    market_data_id BIGINT NOT NULL REFERENCES market_data(id) ON DELETE CASCADE,
    buff_goods_id BIGINT,                          -- Buff 商品ID
    steam_price DECIMAL(12, 2),                    -- Steam 参考价格
    steam_price_cny DECIMAL(12, 2),                -- Steam 价格（人民币）
    sell_min_price DECIMAL(12, 2),                 -- 最低在售价
    buy_max_price DECIMAL(12, 2),                  -- 最高求购价
    timestamp TIMESTAMPTZ NOT NULL,                -- 数据采集时间
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(market_data_id, timestamp)
);

-- ============================================
-- 7. 价格历史快照表
-- ============================================

-- 价格历史快照表（用于详细的历史分析）
CREATE TABLE price_snapshots (
    id BIGSERIAL PRIMARY KEY,
    item_statistics_id BIGINT NOT NULL REFERENCES item_statistics(id) ON DELETE CASCADE,
    market market_type NOT NULL,                   -- 市场类型
    wear_condition wear_condition,                 -- 磨损度
    snapshot_price DECIMAL(12, 2),                 -- 快照时的价格
    snapshot_volume INTEGER,                       -- 快照时的交易量
    snapshot_date DATE NOT NULL,                   -- 快照日期
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(item_statistics_id, market, wear_condition, snapshot_date)
);

-- ============================================
-- 8. 数据源追踪表
-- ============================================

-- 数据源追踪表（追踪数据来源和同步状态）
CREATE TABLE data_sources (
    id BIGSERIAL PRIMARY KEY,
    source_name VARCHAR(50) NOT NULL,              -- 'buff', 'uuyp', 'steam', 'csqaq'
    api_endpoint TEXT,                             -- API 端点
    last_sync_time TIMESTAMPTZ,                    -- 最后同步时间
    sync_status VARCHAR(20),                       -- 'success', 'failed', 'syncing'
    error_message TEXT,                            -- 错误信息
    total_synced INTEGER DEFAULT 0,                -- 累计同步次数
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(source_name)
);

-- ============================================
-- 9. 索引优化
-- ============================================

-- 箱子表索引
CREATE INDEX idx_boxes_name ON boxes(name);
CREATE INDEX idx_boxes_qaq_id ON boxes(qaq_id);
CREATE INDEX idx_boxes_return_rate ON boxes(return_rate);
CREATE INDEX idx_boxes_obtain_method ON boxes(obtain_method);

-- 刀皮手套表索引
CREATE INDEX idx_knife_gloves_name ON knife_gloves(name);
CREATE INDEX idx_knife_gloves_qaq_id ON knife_gloves(qaq_id);
CREATE INDEX idx_knife_gloves_rarity ON knife_gloves(rarity);
CREATE INDEX idx_knife_gloves_item_type ON knife_gloves(item_type);
CREATE INDEX idx_knife_gloves_skin_series ON knife_gloves(skin_series);
CREATE INDEX idx_knife_gloves_is_tradable ON knife_gloves(is_tradable);

-- 枪皮表索引
CREATE INDEX idx_gun_skins_name ON gun_skins(name);
CREATE INDEX idx_gun_skins_qaq_id ON gun_skins(qaq_id);
CREATE INDEX idx_gun_skins_rarity ON gun_skins(rarity);
CREATE INDEX idx_gun_skins_weapon_type ON gun_skins(weapon_type);
CREATE INDEX idx_gun_skins_skin_series ON gun_skins(skin_series);
CREATE INDEX idx_gun_skins_is_tradable ON gun_skins(is_tradable);

-- 关系表索引
CREATE INDEX idx_box_knife_glove_box_id ON box_knife_glove_relations(box_id);
CREATE INDEX idx_box_knife_glove_knife_glove_id ON box_knife_glove_relations(knife_glove_id);
CREATE INDEX idx_box_gun_skin_box_id ON box_gun_skin_relations(box_id);
CREATE INDEX idx_box_gun_skin_gun_skin_id ON box_gun_skin_relations(gun_skin_id);

-- 商品统计表索引
CREATE INDEX idx_item_statistics_item_id ON item_statistics(item_id);
CREATE INDEX idx_item_statistics_item_type ON item_statistics(item_type);
CREATE INDEX idx_item_statistics_rarity ON item_statistics(rarity);
CREATE INDEX idx_item_statistics_name ON item_statistics(name);

-- K线数据表索引
CREATE INDEX idx_kline_data_item_statistics_id ON kline_data(item_statistics_id);
CREATE INDEX idx_kline_data_period ON kline_data(period);
CREATE INDEX idx_kline_data_timestamp ON kline_data(timestamp);
CREATE INDEX idx_kline_data_item_period_timestamp ON kline_data(item_statistics_id, period, timestamp);

-- 市场数据表索引
CREATE INDEX idx_market_data_item_statistics_id ON market_data(item_statistics_id);
CREATE INDEX idx_market_data_market ON market_data(market);
CREATE INDEX idx_market_data_wear_condition ON market_data(wear_condition);
CREATE INDEX idx_market_data_timestamp ON market_data(timestamp);
CREATE INDEX idx_market_data_item_market_timestamp ON market_data(item_statistics_id, market, timestamp);
CREATE INDEX idx_market_data_liquidity_score ON market_data(liquidity_score);
CREATE INDEX idx_market_data_popularity_rank ON market_data(popularity_rank);
CREATE INDEX idx_market_data_price_change_7d ON market_data(price_change_7d);

-- UUYP 数据表索引
CREATE INDEX idx_uuyp_data_market_data_id ON uuyp_data(market_data_id);
CREATE INDEX idx_uuyp_data_timestamp ON uuyp_data(timestamp);

-- Steam 数据表索引
CREATE INDEX idx_steam_data_market_data_id ON steam_data(market_data_id);
CREATE INDEX idx_steam_data_timestamp ON steam_data(timestamp);

-- Buff 数据表索引
CREATE INDEX idx_buff_data_market_data_id ON buff_data(market_data_id);
CREATE INDEX idx_buff_data_buff_goods_id ON buff_data(buff_goods_id);
CREATE INDEX idx_buff_data_timestamp ON buff_data(timestamp);

-- 价格快照表索引
CREATE INDEX idx_price_snapshots_item_statistics_id ON price_snapshots(item_statistics_id);
CREATE INDEX idx_price_snapshots_market ON price_snapshots(market);
CREATE INDEX idx_price_snapshots_snapshot_date ON price_snapshots(snapshot_date);
CREATE INDEX idx_price_snapshots_item_market_date ON price_snapshots(item_statistics_id, market, snapshot_date);

-- 数据源表索引
CREATE INDEX idx_data_sources_source_name ON data_sources(source_name);
CREATE INDEX idx_data_sources_sync_status ON data_sources(sync_status);
CREATE INDEX idx_data_sources_last_sync_time ON data_sources(last_sync_time);

-- ============================================
-- 10. 更新时间触发器
-- ============================================

-- 创建更新 updated_at 字段的函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为需要的表添加触发器
CREATE TRIGGER update_boxes_updated_at BEFORE UPDATE ON boxes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_knife_gloves_updated_at BEFORE UPDATE ON knife_gloves
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_gun_skins_updated_at BEFORE UPDATE ON gun_skins
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_item_statistics_updated_at BEFORE UPDATE ON item_statistics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_data_sources_updated_at BEFORE UPDATE ON data_sources
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 11. 视图（便于查询）
-- ============================================

-- 商品完整信息视图（包含统计信息）
CREATE VIEW v_item_full_info AS
SELECT 
    its.id,
    its.item_id,
    its.item_type,
    its.name,
    its.rarity,
    its.circulation,
    CASE 
        WHEN its.item_type = 'gun_skin' THEN gs.id
        WHEN its.item_type = 'knife_glove' THEN kg.id
        ELSE NULL
    END as original_item_id,
    its.created_at,
    its.updated_at
FROM item_statistics its
LEFT JOIN gun_skins gs ON its.item_type = 'gun_skin' AND its.item_id = gs.id
LEFT JOIN knife_gloves kg ON its.item_type = 'knife_glove' AND its.item_id = kg.id;

-- 市场数据完整视图（包含所有市场信息）
CREATE VIEW v_market_full_data AS
SELECT 
    md.id,
    md.item_statistics_id,
    md.market,
    md.wear_condition,
    md.selling_price,
    md.buying_price,
    md.transaction_price,
    md.transaction_volume,
    md.items_for_sale,
    md.buy_orders,
    md.avg_price_7d,
    md.avg_price_30d,
    md.price_change_24h,
    md.price_change_7d,
    md.liquidity_score,
    md.popularity_rank,
    md.timestamp,
    -- UUYP 独有字段
    uuyp.long_rent_yield,
    uuyp.short_rent_yield,
    uuyp.long_rent_price,
    uuyp.short_rent_price,
    uuyp.rental_buyout,
    -- Steam 独有字段
    steam.buy_order_overprice_ratio,
    steam.sell_order_overprice_ratio,
    -- Buff 独有字段
    buff.buff_goods_id,
    buff.steam_price,
    buff.steam_price_cny,
    buff.sell_min_price,
    buff.buy_max_price
FROM market_data md
LEFT JOIN uuyp_data uuyp ON md.id = uuyp.market_data_id AND md.market = 'uuyp'
LEFT JOIN steam_data steam ON md.id = steam.market_data_id AND md.market = 'steam'
LEFT JOIN buff_data buff ON md.id = buff.market_data_id AND md.market = 'buff';

-- ============================================
-- 12. 注释说明
-- ============================================

COMMENT ON TABLE boxes IS '箱子表，包含箱子的基本信息、回报率、获取途径和当前价格';
COMMENT ON TABLE knife_gloves IS '刀皮和手套表，包含 CSQAQ 商品ID、磨损值范围和皮肤系列';
COMMENT ON TABLE gun_skins IS '枪皮表，包含 CSQAQ 商品ID、武器类型、磨损值范围和皮肤系列';
COMMENT ON TABLE box_knife_glove_relations IS '箱子与刀皮/手套的关系表（一对多）';
COMMENT ON TABLE box_gun_skin_relations IS '箱子与枪皮的关系表（一对多）';
COMMENT ON TABLE item_statistics IS '商品统计主表，存储存世量、名称、类型、稀有度等信息';
COMMENT ON TABLE kline_data IS 'K线数据表，存储开盘价、收盘价、最高价、最低价、交易量';
COMMENT ON TABLE market_data IS '市场数据主表，存储三个市场（buff、uuyp、steam）的共有字段，包含价格趋势和热度数据';
COMMENT ON TABLE uuyp_data IS 'UUYP 市场独有数据表，包含租赁相关数据';
COMMENT ON TABLE steam_data IS 'Steam 市场独有数据表，包含挂刀比数据';
COMMENT ON TABLE buff_data IS 'Buff 市场独有数据表，包含 Steam 参考价格等数据';
COMMENT ON TABLE price_snapshots IS '价格历史快照表，用于详细的价格历史分析';
COMMENT ON TABLE data_sources IS '数据源追踪表，记录各数据源的同步状态和最后同步时间';

