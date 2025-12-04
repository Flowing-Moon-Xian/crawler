"""
K线数据爬虫使用示例
演示如何从 API 获取 K 线数据并存储到 Supabase
"""
from crawler.crawlers.kline_crawler import KlineCrawler
from crawler.config.config import Config


def example_fetch_hourly_kline():
    """示例：获取时K数据"""
    print("=" * 50)
    print("示例1: 获取时K数据")
    print("=" * 50)
    
    crawler = KlineCrawler()
    
    # 获取时K数据（type=1）
    # timestamp 和 max_time 都是可选的
    # 如果不提供 timestamp，API 会返回最新的数据
    # max_time 用于限制数据范围（Unix 时间戳，秒）
    count = crawler.crawl_and_save(
        kline_type=1,  # 时K
        max_time=1762095600  # 限制最大时间戳
    )
    
    print(f"成功保存 {count} 条时K数据\n")


def example_fetch_daily_kline():
    """示例：获取日K数据"""
    print("=" * 50)
    print("示例2: 获取日K数据")
    print("=" * 50)
    
    crawler = KlineCrawler()
    
    # 获取日K数据（type=2）
    count = crawler.crawl_and_save(
        kline_type=2,  # 日K
        max_time=1762095600
    )
    
    print(f"成功保存 {count} 条日K数据\n")


def example_fetch_with_pagination():
    """示例：使用分页获取数据"""
    print("=" * 50)
    print("示例3: 使用分页获取数据")
    print("=" * 50)
    
    crawler = KlineCrawler()
    
    # 使用 timestamp 参数进行分页
    # timestamp 是毫秒级时间戳
    timestamp = 1764727000464
    
    count = crawler.crawl_and_save(
        kline_type=1,  # 时K
        timestamp=timestamp,
        max_time=1762095600
    )
    
    print(f"成功保存 {count} 条数据\n")


def example_fetch_all_types():
    """示例：获取所有类型的 K 线数据"""
    print("=" * 50)
    print("示例4: 获取所有类型的 K 线数据")
    print("=" * 50)
    
    crawler = KlineCrawler()
    
    total_count = 0
    
    # 获取时K
    print("正在获取时K数据...")
    count1 = crawler.crawl_and_save(kline_type=1, max_time=1762095600)
    total_count += count1
    
    # 获取日K
    print("\n正在获取日K数据...")
    count2 = crawler.crawl_and_save(kline_type=2, max_time=1762095600)
    total_count += count2
    
    # 周K（数据库暂不支持，会跳过）
    print("\n正在获取周K数据...")
    count3 = crawler.crawl_and_save(kline_type=3, max_time=1762095600)
    total_count += count3
    
    print(f"\n总共保存 {total_count} 条数据")


def example_step_by_step():
    """示例：分步操作（先获取，再保存）"""
    print("=" * 50)
    print("示例5: 分步操作")
    print("=" * 50)
    
    crawler = KlineCrawler()
    
    # 步骤1: 获取数据
    print("步骤1: 从 API 获取数据...")
    kline_data = crawler.fetch_kline_data(
        kline_type=1,
        max_time=1762095600
    )
    
    if not kline_data:
        print("获取数据失败")
        return
    
    print(f"获取到 {len(kline_data)} 条数据")
    print(f"前3条数据示例:")
    for i, item in enumerate(kline_data[:3]):
        print(f"  {i+1}. {item}")
    
    # 步骤2: 保存数据
    print("\n步骤2: 保存数据到数据库...")
    count = crawler.save_kline_data(kline_data, kline_type=1)
    print(f"成功保存 {count} 条数据\n")


def main():
    """主函数：运行所有示例"""
    try:
        # 示例1: 获取时K数据
        example_fetch_hourly_kline()
        
        # 示例2: 获取日K数据
        # example_fetch_daily_kline()
        
        # 示例3: 使用分页获取数据
        # example_fetch_with_pagination()
        
        # 示例4: 获取所有类型的 K 线数据
        # example_fetch_all_types()
        
        # 示例5: 分步操作
        # example_step_by_step()
        
        print("=" * 50)
        print("示例执行完成！")
        print("=" * 50)
        
    except Exception as e:
        print(f"执行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

