"""
测试API返回的JSON数据
查看箱子详情API的实际返回内容
"""
import json
import requests

def test_api():
    """测试箱子详情API"""
    api_url = "https://api.csqaq.com/api/v1/info/good/container_detail"
    token = "AQPI91A7P5Z9J0U4O3P3N6T8"
    box_qaq_id = 1  # 命悬一线武器箱的qaq_id
    
    headers = {
        "ApiToken": token,
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "application/json",
    }
    
    params = {"id": box_qaq_id}
    
    print(f"正在请求: {api_url}")
    print(f"参数: {params}")
    print(f"Headers: {headers}\n")
    
    try:
        response = requests.get(api_url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        print("=" * 80)
        print("API返回的完整JSON:")
        print("=" * 80)
        print(json.dumps(data, ensure_ascii=False, indent=2))
        print("\n" + "=" * 80)
        
        # 检查数据结构
        if isinstance(data, dict):
            code = data.get("code")
            msg = data.get("msg")
            items = data.get("data", [])
            
            print(f"\n状态码: {code}")
            print(f"消息: {msg}")
            print(f"数据项数量: {len(items)}\n")
            
            # 检查是否有问题数据
            print("检查数据项:")
            for i, item in enumerate(items):
                print(f"\n--- 项目 {i+1} ---")
                print(f"id (qaq_id): {item.get('id')}")
                print(f"short_name: {item.get('short_name')}")
                print(f"rln (稀有度): {item.get('rln')}")
                print(f"完整数据: {json.dumps(item, ensure_ascii=False, indent=2)}")
                
                # 检查是否是箱子本身
                short_name = item.get('short_name', '')
                if '武器箱' in short_name or '收藏品' in short_name:
                    print("⚠️  警告: 这个项目看起来是箱子本身，不是箱子内的物品！")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api()


