-- ============================================
-- 迁移脚本：将 yinhua 改为 sticker
-- ============================================
-- 注意：执行此脚本前请备份数据库
-- 如果数据库尚未创建，直接使用 supabase_schema.sql 即可

-- 1. 重命名表（如果表已存在）
ALTER TABLE IF EXISTS yinhua_kline_data RENAME TO sticker_kline_data;

-- 2. 重命名索引（如果索引已存在）
ALTER INDEX IF EXISTS idx_yinhua_kline_period RENAME TO idx_sticker_kline_period;
ALTER INDEX IF EXISTS idx_yinhua_kline_timestamp RENAME TO idx_sticker_kline_timestamp;
ALTER INDEX IF EXISTS idx_yinhua_kline_period_timestamp RENAME TO idx_sticker_kline_period_timestamp;

-- 3. 确保枚举值 'sticker' 存在（如果枚举类型已存在且尚未添加该值）
-- 注意：如果枚举值已经手动更新，此步骤可以跳过
ALTER TYPE market_index_type ADD VALUE IF NOT EXISTS 'sticker';

-- 注意：由于枚举值已经手动更新，'yinhua' 已不存在于枚举类型中
-- 如果之前有使用 'yinhua' 的数据，需要在更新枚举值之前先更新数据
-- 如果枚举值已经更新，数据应该已经自动转换为 'sticker' 或需要手动处理

-- 4. 更新表注释
COMMENT ON TABLE sticker_kline_data IS '印花大盘 K 线数据表，存储印花大盘的开盘价、收盘价、最高价、最低价、交易量、成交额';
