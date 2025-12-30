"""
SteamDT API 爬虫使用示例
演示如何访问 API 并保存 JSON 数据
"""
from crawler.crawlers.json_savers.steamdt_api_crawler import SteamDTAPICrawler


def example_fetch_all():
    """示例：获取所有配置的 API 端点"""
    print("=" * 60)
    print("示例1: 获取所有配置的 API 端点")
    print("=" * 60)
    
    crawler = SteamDTAPICrawler(output_dir="data/steamdt")
    results = crawler.crawl_all()
    
    print("\n结果:")
    for url, filepath in results.items():
        if filepath:
            print(f"  ✓ {url} -> {filepath}")
        else:
            print(f"  ✗ {url} -> 失败")


def example_fetch_single():
    """示例：获取单个 API 端点"""
    print("=" * 60)
    print("示例2: 获取单个 API 端点")
    print("=" * 60)
    
    crawler = SteamDTAPICrawler(output_dir="data/steamdt")
    
    # 获取 open.steamdt.com
    url1 = "https://open.steamdt.com"
    filepath1 = crawler.fetch_and_save(url1, "open_steamdt.json")
    print(f"结果: {filepath1}")
    
    # 获取 open.steamdt.com/open/cs2/v1/base
    url2 = "https://open.steamdt.com/open/cs2/v1/base"
    filepath2 = crawler.fetch_and_save(url2, "cs2_base.json")
    print(f"结果: {filepath2}")


def example_custom_output_dir():
    """示例：使用自定义输出目录"""
    print("=" * 60)
    print("示例3: 使用自定义输出目录")
    print("=" * 60)
    
    crawler = SteamDTAPICrawler(output_dir="data/custom")
    
    url = "https://open.steamdt.com/open/cs2/v1/base"
    filepath = crawler.fetch_and_save(url)
    print(f"数据保存到: {filepath}")


def main():
    """主函数：运行所有示例"""
    try:
        # 示例1: 获取所有配置的 API 端点
        example_fetch_all()
        
        # 示例2: 获取单个 API 端点
        # example_fetch_single()
        
        # 示例3: 使用自定义输出目录
        # example_custom_output_dir()
        
        print("\n" + "=" * 60)
        print("示例执行完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"执行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

