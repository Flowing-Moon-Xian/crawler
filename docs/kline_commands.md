# K线数据爬取命令说明

## 重要说明

### timestamp 和 maxTime 参数的区别

- **timestamp 参数**：
  - **作用**：仅用于校验，不影响返回的数据范围
  - **格式**：毫秒时间戳
  - **默认行为**：如果不提供，脚本会自动使用当前时间戳（毫秒）
  - **注意**：此参数主要用于 API 校验，不会影响实际返回的数据

- **maxTime 参数**：
  - **作用**：**真正决定返回数据范围的参数**
  - **格式**：秒时间戳
  - **数据范围**：API 每次返回的数据都是 `maxTime` **向前推三个月**的数据
  - **示例**：如果 `maxTime=1735574400`（2024-12-31），则返回 2024-10-01 至 2024-12-31 的数据
  - **建议**：始终提供此参数以限制数据范围

### 时间戳计算
- 2024-12-31 00:00:00 的时间戳（秒）：`1735574400`

---

## 1. 存储到 total_kline_data 表（大盘K线）

使用 `kline_crawler.py`，API: `https://api.steamdt.com/user/statistics/v1/kline`

### 日K数据（type=2）

```bash
# 使用当前时间戳（自动）
python3 -m crawler.crawlers.kline_crawler \
    --type 2 \
    --max-time 1735574400

# 或手动指定 timestamp（毫秒）
python3 -m crawler.crawlers.kline_crawler \
    --type 2 \
    --timestamp 1733097600000 \
    --max-time 1735574400
```

### 时K数据（type=1）

```bash
# 使用当前时间戳（自动）
python3 -m crawler.crawlers.kline_crawler \
    --type 1 \
    --max-time 1735574400

# 或手动指定 timestamp（毫秒）
python3 -m crawler.crawlers.kline_crawler \
    --type 1 \
    --timestamp 1733097600000 \
    --max-time 1735574400
```

### 周K数据（type=3）

```bash
# 使用当前时间戳（自动）
python3 -m crawler.crawlers.kline_crawler \
    --type 3 \
    --max-time 1735574400
```

### 参数说明
- `--type`: K线类型，1=时K，2=日K，3=周K
- `--max-time`: 最大时间戳（秒），用于限制数据范围
- `--timestamp`: （可选）时间戳（毫秒），用于分页。如果不提供，将自动使用当前时间戳

---

## 2. 存储到 qianzhan_kline_data 表（千百战大盘K线）

使用 `sub_kline_crawler.py`，API: `https://api.steamdt.com/user/item/block/v1/kline`

### 日K数据（klineType=2）

```bash
# 使用当前时间戳（自动）
python3 -m crawler.crawlers.sub_kline_crawler \
    --type HOT \
    --kline-type 2 \
    --type-val "1402501509110038528" \
    --table qianzhan_kline_data \
    --max-time 1735574400

# 或手动指定 timestamp（毫秒字符串）
python3 -m crawler.crawlers.sub_kline_crawler \
    --type HOT \
    --kline-type 2 \
    --type-val "1402501509110038528" \
    --table qianzhan_kline_data \
    --timestamp "1733097600000" \
    --max-time 1735574400
```

### 时K数据（klineType=1）

```bash
# 使用当前时间戳（自动）
python3 -m crawler.crawlers.sub_kline_crawler \
    --type HOT \
    --kline-type 1 \
    --type-val "1402501509110038528" \
    --table qianzhan_kline_data \
    --max-time 1735574400
```

### 参数说明
- `--type`: 类型，如 "HOT"
- `--kline-type`: K线类型，1=时K，2=日K，3=周K
- `--type-val`: 类型值，用于区分不同的子大盘（必填）
- `--table`: 目标表名，`qianzhan_kline_data` 或 `agent_kline_data`
- `--max-time`: 最大时间戳（秒），用于限制数据范围
- `--timestamp`: （可选）时间戳（毫秒字符串），用于分页。如果不提供，将自动使用当前时间戳
- `--platform`: （可选）平台，默认为 "ALL"
- `--special-style`: （可选）特殊样式，默认为空字符串

