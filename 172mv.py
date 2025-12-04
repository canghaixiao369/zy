import requests
from bs4 import BeautifulSoup
import time
import logging
import urllib3
import re
import os
import json
from urllib.parse import urljoin, urlparse, parse_qs
from datetime import datetime

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 配置日志（只输出到控制台）
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# 定义要爬取的分类页面
CATEGORY_PAGES = {
    "中文MV舞曲": "https://m.172mixdj.com/categories/zwmv",
    "英文MV舞曲": "https://m.172mixdj.com/categories/ywmv", 
    "中文MV串烧": "https://m.172mixdj.com/categories/zwcs",
    "英文MV串烧": "https://m.172mixdj.com/categories/ywcs"
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
}

class VideoCrawler:
    def __init__(self):
        # 创建目录（如果不存在）
        os.makedirs('./tv', exist_ok=True)
        # 加载已爬取的视频ID记录
        self.load_crawled_records()
        
    def load_crawled_records(self):
        """加载已爬取的记录"""
        self.crawled_ids = set()
        
        # 尝试从主文件中加载已爬取ID（通过序号识别）
        if os.path.exists('./tv/DJMV.txt'):
            try:
                with open('./tv/DJMV.txt', 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith('#') and ',' in line:
                            parts = line.split(',')
                            if len(parts) >= 2:
                                url = parts[1].strip()
                                # 从URL中提取ID
                                video_id = self.extract_video_id_from_url(url)
                                if video_id:
                                    self.crawled_ids.add(video_id)
                logger.info(f"已加载 {len(self.crawled_ids)} 个已爬取的视频ID")
            except Exception as e:
                logger.error(f"加载爬取记录时出错: {e}")
    
    def get_page_content(self, url, page_num=1):
        """获取指定页面的内容"""
        try:
            # 对于分页，构造不同的URL
            if page_num > 1:
                if '?' in url:
                    page_url = f"{url}&page={page_num}"
                else:
                    page_url = f"{url}?page={page_num}"
            else:
                page_url = url
                
            logger.info(f"获取页面 {page_num}: {page_url}")
            response = requests.get(page_url, headers=HEADERS, timeout=15, verify=False)
            response.raise_for_status()
            
            # 检查响应编码
            if response.encoding == 'ISO-8859-1':
                response.encoding = response.apparent_encoding or 'utf-8'
            
            return response.text
            
        except requests.RequestException as e:
            logger.error(f"请求失败 {url} 第{page_num}页: {e}")
            return None
        except Exception as e:
            logger.error(f"获取页面内容时出错: {e}")
            return None
    
    def extract_video_data_from_html(self, html, base_url, page_num):
        """从HTML中提取视频数据，优先提取<a class="post-permalink" title=下的标题"""
        video_data = []
        
        if not html:
            return video_data
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # 优先查找<a class="post-permalink"标签
        permalink_links = soup.find_all('a', class_='post-permalink')
        
        if permalink_links:
            logger.info(f"第{page_num}页找到 {len(permalink_links)} 个post-permalink链接")
        
        for link in permalink_links:
            href = link.get('href', '')
            title = link.get('title', '')
            
            if href and title:
                # 清理和标准化URL
                if href.startswith('//'):
                    href = 'https:' + href
                elif href.startswith('/'):
                    href = urljoin(base_url, href)
                elif not href.startswith(('http://', 'https://')):
                    href = urljoin(base_url, href)
                
                # 尝试从URL中提取ID
                video_id = self.extract_video_id_from_url(href)
                
                if video_id:
                    # 构建最终的URL格式
                    final_url = f"http://zjk.xozv.top/DJMV.php?id={video_id}"
                    
                    # 清理标题（移除HTML标签和多余空格）
                    title = re.sub(r'<[^>]+>', '', title).strip()
                    
                    video_data.append({
                        'title': title,
                        'url': final_url,
                        'id': video_id,
                        'source_url': href,
                        'page': page_num
                    })
        
        # 如果没找到post-permalink链接，尝试其他方法
        if not video_data:
            logger.debug(f"第{page_num}页未找到post-permalink链接，尝试其他提取方法")
            video_data = self.extract_video_data_alternative(soup, base_url, page_num)
        
        return video_data
    
    def extract_video_data_alternative(self, soup, base_url, page_num):
        """备用方法：从HTML中提取视频数据"""
        video_data = []
        
        # 查找所有可能的视频链接
        all_links = soup.find_all('a', href=True)
        
        for link in all_links:
            href = link.get('href', '')
            
            # 检查是否包含视频ID的模式
            if any(pattern in href.lower() for pattern in ['id=', 'video', 'play', 'watch', 'dj.js']):
                # 清理和标准化URL
                if href.startswith('//'):
                    href = 'https:' + href
                elif href.startswith('/'):
                    href = urljoin(base_url, href)
                elif not href.startswith(('http://', 'https://')):
                    href = urljoin(base_url, href)
                
                # 尝试从URL中提取ID
                video_id = self.extract_video_id_from_url(href)
                
                if video_id:
                    # 获取标题
                    title = link.get_text(strip=True)
                    if not title:
                        title = link.get('title', '') or link.get('alt', '')
                    
                    # 如果仍然没有标题，查找附近的标题元素
                    if not title:
                        for parent in link.parents:
                            title_elem = parent.find(['h1', 'h2', 'h3', 'h4', 'h5', 'p', 'span', 'div'], 
                                                    class_=re.compile(r'title|name|heading', re.I))
                            if title_elem and title_elem.get_text(strip=True):
                                title = title_elem.get_text(strip=True)
                                break
                    
                    # 如果还是没有标题，使用默认标题
                    if not title:
                        title = f"视频_{video_id[:8]}_页{page_num}"
                    
                    # 构建最终的URL格式
                    final_url = f"http://zjk.xozv.top/DJMV.php?id={video_id}"
                    
                    video_data.append({
                        'title': title,
                        'url': final_url,
                        'id': video_id,
                        'source_url': href,
                        'page': page_num
                    })
        
        return video_data
    
    def extract_video_id_from_url(self, url):
        """从URL中提取视频ID"""
        video_id = None
        
        # 尝试从查询参数中提取ID
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        
        for key in ['id', 'video', 'v', 'vid']:
            if key in query_params and query_params[key]:
                video_id = query_params[key][0]
                break
        
        # 如果没有从查询参数中找到，尝试从路径中提取
        if not video_id:
            # 使用正则表达式从路径中提取可能的ID
            id_patterns = [
                r'id/([^/?#]+)',  # id/xxx
                r'video/([^/?#]+)',  # video/xxx
                r'v/([^/?#]+)',  # v/xxx
                r'([A-Za-z0-9_-]{8,})'  # 至少8位的字母数字组合
            ]
            
            for pattern in id_patterns:
                match = re.search(pattern, parsed_url.path)
                if match:
                    video_id = match.group(1)
                    break
        
        return video_id
    
    def extract_video_ids_from_page(self, url, category_name, max_pages=30):
        """
        从单个分类页面提取所有视频的标题和ID
        强制爬取max_pages页，直到完成所有页
        
        返回: 列表，每个元素是视频信息的字典
        """
        new_video_data = []
        page_num = 1
        
        logger.info(f"开始抓取分类: {category_name}，强制爬取 {max_pages} 页")
        
        while page_num <= max_pages:
            logger.info(f"正在抓取第 {page_num} 页/共 {max_pages} 页")
            
            # 获取页面内容
            html_content = self.get_page_content(url, page_num)
            
            if not html_content:
                logger.warning(f"第 {page_num} 页获取失败，继续下一页")
                page_num += 1
                time.sleep(1)  # 失败后稍作延迟
                continue
            
            # 从HTML中提取视频数据
            page_video_data = self.extract_video_data_from_html(html_content, url, page_num)
            
            # 过滤已爬取的视频
            new_videos_on_page = []
            for video in page_video_data:
                video_id = video.get('id', '')
                if video_id and video_id not in self.crawled_ids:
                    new_videos_on_page.append(video)
                    self.crawled_ids.add(video_id)  # 添加到已爬取集合
            
            logger.info(f"第 {page_num} 页找到 {len(page_video_data)} 个视频，其中 {len(new_videos_on_page)} 个是新视频")
            
            # 添加到新视频列表
            new_video_data.extend(new_videos_on_page)
            
            # 礼貌性延迟
            time.sleep(1)
            
            page_num += 1
        
        logger.info(f"分类 {category_name} 完成 {max_pages} 页爬取，共找到 {len(new_video_data)} 个新视频")
        return new_video_data
    
    def get_last_index_from_file(self):
        """从主文件中获取最后一个序号"""
        last_index = 0
        filepath = './tv/DJMV.txt'
        
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in reversed(lines):  # 从文件末尾开始查找
                        line = line.strip()
                        if line and not line.startswith('#') and ',' in line:
                            # 尝试提取序号
                            if '.' in line.split(',')[0]:
                                index_part = line.split(',')[0].split('.')[0]
                                if index_part.isdigit():
                                    last_index = int(index_part)
                                    break
            except Exception as e:
                logger.error(f"读取文件 {filepath} 时出错: {e}")
        
        return last_index
    
    def save_to_txt(self, video_data_list):
        """
        将提取的视频数据保存到TXT文件
        在标题前加上序号
        
        Args:
            video_data_list: 列表，每个元素是(分类名称, 视频数据列表)的元组
        """
        try:
            filepath = './tv/DJMV.txt'
            
            # 判断文件是否存在，决定是追加还是创建新文件
            file_exists = os.path.exists(filepath)
            
            # 获取文件中的最后一个序号
            current_index = self.get_last_index_from_file() + 1 if file_exists else 1
            
            with open(filepath, 'a' if file_exists else 'w', encoding='utf-8') as f:
                total_count = 0
                
                # 如果是新文件，写入文件头
                if not file_exists:
                    f.write("# 提取的视频ID列表\n")
                    f.write(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("# 格式: 序号.标题,完整URL\n")
                    f.write("=" * 50 + "\n\n")
                else:
                    # 如果是追加模式且文件不为空，添加分隔线
                    f.write(f"\n\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 新增内容:\n")
                    f.write("-" * 40 + "\n")
                
                # 按分类写入数据
                for category_name, video_data in video_data_list:
                    if video_data:
                        f.write(f"\n# {category_name} ({len(video_data)}个视频)\n")
                        
                        for video in video_data:
                            # 清理标题中的逗号，避免CSV格式问题
                            clean_title = video['title'].replace(',', '，')
                            
                            # 在标题前加上序号
                            indexed_title = f"{current_index}.{clean_title}"
                            
                            # 写入文件
                            f.write(f"{indexed_title},{video['url']}\n")
                            
                            current_index += 1
                            total_count += 1
            
            logger.info(f"数据已保存到 {filepath}，本次新增 {total_count} 个视频")
            return total_count
            
        except Exception as e:
            logger.error(f"保存文件时出错: {e}")
            return 0
    
    def run(self, max_pages_per_category=30):
        """运行爬虫，强制爬取指定页数"""
        print("="*60)
        print("视频爬虫 - 强制爬取模式")
        print("="*60)
        print(f"将爬取 {len(CATEGORY_PAGES)} 个分类")
        print(f"每个分类爬取 {max_pages_per_category} 页")
        print(f"输出文件: ./tv/DJMV.txt")
        print(f"当前已记录 {len(self.crawled_ids)} 个已爬取视频ID")
        print("="*60)
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-"*60)
        
        all_new_video_data = []
        total_new_videos = 0
        
        # 开始时间
        start_time = time.time()
        
        # 遍历所有分类页面
        for category_name, url in CATEGORY_PAGES.items():
            category_start_time = time.time()
            logger.info(f"=== 开始处理分类: {category_name} ===")
            
            # 先尝试HTTPS
            new_video_data = self.extract_video_ids_from_page(url, category_name, max_pages=max_pages_per_category)
            
            if not new_video_data:
                # 如果HTTPS失败，尝试HTTP
                http_url = url.replace('https://', 'http://')
                logger.info(f"HTTPS抓取失败，尝试HTTP: {http_url}")
                new_video_data = self.extract_video_ids_from_page(http_url, category_name, max_pages=max_pages_per_category)
            
            category_elapsed_time = time.time() - category_start_time
            
            if new_video_data:
                all_new_video_data.append((category_name, new_video_data))
                total_new_videos += len(new_video_data)
                logger.info(f"分类 {category_name} 完成，耗时 {category_elapsed_time:.1f} 秒，新增 {len(new_video_data)} 个视频")
            else:
                logger.info(f"分类 {category_name} 完成，耗时 {category_elapsed_time:.1f} 秒，没有找到新视频")
            
            # 分类之间的延迟
            time.sleep(2)
        
        # 总耗时
        total_elapsed_time = time.time() - start_time
        
        # 保存结果到主文件
        if all_new_video_data:
            saved_count = self.save_to_txt(all_new_video_data)
            
            # 打印摘要
            self.print_summary(all_new_video_data, saved_count, total_elapsed_time)
        else:
            print("\n未提取到任何新的视频数据。")
            print(f"总耗时: {total_elapsed_time:.1f} 秒")
            print("提示: 可能所有视频都已爬取过")
    
    def print_summary(self, all_new_video_data, total_new_videos, total_elapsed_time):
        """打印摘要信息"""
        print("\n" + "="*60)
        print("提取完成！结果摘要:")
        print("="*60)
        
        total_pages_crawled = len(CATEGORY_PAGES) * 30  # 每个分类30页
        
        # 读取主文件的最后一个序号
        last_index = self.get_last_index_from_file()
        start_index = last_index - total_new_videos + 1
        
        for category_name, video_data in all_new_video_data:
            print(f"\n{category_name}:")
            print(f"  • 新增视频: {len(video_data)} 个")
            print(f"  • 爬取页数: 30 页")
            
            # 显示前2个示例（带序号）
            if video_data:
                category_start = start_index
                for i, video in enumerate(video_data[:2]):
                    indexed_title = f"{category_start + i}.{video['title']}"
                    title_display = indexed_title[:40] + "..." if len(indexed_title) > 40 else indexed_title
                    print(f"  示例{i+1}: {title_display}")
                if len(video_data) > 2:
                    print(f"  ... 以及另外 {len(video_data)-2} 个视频")
            
            start_index += len(video_data)
        
        print(f"\n" + "="*60)
        print(f"总计: {total_new_videos} 个新视频")
        print(f"总爬取页数: {total_pages_crawled} 页 ({len(CATEGORY_PAGES)}个分类 × 30页)")
        print(f"总耗时: {total_elapsed_time:.1f} 秒")
        print(f"平均每页耗时: {total_elapsed_time/total_pages_crawled:.1f} 秒")
        print(f"输出文件: ./tv/DJMV.txt")
        print(f"累计已爬取视频: {len(self.crawled_ids)} 个")
        print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)

def main():
    """主函数"""
    try:
        crawler = VideoCrawler()
        crawler.run(max_pages_per_category=30)
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"\n程序运行出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()