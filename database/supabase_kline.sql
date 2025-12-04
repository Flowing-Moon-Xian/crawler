-- 大盘 K 线表
CREATE TABLE total_kline_data (
    id BIGSERIAL PRIMARY KEY,
    period kline_period NOT NULL,          -- K 线周期（hourly / daily）
    timestamp TIMESTAMPTZ NOT NULL,        -- 时间戳
    open_price DECIMAL(12, 2),             -- 开盘价
    close_price DECIMAL(12, 2),            -- 收盘价
    high_price DECIMAL(12, 2),             -- 最高价
    low_price DECIMAL(12, 2),              -- 最低价
    volume BIGINT,                         -- 成交量（手数/张数，根据你业务定义）
    turnover DECIMAL(18, 2),               -- 成交额（可选，不需要可以删掉）
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(period, timestamp)              -- 同一周期+时间只允许一条 K 线
);

-- 千百战大盘 K 线表
CREATE TABLE qianzhan_kline_data (
    id BIGSERIAL PRIMARY KEY,
    period kline_period NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    open_price DECIMAL(12, 2),
    close_price DECIMAL(12, 2),
    high_price DECIMAL(12, 2),
    low_price DECIMAL(12, 2),
    volume BIGINT,
    turnover DECIMAL(18, 2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(period, timestamp)
);

-- 探员大盘 K 线表
CREATE TABLE agent_kline_data (
    id BIGSERIAL PRIMARY KEY,
    period kline_period NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    open_price DECIMAL(12, 2),
    close_price DECIMAL(12, 2),
    high_price DECIMAL(12, 2),
    low_price DECIMAL(12, 2),
    volume BIGINT,
    turnover DECIMAL(18, 2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(period, timestamp)
);

-- 大盘
CREATE INDEX idx_dapan_kline_period ON total_kline_data(period);
CREATE INDEX idx_dapan_kline_timestamp ON total_kline_data(timestamp);
CREATE INDEX idx_dapan_kline_period_timestamp
    ON total_kline_data(period, timestamp);

-- 千百战
CREATE INDEX idx_qbz_kline_period ON qianzhan_kline_data(period);
CREATE INDEX idx_qbz_kline_timestamp ON qianzhan_kline_data(timestamp);
CREATE INDEX idx_qbz_kline_period_timestamp
    ON qianzhan_kline_data(period, timestamp);

-- 探员
CREATE INDEX idx_agent_kline_period ON agent_kline_data(period);
CREATE INDEX idx_agent_kline_timestamp ON agent_kline_data(timestamp);
CREATE INDEX idx_agent_kline_period_timestamp
    ON agent_kline_data(period, timestamp);