import logging
import re
from typing import Optional
from playwright.sync_api import sync_playwright

logger = logging.getLogger("TimestampRefresher")

def get_valid_timestamp() -> Optional[int]:
    """
    使用 Playwright 启动浏览器，访问 SteamDT，并从网络请求中提取有效的 timestamp 参数。
    该 timestamp 有效期约为 4 分钟。
    """
    timestamp_found = None
    
    try:
        with sync_playwright() as p:
            # 启动浏览器 (headless=True 以无头模式运行)
            # 优化: 添加参数以适应低配 Docker 环境
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage', # 关键: 在 Docker 中避免 /dev/shm 溢出
                    '--disable-gpu',
                    '--blink-settings=imagesEnabled=false' # 禁止加载图片
                ]
            )
            # 模拟真实浏览器 UA 和 分辨率
            page = browser.new_page(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080}
            )
            
            # 优化: 拦截并拒绝不必要的资源请求 (图片、字体、媒体)
            def route_intercept(route):
                if route.request.resource_type in ["image", "media", "font", "stylesheet"]:
                    route.abort()
                else:
                    route.continue_()
            
            page.route("**/*", route_intercept)
            
            # 监听请求
            def handle_request(request):
                nonlocal timestamp_found
                if timestamp_found:
                    return
                
                url = request.url
                # 调试: 打印所有 steamdt API 请求，以便排查
                if "api.steamdt.com" in url:
                    logger.info(f"Capture API Request: {url}")

                # 检查 URL 中是否包含 timestamp 参数
                if "timestamp=" in url and "api.steamdt.com" in url:
                    match = re.search(r"timestamp=(\d+)", url)
                    if match:
                        timestamp_found = int(match.group(1))

            page.on("request", handle_request)
            
            logger.info("正在使用 Playwright 获取新 timestamp (Target: multiple sites)...")
            
            # 定义尝试列表: [ (URL, 描述) ]
            # 优先尝试具体商品页，因为更容易触发数据请求，主页有时仅仅是静态展示
            targets = [
                ("https://www.steamdt.com/item/18863", "蝴蝶刀 (Butterfly Knife)"), # 热门商品
                ("https://www.steamdt.com", "主页 (Home)")
            ]
            
            for url, desc in targets:
                if timestamp_found:
                    break
                    
                logger.info(f"正在尝试访问: {desc} -> {url}")
                try:
                    # 访问页面
                    # 优化: 超时 60s, domcontentloaded (不用太长，因为有重试)
                    page.goto(url, timeout=60000, wait_until="domcontentloaded")
                    
                    # 尝试滚动页面触发 lazy load
                    page.evaluate("window.scrollTo(0, 500)")
                    page.wait_for_timeout(1000)
                    page.evaluate("window.scrollTo(0, 2000)")
                    
                    # 等待一下看是否捕获到
                    for _ in range(10):
                        if timestamp_found:
                            break
                        page.wait_for_timeout(1000)
                        
                except Exception as nav_e:
                    logger.warning(f"访问 {desc} 遇到问题: {nav_e}")
                    
                if not timestamp_found:
                    logger.warning(f"在 {desc} 未捕获到 timestamp，尝试下一个...")
            
            # 打印最终结果状态
            if not timestamp_found:
                try:
                    logger.warning(f"最终页面标题: {page.title()}")
                except:
                    pass
            
            # 等待一会，让 API 请求发出
            # 可以等待特定选择器，或者简单的 sleep
            # 这里简单 wait，或者因为我们已经用 on_request 捕获了，只要触发了就行
            # 等待直到捕获到 timestamp 或超时
            
            for _ in range(20): # 最多等待 10 秒
                if timestamp_found:
                    break
                page.wait_for_timeout(500)
                
            browser.close()
            
    except Exception as e:
        logger.error(f"Playwright 获取 timestamp 失败: {e}")
        return None
        
    if timestamp_found:
        logger.info(f"获取 timestamp 成功: {timestamp_found}")
    else:
        logger.warning("未能在请求中捕获到 timestamp")
        
    return timestamp_found
