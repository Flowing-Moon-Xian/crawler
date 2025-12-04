"""
子大盘 K 线数据爬虫使用示例
演示如何从 API 获取子大盘 K 线数据并存储到 Supabase
"""
from crawler.crawlers.sub_kline_crawler import SubKlineCrawler
from crawler.config.config import Config


def example_fetch_hot_daily_kline():
    """示例：获取 HOT 类型的日K数据（千百战大盘）"""
    print("=" * 50)
    print("示例1: 获取 HOT 类型的日K数据（千百战大盘）")
    print("=" * 50)
    
    crawler = SubKlineCrawler()
    
    # 获取 HOT 类型的日K数据，存储到千百战大盘表
    count = crawler.crawl_and_save(
        type="HOT",
        kline_type=2,  # 日K
        type_val="1402501509110038528",  # 千百战的 typeVal
        table_name="qianzhan_kline_data",  # 千百战大盘表
        max_time=1756911600
    )
    
    print(f"成功保存 {count} 条日K数据到千百战大盘表\n")


def example_fetch_hot_hourly_kline():
    """示例：获取 HOT 类型的时K数据"""
    print("=" * 50)
    print("示例2: 获取 HOT 类型的时K数据")
    print("=" * 50)
    
    crawler = SubKlineCrawler()
    
    # 获取 HOT 类型的时K数据
    count = crawler.crawl_and_save(
        type="HOT",
        kline_type=1,  # 时K
        type_val="1402501509110038528",
        max_time=1756911600
    )
    
    print(f"成功保存 {count} 条时K数据\n")


def example_fetch_with_timestamp():
    """示例：使用时间戳分页获取数据"""
    print("=" * 50)
    print("示例3: 使用时间戳分页获取数据")
    print("=" * 50)
    
    crawler = SubKlineCrawler()
    
    # 使用 timestamp 参数进行分页
    timestamp = "1764729043799"
    
    count = crawler.crawl_and_save(
        type="HOT",
        kline_type=2,  # 日K
        type_val="1402501509110038528",
        timestamp=timestamp,
        max_time=1756911600
    )
    
    print(f"成功保存 {count} 条数据\n")


def example_fetch_all_kline_types():
    """示例：获取所有类型的 K 线数据"""
    print("=" * 50)
    print("示例4: 获取所有类型的 K 线数据")
    print("=" * 50)
    
    crawler = SubKlineCrawler()
    
    type_val = "1402501509110038528"
    max_time = 1756911600
    
    total_count = 0
    
    # 获取时K
    print("正在获取时K数据...")
    count1 = crawler.crawl_and_save(
        type="HOT",
        kline_type=1,
        type_val=type_val,
        max_time=max_time
    )
    total_count += count1
    
    # 获取日K
    print("\n正在获取日K数据...")
    count2 = crawler.crawl_and_save(
        type="HOT",
        kline_type=2,
        type_val=type_val,
        max_time=max_time
    )
    total_count += count2
    
    # 周K（数据库暂不支持，会跳过）
    print("\n正在获取周K数据...")
    count3 = crawler.crawl_and_save(
        type="HOT",
        kline_type=3,
        type_val=type_val,
        max_time=max_time
    )
    total_count += count3
    
    print(f"\n总共保存 {total_count} 条数据")


def example_step_by_step():
    """示例：分步操作（先获取，再保存）"""
    print("=" * 50)
    print("示例5: 分步操作")
    print("=" * 50)
    
    crawler = SubKlineCrawler()
    
    # 步骤1: 获取数据
    print("步骤1: 从 API 获取数据...")
    kline_data = crawler.fetch_kline_data(
        type="HOT",
        kline_type=2,
        type_val="1402501509110038528",
        max_time=1756911600
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
    count = crawler.save_kline_data(kline_data, kline_type=2)
    print(f"成功保存 {count} 条数据\n")


def example_fetch_agent_kline():
    """示例：获取探员大盘的 K 线数据"""
    print("=" * 50)
    print("示例6: 获取探员大盘的 K 线数据")
    print("=" * 50)
    
    crawler = SubKlineCrawler()
    
    # 获取探员大盘的日K数据
    # 注意：需要替换为探员大盘对应的 typeVal
    agent_type_val = "探员大盘的typeVal"  # 请替换为实际的 typeVal
    
    count = crawler.crawl_and_save(
        type="HOT",
        kline_type=2,
        type_val=agent_type_val,
        table_name="agent_kline_data",  # 探员大盘表
        max_time=1756911600
    )
    
    print(f"成功保存 {count} 条数据到探员大盘表\n")


def example_different_sub_markets():
    """示例：获取不同子大盘的数据"""
    print("=" * 50)
    print("示例7: 获取不同子大盘的数据")
    print("=" * 50)
    
    crawler = SubKlineCrawler()
    
    # 配置不同子大盘的 typeVal 和对应的表名
    sub_markets = [
        {
            "name": "千百战大盘",
            "type_val": "1402501509110038528",
            "table_name": "qianzhan_kline_data"
        },
        {
            "name": "探员大盘",
            "type_val": "探员大盘的typeVal",  # 请替换为实际的 typeVal
            "table_name": "agent_kline_data"
        }
    ]
    
    total_count = 0
    
    for market in sub_markets:
        print(f"\n正在获取 {market['name']} 的数据...")
        count = crawler.crawl_and_save(
            type="HOT",
            kline_type=2,  # 日K
            type_val=market["type_val"],
            table_name=market["table_name"],
            max_time=1756911600
        )
        total_count += count
        print(f"{market['name']} 保存了 {count} 条数据")
    
    print(f"\n总共保存 {total_count} 条数据到不同子大盘表\n")


def example_custom_platform():
    """示例：使用自定义平台参数"""
    print("=" * 50)
    print("示例8: 使用自定义平台参数")
    print("=" * 50)
    
    crawler = SubKlineCrawler()
    
    # 使用自定义平台和特殊样式
    count = crawler.crawl_and_save(
        type="HOT",
        kline_type=2,
        type_val="1402501509110038528",
        table_name="qianzhan_kline_data",
        platform="ALL",
        special_style="",
        max_time=1756911600
    )
    
    print(f"成功保存 {count} 条数据\n")


def main():
    """主函数：运行所有示例"""
    try:
        # 示例1: 获取 HOT 类型的日K数据
        example_fetch_hot_daily_kline()
        
        # 示例2: 获取 HOT 类型的时K数据
        # example_fetch_hot_hourly_kline()
        
        # 示例3: 使用时间戳分页获取数据
        # example_fetch_with_timestamp()
        
        # 示例4: 获取所有类型的 K 线数据
        # example_fetch_all_kline_types()
        
        # 示例5: 分步操作
        # example_step_by_step()
        
        # 示例6: 获取探员大盘的 K 线数据
        # example_fetch_agent_kline()
        
        # 示例7: 获取不同子大盘的数据
        # example_different_sub_markets()
        
        # 示例8: 使用自定义平台参数
        # example_custom_platform()
        
        print("=" * 50)
        print("示例执行完成！")
        print("=" * 50)
        
    except Exception as e:
        print(f"执行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

