"""
Pydantic 模型定义

请求和响应的数据模型
"""
from typing import Optional, List, Any
from pydantic import BaseModel, Field
from datetime import datetime


# ============= K线相关模型 =============

class KlineCrawlRequest(BaseModel):
    """K线爬取请求"""
    kline_type: int = Field(..., description="K线类型: 1=时K, 2=日K, 3=周K", ge=1, le=3)
    type_val: int = Field(..., description="SteamDT 商品ID")
    timestamp: Optional[int] = Field(None, description="时间戳（毫秒）")
    max_time: Optional[int] = Field(None, description="最大时间戳（秒）")
    platform: str = Field("ALL", description="平台")
    special_style: str = Field("", description="特殊样式")
    start_time: Optional[datetime] = Field(None, description="开始时间，只保存 >= 此时间的数据")
    end_time: Optional[datetime] = Field(None, description="结束时间，只保存 <= 此时间的数据")

    class Config:
        json_schema_extra = {
            "example": {
                "kline_type": 2,
                "type_val": 24721,
                "max_time": 1735776000
            }
        }


class KlineFetchRequest(BaseModel):
    """K线获取请求（查询参数）"""
    kline_type: int = Field(..., description="K线类型: 1=时K, 2=日K, 3=周K", ge=1, le=3)
    type_val: int = Field(..., description="SteamDT 商品ID")
    timestamp: Optional[int] = Field(None, description="时间戳（毫秒）")
    max_time: Optional[int] = Field(None, description="最大时间戳（秒）")
    platform: str = Field("ALL", description="平台")
    special_style: str = Field("", description="特殊样式")


class KlineCrawlResponse(BaseModel):
    """K线爬取响应"""
    success: bool
    message: str
    data: Optional[dict] = None


class KlineFetchResponse(BaseModel):
    """K线获取响应"""
    success: bool
    data: Optional[dict] = None


# ============= 走势相关模型 =============

class TrendCrawlRequest(BaseModel):
    """走势爬取请求"""
    item_id: int = Field(..., description="SteamDT 商品ID")
    type_day: int = Field(1, description="时间范围: 1=近一月, 2=三个月, 3=六个月, 4=一年, 5=三年", ge=1, le=5)
    timestamp: Optional[int] = Field(None, description="时间戳（毫秒）")
    date_type: int = Field(3, description="日期类型")
    platform: str = Field("ALL", description="平台")
    special_style: str = Field("", description="特殊样式")
    start_time: Optional[datetime] = Field(None, description="开始时间，只保存 >= 此时间的数据")
    end_time: Optional[datetime] = Field(None, description="结束时间，只保存 <= 此时间的数据")

    class Config:
        json_schema_extra = {
            "example": {
                "item_id": 295893123,
                "type_day": 1
            }
        }


class TrendFetchRequest(BaseModel):
    """走势获取请求（查询参数）"""
    item_id: int = Field(..., description="SteamDT 商品ID")
    type_day: int = Field(1, description="时间范围: 1=近一月, 2=三个月, 3=六个月, 4=一年, 5=三年", ge=1, le=5)
    timestamp: Optional[int] = Field(None, description="时间戳（毫秒）")
    date_type: int = Field(3, description="日期类型")
    platform: str = Field("ALL", description="平台")
    special_style: str = Field("", description="特殊样式")


class TrendCrawlResponse(BaseModel):
    """走势爬取响应"""
    success: bool
    message: str
    data: Optional[dict] = None


class TrendFetchResponse(BaseModel):
    """走势获取响应"""
    success: bool
    data: Optional[dict] = None


# ============= 通用模型 =============

class ErrorResponse(BaseModel):
    """错误响应"""
    success: bool = False
    error: dict

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": {
                    "code": "ITEM_NOT_FOUND",
                    "message": "商品 ID 不存在",
                    "details": "steamdt_id=12345 未找到对应的 item_statistics 记录"
                }
            }
        }


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    version: str
    timestamp: str
