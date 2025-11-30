import requests
import json
import os

def get_video_info(page):
    """获取指定页的视频信息"""
    url = f"https://api-h5.tangdou.com/mtangdou/home/feed?page={page}&num=20&uuid="
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": "https://www.tangdou.com/",
        "Accept": "application/json, text/plain, */*"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
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
        
        return videos
    except Exception as e:
        print(f"获取第{page}页数据失败: {str(e)[:100]}")
        return []

def load_existing_ids(file_path):
    """加载已存在的视频ID用于去重"""
    existing_ids = set()
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if "-" in line and "," in line:
                    url_part = line.split(",")[-1].strip()
                    if "id=" in url_part:
                        video_id = url_part.split("id=")[-1]
                        existing_ids.add(video_id)
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
        with open(file_path, "a", encoding="utf-8") as f:
            f.writelines(new_entries)
        print(f"成功添加{len(new_entries)}条新视频信息")
    else:
        print("没有新的视频信息需要添加")
    
    return start_index, len(new_entries)

def clean_video_titles(input_file):
    """清洗视频标题中的特定文本和格式问题"""
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

def main():
    output_file = "/storage/emulated/0/@内置接口学习/自制接口/zyck/tv/糖豆.txt"
    page = 1
    start_index = 1
    total_added = 0
    max_pages = 180
    
    # 初始化文件
    if not os.path.exists(output_file):
        with open(output_file, "w", encoding="utf-8") as f:
            pass
    else:
        # 获取起始序号
        with open(output_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            if lines:
                last_line = lines[-1].strip()
                if "-" in last_line:
                    start_index = int(last_line.split("-")[0]) + 1
    
    print(f"开始获取糖豆广场舞视频信息，起始序号: {start_index}")
    
    # 数据抓取
    while page <= max_pages:
        print(f"\n===== 获取第{page}页数据 =====")
        videos = get_video_info(page)
        
        print(f"第{page}页有效视频数据: {len(videos)}条")
        if videos:
            start_index, added = save_videos_to_file(output_file, videos, start_index)
            total_added += added
        
        page += 1
    
    # 数据清洗（不备份文件）
    print(f"\n开始数据清洗...")
    clean_video_titles(output_file)
    
    print(f"\n任务完成，结果已保存至: {output_file}")
    print(f"本次新增数据总量: {total_added}条")
    print(f"生成成功")

if __name__ == "__main__":
    main()
