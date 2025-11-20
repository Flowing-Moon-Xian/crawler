-- ============================================
-- Supabase RLS 策略配置
-- 为所有表批量添加允许所有权限的策略
-- ============================================

-- 注意：这个脚本会为所有表添加允许匿名用户（anon）和认证用户（authenticated）所有操作的策略
-- 在生产环境中，建议根据实际需求调整策略，只授予必要的权限

-- 所有表的列表
DO $$
DECLARE
    table_name TEXT;
    tables TEXT[] := ARRAY[
        'boxes',
        'knife_gloves',
        'gun_skins',
        'box_knife_glove_relations',
        'box_gun_skin_relations',
        'item_statistics',
        'kline_data',
        'market_data',
        'uuyp_data',
        'steam_data',
        'buff_data',
        'price_snapshots',
        'data_sources'
    ];
BEGIN
    FOREACH table_name IN ARRAY tables
    LOOP
        -- 启用 RLS
        EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY;', table_name);
        
        -- 删除已存在的策略（如果存在）
        EXECUTE format('DROP POLICY IF EXISTS "Allow all for anon" ON %I;', table_name);
        EXECUTE format('DROP POLICY IF EXISTS "Allow all for authenticated" ON %I;', table_name);
        EXECUTE format('DROP POLICY IF EXISTS "Allow all operations for anon" ON %I;', table_name);
        EXECUTE format('DROP POLICY IF EXISTS "Allow all operations for authenticated" ON %I;', table_name);
        
        -- 为匿名用户（anon）创建允许所有操作的策略
        EXECUTE format('
            CREATE POLICY "Allow all operations for anon" ON %I
            FOR ALL
            TO anon
            USING (true)
            WITH CHECK (true);
        ', table_name);
        
        -- 为认证用户（authenticated）创建允许所有操作的策略
        EXECUTE format('
            CREATE POLICY "Allow all operations for authenticated" ON %I
            FOR ALL
            TO authenticated
            USING (true)
            WITH CHECK (true);
        ', table_name);
        
        RAISE NOTICE '已为表 % 添加 RLS 策略', table_name;
    END LOOP;
END $$;

-- 验证策略是否创建成功
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual,
    with_check
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, policyname;

