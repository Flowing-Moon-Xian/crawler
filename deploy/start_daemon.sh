#!/bin/bash
# 在容器内启动守护进程爬虫的便捷脚本

set -e

CONTAINER_NAME="cs2-crawler"
LOG_FILE="/app/logs/daily_crawler.log"

echo "=================================================="
echo "启动 CS2 Crawler 守护进程"
echo "=================================================="

# 检查容器是否运行
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "❌ 容器 $CONTAINER_NAME 未运行"
    echo "请先启动容器: docker-compose up -d"
    exit 1
fi

echo "✅ 容器 $CONTAINER_NAME 正在运行"

# 创建日志目录（如果不存在）
echo "📁 确保日志目录存在..."
docker exec "$CONTAINER_NAME" mkdir -p /app/logs

# 检查是否已有守护进程在运行
if docker exec "$CONTAINER_NAME" pgrep -f "run_daily_crawler.*daemon" > /dev/null 2>&1; then
    echo "⚠️  守护进程已在运行"
    echo ""
    echo "当前进程："
    docker exec "$CONTAINER_NAME" ps aux | grep "run_daily_crawler" | grep -v grep
    echo ""
    read -p "是否要重启守护进程？(y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "取消操作"
        exit 0
    fi
    
    echo "🛑 停止现有守护进程..."
    docker exec "$CONTAINER_NAME" pkill -f "run_daily_crawler.*daemon" || true
    sleep 2
fi

# 启动守护进程
echo "🚀 启动守护进程..."
docker exec -d "$CONTAINER_NAME" sh -c "nohup python -m crawler.worker.run_daily_crawler --mode daemon > $LOG_FILE 2>&1 &"

# 等待进程启动
sleep 2

# 验证进程是否启动
if docker exec "$CONTAINER_NAME" pgrep -f "run_daily_crawler.*daemon" > /dev/null 2>&1; then
    echo "✅ 守护进程启动成功！"
    echo ""
    echo "进程信息："
    docker exec "$CONTAINER_NAME" ps aux | grep "run_daily_crawler" | grep -v grep
    echo ""
    echo "📋 日志位置："
    echo "  容器内: $LOG_FILE"
    echo "  宿主机: $(pwd)/logs/daily_crawler.log"
    echo ""
    echo "查看日志："
    echo "  tail -f $(pwd)/logs/daily_crawler.log"
else
    echo "❌ 守护进程启动失败"
    echo "请检查日志: $(pwd)/logs/daily_crawler.log"
    exit 1
fi

echo "=================================================="
