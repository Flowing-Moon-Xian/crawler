# Worker Scripts

## 通用增量更新 Worker

### universal_incremental_update.py

对 `item_statistics_market_index_relations` 表中的所有商品进行增量更新，不区分市场类型。

**功能特点：**
- ✅ 处理所有在 `item_statistics_market_index_relations` 表中的商品
- ✅ 不区分市场类型（total/qianzhan/agent/baizhan）
- ✅ 智能增量更新（只拉取缺失或过时的数据）
- ✅ 默认爬取日K和近一月走势数据
- ✅ **低内存优化**：分批处理 + 垃圾回收（适合 2GB 内存环境）

**使用方法：**

```bash
# 直接运行
python3 -m crawler.worker.universal_incremental_update

# 或者使用 Python 路径
cd /Users/shenyanlu/Documents/量化/cs2
python3 crawler/worker/universal_incremental_update.py
```

**增量更新逻辑：**

1. **K线数据（日K）**：
   - 查询 `kline_data` 表的最后时间戳
   - 如果超过 1 天则更新
   - 只拉取新数据

2. **走势数据（近一月）**：
   - 查询 `trend_data` 表的最后时间戳
   - 如果超过 1 天则更新
   - 只拉取新数据

**配置说明：**

默认配置（低内存优化）：
- `market_index_type`: `None` (处理所有商品)
- `kline_types`: `[2]` (只爬取日K)
- `type_days`: `[1]` (只爬取近一月)
- `delay`: `2.0` (每次请求间隔2秒，降低内存压力)
- `batch_size`: `20` (批量大小20，降低内存占用)
- `items_per_batch`: `10` (每批处理10个商品，定期垃圾回收)

> 💡 **低内存环境优化**：脚本会自动分批处理商品，每批10个，批次间进行垃圾回收和5秒等待，确保在 2GB 内存环境下稳定运行。

**部署建议：**

1. **使用 cron 定时执行**：
```bash
# 每天凌晨1点执行
0 1 * * * cd /path/to/cs2 && python3 -m crawler.worker.universal_incremental_update >> /var/log/universal-update.log 2>&1
```

2. **手动执行**：
```bash
python3 -m crawler.worker.universal_incremental_update
```

**与其他 Worker 的区别：**

- `run_daily_crawler.py`: 提供多种示例模式（一次性、守护进程、市场特定）
- `universal_incremental_update.py`: 专注于通用增量更新，简单直接

**日志输出示例：**

```
============================================================
通用增量更新 Worker
对所有 item_statistics_market_index_relations 表中的商品进行增量更新
============================================================
2025-12-31 16:14:15,306 - DailyKlineTrendScheduler - INFO - 开始执行每日 K 线和趋势数据爬取任务
2025-12-31 16:14:15,306 - DailyKlineTrendScheduler - INFO - 大盘类型: 所有商品
2025-12-31 16:14:15,306 - DailyKlineTrendScheduler - INFO - K 线类型: [2]
2025-12-31 16:14:15,306 - DailyKlineTrendScheduler - INFO - 走势时间范围: [1]
...
✅ 增量更新完成！
```