---

## 3. 存储到 agent_kline_data 表（探员大盘K线）

```bash
python3 -m crawler.crawlers.sub_kline_crawler \
    --type HOT \
    --kline-type 2 \
    --type-val "探员大盘的typeVal" \
    --table agent_kline_data \
    --max-time 1735574400
```

**注意**: 需要将 `"探员大盘的typeVal"` 替换为实际的 typeVal 值。

---

## 4. 存储到 kline_data 表（商品K线）

使用 `item_kline_crawler.py`，API: `https://api.steamdt.com/user/steam/category/v1/kline`

### 日K数据（type=2）

```bash
# 使用当前时间戳（自动）
python3 -m crawler.crawlers.item_kline_crawler \
    --kline-type 2 \
    --type-val 24721 \
    --max-time 1735574400

# 或手动指定 timestamp（毫秒）
python3 -m crawler.crawlers.item_kline_crawler \
    --kline-type 2 \
    --type-val 24721 \
    --timestamp 1733097600000 \
    --max-time 1735574400
```

### 时K数据（type=1）

```bash
python3 -m crawler.crawlers.item_kline_crawler \
    --kline-type 1 \
    --type-val 24721 \
    --max-time 1735574400
```

### 参数说明
- `--kline-type`: K线类型，1=时K，2=日K，3=周K
- `--type-val`: SteamDT 商品 / 分类 ID（对应 item_statistics.steamdt_id，必填）
- `--max-time`: 最大时间戳（秒），用于限制数据范围
- `--timestamp`: （可选）时间戳（毫秒），用于分页。如果不提供，将自动使用当前时间戳
- `--platform`: （可选）平台，默认为 "ALL"
- `--special-style`: （可选）特殊样式，默认为空字符串

**注意**：
- 脚本会自动根据 `type-val` 去 `item_statistics` 表查找对应的 `item_statistics_id`
- 如果找不到对应的记录，脚本会提示并终止

---

## 5. 存储到 trend_data 表（商品走势数据）

使用 `item_trend_crawler.py`，API: `https://api.steamdt.com/user/steam/type-trend/v2/item/details`

### 近一个月走势数据（typeDay=1）

```bash
# 使用当前时间戳（自动）
python3 -m crawler.crawlers.item_trend_crawler \
    --item-id 295893123 \
    --type-day 1

# 或手动指定 timestamp（毫秒）
python3 -m crawler.crawlers.item_trend_crawler \
    --item-id 295893123 \
    --type-day 1 \
    --timestamp 1764749386230
```

### 三个月走势数据（typeDay=2）

```bash
python3 -m crawler.crawlers.item_trend_crawler \
    --item-id 295893123 \
    --type-day 2
```

### 参数说明
- `--item-id`: SteamDT 商品 ID（对应 item_statistics.steamdt_id，必填）
- `--type-day`: 时间范围，1=近一月，2=三个月，3=六个月，4=一年，5=三年（默认: 1）
- `--timestamp`: （可选）时间戳（毫秒），用于 API 请求。如果不提供，将使用当前时间戳
- `--date-type`: dateType 参数，默认为 3（按接口文档固定）
- `--platform`: （可选）平台，默认为 "ALL"
- `--special-style`: （可选）特殊样式，默认为空字符串

**注意**：
- 脚本会自动根据 `item-id` 去 `item_statistics` 表查找对应的 `item_statistics_id`
- 如果找不到对应的记录，脚本会提示并终止
- 返回数据格式：`[时间戳, 价格, 在售数量, 求购价格, 求购数量, 成交额, 成交量, 存世量]`

---

## 6. 批量爬取（自动重复执行）

使用 `batch_kline_crawler.py` 可以自动重复执行爬虫，从当前时间开始，每次获取 `maxTime` 前三个月的数据，直到达到指定的目标 `max-time`。

### 工作原理

