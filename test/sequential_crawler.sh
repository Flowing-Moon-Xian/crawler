#!/bin/bash

# 顺序爬取脚本 - 适用于低内存环境（2GB RAM）
# 
# 功能：按顺序执行所有爬虫任务，避免内存溢出
# 使用：chmod +x sequential_crawler.sh && ./sequential_crawler.sh

LOG_DIR="/var/log/crawler"
mkdir -p $LOG_DIR

echo "========================================" | tee -a $LOG_DIR/sequential.log
echo "开始顺序爬取任务: $(date)" | tee -a $LOG_DIR/sequential.log
echo "系统内存: $(free -h | awk 'NR==2{print $2}')" | tee -a $LOG_DIR/sequential.log
echo "========================================" | tee -a $LOG_DIR/sequential.log

# 切换到项目目录
cd "$(dirname "$0")/../.." || exit 1

# 1. 增量更新所有商品（日K + 走势）
echo "[1/4] 增量更新所有商品..." | tee -a $LOG_DIR/sequential.log
python3 -m crawler.worker.universal_incremental_update >> $LOG_DIR/daily-update.log 2>&1
EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ 增量更新完成" | tee -a $LOG_DIR/sequential.log
else
    echo "❌ 增量更新失败 (退出码: $EXIT_CODE)" | tee -a $LOG_DIR/sequential.log
fi

# 等待 30 秒，让系统释放内存
echo "等待 30 秒释放内存..." | tee -a $LOG_DIR/sequential.log
sleep 30

# 2. 大盘K线
echo "[2/4] 爬取大盘K线..." | tee -a $LOG_DIR/sequential.log
MAX_TIME=$(date +%s)
python3 -m crawler.crawlers.url_crawlers.kline_crawler \
    --type 2 \
    --max-time $MAX_TIME >> $LOG_DIR/market-kline.log 2>&1
EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ 大盘K线完成" | tee -a $LOG_DIR/sequential.log
else
    echo "❌ 大盘K线失败 (退出码: $EXIT_CODE)" | tee -a $LOG_DIR/sequential.log
fi

sleep 30

# 3. 子大盘K线（千百战）
echo "[3/4] 爬取子大盘K线（千百战）..." | tee -a $LOG_DIR/sequential.log
python3 -m crawler.crawlers.url_crawlers.sub_kline_crawler \
    --type HOT \
    --kline-type 2 \
    --type-val 1402501509110038528 \
    --table qianzhan_kline_data \
    --max-time $MAX_TIME >> $LOG_DIR/sub-kline.log 2>&1
EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ 子大盘K线完成" | tee -a $LOG_DIR/sequential.log
else
    echo "❌ 子大盘K线失败 (退出码: $EXIT_CODE)" | tee -a $LOG_DIR/sequential.log
fi

sleep 30

# 4. 每周更新大盘商品关系（仅周日执行）
if [ $(date +%u) -eq 7 ]; then
    echo "[4/4] 更新大盘商品关系（周日任务）..." | tee -a $LOG_DIR/sequential.log
    python3 -m crawler.crawlers.url_crawlers.qianzhan_market_index_crawler >> $LOG_DIR/relations.log 2>&1
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 0 ]; then
        echo "✅ 大盘关系更新完成" | tee -a $LOG_DIR/sequential.log
    else
        echo "❌ 大盘关系更新失败 (退出码: $EXIT_CODE)" | tee -a $LOG_DIR/sequential.log
    fi
else
    echo "[4/4] 跳过大盘关系更新（非周日）" | tee -a $LOG_DIR/sequential.log
fi

# 显示最终内存使用情况
echo "========================================" | tee -a $LOG_DIR/sequential.log
echo "顺序爬取任务完成: $(date)" | tee -a $LOG_DIR/sequential.log
echo "最终内存使用:" | tee -a $LOG_DIR/sequential.log
free -h | tee -a $LOG_DIR/sequential.log
echo "========================================" | tee -a $LOG_DIR/sequential.log
