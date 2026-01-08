# Docker 部署说明

## 🐳 极致省内存方案 (单容器)

仅需一个 docker-compose.yml 文件，包含 API 和 Worker 环境。

## ⚙️ 配置说明

您有两种方式配置 Supabase：

### 方式 A：直接编辑 (最简单)
修改 `deploy/docker-compose.yml` 文件：
```yaml
environment:
  - SUPABASE_URL=您的真实URL
  - SUPABASE_KEY=您的真实KEY
```

### 方式 B：使用 .env 文件 (更安全)
在 `deploy` 目录下创建 `.env` 文件：
```bash
SUPABASE_URL=https://xyz.supabase.co
SUPABASE_KEY=eyJ...
```

## 🚀 常用命令

### 1. 启动服务 (与之前相同)
```bash
cd deploy
docker-compose up -d
```

### 2. 手动运行 Worker
```bash
docker exec -it cs2-crawler python -m crawler.worker.universal_incremental_update
```
