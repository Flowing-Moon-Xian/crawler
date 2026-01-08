"""
走势数据相关路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from crawler.api.models import (
    TrendCrawlRequest,
    TrendCrawlResponse,
    TrendFetchResponse,
    ErrorResponse
)
from crawler.api.dependencies import get_trend_crawler
from crawler.crawlers.url_crawlers.item_trend_crawler import ItemTrendCrawler

router = APIRouter(prefix="/api/v1/trend", tags=["走势数据"])


@router.post("/crawl", response_model=TrendCrawlResponse, summary="爬取并保存走势数据")
async def crawl_trend(
    request: TrendCrawlRequest,
    crawler: ItemTrendCrawler = Depends(get_trend_crawler)
):
    """
    爬取走势数据并保存到数据库
    
    - **item_id**: SteamDT 商品ID
    - **type_day**: 时间范围 (1=近一月, 2=三个月, 3=六个月, 4=一年, 5=三年)
    - **timestamp**: 可选，时间戳（毫秒）
    - **date_type**: 可选，日期类型（默认 3）
    - **platform**: 可选，平台（默认 "ALL"）
    - **special_style**: 可选，特殊样式（默认空）
    """
    try:
        records_saved = crawler.crawl_and_save(
            item_id=request.item_id,
            type_day=request.type_day,
            timestamp=request.timestamp,
            date_type=request.date_type,
            platform=request.platform,
            special_style=request.special_style,
            incremental=True,
            start_time=request.start_time,
            end_time=request.end_time,
        )
        
        if records_saved == 0:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "ITEM_NOT_FOUND",
                    "message": f"商品 ID {request.item_id} 不存在或无数据",
                    "details": f"steamdt_id={request.item_id} 未找到对应记录"
                }
            )
        
        # 获取 item_statistics_id
        item_statistics_id = crawler._get_item_statistics_id_by_steamdt(request.item_id)
        
        return TrendCrawlResponse(
            success=True,
            message=f"成功保存 {records_saved} 条走势数据",
            data={
                "item_statistics_id": item_statistics_id,
                "records_saved": records_saved,
                "type_day": request.type_day
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "CRAWL_ERROR",
                "message": "爬取走势数据失败",
                "details": str(e)
            }
        )


@router.get("/fetch", response_model=TrendFetchResponse, summary="获取走势数据（不保存）")
async def fetch_trend(
    item_id: int = Query(..., description="SteamDT 商品ID"),
    type_day: int = Query(1, description="时间范围: 1=近一月, 2=三个月, 3=六个月, 4=一年, 5=三年", ge=1, le=5),
    timestamp: Optional[int] = Query(None, description="时间戳（毫秒）"),
    date_type: int = Query(3, description="日期类型"),
    platform: str = Query("ALL", description="平台"),
    special_style: str = Query("", description="特殊样式"),
    crawler: ItemTrendCrawler = Depends(get_trend_crawler)
):
    """
    仅获取走势数据，不保存到数据库
    
    返回原始的走势数据数组
    """
    try:
        trend_data = crawler.fetch_trend_data(
            item_id=item_id,
            type_day=type_day,
            timestamp=timestamp,
            date_type=date_type,
            platform=platform,
            special_style=special_style
        )
        
        if not trend_data:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "NO_DATA",
                    "message": "未获取到走势数据",
                    "details": f"item_id={item_id}, type_day={type_day}"
                }
            )
        
        return TrendFetchResponse(
            success=True,
            data={
                "trend_data": trend_data,
                "count": len(trend_data),
                "type_day": type_day,
                "item_id": item_id
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "FETCH_ERROR",
                "message": "获取走势数据失败",
                "details": str(e)
            }
        )
