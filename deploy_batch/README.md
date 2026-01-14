# 批量爬虫 Docker 部署

这个目录包含了批量爬虫的 Docker 部署配置，用于在服务器上运行各种批量数据采集任务。

## 📦 包含的脚本

### 1. 大盘商品关系爬虫
用于爬取大盘（千百战、百战、探员等）包含的商品，并自动补全 `item_statistics` 和 `item_statistics_market_index_relations` 表的数据。

**特点：**
- ✅ 自动创建缺失的 `item_statistics` 记录
- ✅ 使用 UPSERT 操作，避免重复数据
- ✅ 支持增量更新和数据修复
- ✅ 幂等性设计，可安全多次运行

## 🚀 快速开始

### 1. 构建并启动容器

```bash
cd /path/to/crawler/deploy_batch
docker-compose up -d
```

### 2. 运行大盘商品关系爬虫

```bash
# 给脚本添加执行权限
chmod +x run_market_index_crawler.sh

# 运行千百战大盘爬虫
./run_market_index_crawler.sh --market-type qianzhan

# 运行百战大盘爬虫
./run_market_index_crawler.sh --market-type baizhan

# 运行探员大盘爬虫
./run_market_index_crawler.sh --market-type agent

# 一次性运行所有大盘类型
./run_market_index_crawler.sh --all
```

### 3. 查看帮助信息

```bash
./run_market_index_crawler.sh --help
```

## 📋 脚本参数说明

### run_market_index_crawler.sh

| 参数 | 说明 | 默认值 | 示例 |
|------|------|--------|------|
| `--market-type` | 大盘类型：qianzhan(千百战), baizhan(百战), agent(探员), sticker(贴纸) | qianzhan | `--market-type baizhan` |
| `--type-val` | 自定义 typeVal（可选） | 使用预定义值 | `--type-val 1234567890` |
| `--batch-size` | 批量插入的批次大小 | 100 | `--batch-size 200` |
| `--all` | 运行所有大盘类型 | false | `--all` |
| `-h, --help` | 显示帮助信息 | - | `--help` |

## 🔧 手动运行命令

如果你想手动进入容器执行命令：

```bash
# 进入容器
docker exec -it cs2-crawler-batch sh

# 运行千百战大盘爬虫
python -m crawler.crawlers.url_crawlers.qianzhan_market_index_crawler --market-type qianzhan

# 运行百战大盘爬虫
python -m crawler.crawlers.url_crawlers.qianzhan_market_index_crawler --market-type baizhan

# 运行探员大盘爬虫
python -m crawler.crawlers.url_crawlers.qianzhan_market_index_crawler --market-type agent

# 自定义批次大小
python -m crawler.crawlers.url_crawlers.qianzhan_market_index_crawler --market-type qianzhan --batch-size 200
```

## 📊 运行结果

脚本运行完成后会显示：
- ✅ 总页数
- ✅ 总商品数
- ✅ 成功插入的关系数
- ✅ 跳过的关系数（已存在）
- ✅ 未找到 item_statistics 的商品数

示例输出：
```
✅ 成功！
总页数: 15
总商品数: 300
成功插入关系: 250
跳过关系（已存在）: 50
未找到 item_statistics 的商品数: 0
```

## 🔍 日志查看

日志文件会保存在宿主机的 `logs/` 目录中：

```bash
# 查看最新日志
tail -f ../logs/qianzhan_market_index.log

# 查看所有日志文件
ls -lh ../logs/
```

## 🛠️ 故障排查

### 容器未运行
```bash
# 检查容器状态
docker ps -a | grep cs2-crawler-batch

# 启动容器
docker-compose up -d

# 查看容器日志
docker logs cs2-crawler-batch
```

### 数据库连接失败
检查 `.env` 文件中的数据库配置：
```bash
# 查看环境变量
docker exec cs2-crawler-batch env | grep SUPABASE
```

### 脚本执行权限问题
```bash
# 添加执行权限
chmod +x run_market_index_crawler.sh
```

## 📝 使用场景

### 1. 增量更新缺失数据
如果你的关联表数据有缺漏（因为 `item_statistics` 中缺少对应数据），运行此脚本可以：
- 自动创建缺失的 `item_statistics` 记录
- 补全关联表数据

### 2. 定期同步大盘商品
定期运行脚本，确保大盘包含的商品列表是最新的。

### 3. 数据修复
如果数据库出现问题，可以重新运行脚本修复数据。

## ⚠️ 注意事项

1. **幂等性**：脚本可以安全地多次运行，不会产生重复数据
2. **item_type 推断**：脚本会根据大盘类型自动推断商品类型：
   - `agent` 大盘 → `ItemType.AGENT`
   - `sticker` 大盘 → `ItemType.STICKER`
   - 其他大盘 → `ItemType.GUN_SKIN`
3. **资源限制**：容器默认限制内存为 1G，可根据需要调整
4. **时区设置**：容器时区已设置为 `Asia/Shanghai`

## 🔄 更新部署

```bash
# 停止容器
docker-compose down

# 重新构建镜像
docker-compose build

# 启动容器
docker-compose up -d
```

## 📦 打包镜像（可选）

如果需要将镜像打包到其他服务器：

```bash
# 构建镜像
docker-compose build

# 保存镜像
docker save cs2-crawler-batch:latest | gzip > cs2-crawler-batch-latest.tar.gz

# 在目标服务器上加载镜像
gunzip -c cs2-crawler-batch-latest.tar.gz | docker load
```
