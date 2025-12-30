# 爬虫脚本使用说明

本文档包含所有爬虫脚本的命令行使用方法，每个脚本的参数说明。

## 目录

- [URL 爬虫](#url-爬虫)
  - [商品 K 线爬虫](#商品-k-线爬虫-item_kline_crawlerpy)
  - [商品走势爬虫](#商品走势爬虫-item_trend_crawlerpy)
  - [大盘 K 线爬虫](#大盘-k-线爬虫-kline_crawlerpy)
  - [子大盘 K 线爬虫](#子大盘-k-线爬虫-sub_kline_crawlerpy)
  - [批量 K 线爬虫](#批量-k-线爬虫-batch_kline_crawlerpy)
  - [千百战大盘商品关系爬虫](#千百战大盘商品关系爬虫-qianzhan_market_index_crawlerpy)
- [数据库更新器](#数据库更新器)
  - [批量爬取大盘商品](#批量爬取大盘商品-batch_crawl_market_itemspy)
  - [商品统计同步](#商品统计同步-item_statistics_syncpy)
  - [更新 SteamDT ID](#更新-steamdt-id-update_steamdt_idpy)
  - [更新磨损度](#更新磨损度-update_wear_conditionpy)
- [JSON 保存器](#json-保存器)
  - [分页列表爬虫](#分页列表爬虫-page_list_crawlerpy)
  - [SteamDT API 爬虫](#steamdt-api-爬虫-steamdt_api_crawlerpy)

---

## URL 爬虫

### 商品 K 线爬虫 (`item_kline_crawler.py`)

爬取指定商品的 K 线数据并保存到 `kline_data` 表。

```bash
python3 -m crawler.crawlers.url_crawlers.item_kline_crawler \
  --kline-type 2 \
  --type-val 24721 \
  --max-time 1764814953
```

**参数说明：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--kline-type` | int | 是 | K 线类型：1=时K, 2=日K, 3=周K |
| `--type-val` | int | 是 | SteamDT 商品/分类 ID（对应 `item_statistics.steamdt_id`） |
| `--timestamp` | int | 否 | 时间戳（毫秒），用于分页。如果不提供，将使用当前时间戳 |
| `--max-time` | int | 否 | 最大时间戳（秒），用于限制数据范围 |
| `--platform` | str | 否 | 平台，默认为 'ALL' |
| `--special-style` | str | 否 | 特殊样式，默认为空字符串 |

**示例：**

```bash
# 爬取日K数据
python3 -m crawler.crawlers.url_crawlers.item_kline_crawler \
  --kline-type 2 \
  --type-val 24721 \
  --max-time 1764814953

# 爬取时K数据，指定时间戳
python3 -m crawler.crawlers.url_crawlers.item_kline_crawler \
  --kline-type 1 \
  --type-val 24721 \
  --timestamp 1735689600000 \
  --max-time 1735776000
```

---

### 商品走势爬虫 (`item_trend_crawler.py`)

爬取指定商品的走势数据并保存到 `trend_data` 表。

```bash
python3 -m crawler.crawlers.url_crawlers.item_trend_crawler \
  --item-id 295893123 \
  --type-day 1 \
  --date-type 3
```

**参数说明：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--item-id` | int | 是 | SteamDT 商品 ID（对应 `item_statistics.steamdt_id`） |
| `--type-day` | int | 否 | 时间范围：1=近一月, 2=三个月, 3=六个月, 4=一年, 5=三年（默认: 1） |
| `--timestamp` | int | 否 | 时间戳（毫秒），用于 API 请求。如果不提供，将使用当前时间戳 |
| `--date-type` | int | 否 | dateType 参数，默认为 3（按接口文档固定） |
| `--platform` | str | 否 | 平台，默认为 'ALL' |
| `--special-style` | str | 否 | 特殊样式，默认为空字符串 |

**示例：**

```bash
# 爬取近一月走势数据
python3 -m crawler.crawlers.url_crawlers.item_trend_crawler \
  --item-id 295893123 \
  --type-day 1 \
  --date-type 3

# 爬取一年走势数据
python3 -m crawler.crawlers.url_crawlers.item_trend_crawler \
  --item-id 295893123 \
  --type-day 4 \
  --date-type 3
```

---

### 大盘 K 线爬虫 (`kline_crawler.py`)

爬取大盘 K 线数据并保存到 `total_kline_data` 表。

```bash
python3 -m crawler.crawlers.url_crawlers.kline_crawler \
  --type 2 \
  --timestamp 1735689600000 \
  --max-time 1735776000
```

**参数说明：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--type` | int | 是 | K 线类型：1=时K, 2=日K, 3=周K |
| `--timestamp` | int | 否 | 时间戳（毫秒），用于分页。如果不提供，将使用当前时间戳 |
| `--max-time` | int | 否 | 最大时间戳（秒），用于限制数据范围 |

**示例：**

```bash
# 爬取大盘日K数据
python3 -m crawler.crawlers.url_crawlers.kline_crawler \
  --type 2 \
  --max-time 1735776000

# 爬取大盘时K数据，指定起始时间戳
python3 -m crawler.crawlers.url_crawlers.kline_crawler \
  --type 1 \
  --timestamp 1735689600000 \
  --max-time 1735776000
```

---

### 子大盘 K 线爬虫 (`sub_kline_crawler.py`)

爬取子大盘（千百战/探员/百战）K 线数据并保存到对应的子大盘表。

```bash
python3 -m crawler.crawlers.url_crawlers.sub_kline_crawler \
  --type HOT \
  --kline-type 2 \
  --type-val 1402501509110038528 \
  --table qianzhan_kline_data \
  --max-time 1735776000
```

**参数说明：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--type` | str | 是 | 类型，如 'HOT' |
| `--kline-type` | int | 是 | K 线类型：1=时K, 2=日K, 3=周K |
| `--type-val` | str | 是 | 类型值，如 '1402501509110038528' |
| `--table` | str | 否 | 目标表名，默认为 'qianzhan_kline_data'，可选: 'qianzhan_kline_data', 'agent_kline_data', 'baizhan_kline_data' |
| `--timestamp` | str | 否 | 时间戳（毫秒字符串），用于分页。如果不提供，将使用当前时间戳 |
| `--max-time` | int | 否 | 最大时间戳（秒），用于限制数据范围 |
| `--platform` | str | 否 | 平台，默认为 'ALL' |
| `--special-style` | str | 否 | 特殊样式，默认为空字符串 |

**示例：**

```bash
# 爬取千百战大盘日K数据
python3 -m crawler.crawlers.url_crawlers.sub_kline_crawler \
  --type HOT \
  --kline-type 2 \
  --type-val 1402501509110038528 \
  --table qianzhan_kline_data \
  --max-time 1735776000

# 爬取探员大盘时K数据
python3 -m crawler.crawlers.url_crawlers.sub_kline_crawler \
  --type HOT \
  --kline-type 1 \
  --type-val 1402501509110038528 \
  --table agent_kline_data \
  --max-time 1735776000

# 爬取百战大盘日K数据
python3 -m crawler.crawlers.url_crawlers.sub_kline_crawler \
  --type HOT \
  --kline-type 2 \
  --type-val 1368024613355786240 \
  --table baizhan_kline_data \
  --max-time 1764747816
```

---

### 批量 K 线爬虫 (`batch_kline_crawler.py`)

批量爬取 K 线数据（自动重复执行，从当前时间到目标时间）。

```bash
python3 -m crawler.crawlers.url_crawlers.batch_kline_crawler \
  --crawler-type sub \
  --kline-type 2 \
  --target-max-time 1735776000 \
  --type HOT \
  --type-val 1402501509110038528 \
  --table qianzhan_kline_data
```

**参数说明：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--crawler-type` | str | 是 | 爬虫类型：total=大盘K线, sub=子大盘K线, item=商品K线 |
| `--kline-type` | int | 是 | K 线类型：1=时K, 2=日K, 3=周K |
| `--target-max-time` | int | 是 | 目标最大时间戳（秒），爬取到此时间为止。例如：1735574400（2024-12-31） |
| `--start-time` | int | 否 | 起始时间戳（秒），如果不提供则使用当前时间 |
| `--type` | str | 否 | 子大盘类型（仅用于 sub 类型），如 'HOT' |
| `--type-val` | str | 否 | 类型值（用于 sub 和 item 类型），子大盘如 '1402501509110038528'，商品为整数 |
| `--table` | str | 否 | 目标表名（仅用于 sub 类型），默认为 'qianzhan_kline_data'，可选: 'qianzhan_kline_data', 'agent_kline_data', 'baizhan_kline_data' |
| `--platform` | str | 否 | 平台，默认为 'ALL' |
| `--special-style` | str | 否 | 特殊样式，默认为空字符串 |

**示例：**

```bash
# 批量爬取大盘日K数据
python3 -m crawler.crawlers.url_crawlers.batch_kline_crawler \
  --crawler-type total \
  --kline-type 2 \
  --target-max-time 1735776000

# 批量爬取千百战大盘时K数据
python3 -m crawler.crawlers.url_crawlers.batch_kline_crawler \
  --crawler-type sub \
  --kline-type 1 \
  --target-max-time 1735776000 \
  --type HOT \
  --type-val 1402501509110038528 \
  --table qianzhan_kline_data

# 批量爬取百战大盘日K数据
python3 -m crawler.crawlers.url_crawlers.batch_kline_crawler \
  --crawler-type sub \
  --kline-type 2 \
  --target-max-time 1764747816 \
  --type HOT \
  --type-val 1368024613355786240 \
  --table baizhan_kline_data

# 批量爬取商品日K数据
python3 -m crawler.crawlers.url_crawlers.batch_kline_crawler \
  --crawler-type item \
  --kline-type 2 \
  --target-max-time 1735776000 \
  --type-val 24721
```

---

### 大盘商品关系爬虫 (`qianzhan_market_index_crawler.py`)

爬取大盘（千百战、百战等）包含的商品，并插入到 `item_statistics_market_index_relations` 表。

```bash
python3 -m crawler.crawlers.url_crawlers.qianzhan_market_index_crawler \
  --market-type qianzhan \
  --batch-size 100
```

**参数说明：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--market-type` | str | 否 | 大盘类型（默认: qianzhan），可选: qianzhan=千百战大盘, baizhan=百战大盘, agent=探员大盘 |
| `--type-val` | str | 否 | 类型值（typeVal），如果不提供则使用预定义的值。千百战: 1402501509110038528, 百战: 1368024613355786240, 探员: 1368076160637956096 |
| `--batch-size` | int | 否 | 批量插入的批次大小（默认: 100） |

**示例：**

```bash
# 爬取千百战大盘商品关系（使用默认值）
python3 -m crawler.crawlers.url_crawlers.qianzhan_market_index_crawler

# 爬取千百战大盘商品关系（显式指定）
python3 -m crawler.crawlers.url_crawlers.qianzhan_market_index_crawler \
  --market-type qianzhan \
  --batch-size 200

# 爬取百战大盘商品关系
python3 -m crawler.crawlers.url_crawlers.qianzhan_market_index_crawler \
  --market-type baizhan \
  --batch-size 100

# 爬取探员大盘商品关系
python3 -m crawler.crawlers.url_crawlers.qianzhan_market_index_crawler \
  --market-type agent \
  --batch-size 100

# 使用自定义 typeVal（适用于其他大盘类型）
python3 -m crawler.crawlers.url_crawlers.qianzhan_market_index_crawler \
  --market-type agent \
  --type-val 1368076160637956096 \
  --batch-size 100
```

---

## 数据库更新器

### 批量爬取大盘商品 (`batch_crawl_market_items.py`)

批量爬取大盘商品的 K 线和走势数据。

```bash
python3 -m crawler.crawlers.db_updaters.batch_crawl_market_items \
  --market-type qianzhan \
  --max-date 2025-12-03 \
  --kline-types 1 2 \
  --type-days 1
```

**参数说明：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--market-type` | str | 否 | 大盘类型（默认: qianzhan），可选: total, qianzhan, agent |
| `--max-date` | str | 否 | 最大日期（格式：YYYY-MM-DD，默认: 2025-12-03） |
| `--max-time` | int | 否 | 最大时间戳（秒），如果不提供则使用 --max-date 计算 |
| `--kline-types` | int[] | 否 | K 线类型列表（默认: 1 2，即时K和日K），可选: 1=时K, 2=日K, 3=周K |
| `--type-days` | int[] | 否 | 走势时间范围列表（默认: 1，即近一月），可选: 1=近一月, 2=三个月, 3=六个月, 4=一年, 5=三年 |
| `--delay` | float | 否 | 每次请求之间的延迟（秒，默认: 1.0） |
| `--limit` | int | 否 | 限制处理的商品数量（用于测试），不指定则处理所有 |

**示例：**

```bash
# 爬取千百战大盘商品的时K和日K数据，以及近一月走势
python3 -m crawler.crawlers.db_updaters.batch_crawl_market_items \
  --market-type qianzhan \
  --max-date 2025-12-03 \
  --kline-types 1 2 \
  --type-days 1

# 爬取探员大盘商品的所有K线类型和多种走势时间范围
python3 -m crawler.crawlers.db_updaters.batch_crawl_market_items \
  --market-type agent \
  --max-date 2025-12-03 \
  --kline-types 1 2 3 \
  --type-days 1 2 3 \
  --delay 2.0

# 测试模式：只处理前10个商品
python3 -m crawler.crawlers.db_updaters.batch_crawl_market_items \
  --market-type qianzhan \
  --limit 10
```

---

### 商品统计同步 (`item_statistics_sync.py`)

同步商品统计信息到数据库。无参数。

```bash
python3 -m crawler.crawlers.db_updaters.item_statistics_sync
```

---

### 更新 SteamDT ID (`update_steamdt_id.py`)

从 JSON 文件更新数据库中的 SteamDT ID。

```bash
python3 -m crawler.crawlers.db_updaters.update_steamdt_id \
  --json-dir data
```

**参数说明：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--json-dir` | str | 否 | JSON 文件目录（默认: data） |

**示例：**

```bash
# 使用默认目录
python3 -m crawler.crawlers.db_updaters.update_steamdt_id

# 指定JSON文件目录
python3 -m crawler.crawlers.db_updaters.update_steamdt_id \
  --json-dir data/custom_dir
```

---

### 更新磨损度 (`update_wear_condition.py`)

从 JSON 文件更新数据库中的磨损度字段。

```bash
python3 -m crawler.crawlers.db_updaters.update_wear_condition \
  --json-dir data/page_list
```

**参数说明：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--json-dir` | str | 否 | JSON 文件目录（默认: data/page_list） |

**示例：**

```bash
# 使用默认目录
python3 -m crawler.crawlers.db_updaters.update_wear_condition

# 指定JSON文件目录
python3 -m crawler.crawlers.db_updaters.update_wear_condition \
  --json-dir data/custom_dir
```

---

## JSON 保存器

### 分页列表爬虫 (`page_list_crawler.py`)

爬取分页列表数据并保存为 JSON 文件。

```bash
python3 -m crawler.crawlers.json_savers.page_list_crawler \
  --page-size 500 \
  --start-page 1 \
  --output-dir data/page_list
```

**参数说明：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--page-size` | int | 否 | 每页大小（默认: 500） |
| `--start-page` | int | 否 | 起始页码（默认: 1） |
| `--output-dir` | str | 否 | 输出目录（默认: data/page_list） |

**示例：**

```bash
# 使用默认参数
python3 -m crawler.crawlers.json_savers.page_list_crawler

# 自定义参数
python3 -m crawler.crawlers.json_savers.page_list_crawler \
  --page-size 1000 \
  --start-page 10 \
  --output-dir data/custom
```

---

### SteamDT API 爬虫 (`steamdt_api_crawler.py`)

爬取 SteamDT API 数据并保存为 JSON 文件。

```bash
python3 -m crawler.crawlers.json_savers.steamdt_api_crawler \
  --output-dir data \
  --url "https://api.steamdt.com/endpoint" \
  --filename custom.json
```

**参数说明：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--output-dir` | str | 否 | 输出目录（默认: data） |
| `--url` | str | 否 | 指定要访问的 URL（GET 请求，如果不指定，则访问所有配置的端点） |
| `--filename` | str | 否 | 指定保存的文件名（仅在使用 --url 或 --inspect-url 时有效） |
| `--inspect-url` | str | 否 | Steam 检查链接（用于调用 wear API，例如: steam://rungame/730/...） |
| `--notify-url` | str | 否 | 回调通知 URL（可选，仅在使用 --inspect-url 时有效） |
| `--api-token` | str | 否 | SteamDT API Token（如果不指定，则使用默认值或环境变量 STEAMDT_API_TOKEN） |

**示例：**

```bash
# 访问所有配置的端点
python3 -m crawler.crawlers.json_savers.steamdt_api_crawler

# 访问指定URL并保存为自定义文件名
python3 -m crawler.crawlers.json_savers.steamdt_api_crawler \
  --url "https://api.steamdt.com/user/item/block/v1/skin-list" \
  --filename skin_list.json

# 调用 wear API
python3 -m crawler.crawlers.json_savers.steamdt_api_crawler \
  --inspect-url "steam://rungame/730/..." \
  --notify-url "https://your-callback-url.com/notify" \
  --filename wear_result.json

# 使用自定义API Token
python3 -m crawler.crawlers.json_savers.steamdt_api_crawler \
  --api-token "your-api-token"
```

---

## 注意事项

1. **时间戳格式**：
   - `--timestamp` 参数使用毫秒（milliseconds）单位
   - `--max-time` 参数使用秒（seconds）单位

2. **K 线类型**：
   - `1` = 时K（hourly）
   - `2` = 日K（daily）
   - `3` = 周K（weekly）

3. **大盘类型**：
   - `total` = 大盘
   - `qianzhan` = 千百战大盘
   - `agent` = 探员大盘
   - `baizhan` = 百战大盘

4. **表名选项**：
   - `qianzhan_kline_data` = 千百战大盘 K 线数据表
   - `agent_kline_data` = 探员大盘 K 线数据表
   - `baizhan_kline_data` = 百战大盘 K 线数据表

5. **环境变量**：
   - 确保已配置 `SUPABASE_URL` 和 `SUPABASE_KEY` 环境变量
   - SteamDT API 爬虫需要 `STEAMDT_API_TOKEN` 环境变量（或通过 `--api-token` 参数指定）

