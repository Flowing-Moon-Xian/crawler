#!/usr/bin/env python3
"""
API 测试脚本

测试所有 API 端点的功能
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"


def test_health():
    """测试健康检查"""
    print("\n=== 测试健康检查 ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    print("✅ 健康检查通过")


def test_kline_fetch():
    """测试获取K线数据"""
    print("\n=== 测试获取K线数据 ===")
    params = {
        "kline_type": 2,
        "type_val": 24721
    }
    response = requests.get(f"{BASE_URL}/api/v1/kline/fetch", params=params)
    print(f"状态码: {response.status_code}")
    data = response.json()
    print(f"成功: {data.get('success')}")
    if data.get('success'):
        print(f"数据条数: {data['data'].get('count')}")
        print("✅ 获取K线数据成功")
    else:
        print(f"错误: {data.get('error')}")


def test_kline_crawl():
    """测试爬取并保存K线数据"""
    print("\n=== 测试爬取并保存K线数据 ===")
    payload = {
        "kline_type": 2,
        "type_val": 24721,
        "max_time": int(time.time())
    }
    response = requests.post(
        f"{BASE_URL}/api/v1/kline/crawl",
        json=payload
    )
    print(f"状态码: {response.status_code}")
    data = response.json()
    print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
    if data.get('success'):
        print("✅ 爬取K线数据成功")
    else:
        print(f"错误: {data.get('error')}")


def test_trend_fetch():
    """测试获取走势数据"""
    print("\n=== 测试获取走势数据 ===")
    params = {
        "item_id": 295893123,
        "type_day": 1
    }
    response = requests.get(f"{BASE_URL}/api/v1/trend/fetch", params=params)
    print(f"状态码: {response.status_code}")
    data = response.json()
    print(f"成功: {data.get('success')}")
    if data.get('success'):
        print(f"数据条数: {data['data'].get('count')}")
        print("✅ 获取走势数据成功")
    else:
        print(f"错误: {data.get('error')}")


def test_trend_crawl():
    """测试爬取并保存走势数据"""
    print("\n=== 测试爬取并保存走势数据 ===")
    payload = {
        "item_id": 295893123,
        "type_day": 1
    }
    response = requests.post(
        f"{BASE_URL}/api/v1/trend/crawl",
        json=payload
    )
    print(f"状态码: {response.status_code}")
    data = response.json()
    print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
    if data.get('success'):
        print("✅ 爬取走势数据成功")
    else:
        print(f"错误: {data.get('error')}")


def main():
    """运行所有测试"""
    print("=" * 60)
    print("CS2 爬虫 API 测试")
    print("=" * 60)
    
    try:
        # 1. 健康检查
        test_health()
        
        # 2. K线数据测试
        test_kline_fetch()
        time.sleep(2)  # 避免请求过快
        
        # test_kline_crawl()  # 注释掉，避免重复写入数据库
        # time.sleep(2)
        
        # 3. 走势数据测试
        test_trend_fetch()
        time.sleep(2)
        
        # test_trend_crawl()  # 注释掉，避免重复写入数据库
        
        print("\n" + "=" * 60)
        print("✅ 所有测试完成！")
        print("=" * 60)
        
    except requests.ConnectionError:
        print("\n❌ 无法连接到 API 服务")
        print("请确保服务已启动: python3 -m uvicorn api.main:app")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
