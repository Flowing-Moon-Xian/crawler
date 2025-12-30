"""
子大盘 K 线数据爬虫配置示例
展示如何通过更换 typeVal 和表名来存储不同子大盘的数据
"""
from crawler.crawlers.url_crawlers.sub_kline_crawler import SubKlineCrawler


# 子大盘配置映射
# 格式: {子大盘名称: {"type_val": "类型值", "table_name": "表名"}}
SUB_MARKET_CONFIG = {
    "千百战大盘": {
        "type_val": "1402501509110038528",
        "table_name": "qianzhan_kline_data"
    },
    "探员大盘": {
        "type_val": "探员大盘的typeVal",  # 请替换为实际的 typeVal
        "table_name": "agent_kline_data"
    },
    # 可以继续添加其他子大盘配置
    # "其他子大盘": {
    #     "type_val": "对应的typeVal",
    #     "table_name": "对应的表名"
    # }
}


def crawl_sub_market(
    market_name: str,
    kline_type: int = 2,
    max_time: int = None
):
    """
    爬取指定子大盘的 K 线数据
    
    Args:
        market_name: 子大盘名称（必须在 SUB_MARKET_CONFIG 中定义）
        kline_type: K 线类型，1=时K，2=日K，3=周K
        max_time: 最大时间戳（秒），用于限制数据范围
    """
    if market_name not in SUB_MARKET_CONFIG:
        print(f"错误: 未找到子大盘配置 '{market_name}'")
        print(f"可用的子大盘: {list(SUB_MARKET_CONFIG.keys())}")
        return 0
    
    config = SUB_MARKET_CONFIG[market_name]
    crawler = SubKlineCrawler()
    
    print(f"正在爬取 {market_name} 的 K 线数据...")
    print(f"  typeVal: {config['type_val']}")
    print(f"  表名: {config['table_name']}")
    print(f"  K线类型: {kline_type} ({'时K' if kline_type == 1 else '日K' if kline_type == 2 else '周K'})")
    
    count = crawler.crawl_and_save(
        type="HOT",
        kline_type=kline_type,
        type_val=config["type_val"],
        table_name=config["table_name"],
        max_time=max_time
    )
    
    print(f"成功保存 {count} 条数据到 {market_name}\n")
    return count


def crawl_all_sub_markets(kline_type: int = 2, max_time: int = None):
    """
    爬取所有配置的子大盘的 K 线数据
    
    Args:
        kline_type: K 线类型，1=时K，2=日K，3=周K
        max_time: 最大时间戳（秒），用于限制数据范围
    """
    print("=" * 50)
    print(f"开始爬取所有子大盘的 K 线数据 (klineType={kline_type})")
    print("=" * 50)
    
    total_count = 0
    
    for market_name in SUB_MARKET_CONFIG.keys():
        count = crawl_sub_market(market_name, kline_type, max_time)
        total_count += count
    
    print("=" * 50)
    print(f"完成！总共保存 {total_count} 条数据")
    print("=" * 50)
    
    return total_count


def main():
    """主函数：示例用法"""
    
    # 示例1: 爬取单个子大盘
    print("示例1: 爬取千百战大盘的日K数据")
    crawl_sub_market("千百战大盘", kline_type=2, max_time=1756911600)
    
    # 示例2: 爬取所有子大盘
    # print("\n示例2: 爬取所有子大盘的日K数据")
    # crawl_all_sub_markets(kline_type=2, max_time=1756911600)
    
    # 示例3: 爬取不同 K 线类型
    # print("\n示例3: 爬取千百战大盘的时K数据")
    # crawl_sub_market("千百战大盘", kline_type=1, max_time=1756911600)


if __name__ == "__main__":
    main()

