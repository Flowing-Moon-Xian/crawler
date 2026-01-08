#!/bin/bash

# 内存监控脚本
# 
# 功能：持续监控系统内存和 Swap 使用情况
# 使用：chmod +x monitor_memory.sh && ./monitor_memory.sh &

LOG_FILE="/var/log/memory-monitor.log"

echo "开始内存监控: $(date)" | tee -a $LOG_FILE
echo "监控间隔: 60 秒" | tee -a $LOG_FILE
echo "========================================" | tee -a $LOG_FILE

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    # 获取内存信息
    MEM_USED=$(free -m | awk 'NR==2{printf "%.0f", $3}')
    MEM_TOTAL=$(free -m | awk 'NR==2{printf "%.0f", $2}')
    MEM_PERCENT=$(free -m | awk 'NR==2{printf "%.1f", $3*100/$2}')
    
    # 获取 Swap 信息
    SWAP_USED=$(free -m | awk 'NR==3{printf "%.0f", $3}')
    SWAP_TOTAL=$(free -m | awk 'NR==3{printf "%.0f", $2}')
    
    # 记录日志
    echo "$TIMESTAMP | RAM: ${MEM_USED}/${MEM_TOTAL}MB (${MEM_PERCENT}%) | Swap: ${SWAP_USED}/${SWAP_TOTAL}MB" >> $LOG_FILE
    
    # 内存使用超过 90% 时发出警告
    if (( $(echo "$MEM_PERCENT > 90" | bc -l) )); then
        echo "⚠️  WARNING: Memory usage high: ${MEM_PERCENT}%" | tee -a $LOG_FILE
        
        # 显示占用内存最多的进程
        echo "Top 5 memory-consuming processes:" | tee -a $LOG_FILE
        ps aux --sort=-%mem | head -6 | tee -a $LOG_FILE
    fi
    
    # Swap 使用超过 50% 时发出警告
    if [ $SWAP_TOTAL -gt 0 ]; then
        SWAP_PERCENT=$(echo "scale=1; $SWAP_USED*100/$SWAP_TOTAL" | bc)
        if (( $(echo "$SWAP_PERCENT > 50" | bc -l) )); then
            echo "⚠️  WARNING: Swap usage high: ${SWAP_PERCENT}%" | tee -a $LOG_FILE
        fi
    fi
    
    sleep 60
done
