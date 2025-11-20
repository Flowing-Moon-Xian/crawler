"""
箱子详情爬虫使用示例
"""
import sys
import time
from crawler.config.config import Config
from crawler.crawlers.container_detail_crawler import ContainerDetailCrawler


def main():
    """主函数"""
    # 创建配置
    config = Config.from_env()
    
    # 创建爬虫
    crawler = ContainerDetailCrawler(config, name="container_detail")
    
    # 如果提供了 box_qaq_id，只处理该箱子
    if len(sys.argv) >= 2:
        try:
            box_qaq_id = int(sys.argv[1])
            # 运行单个箱子
            result = crawler.run(box_qaq_id)
            
            # 输出结果
            if result["success"]:
                print(f"\n✅ 成功获取箱子 {box_qaq_id} 的详情")
                print(f"   数据条数: {result['data_count']}")
                print(f"   保存条数: {result['saved_count']}")
                if "db_stats" in result:
                    stats = result["db_stats"]
                    print(f"   枪皮: {stats['gun_skins']} 条")
                    print(f"   刀/手套: {stats['knife_gloves']} 条")
                    print(f"   关系: {stats['gun_skin_relations'] + stats['knife_glove_relations']} 条")
            else:
                print(f"\n❌ 获取失败: {result.get('error', 'Unknown error')}")
                sys.exit(1)
        except ValueError:
            print(f"错误: '{sys.argv[1]}' 不是有效的数字")
            sys.exit(1)
    else:
        # 批量处理所有符合条件的箱子
        print("获取符合条件的箱子列表（名字包含'武器箱'或'收藏品'）...")
        boxes = crawler.get_filtered_boxes()
        
        if not boxes:
            print("未找到符合条件的箱子")
            sys.exit(0)
        
        print(f"找到 {len(boxes)} 个箱子，开始处理...\n")
        
        success_count = 0
        failed_count = 0
        
        for i, box in enumerate(boxes):
            box_qaq_id = box["qaq_id"]
            box_name = box.get("name", "Unknown")
            print(f"处理箱子 [{i+1}/{len(boxes)}]: {box_name} (qaq_id: {box_qaq_id})")
            
            result = crawler.run(box_qaq_id)
            
            if result["success"]:
                success_count += 1
                print(f"  ✅ 成功: {result['data_count']} 条数据")
            else:
                failed_count += 1
                print(f"  ❌ 失败: {result.get('error', 'Unknown error')}")
            print()
            
            # 每个请求间隔 1 秒（最后一个不需要等待）
            if i < len(boxes) - 1:
                time.sleep(1)
        
        print(f"\n处理完成: 成功 {success_count}/{len(boxes)}, 失败 {failed_count}/{len(boxes)}")


if __name__ == "__main__":
    main()

