"""
SteamDT API 爬虫
访问 open.steamdt.com API 并保存 JSON 数据到本地
"""
import requests
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

from crawler.config.config import Config


class SteamDTAPICrawler:
    """SteamDT API 爬虫"""
    
    def __init__(self, config: Optional[Config] = None, output_dir: str = "data", api_token: Optional[str] = None):
        """
        初始化爬虫
        
        Args:
            config: 配置对象，如果为 None 则从环境变量加载
            output_dir: 输出目录，默认为 "data"
            api_token: SteamDT API Token，如果为 None 则从环境变量 STEAMDT_API_TOKEN 加载
        """
        self.config = config or Config.from_env()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 获取 API token
        self.api_token = api_token or os.getenv("STEAMDT_API_TOKEN", "e2b0c8d38975485fa98146cde6bfd580")
        
        # 初始化 requests session
        self.session = requests.Session()
        
        # 配置代理（如果提供）
        if self.config.crawler.proxy:
            self.session.proxies = {
                "http": self.config.crawler.proxy,
                "https": self.config.crawler.proxy
            }
            print(f"使用代理: {self.config.crawler.proxy}")
        
        # 设置请求头
        self.session.headers.update({
            "User-Agent": self.config.csqaq.user_agent,
            "Accept": "application/json",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Content-Type": "application/json",
        })
        
        # 设置 Authorization header（如果提供了 token）
        if self.api_token:
            self.session.headers.update({
                "Authorization": f"Bearer {self.api_token}"
            })
    
    def fetch_api(self, url: str) -> Optional[Dict[str, Any]]:
        """
        从 API 获取数据（GET 请求）
        
        Args:
            url: API URL
            
        Returns:
            JSON 数据字典，如果失败返回 None
        """
        try:
            print(f"正在访问: {url}")
            response = self.session.get(
                url,
                timeout=self.config.crawler.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            print(f"成功获取数据，响应大小: {len(response.content)} 字节")
            return data
            
        except requests.RequestException as e:
            print(f"API 请求失败: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON 解析失败: {e}")
            return None
        except Exception as e:
            print(f"获取数据失败: {e}")
            return None
    
    def post_api(self, url: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        向 API 发送 POST 请求
        
        Args:
            url: API URL
            data: 要发送的 JSON 数据
            
        Returns:
            JSON 响应数据字典，如果失败返回 None
        """
        try:
            print(f"正在发送 POST 请求到: {url}")
            print(f"请求数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
            response = self.session.post(
                url,
                json=data,
                timeout=self.config.crawler.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            print(f"成功获取数据，响应大小: {len(response.content)} 字节")
            return result
            
        except requests.RequestException as e:
            print(f"API 请求失败: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    print(f"错误详情: {json.dumps(error_detail, ensure_ascii=False, indent=2)}")
                except:
                    print(f"响应内容: {e.response.text}")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON 解析失败: {e}")
            return None
        except Exception as e:
            print(f"获取数据失败: {e}")
            return None
    
    def fetch_wear(self, inspect_url: str, notify_url: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        获取磨损信息（调用 wear API）
        
        Args:
            inspect_url: Steam 检查链接（steam://rungame/...）
            notify_url: 回调通知 URL（可选）
            
        Returns:
            JSON 响应数据字典，如果失败返回 None
        """
        url = "https://open.steamdt.com/open/cs2/v1/wear"
        
        data = {
            "inspectUrl": inspect_url
        }
        
        if notify_url:
            data["notifyUrl"] = notify_url
        
        return self.post_api(url, data)
    
    def save_json(self, data: Dict[str, Any], filename: str) -> str:
        """
        保存 JSON 数据到文件
        
        Args:
            data: 要保存的数据
            filename: 文件名（不含路径）
            
        Returns:
            保存的文件路径
        """
        filepath = self.output_dir / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"数据已保存到: {filepath}")
        return str(filepath)
    
    def fetch_and_save(self, url: str, filename: Optional[str] = None) -> Optional[str]:
        """
        获取数据并保存到文件（一步完成，GET 请求）
        
        Args:
            url: API URL
            filename: 文件名，如果为 None 则自动生成
            
        Returns:
            保存的文件路径，如果失败返回 None
        """
        # 获取数据
        data = self.fetch_api(url)
        if not data:
            return None
        
        # 生成文件名
        if filename is None:
            # 从 URL 生成文件名
            url_parts = url.replace("https://", "").replace("http://", "").split("/")
            url_parts = [part for part in url_parts if part]
            base_name = "_".join(url_parts).replace(".", "_")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{base_name}_{timestamp}.json"
        
        # 保存数据
        return self.save_json(data, filename)
    
    def fetch_wear_and_save(self, inspect_url: str, notify_url: Optional[str] = None, filename: Optional[str] = None) -> Optional[str]:
        """
        获取磨损信息并保存到文件（一步完成）
        
        Args:
            inspect_url: Steam 检查链接
            notify_url: 回调通知 URL（可选）
            filename: 文件名，如果为 None 则自动生成
            
        Returns:
            保存的文件路径，如果失败返回 None
        """
        # 获取数据
        data = self.fetch_wear(inspect_url, notify_url)
        if not data:
            return None
        
        # 生成文件名
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"wear_{timestamp}.json"
        
        # 保存数据
        return self.save_json(data, filename)
    
    def crawl_all(self) -> Dict[str, Optional[str]]:
        """
        爬取所有配置的 API 端点
        
        Returns:
            结果字典，key 为 URL，value 为保存的文件路径
        """
        results = {}
        
        # API 端点列表
        api_endpoints = [
            "https://open.steamdt.com/open/cs2/v1/base"
        ]
        
        print("=" * 60)
        print("开始爬取 SteamDT API 数据")
        print("=" * 60)
        
        for url in api_endpoints:
            print(f"\n处理: {url}")
            filepath = self.fetch_and_save(url)
            results[url] = filepath
        
        print("\n" + "=" * 60)
        print("爬取完成")
        print("=" * 60)
        
        # 打印结果摘要
        print("\n结果摘要:")
        for url, filepath in results.items():
            status = "✓ 成功" if filepath else "✗ 失败"
            print(f"  {status}: {url}")
            if filepath:
                print(f"    保存到: {filepath}")
        
        return results


def main():
    """主函数：运行爬虫"""
    import argparse
    
    parser = argparse.ArgumentParser(description="SteamDT API 爬虫")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data",
        help="输出目录（默认: data）"
    )
    parser.add_argument(
        "--url",
        type=str,
        help="指定要访问的 URL（GET 请求，如果不指定，则访问所有配置的端点）"
    )
    parser.add_argument(
        "--filename",
        type=str,
        help="指定保存的文件名（仅在使用 --url 或 --inspect-url 时有效）"
    )
    parser.add_argument(
        "--inspect-url",
        type=str,
        help="Steam 检查链接（用于调用 wear API，例如: steam://rungame/730/...）"
    )
    parser.add_argument(
        "--notify-url",
        type=str,
        help="回调通知 URL（可选，仅在使用 --inspect-url 时有效）"
    )
    parser.add_argument(
        "--api-token",
        type=str,
        help="SteamDT API Token（如果不指定，则使用默认值或环境变量 STEAMDT_API_TOKEN）"
    )
    
    args = parser.parse_args()
    
    # 创建爬虫
    crawler = SteamDTAPICrawler(output_dir=args.output_dir, api_token=args.api_token)
    
    if args.inspect_url:
        # 调用 wear API
        filepath = crawler.fetch_wear_and_save(args.inspect_url, args.notify_url, args.filename)
        if filepath:
            print(f"\n成功！数据已保存到: {filepath}")
        else:
            print("\n失败！无法获取或保存数据")
    elif args.url:
        # 访问指定的 URL（GET 请求）
        filepath = crawler.fetch_and_save(args.url, args.filename)
        if filepath:
            print(f"\n成功！数据已保存到: {filepath}")
        else:
            print("\n失败！无法获取或保存数据")
    else:
        # 访问所有配置的端点
        results = crawler.crawl_all()
        
        success_count = sum(1 for v in results.values() if v is not None)
        total_count = len(results)
        print(f"\n完成！成功 {success_count}/{total_count}")


if __name__ == "__main__":
    main()

