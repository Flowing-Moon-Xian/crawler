# 统一 Dockerfile (Debian based for Playwright support)
# 包含 API 服务和 Worker 脚本的所有依赖和代码
FROM python:3.9-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1


# 设置时区和安装基础依赖
ENV TZ=Asia/Shanghai
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    libssl-dev \
    tzdata \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 安装 Playwright 浏览器和依赖
RUN playwright install chromium
RUN playwright install-deps chromium

# 复制项目文件
COPY __init__.py ./crawler/
COPY config/ ./crawler/config/
COPY core/ ./crawler/core/
COPY database/ ./crawler/database/
COPY crawlers/ ./crawler/crawlers/
COPY worker/ ./crawler/worker/
COPY api/ ./crawler/api/
COPY utils/ ./crawler/utils/

# 设置 Python 路径
ENV PYTHONPATH=/app:$PYTHONPATH

# 暴露 API 端口
EXPOSE 8000

# 默认启动命令 (守护进程模式)
CMD ["python", "-m", "crawler.worker.run_daily_crawler", "--mode", "daemon"]
