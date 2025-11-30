import requests
import json
import os
import time
import random
from urllib.parse import urlparse

def get_video_info(page, session):
    """获取指定页的视频信息"""
    url = f"https://api-h5.tangdou.com/mtangdou/home/feed?page={page}&num=20&uuid="
    
    # 更真实的请求头
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.tangdou.com/",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache"
    }
    
    try:
        # 添加随机延迟，避免请求过快
        time.sleep(random.uniform(1, 3))
        
        # 使用session保持连接，禁用SSL验证
        response = session.get(
            url, 
            headers=headers, 
            timeout=15,
            verify=False  # 禁用SSL验证
        )
        response.raise_for_status()
        
        # 检查响应内容
        if not response.text.strip():
            print(f"第{page}页响应内容为空")
            return []
            
        data = response.json()
        
        # 检查API响应结构
        if "data" not in data:
            print(f"第{page}页响应格式异常: {data}")
            return []
            
        items = data.get("data", [])
        
        videos = []
        for item in items:
            if isinstance(item, dict):
                video_id = item.get("vid")
                title = item.get("title", "") \
                    .replace(",", "，") \
                    .replace("\n", "") \
                    .replace("\r", "") \
                    .replace("神灵见证", "") \
                    .replace("正面演示", "")
                if video_id and title:
                    videos.append((str(video_id), title))
        
        print(f"第{page}页成功获取 {len(videos)} 个视频")
        return videos
        
    except requests.exceptions.RequestException as e:
        print(f"第{page}页网络请求失败: {str(e)}")
        return []
    except json.JSONDecodeError as e:
        print(f"第{page}页JSON解析失败: {str(e)}")
        print(f"响应内容: {response.text[:200]}...")
        return []
    except Exception as e:
        print(f"第{page}页未知错误: {str(e)}")
        return []

def load_existing_ids(file_path):
    """加载已存在的视频ID用于去重"""
    existing_ids = set()
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    if "-" in line and "," in line:
                        url_part = line.split(",")[-1].strip()
                        if "id=" in url_part:
                            video_id = url_part.split("id=")[-1]
                            existing_ids.add(video_id)
        except Exception as e:
            print(f"读取现有文件失败: {e}")
    return existing_ids

def save_videos_to_file(file_path, new_videos, start_index=1):
    """保存视频信息到TXT文件，支持增量更新"""
    existing_ids = load_existing_ids(file_path)
    new_entries = []
    
    for video_id, title in new_videos:
        if video_id not in existing_ids:
            entry = f"{start_index}-{title},http://zjk.xozv.top/糖豆.php?id={video_id}\n"
            new_entries.append(entry)
            start_index += 1
            existing_ids.add(video_id)
    
    if new_entries:
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, "a", encoding="utf-8") as f:
            f.writelines(new_entries)
        print(f"成功添加{len(new_entries)}条新视频信息")
    else:
        print("没有新的视频信息需要添加")
    
    return start_index, len(new_entries)

def clean_video_titles(input_file):
    """清洗视频标题中的特定文本和格式问题"""
    if not os.path.exists(input_file):
        print("清洗失败：文件不存在")
        return input_file
        
    try:
        cleaned_lines = []
        current_index = 1  # 重置序号计数器
        
        with open(input_file, "r", encoding="utf-8") as f:
            for line in f:
                # 1. 删除包含"不正确"的整行
                if "不正确" in line:
                    continue
                    
                # 2. 移除指定关键词
                cleaned_line = line \
                    .replace("正面演示", "") \
                    .replace("第四节", "") \
                    .replace("\n", "") \
                    .replace("\r", "")
                
                # 3. 处理序号问题，重新生成正确序号
                if "-" in cleaned_line and "," in cleaned_line:
                    # 提取标题和URL部分
                    title_part = cleaned_line.split(",")[0].split("-", 1)[1] if "-" in cleaned_line.split(",")[0] else cleaned_line.split(",")[0]
                    url_part = cleaned_line.split(",")[-1]
                    
                    # 生成新行
                    new_line = f"{current_index}-{title_part},{url_part}\n"
                    cleaned_lines.append(new_line)
                    current_index += 1
        
        # 保存清洗后的结果
        with open(input_file, "w", encoding="utf-8") as f:
            f.writelines(cleaned_lines)
        
        print(f"清洗完成，共处理 {len(cleaned_lines)} 条记录")
        return input_file
    except Exception as e:
        print(f"清洗过程出错: {e}")
        return input_file

def test_connection(session):
    """测试网络连接"""
    test_urls = [
        "https://api-h5.tangdou.com/mtangdou/home/feed?page=1&num=20&uuid=",
        "https://www.tangdou.com/"
    ]
    
    for test_url in test_urls:
        try:
            response = session.get(test_url, timeout=10, verify=False)
            print(f"连接测试 {test_url}: 状态码 {response.status_code}")
            if response.status_code == 200:
                return True
        except Exception as e:
            print(f"连接测试失败 {test_url}: {e}")
    
    return False

def main():
    # 修改为相对路径，避免路径问题
    output_file = "./tv/糖豆.txt"
    
    # 创建session对象，保持会话
    session = requests.Session()
    
    # 禁用SSL警告
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    print("开始网络连接测试...")
    if not test_connection(session):
        print("网络连接测试失败，请检查网络环境")
        return
    
    page = 1
    start_index = 1
    total_added = 0
    max_pages = 50  # 减少页数，避免被封
    
    # 初始化文件
    if not os.path.exists(output_file):
        with open(output_file, "w", encoding="utf-8") as f:
            pass
        print("创建新文件")
    else:
        # 获取起始序号
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                if lines:
                    last_line = lines[-1].strip()
                    if "-" in last_line:
                        start_index = int(last_line.split("-")[0]) + 1
            print(f"找到现有文件，共 {len(lines)} 行，起始序号: {start_index}")
        except Exception as e:
            print(f"读取现有文件失败: {e}")
            start_index = 1
    
    print(f"开始获取糖豆广场舞视频信息...")
    
    # 数据抓取
    consecutive_empty = 0  # 连续空页计数器
    
    while page <= max_pages and consecutive_empty < 3:  # 连续3页为空则停止
        print(f"\n===== 获取第{page}页数据 =====")
        videos = get_video_info(page, session)
        
        if not videos:
            consecutive_empty += 1
            print(f"第{page}页无数据，连续空页数: {consecutive_empty}")
        else:
            consecutive_empty = 0  # 重置计数器
            start_index, added = save_videos_to_file(output_file, videos, start_index)
            total_added += added
        
        page += 1
        
        # 每5页休息一下
        if page % 5 == 0:
            rest_time = random.uniform(5, 10)
            print(f"已处理{page}页，休息{rest_time:.1f}秒...")
            time.sleep(rest_time)
    
    # 数据清洗
    if total_added > 0:
        print(f"\n开始数据清洗...")
        clean_video_titles(output_file)
    
    print(f"\n任务完成，结果已保存至: {output_file}")
    print(f"本次新增数据总量: {total_added}条")
    print(f"共处理 {page-1} 页数据")

if __name__ == "__main__":
    main()