1. 从当前时间（或指定的 `--start-time`）开始
2. 每次向前推三个月（约 90 天）
3. 重复调用爬虫，直到 `maxTime <= 目标 max-time`
4. 自动处理时间范围，确保覆盖所有数据

### 大盘 K 线批量爬取（total_kline_data）

```bash
# 从当前时间爬取到 2024-12-31
python3 -m crawler.crawlers.batch_kline_crawler \
    --crawler-type total \
    --kline-type 2 \
    --target-max-time 1735574400

# 从指定时间开始爬取
python3 -m crawler.crawlers.batch_kline_crawler \
    --crawler-type total \
    --kline-type 2 \
    --target-max-time 1735574400 \
    --start-time 1735689600
```

### 子大盘 K 线批量爬取（qianzhan_kline_data / agent_kline_data）

```bash
# 千百战大盘
python3 -m crawler.crawlers.batch_kline_crawler \
    --crawler-type sub \
    --kline-type 2 \
    --type HOT \
    --type-val "1402501509110038528" \
    --table qianzhan_kline_data \
    --target-max-time 1735574400

# 探员大盘
python3 -m crawler.crawlers.batch_kline_crawler \
    --crawler-type sub \
    --kline-type 2 \
    --type HOT \
    --type-val "探员大盘的typeVal" \
    --table agent_kline_data \
    --target-max-time 1735574400
```

### 商品 K 线批量爬取（kline_data）

```bash
# 爬取指定商品的 K 线数据
python3 -m crawler.crawlers.batch_kline_crawler \
    --crawler-type item \
    --kline-type 2 \
    --type-val 24721 \
    --target-max-time 1735574400
```

### 批量爬取参数说明

**通用参数：**
- `--crawler-type`: 爬虫类型，`total`（大盘）、`sub`（子大盘）、`item`（商品）
- `--kline-type`: K 线类型，1=时K，2=日K，3=周K
- `--target-max-time`: **目标最大时间戳（秒）**，爬取到此时间为止
- `--start-time`: （可选）起始时间戳（秒），如果不提供则使用当前时间

**子大盘专用参数（`--crawler-type sub`）：**
- `--type`: 类型，如 "HOT"（必填）
- `--type-val`: 类型值，如 "1402501509110038528"（必填）
- `--table`: 目标表名，`qianzhan_kline_data` 或 `agent_kline_data`（默认：`qianzhan_kline_data`）

**商品专用参数（`--crawler-type item`）：**
- `--type-val`: SteamDT 商品 ID（整数，必填）

**其他可选参数：**
- `--platform`: 平台，默认为 "ALL"
- `--special-style`: 特殊样式，默认为空字符串

### 批量爬取示例

**示例 1：爬取大盘日K数据，从当前时间到 2024-12-31**
```bash
python3 -m crawler.crawlers.batch_kline_crawler \
    --crawler-type total \
    --kline-type 2 \
    --target-max-time 1735574400
```

**示例 2：爬取千百战大盘时K数据，从当前时间到 2024-01-01**
```bash
python3 -m crawler.crawlers.batch_kline_crawler \
    --crawler-type sub \
    --kline-type 1 \
    --type HOT \
    --type-val "1402501509110038528" \
    --table qianzhan_kline_data \
    --target-max-time 1704067200
```

**示例 3：爬取商品日K数据，从指定时间到 2024-12-31**
```bash
python3 -m crawler.crawlers.batch_kline_crawler \
    --crawler-type item \
    --kline-type 2 \
    --type-val 24721 \
    --target-max-time 1735574400 \
    --start-time 1735689600
```

### 批量爬取的优势

- **自动化**：无需手动计算时间范围，自动处理三个月间隔
- **完整覆盖**：确保从当前时间到目标时间的所有数据都被爬取
- **进度显示**：实时显示每轮爬取的进度和数据量
- **错误恢复**：如果某轮失败，可以调整 `--start-time` 继续爬取

---

## 快速参考

### 时间戳计算

```bash
# 2024-12-31 00:00:00 的时间戳（秒）: 1735574400
# 2024-01-01 00:00:00 的时间戳（秒）: 1704067200
```

