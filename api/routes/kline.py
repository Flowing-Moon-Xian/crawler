"""
K线数据相关路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from crawler.api.models import (
    KlineCrawlRequest,
    KlineCrawlResponse,
    KlineFetchResponse,
    ErrorResponse
)
from crawler.api.dependencies import get_kline_crawler
from crawler.crawlers.url_crawlers.item_kline_crawler import ItemKlineCrawler

router = APIRouter(prefix="/api/v1/kline", tags=["K线数据"])


@router.post("/crawl", response_model=KlineCrawlResponse, summary="爬取并保存K线数据")
async def crawl_kline(
    request: KlineCrawlRequest,
    crawler: ItemKlineCrawler = Depends(get_kline_crawler)
):
    """
    爬取K线数据并保存到数据库
    
    - **kline_type**: K线类型 (1=时K, 2=日K, 3=周K)
    - **type_val**: SteamDT 商品ID
    - **timestamp**: 可选，时间戳（毫秒）
    - **max_time**: 可选，最大时间戳（秒）
    - **platform**: 可选，平台（默认 "ALL"）
    - **special_style**: 可选，特殊样式（默认空）
    """
    try:
        records_saved = crawler.crawl_and_save(
            kline_type=request.kline_type,
            type_val=request.type_val,
            timestamp=request.timestamp,
            max_time=request.max_time,
            platform=request.platform,
            special_style=request.special_style,
            start_time=request.start_time,
            end_time=request.end_time,
        )
        
        if records_saved == 0:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "ITEM_NOT_FOUND",
                    "message": f"商品 ID {request.type_val} 不存在或无数据",
                    "details": f"steamdt_id={request.type_val} 未找到对应记录"
                }
            )
        
        # 获取 item_statistics_id
        item_statistics_id = crawler._get_item_statistics_id_by_steamdt(request.type_val)
        
        return KlineCrawlResponse(
            success=True,
            message=f"成功保存 {records_saved} 条K线数据",
            data={
                "item_statistics_id": item_statistics_id,
                "records_saved": records_saved,
                "kline_type": request.kline_type
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "CRAWL_ERROR",
                "message": "爬取K线数据失败",
                "details": str(e)
            }
        )


@router.get("/fetch", response_model=KlineFetchResponse, summary="获取K线数据（不保存）")
async def fetch_kline(
    kline_type: int = Query(..., description="K线类型: 1=时K, 2=日K, 3=周K", ge=1, le=3),
    type_val: int = Query(..., description="SteamDT 商品ID"),
    timestamp: Optional[int] = Query(None, description="时间戳（毫秒）"),
    max_time: Optional[int] = Query(None, description="最大时间戳（秒）"),
    platform: str = Query("ALL", description="平台"),
    special_style: str = Query("", description="特殊样式"),
    crawler: ItemKlineCrawler = Depends(get_kline_crawler)
):
    """
    仅获取K线数据，不保存到数据库
    
    返回原始的K线数据数组
    """
    try:
        kline_data = crawler.fetch_kline_data(
            kline_type=kline_type,
            type_val=type_val,
            timestamp=timestamp,
            max_time=max_time,
            platform=platform,
            special_style=special_style
        )
        
        if not kline_data:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "NO_DATA",
                    "message": "未获取到K线数据",
                    "details": f"kline_type={kline_type}, type_val={type_val}"
                }
            )
        
        return KlineFetchResponse(
            success=True,
            data={
                "kline_data": kline_data,
                "count": len(kline_data),
                "kline_type": kline_type,
                "type_val": type_val
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "FETCH_ERROR",
                "message": "获取K线数据失败",
                "details": str(e)
            }
        )
