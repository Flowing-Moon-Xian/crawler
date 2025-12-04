# 爬虫模块

用于数据采集和存储到 Supabase 的统一爬虫架构。

## 架构概述

这是一个统一的爬虫架构，支持两种爬虫模式：
- **浏览器爬虫**：使用 Playwright 自动化浏览器拦截 API（适用于 token 动态生成的场景）
- **API 爬虫**：直接调用 API（适用于可以直接获取 token 的场景）

所有爬虫通过 `CrawlerManager` 统一管理，共享 Supabase 连接和配置。

## 目录结构

```
crawler/
├── __init__.py              # 模块导出
├── config.py                # 配置管理
├── base.py                  # 基础爬虫类
├── browser_crawler.py       # 浏览器爬虫基类
├── api_crawler.py           # API 爬虫基类
├── manager.py               # 爬虫管理器
├── supabase_client.py       # Supabase 客户端
├── main.py                  # 主入口
├── crawlers/                # 具体爬虫实现
│   ├── __init__.py
│   └── container_crawler.py # 容器数据爬虫
├── models.py                # 数据模型
├── ARCHITECTURE.md          # 架构设计文档
└── README.md                # 本文件
```

## 安装依赖

```bash
pip install supabase playwright requests
playwright install chromium
```

或者添加到 `requirements.txt`：

```
supabase
playwright
requests
```

## 配置 Supabase

### 方式一：环境变量（推荐）

在 `.env` 文件中设置：

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
```

### 方式二：代码中直接配置

```python
from crawler.supabase_client import SupabaseManager

supabase = SupabaseManager(
    url="your_supabase_project_url",
    key="your_supabase_anon_key"
)
```

## 快速开始

### 1. 配置环境变量

```bash
export SUPABASE_URL="your_supabase_project_url"
export SUPABASE_KEY="your_supabase_anon_key"
```

### 2. 运行爬虫

#### 运行所有爬虫
```bash
python3 -m crawler.main
```

#### 运行指定爬虫
```bash
python3 -m crawler.main --crawler container
```

#### 列出所有爬虫
```bash
python3 -m crawler.main --list
```

#### 查看状态
```bash
python3 -m crawler.main --status
```

## 使用方法

### 1. 使用命令行

```bash
# 运行所有爬虫
python3 -m crawler.main

# 运行指定爬虫
python3 -m crawler.main --crawler container

# 只保存到文件（不保存到数据库）
python3 -m crawler.main --no-db

# 只保存到数据库（不保存到文件）
python3 -m crawler.main --no-file
```

### 2. 编程方式使用

```python
from crawler import Config, CrawlerManager
from crawler.crawlers.container_crawler import ContainerCrawler

# 创建配置（从环境变量加载）
config = Config.from_env()

# 创建管理器
manager = CrawlerManager(config)

# 注册爬虫
manager.register_class(ContainerCrawler, name="container")

# 运行爬虫
result = manager.run_crawler("container")
print(result)
```

### 3. 创建新爬虫

#### 浏览器爬虫示例

```python
from crawler.browser_crawler import BrowserCrawler
from crawler.config import Config

class MyBrowserCrawler(BrowserCrawler):
    def __init__(self, config: Config, name: str = "my_crawler"):
        super().__init__(
            config=config,
            name=name,
            target_table="my_table",
            page_url="https://example.com/page",
            api_pattern="api_endpoint",
            unique_key="id"
        )
    
    def transform_data(self, raw_data):
        # 实现数据转换逻辑
        transformed = []
        for item in raw_data:
            transformed.append({
                'id': item.get('id'),
                'name': item.get('name'),
            })
        return transformed
```

#### API 爬虫示例

```python
from crawler.api_crawler import APICrawler
from crawler.config import Config

class MyAPICrawler(APICrawler):
    def __init__(self, config: Config, name: str = "my_api_crawler"):
        super().__init__(
            config=config,
            name=name,
            target_table="my_table",
            api_url="https://api.example.com/data",
            unique_key="id"
        )
    
    def fetch_data(self):
        # 可以重写以自定义请求
        return super().fetch_data(
            method="POST",
            json_data={"param": "value"},
            authorization="your_token"
        )
    
    def transform_data(self, raw_data):
        # 实现数据转换逻辑
        return raw_data
```

## 详细文档

更多详细信息请参考 [ARCHITECTURE.md](./ARCHITECTURE.md)

## 核心组件

### CrawlerManager

爬虫管理器，统一管理所有爬虫。

- `register(crawler)`: 注册爬虫实例
- `register_class(crawler_class, name, **kwargs)`: 注册爬虫类
- `get_crawler(name)`: 获取爬虫实例
- `run_crawler(name)`: 运行指定爬虫
- `run_all()`: 运行所有爬虫
- `list_crawlers()`: 列出所有爬虫
- `get_status()`: 获取管理器状态

### BaseCrawler

基础爬虫抽象类，所有爬虫的基类。

- `fetch_data()`: 获取数据（子类必须实现）
- `transform_data(raw_data)`: 转换数据格式（子类必须实现）
- `validate_data(data)`: 验证数据
- `save_to_database(data, upsert=True)`: 保存到数据库
- `save_to_file(data, filename=None)`: 保存到文件
- `run()`: 运行爬虫主流程

### BrowserCrawler

浏览器爬虫基类，用于需要浏览器自动化的场景。

- `intercept_api(timeout, wait_after_load)`: 拦截 API 响应

### APICrawler

API 爬虫基类，用于直接调用 API 的场景。

- `fetch_data(method, params, json_data, authorization)`: 获取数据

## 注意事项

1. **Playwright 安装**：浏览器爬虫需要安装 Playwright
   ```bash
   pip install playwright
   playwright install chromium
   ```

2. **环境变量**：必须配置 `SUPABASE_URL` 和 `SUPABASE_KEY` 才能保存到数据库

3. **数据映射**：每个爬虫需要实现 `transform_data()` 方法，将 API 返回的数据映射到数据库表格式

4. **唯一键**：确保每个爬虫指定正确的 `unique_key`，用于 upsert 操作

5. **错误处理**：爬虫会自动处理错误并记录日志

## 架构优势

- ✅ 统一管理：所有爬虫通过管理器统一管理
- ✅ 代码复用：基础功能在基类中实现
- ✅ 易于扩展：添加新爬虫只需继承基类
- ✅ 灵活配置：支持环境变量和代码配置
- ✅ 统一存储：所有爬虫共享 Supabase 连接
- ✅ 错误处理：统一的错误处理和日志记录


