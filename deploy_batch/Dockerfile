# Batch Crawler Dockerfile (Alpine based)
# 专门用于批量爬虫脚本的镜像
FROM python:3.9-alpine

WORKDIR /app

# 安装系统依赖
# gcc, musl-dev, libffi-dev, openssl-dev: 编译 Python依赖包需要
# tzdata: 时区设置
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

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
# 这是一个专门的构建，我们只需要爬虫运行所需的模块
# 注意：上下文应该是项目根目录 crawler/

# 1. 核心与配置
COPY __init__.py ./crawler/
COPY config/ ./crawler/config/
COPY core/ ./crawler/core/
COPY database/ ./crawler/database/

# 2. 爬虫模块
COPY crawlers/ ./crawler/crawlers/

# 设置 Python 路径，确保可以找到 crawler 包
ENV PYTHONPATH=/app:$PYTHONPATH

# 默认命令：保持容器运行，方便进入执行命令
# 使用 tail -f /dev/null 让容器一直挂起
CMD ["tail", "-f", "/dev/null"]