### 常用命令组合

**大盘日K（total_kline_data）:**
```bash
python3 -m crawler.crawlers.kline_crawler --type 2 --max-time 1735574400
```

**千百战大盘日K（qianzhan_kline_data）:**
```bash
python3 -m crawler.crawlers.sub_kline_crawler \
    --type HOT \
    --kline-type 2 \
    --type-val "1402501509110038528" \
    --table qianzhan_kline_data \
    --max-time 1735574400
```

**商品日K（kline_data）:**
```bash
python3 -m crawler.crawlers.item_kline_crawler \
    --kline-type 2 \
    --type-val 24721 \
    --max-time 1735574400
```

**商品走势数据（trend_data）:**
```bash
python3 -m crawler.crawlers.item_trend_crawler \
    --item-id 295893123 \
    --type-day 1
```

---

## 参数详细说明

### timestamp 参数
- **作用**：仅用于校验，不影响返回的数据范围
- **格式**：
  - `kline_crawler.py`: 整数（毫秒），如 `1733097600000`
  - `sub_kline_crawler.py`: 字符串（毫秒），如 `"1733097600000"`
  - `item_kline_crawler.py`: 整数（毫秒），如 `1733097600000`
  - `item_trend_crawler.py`: 整数（毫秒），如 `1764749386230`
- **默认行为**：如果不提供 `--timestamp` 参数，脚本会自动使用当前时间戳（毫秒）
- **注意**：此参数主要用于 API 校验，不会影响实际返回的数据

### max-time 参数
- **作用**：**真正决定返回数据范围的参数**
- **格式**：整数（秒），如 `1735574400`（对应 2024-12-31 00:00:00）
- **数据范围**：API 每次返回的数据都是 `maxTime` **向前推三个月**的数据
  - 例如：`maxTime=1735574400`（2024-12-31）会返回 2024-10-01 至 2024-12-31 的数据
- **建议**：始终提供此参数以限制数据范围

### type-day 参数（仅用于走势数据）
- **作用**：决定返回走势数据的时间范围
- **可选值**：
  - `1`: 近一月
  - `2`: 三个月
  - `3`: 六个月
  - `4`: 一年
  - `5`: 三年
- **默认值**：`1`（近一月）

---

## 数据表说明

### K线数据表

1. **total_kline_data** - 大盘 K 线数据
   - 存储整个市场的 K 线数据
   - 唯一约束：`(period, timestamp)`

2. **qianzhan_kline_data** - 千百战大盘 K 线数据
   - 存储千百战子市场的 K 线数据
   - 唯一约束：`(period, timestamp)`

3. **agent_kline_data** - 探员大盘 K 线数据
   - 存储探员子市场的 K 线数据
   - 唯一约束：`(period, timestamp)`

4. **kline_data** - 商品 K 线数据
   - 存储具体商品的 K 线数据
   - 关联 `item_statistics` 表
   - 唯一约束：`(item_statistics_id, period, timestamp)`

### 走势数据表

5. **trend_data** - 商品走势数据
   - 存储商品的市场趋势数据（价格、在售数量、求购价、求购数量、存世量、成交量、成交额）
   - 关联 `item_statistics` 表
   - 支持时K、日K、周K三种周期
   - 唯一约束：`(item_statistics_id, period, timestamp)`

---

## 注意事项

1. **唯一约束处理**：所有脚本都实现了智能的唯一约束处理，如果遇到已存在的记录，会自动跳过，只保存不存在的记录。

2. **自动时间戳**：如果不提供 `timestamp` 参数，所有脚本都会自动使用当前时间戳（毫秒），简化使用。

3. **数据范围**：记住 `maxTime` 才是真正决定数据范围的参数，`timestamp` 仅用于校验。

4. **批量爬取**：使用批量爬取脚本时，建议在非高峰时段运行，避免对 API 造成过大压力。

5. **错误处理**：如果某次爬取失败，可以调整参数重新运行，脚本会自动跳过已存在的记录。
