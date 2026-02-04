"""
CS2 爬虫 REST API 服务

FastAPI 应用主文件
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent

from crawler.api import __version__
from crawler.api.routes import kline, trend
from crawler.api.models import HealthResponse

# 创建 FastAPI 应用
app = FastAPI(
    title="CS2 爬虫 API",
    description="提供 K线数据和走势数据的 REST API 接口",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(kline.router)
app.include_router(trend.router)


@app.get("/", summary="API 根路径")
async def root():
    """API 根路径，返回基本信息"""
    return {
        "name": "CS2 爬虫 API",
        "version": __version__,
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse, summary="健康检查")
async def health_check():
    """
    服务健康检查
    
    返回服务状态和版本信息
    """
    return HealthResponse(
        status="healthy",
        version=__version__,
        timestamp=datetime.now().isoformat()
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "服务器内部错误",
                "details": str(exc)
            }
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # 开发模式
        log_level="info"
    )
