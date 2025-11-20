# 项目结构说明

## 目录结构

```
crawler/
├── __init__.py              # 模块导出（统一导出主要类和函数）
│
├── core/                    # 核心模块
│   ├── __init__.py          # 导出核心类
│   ├── base.py              # 基础爬虫抽象类
│   ├── api_crawler.py       # API 爬虫基类
│   ├── browser_crawler.py   # 浏览器爬虫基类
│   └── manager.py           # 爬虫管理器
│
├── config/                  # 配置模块
│   ├── __init__.py          # 导出配置类
│   ├── config.py            # 配置管理（SupabaseConfig, CrawlerConfig, CSQAQConfig, Config）
│   └── config_local.py      # 本地配置（不纳入版本控制，包含 Supabase URL 和 Key）
│
├── database/                # 数据库模块
│   ├── __init__.py          # 导出数据库相关类
│   ├── supabase_client.py   # Supabase 客户端管理器
│   ├── models.py            # 数据模型（Box, GunSkin, KnifeGlove 等）
│   ├── supabase_schema.sql  # 数据库架构 SQL
│   └── supabase_rls_policies.sql  # RLS 策略 SQL
│
├── crawlers/                # 具体爬虫实现
│   ├── __init__.py
│   ├── container_crawler.py         # 容器数据爬虫（浏览器爬虫）
│   └── container_detail_crawler.py  # 箱子详情爬虫（API 爬虫）
│
├── examples/                # 示例代码
│   ├── database_example.py          # 数据库使用示例
│   └── container_detail_example.py  # 箱子详情爬虫使用示例
│
├── docs/                    # 文档
│   ├── README.md            # 使用文档
│   └── DATABASE_SCHEMA.md   # 数据库架构文档
│
└── README.md                # 项目总览
```

## 模块说明

### core/ - 核心模块
- **base.py**: 所有爬虫的抽象基类，定义了统一的接口
- **api_crawler.py**: API 爬虫基类，用于直接调用 API
- **browser_crawler.py**: 浏览器爬虫基类，用于需要浏览器自动化的场景
- **manager.py**: 爬虫管理器，统一管理所有爬虫的注册和运行

### config/ - 配置模块
- **config.py**: 配置管理类，支持从环境变量或 config_local 加载配置
- **config_local.py**: 本地配置文件（不纳入版本控制），包含 Supabase 凭证

### database/ - 数据库模块
- **supabase_client.py**: Supabase 客户端封装
- **models.py**: 数据模型定义（Pydantic/dataclass）
- **supabase_schema.sql**: 数据库表结构定义
- **supabase_rls_policies.sql**: Row Level Security 策略

### crawlers/ - 具体爬虫实现
- **container_crawler.py**: 爬取容器列表（使用浏览器自动化）
- **container_detail_crawler.py**: 爬取箱子详情（使用 API）

### examples/ - 示例代码
- **database_example.py**: 演示如何使用数据库模型和客户端
- **container_detail_example.py**: 演示如何使用箱子详情爬虫

## 导入路径

### 推荐导入方式

```python
# 配置
from crawler.config.config import Config

# 核心类
from crawler.core.base import BaseCrawler
from crawler.core.api_crawler import APICrawler
from crawler.core.browser_crawler import BrowserCrawler
from crawler.core.manager import CrawlerManager

# 数据库
from crawler.database.supabase_client import SupabaseManager
from crawler.database.models import Box, GunSkin, KnifeGlove

# 具体爬虫
from crawler.crawlers.container_crawler import ContainerCrawler
from crawler.crawlers.container_detail_crawler import ContainerDetailCrawler
```

### 简化导入（通过 __init__.py）

```python
# 从主模块导入（推荐）
from crawler import Config, CrawlerManager, BaseCrawler, SupabaseManager
```

## 文件组织原则

1. **按功能分类**：相关功能的文件放在同一文件夹
2. **清晰的层次**：核心 → 配置 → 数据库 → 具体实现
3. **易于扩展**：新爬虫只需在 `crawlers/` 中添加
4. **文档分离**：文档放在 `docs/` 文件夹
5. **示例独立**：示例代码放在 `examples/` 文件夹

## 添加新文件指南

- **新爬虫**：放在 `crawlers/` 文件夹
- **新配置**：放在 `config/` 文件夹
- **新数据模型**：放在 `database/models.py` 或创建新文件
- **新示例**：放在 `examples/` 文件夹
- **新文档**：放在 `docs/` 文件夹

