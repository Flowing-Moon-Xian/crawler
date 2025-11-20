# 爬虫模块

用于数据采集和存储到 Supabase 的统一爬虫架构。

## 项目结构

```
crawler/
├── __init__.py              # 模块导出
├── core/                    # 核心模块
│   ├── __init__.py
│   ├── base.py              # 基础爬虫类
│   ├── api_crawler.py       # API 爬虫基类
│   ├── browser_crawler.py   # 浏览器爬虫基类
│   └── manager.py           # 爬虫管理器
├── config/                  # 配置模块
│   ├── __init__.py
│   ├── config.py            # 配置管理
│   └── config_local.py      # 本地配置（不纳入版本控制）
├── database/                # 数据库模块
│   ├── __init__.py
│   ├── supabase_client.py   # Supabase 客户端
│   ├── models.py            # 数据模型
│   ├── supabase_schema.sql  # 数据库架构
│   └── supabase_rls_policies.sql  # RLS 策略
├── crawlers/                # 具体爬虫实现
│   ├── __init__.py
│   ├── container_crawler.py         # 容器数据爬虫
│   └── container_detail_crawler.py  # 箱子详情爬虫
├── examples/                # 示例代码
│   ├── database_example.py          # 数据库使用示例
│   └── container_detail_example.py  # 箱子详情爬虫示例
└── docs/                    # 文档
    ├── README.md            # 使用文档
    └── DATABASE_SCHEMA.md   # 数据库架构文档
```

## 快速开始

### 1. 安装依赖

```bash
pip install supabase playwright requests
playwright install chromium
```

### 2. 配置 Supabase

在 `config/config_local.py` 中设置 Supabase 配置：

```python
SUPABASE_URL = "your_supabase_url"
SUPABASE_KEY = "your_supabase_key"
```

### 3. 运行爬虫

#### 箱子详情爬虫

```bash
# 批量处理所有符合条件的箱子（名字包含"武器箱"或"收藏品"）
python3 -m crawler.examples.container_detail_example

# 处理指定箱子
python3 -m crawler.examples.container_detail_example 1272
```

#### 容器数据爬虫

```bash
# 使用编程方式运行
python3 -c "
from crawler.config.config import Config
from crawler.core.manager import CrawlerManager
from crawler.crawlers.container_crawler import ContainerCrawler

config = Config.from_env()
manager = CrawlerManager(config)
manager.register_class(ContainerCrawler, name='container')
result = manager.run_crawler('container')
print(result)
"
```

## 使用方式

### 编程方式使用

```python
from crawler.config.config import Config
from crawler.crawlers.container_detail_crawler import ContainerDetailCrawler

# 创建配置
config = Config.from_env()

# 创建爬虫
crawler = ContainerDetailCrawler(config, name="container_detail")

# 运行爬虫（处理指定箱子）
result = crawler.run(box_qaq_id=1272)
print(result)

# 或者批量处理所有符合条件的箱子
boxes = crawler.get_filtered_boxes()
for box in boxes:
    result = crawler.run(box["qaq_id"])
    print(result)
```

## 详细文档

更多信息请参考：
- `docs/README.md` - 详细使用文档
- `PROJECT_STRUCTURE.md` - 项目结构说明

