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
from crawler.database.supabase_client import SupabaseManager

supabase = SupabaseManager(
    url="your_supabase_project_url",
    key="your_supabase_anon_key"
)
```

## 快速开始

### 1. 安装依赖

```bash
pip install supabase playwright requests
playwright install chromium
```

### 2. 配置 Supabase

在 `config/config_local.py` 中设置：

```python
SUPABASE_URL = "your_supabase_url"
SUPABASE_KEY = "your_supabase_key"
```

或者使用环境变量：

```bash
export SUPABASE_URL="your_supabase_project_url"
export SUPABASE_KEY="your_supabase_anon_key"
```

### 3. 配置代理（可选，用于 IP 白名单场景）

如果 API 接口需要 IP 白名单验证，可以通过代理服务器使用固定 IP 访问。

#### 方式一：环境变量（推荐）

在 `.env` 文件中设置：

```env
PROXY=http://proxy.example.com:8080
# 或带认证的代理
PROXY=http://username:password@proxy.example.com:8080
```

或者使用命令行：

```bash
export PROXY="http://proxy.example.com:8080"
# 或带认证
export PROXY="http://username:password@proxy.example.com:8080"
```

#### 方式二：在 config_local.py 中配置

```python
# 在 config/config_local.py 中
PROXY = "http://proxy.example.com:8080"
# 或带认证
PROXY = "http://username:password@proxy.example.com:8080"
```

然后在代码中：

```python
from crawler.config.config import Config, CrawlerConfig

crawler_config = CrawlerConfig(proxy="http://proxy.example.com:8080")
config = Config(crawler_config=crawler_config)
```

**注意**：
- 代理格式：`http://host:port` 或 `http://user:pass@host:port`
- 代理会同时用于 HTTP 和 HTTPS 请求
- 如果不需要代理，可以不设置（默认不使用代理）

### 4. 运行爬虫

#### 箱子详情爬虫（推荐）

```bash
# 批量处理所有符合条件的箱子（名字包含"武器箱"或"收藏品"）
python3 -m crawler.examples.container_detail_example

# 处理指定箱子
python3 -m crawler.examples.container_detail_example 1272
```

#### 容器数据爬虫

使用编程方式运行（见下方"编程方式使用"部分）

## 使用方法

### 1. 使用命令行运行示例

```bash
# 运行箱子详情爬虫（批量处理所有符合条件的箱子）
python3 -m crawler.examples.container_detail_example

# 运行指定箱子
python3 -m crawler.examples.container_detail_example 1272
```

### 2. 编程方式使用

```python
from crawler.config.config import Config
from crawler.core.manager import CrawlerManager
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
from crawler.core.browser_crawler import BrowserCrawler
from crawler.config.config import Config

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
from crawler.core.api_crawler import APICrawler
from crawler.config.config import Config

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

更多详细信息请参考：
- `PROJECT_STRUCTURE.md` - 项目结构说明
- `DATABASE_SCHEMA.md` - 数据库架构文档

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

3. **IP 白名单问题**：如果 API 接口需要 IP 白名单验证，请配置代理服务器
   ```bash
   export PROXY="http://your-proxy-server:port"
   ```

4. **数据映射**：每个爬虫需要实现 `transform_data()` 方法，将 API 返回的数据映射到数据库表格式

5. **唯一键**：确保每个爬虫指定正确的 `unique_key`，用于 upsert 操作

6. **错误处理**：爬虫会自动处理错误并记录日志

## 架构优势

- ✅ 统一管理：所有爬虫通过管理器统一管理
- ✅ 代码复用：基础功能在基类中实现
- ✅ 易于扩展：添加新爬虫只需继承基类
- ✅ 灵活配置：支持环境变量和代码配置
- ✅ 统一存储：所有爬虫共享 Supabase 连接
- ✅ 错误处理：统一的错误处理和日志记录


