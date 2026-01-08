# 统一 Dockerfile (Alpine based)
# 包含 API 服务和 Worker 脚本的所有依赖和代码
FROM python:3.9-alpine

WORKDIR /app

# 安装系统依赖
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    tzdata \
    && rm -rf /var/cache/apk/* \
    && cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && echo "Asia/Shanghai" > /etc/timezone

# 设置时区环境变量
ENV TZ=Asia/Shanghai

# 复制依赖文件
COPY requirements.txt .

# 安装所有 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
# 1. 核心模块
COPY __init__.py ./crawler/
COPY config/ ./crawler/config/
COPY core/ ./crawler/core/
COPY database/ ./crawler/database/

# 2. 爬虫模块 (直接复制整个目录)
COPY crawlers/ ./crawler/crawlers/

# 3. Worker 脚本
COPY worker/ ./crawler/worker/

# 4. API 服务
COPY api/ ./crawler/api/

# 设置 Python 路径
ENV PYTHONPATH=/app:$PYTHONPATH

# 暴露 API 端口 (仅在运行 API 时有效)
EXPOSE 8000

# 默认启动命令 (Worker)
CMD ["python", "-m", "crawler.worker.universal_incremental_update"]
