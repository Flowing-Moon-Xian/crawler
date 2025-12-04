"""
批量 K 线数据爬虫

自动重复执行 K 线爬虫，从当前时间开始，每次获取 maxTime 前三个月的数据，
直到达到指定的目标 max_time。

支持三种爬虫类型：
1. total_kline - 大盘 K 线（total_kline_data 表）
2. sub_kline - 子大盘 K 线（qianzhan_kline_data / agent_kline_data 表）
3. item_kline - 商品 K 线（kline_data 表）

逻辑：
- 从当前时间开始，每次向前推三个月（约 90 天）
- 重复调用爬虫，直到 maxTime <= 目标 max_time
- 每次调用都会自动使用当前时间戳作为 timestamp（用于校验）
"""

import time
from datetime import datetime, timedelta
from typing import Optional

from crawler.config.config import Config
from crawler.crawlers.kline_crawler import KlineCrawler
from crawler.crawlers.sub_kline_crawler import SubKlineCrawler
from crawler.crawlers.item_kline_crawler import ItemKlineCrawler


class BatchKlineCrawler:
    """批量 K 线数据爬虫"""

    # 三个月约等于 90 天（秒）
    THREE_MONTHS_SECONDS = 90 * 24 * 60 * 60

    def __init__(self, config: Optional[Config] = None):
        """
        初始化批量爬虫

        Args:
            config: 配置对象，如果为 None 则从环境变量加载
        """
        self.config = config or Config.from_env()

    def crawl_total_kline(
        self,
        kline_type: int,
        target_max_time: int,
        start_time: Optional[int] = None,
    ) -> int:
        """
        批量爬取大盘 K 线数据（total_kline_data 表）

        Args:
            kline_type: K 线类型，1=时K，2=日K，3=周K
            target_max_time: 目标最大时间戳（秒），爬取到此时间为止
            start_time: 起始时间戳（秒），如果不提供则使用当前时间

        Returns:
            总共保存的记录数
        """
        crawler = KlineCrawler(self.config)

        if start_time is None:
            start_time = int(time.time())

        current_max_time = start_time
        total_count = 0
        round_num = 1

        print(f"\n开始批量爬取大盘 K 线数据")
        print(f"K 线类型: {kline_type} ({'时K' if kline_type == 1 else '日K' if kline_type == 2 else '周K'})")
        print(f"起始时间: {datetime.fromtimestamp(current_max_time).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"目标时间: {datetime.fromtimestamp(target_max_time).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"预计需要 {max(1, (current_max_time - target_max_time) // self.THREE_MONTHS_SECONDS + 1)} 轮爬取\n")

        while current_max_time > target_max_time:
            print(f"\n{'='*60}")
            print(f"第 {round_num} 轮爬取")
            print(f"当前 maxTime: {current_max_time} ({datetime.fromtimestamp(current_max_time).strftime('%Y-%m-%d %H:%M:%S')})")
            print(f"数据范围: {datetime.fromtimestamp(max(current_max_time - self.THREE_MONTHS_SECONDS, target_max_time)).strftime('%Y-%m-%d %H:%M:%S')} 至 {datetime.fromtimestamp(current_max_time).strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}\n")

            count = crawler.crawl_and_save(
                kline_type=kline_type,
                timestamp=None,  # 自动使用当前时间戳
                max_time=current_max_time,
            )

            total_count += count
            print(f"本轮保存 {count} 条数据，累计 {total_count} 条\n")

            # 向前推三个月
            current_max_time -= self.THREE_MONTHS_SECONDS

            # 如果下一轮会超过目标时间，直接设置为目标时间
            if current_max_time > target_max_time:
                round_num += 1
                # 添加延迟，避免请求过快
                time.sleep(1)
            else:
                # 最后一次，使用目标时间
                if current_max_time < target_max_time:
                    print(f"\n{'='*60}")
                    print(f"最后一轮爬取（使用目标时间）")
                    print(f"当前 maxTime: {target_max_time} ({datetime.fromtimestamp(target_max_time).strftime('%Y-%m-%d %H:%M:%S')})")
                    print(f"{'='*60}\n")

                    count = crawler.crawl_and_save(
                        kline_type=kline_type,
                        timestamp=None,
                        max_time=target_max_time,
                    )
                    total_count += count
                    print(f"本轮保存 {count} 条数据，累计 {total_count} 条\n")
                break

        print(f"\n{'='*60}")
        print(f"批量爬取完成！")
        print(f"总共保存 {total_count} 条大盘 K 线数据")
        print(f"{'='*60}\n")

        return total_count

    def crawl_sub_kline(
        self,
        type: str,
        kline_type: int,
        type_val: str,
        target_max_time: int,
        table_name: str = "qianzhan_kline_data",
        start_time: Optional[int] = None,
        platform: str = "ALL",
        special_style: str = "",
    ) -> int:
        """
        批量爬取子大盘 K 线数据（qianzhan_kline_data / agent_kline_data 表）

        Args:
            type: 类型，如 "HOT"
            kline_type: K 线类型，1=时K，2=日K，3=周K
            type_val: 类型值，如 "1402501509110038528"
            target_max_time: 目标最大时间戳（秒），爬取到此时间为止
            table_name: 目标表名，默认为 "qianzhan_kline_data"
            start_time: 起始时间戳（秒），如果不提供则使用当前时间
            platform: 平台，默认为 "ALL"
            special_style: 特殊样式，默认为空字符串

        Returns:
            总共保存的记录数
        """
        crawler = SubKlineCrawler(self.config)

        if start_time is None:
            start_time = int(time.time())

        current_max_time = start_time
        total_count = 0
        round_num = 1

        print(f"\n开始批量爬取子大盘 K 线数据")
        print(f"类型: {type}, K 线类型: {kline_type}, typeVal: {type_val}")
        print(f"目标表: {table_name}")
        print(f"起始时间: {datetime.fromtimestamp(current_max_time).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"目标时间: {datetime.fromtimestamp(target_max_time).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"预计需要 {max(1, (current_max_time - target_max_time) // self.THREE_MONTHS_SECONDS + 1)} 轮爬取\n")

        while current_max_time > target_max_time:
            print(f"\n{'='*60}")
            print(f"第 {round_num} 轮爬取")
            print(f"当前 maxTime: {current_max_time} ({datetime.fromtimestamp(current_max_time).strftime('%Y-%m-%d %H:%M:%S')})")
            print(f"数据范围: {datetime.fromtimestamp(max(current_max_time - self.THREE_MONTHS_SECONDS, target_max_time)).strftime('%Y-%m-%d %H:%M:%S')} 至 {datetime.fromtimestamp(current_max_time).strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}\n")

            count = crawler.crawl_and_save(
                type=type,
                kline_type=kline_type,
                type_val=type_val,
                table_name=table_name,
                timestamp=None,  # 自动使用当前时间戳
                max_time=current_max_time,
                platform=platform,
                special_style=special_style,
            )

            total_count += count
            print(f"本轮保存 {count} 条数据，累计 {total_count} 条\n")

            # 向前推三个月
            current_max_time -= self.THREE_MONTHS_SECONDS

            # 如果下一轮会超过目标时间，直接设置为目标时间
            if current_max_time > target_max_time:
                round_num += 1
                # 添加延迟，避免请求过快
                time.sleep(1)
            else:
                # 最后一次，使用目标时间
                if current_max_time < target_max_time:
                    print(f"\n{'='*60}")
                    print(f"最后一轮爬取（使用目标时间）")
                    print(f"当前 maxTime: {target_max_time} ({datetime.fromtimestamp(target_max_time).strftime('%Y-%m-%d %H:%M:%S')})")
                    print(f"{'='*60}\n")

                    count = crawler.crawl_and_save(
                        type=type,
                        kline_type=kline_type,
                        type_val=type_val,
                        table_name=table_name,
                        timestamp=None,
                        max_time=target_max_time,
                        platform=platform,
                        special_style=special_style,
                    )
                    total_count += count
                    print(f"本轮保存 {count} 条数据，累计 {total_count} 条\n")
                break

        print(f"\n{'='*60}")
        print(f"批量爬取完成！")
        print(f"总共保存 {total_count} 条子大盘 K 线数据到 {table_name} 表")
        print(f"{'='*60}\n")

        return total_count

    def crawl_item_kline(
        self,
        kline_type: int,
        type_val: int,
        target_max_time: int,
        start_time: Optional[int] = None,
        platform: str = "ALL",
        special_style: str = "",
    ) -> int:
        """
        批量爬取商品 K 线数据（kline_data 表）

        Args:
            kline_type: K 线类型，1=时K，2=日K，3=周K
            type_val: SteamDT 商品 / 分类 ID（对应 item_statistics.steamdt_id）
            target_max_time: 目标最大时间戳（秒），爬取到此时间为止
            start_time: 起始时间戳（秒），如果不提供则使用当前时间
            platform: 平台，默认为 "ALL"
            special_style: 特殊样式，默认为空字符串

        Returns:
            总共保存的记录数
        """
        crawler = ItemKlineCrawler(self.config)

        if start_time is None:
            start_time = int(time.time())

        current_max_time = start_time
        total_count = 0
        round_num = 1

        print(f"\n开始批量爬取商品 K 线数据")
        print(f"K 线类型: {kline_type}, typeVal: {type_val}")
        print(f"起始时间: {datetime.fromtimestamp(current_max_time).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"目标时间: {datetime.fromtimestamp(target_max_time).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"预计需要 {max(1, (current_max_time - target_max_time) // self.THREE_MONTHS_SECONDS + 1)} 轮爬取\n")

        while current_max_time > target_max_time:
            print(f"\n{'='*60}")
            print(f"第 {round_num} 轮爬取")
            print(f"当前 maxTime: {current_max_time} ({datetime.fromtimestamp(current_max_time).strftime('%Y-%m-%d %H:%M:%S')})")
            print(f"数据范围: {datetime.fromtimestamp(max(current_max_time - self.THREE_MONTHS_SECONDS, target_max_time)).strftime('%Y-%m-%d %H:%M:%S')} 至 {datetime.fromtimestamp(current_max_time).strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}\n")

            count = crawler.crawl_and_save(
                kline_type=kline_type,
                type_val=type_val,
                timestamp=None,  # 自动使用当前时间戳
                max_time=current_max_time,
                platform=platform,
                special_style=special_style,
            )

            total_count += count
            print(f"本轮保存 {count} 条数据，累计 {total_count} 条\n")

            # 向前推三个月
            current_max_time -= self.THREE_MONTHS_SECONDS

            # 如果下一轮会超过目标时间，直接设置为目标时间
            if current_max_time > target_max_time:
                round_num += 1
                # 添加延迟，避免请求过快
                time.sleep(1)
            else:
                # 最后一次，使用目标时间
                if current_max_time < target_max_time:
                    print(f"\n{'='*60}")
                    print(f"最后一轮爬取（使用目标时间）")
                    print(f"当前 maxTime: {target_max_time} ({datetime.fromtimestamp(target_max_time).strftime('%Y-%m-%d %H:%M:%S')})")
                    print(f"{'='*60}\n")

                    count = crawler.crawl_and_save(
                        kline_type=kline_type,
                        type_val=type_val,
                        timestamp=None,
                        max_time=target_max_time,
                        platform=platform,
                        special_style=special_style,
                    )
                    total_count += count
                    print(f"本轮保存 {count} 条数据，累计 {total_count} 条\n")
                break

        print(f"\n{'='*60}")
        print(f"批量爬取完成！")
        print(f"总共保存 {total_count} 条商品 K 线数据到 kline_data 表")
        print(f"{'='*60}\n")

        return total_count


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(
        description="批量 K 线数据爬虫（自动重复执行，从当前时间到目标时间）"
    )

    # 爬虫类型
    parser.add_argument(
        "--crawler-type",
        type=str,
        required=True,
        choices=["total", "sub", "item"],
        help="爬虫类型: total=大盘K线, sub=子大盘K线, item=商品K线",
    )

    # 通用参数
    parser.add_argument(
        "--kline-type",
        type=int,
        required=True,
        choices=[1, 2, 3],
        help="K线类型: 1=时K, 2=日K, 3=周K",
    )
    parser.add_argument(
        "--target-max-time",
        type=int,
        required=True,
        help="目标最大时间戳（秒），爬取到此时间为止。例如：1735574400（2024-12-31）",
    )
    parser.add_argument(
        "--start-time",
        type=int,
        default=None,
        help="起始时间戳（秒），如果不提供则使用当前时间",
    )

    # 子大盘参数
    parser.add_argument(
        "--type",
        type=str,
        help="子大盘类型（仅用于 sub 类型），如 'HOT'",
    )
    parser.add_argument(
        "--type-val",
        type=str,
        help="类型值（用于 sub 和 item 类型），子大盘如 '1402501509110038528'，商品为整数",
    )
    parser.add_argument(
        "--table",
        type=str,
        default="qianzhan_kline_data",
        choices=["qianzhan_kline_data", "agent_kline_data"],
        help="目标表名（仅用于 sub 类型），默认为 'qianzhan_kline_data'",
    )

    # 其他参数
    parser.add_argument(
        "--platform",
        type=str,
        default="ALL",
        help="平台，默认为 'ALL'",
    )
    parser.add_argument(
        "--special-style",
        type=str,
        default="",
        help="特殊样式，默认为空字符串",
    )

    args = parser.parse_args()

    batch_crawler = BatchKlineCrawler()

    if args.crawler_type == "total":
        # 大盘 K 线
        batch_crawler.crawl_total_kline(
            kline_type=args.kline_type,
            target_max_time=args.target_max_time,
            start_time=args.start_time,
        )

    elif args.crawler_type == "sub":
        # 子大盘 K 线
        if not args.type or not args.type_val:
            parser.error("子大盘爬虫需要 --type 和 --type-val 参数")

        batch_crawler.crawl_sub_kline(
            type=args.type,
            kline_type=args.kline_type,
            type_val=args.type_val,
            target_max_time=args.target_max_time,
            table_name=args.table,
            start_time=args.start_time,
            platform=args.platform,
            special_style=args.special_style,
        )

    elif args.crawler_type == "item":
        # 商品 K 线
        if not args.type_val:
            parser.error("商品爬虫需要 --type-val 参数（整数）")

        try:
            type_val_int = int(args.type_val)
        except ValueError:
            parser.error("--type-val 必须是整数（商品爬虫）")

        batch_crawler.crawl_item_kline(
            kline_type=args.kline_type,
            type_val=type_val_int,
            target_max_time=args.target_max_time,
            start_time=args.start_time,
            platform=args.platform,
            special_style=args.special_style,
        )


if __name__ == "__main__":
    main()

