"""
测试代理配置和 IP 地址
用于验证代理是否正常工作，以及当前使用的 IP 地址
"""
import sys
import requests
from crawler.config.config import Config


def get_current_ip():
    """获取当前 IP 地址"""
    try:
        # 使用多个服务来获取 IP
        services = [
            "https://api.ipify.org?format=json",
            "https://ifconfig.me/ip",
            "https://api.ip.sb/ip",
        ]
        
        for service in services:
            try:
                response = requests.get(service, timeout=5)
                if response.status_code == 200:
                    ip = response.text.strip()
                    # 如果是 JSON 格式
                    if ip.startswith("{"):
                        import json
                        ip = json.loads(ip).get("ip", ip)
                    return ip
            except:
                continue
        
        return None
    except Exception as e:
        print(f"获取 IP 失败: {e}")
        return None


def test_proxy(proxy_url=None):
    """测试代理配置"""
    print("=" * 60)
    print("代理配置测试")
    print("=" * 60)
    
    # 1. 显示配置的代理
    config = Config.from_env()
    configured_proxy = config.crawler.proxy
    whitelist_ip = "117.13.152.51"
    
    print(f"\n白名单 IP: {whitelist_ip}")
    print(f"配置的代理: {configured_proxy or '未配置'}")
    
    # 2. 测试不使用代理的 IP
    print("\n1. 测试当前 IP（不使用代理）...")
    session = requests.Session()
    current_ip = get_current_ip()
    if current_ip:
        print(f"   当前 IP: {current_ip}")
        if current_ip == whitelist_ip:
            print("   ✅ IP 匹配白名单，无需代理")
        else:
            print(f"   ❌ IP 不匹配白名单（需要: {whitelist_ip}）")
    else:
        print("   ❌ 无法获取当前 IP")
    
    # 3. 测试使用代理的 IP
    test_proxy = proxy_url or configured_proxy
    if test_proxy:
        print(f"\n2. 测试代理 IP（使用代理: {test_proxy}）...")
        session = requests.Session()
        session.proxies = {
            "http": test_proxy,
            "https": test_proxy
        }
        
        try:
            proxy_ip = None
            services = [
                "https://api.ipify.org?format=json",
                "https://ifconfig.me/ip",
            ]
            
            for service in services:
                try:
                    response = session.get(service, timeout=10)
                    if response.status_code == 200:
                        proxy_ip = response.text.strip()
                        if proxy_ip.startswith("{"):
                            import json
                            proxy_ip = json.loads(proxy_ip).get("ip", proxy_ip)
                        break
                except Exception as e:
                    print(f"   尝试 {service} 失败: {e}")
                    continue
            
            if proxy_ip:
                print(f"   代理 IP: {proxy_ip}")
                if proxy_ip == whitelist_ip:
                    print("   ✅ 代理 IP 匹配白名单")
                    return True
                else:
                    print(f"   ❌ 代理 IP 不匹配白名单（需要: {whitelist_ip}）")
                    return False
            else:
                print("   ❌ 无法通过代理获取 IP，代理可能不可用")
                return False
        except Exception as e:
            print(f"   ❌ 代理测试失败: {e}")
            return False
    else:
        print("\n2. 未配置代理，跳过代理测试")
        # 如果当前 IP 匹配白名单，返回 True 表示可以使用
        if current_ip == whitelist_ip:
            print("   ✅ 当前 IP 已匹配白名单，可以直接使用")
            return True
        else:
            print("   提示: 设置环境变量 PROXY 来配置代理")
            return False
    
    print("\n" + "=" * 60)
    return False


def test_api_access():
    """测试 API 访问"""
    print("\n" + "=" * 60)
    print("API 访问测试")
    print("=" * 60)
    
    config = Config.from_env()
    
    # 创建测试请求
    session = requests.Session()
    if config.crawler.proxy:
        session.proxies = {
            "http": config.crawler.proxy,
            "https": config.crawler.proxy
        }
        print(f"使用代理: {config.crawler.proxy}")
    
    # 测试 API 访问
    test_url = "https://api.csqaq.com/api/v1/info/good/container_detail"
    token = "AQPI91A7P5Z9J0U4O3P3N6T8"
    
    headers = {
        "ApiToken": token,  # API 使用 ApiToken 头，不是 Authorization
        "User-Agent": config.csqaq.user_agent,
        "Accept": "application/json",
    }
    
    print(f"\n测试 API: {test_url}")
    print(f"参数: id=1")
    print(f"请求头: ApiToken={headers.get('ApiToken', 'N/A')[:20]}...")
    
    try:
        # 先测试一个简单的请求，看看服务器返回什么
        response = session.get(
            test_url,
            params={"id": 1},  # API 使用 id 参数
            headers=headers,
            timeout=10
        )
        
        print(f"\n状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        try:
            data = response.json()
            print(f"响应内容: {data}")
        except:
            print(f"响应文本: {response.text[:500]}")
        
        if response.status_code == 200:
            print("\n✅ API 访问成功")
            return True
        elif response.status_code == 401:
            print("\n❌ 401 Unauthorized")
            print("可能的原因:")
            print("  1. IP 地址不在白名单中（服务器看到的 IP 可能不同）")
            print("  2. Token 已过期或无效")
            print("  3. 需要其他认证信息")
            print("\n建议:")
            print("  1. 检查 API 服务器实际看到的 IP 地址")
            print("  2. 验证 Token 是否有效")
            print("  3. 尝试使用浏览器爬虫（BrowserCrawler）自动获取 token")
            return False
        else:
            print(f"\n❌ API 访问失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"\n❌ API 访问异常: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # 如果提供了代理 URL 作为参数，使用它
    proxy_url = sys.argv[1] if len(sys.argv) > 1 else None
    
    # 测试代理配置
    proxy_ok = test_proxy(proxy_url)
    
    # 如果 IP 匹配白名单（无论是否使用代理），测试 API 访问
    if proxy_ok:
        test_api_access()
    else:
        print("\n提示:")
        print("1. 配置代理: export PROXY='http://proxy-server:port'")
        print("2. 或作为参数: python3 -m crawler.examples.test_proxy 'http://proxy-server:port'")
        print("3. 确保代理服务器的出口 IP 是 117.13.152.51")

