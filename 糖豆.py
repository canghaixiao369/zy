import requests
import json
import uuid
import time
import random
import os
from urllib.parse import urlencode

def get_tangdou_videos():
    session = requests.Session()
    
    # 更完整的请求头
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        "Referer": "https://www.tangdou.com/videos",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Origin": "https://www.tangdou.com",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "X-Requested-With": "XMLHttpRequest"
    })
    
    page = 1
    num = 100
    base_url = "https://api-h5.tangdou.com/mtangdou/home/feed"
    results = []
    seen_urls = set()
    
    # 防止无效循环的计数器
    empty_page_count = 0
    max_empty_pages = 3
    fail_count = 0
    max_fail_count = 5
    max_pages = 70
    
    try:
        print("开始初始化...")
        
        # 先访问主页获取必要Cookie
        home_response = session.get(
            "https://www.tangdou.com/videos", 
            timeout=10,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
            }
        )
        
        print(f"主页访问状态: {home_response.status_code}")
        
        time.sleep(random.uniform(2, 3))
        
        while (empty_page_count < max_empty_pages and 
               fail_count < max_fail_count and 
               page <= max_pages):
            
            current_uuid = str(uuid.uuid4())
            timestamp = int(time.time() * 1000)
            
            params = {
                "page": page,
                "num": num,
                "uuid": current_uuid,
                "timestamp": timestamp,
                "source": "h5",
                "version": "1.0.0"
            }
            
            session.headers.update({
                "Cookie": f"uuid={current_uuid}",
                "Referer": f"https://www.tangdou.com/videos?page={page}"
            })
            
            print(f"\n=== 正在请求第{page}页 ===")
            
            try:
                response = session.get(
                    base_url,
                    params=params,
                    timeout=20,
                    verify=True
                )
                
                print(f"响应状态码: {response.status_code}")
                print(f"响应内容长度: {len(response.text)}")
                
                if response.status_code == 403:
                    print("⚠️ 遇到403禁止访问，可能被反爬机制拦截")
                    fail_count += 1
                    time.sleep(random.uniform(10, 15))
                    continue
                elif response.status_code == 429:
                    print("⚠️ 请求过于频繁，被限流")
                    fail_count += 1
                    time.sleep(random.uniform(30, 60))
                    continue
                elif response.status_code != 200:
                    print(f"❌ 请求失败，状态码: {response.status_code}")
                    fail_count += 1
                    time.sleep(random.uniform(5, 8))
                    continue
                
                # 尝试解析JSON
                try:
                    data = response.json()
                    print(f"✅ JSON解析成功")
                except json.JSONDecodeError as e:
                    print(f"❌ JSON解析失败: {e}")
                    fail_count += 1
                    time.sleep(random.uniform(3, 5))
                    continue
                
                # 检查API返回码
                api_code = data.get("code")
                api_message = data.get("message", "无错误信息")
                
                if api_code is not None and api_code != 200:
                    print(f"❌ API返回错误: code={api_code}, message={api_message}")
                    fail_count += 1
                    time.sleep(random.uniform(5, 8))
                    continue
                
                # 获取数据
                feed_data = data.get("data", [])
                
                if not feed_data:
                    empty_page_count += 1
                    print(f"📭 第{page}页无数据，连续空页{empty_page_count}/{max_empty_pages}")
                    page += 1
                    time.sleep(random.uniform(2, 4))
                    continue
                else:
                    empty_page_count = 0
                    fail_count = 0
                    print(f"📊 获取到{len(feed_data)}条数据")
                
                # 提取视频信息
                page_items = 0
                duplicate_count = 0
                for index, item in enumerate(feed_data):
                    video_id = item.get("video_id") or item.get("vid") or item.get("id")
                    title = item.get("title", "").strip().replace(",", "，")
                    
                    if video_id and title:
                        video_url = f"http://zjk.xozv.top/糖豆.php?id={video_id}"
                        
                        # 检查是否重复
                        if video_url in seen_urls:
                            duplicate_count += 1
                            continue
                        
                        # 添加到结果和已见集合
                        results.append(f"{title},{video_url}")
                        seen_urls.add(video_url)
                        page_items += 1
                
                print(f"✅ 第{page}页处理完成，新增{page_items}条，跳过{duplicate_count}条重复，累计{len(results)}条")
                page += 1
                
                # 随机延迟，模拟人工操作
                delay = random.uniform(3, 6)
                print(f"⏳ 等待{delay:.1f}秒后继续...")
                time.sleep(delay)
                
            except requests.exceptions.Timeout:
                print(f"⏰ 第{page}页请求超时")
                fail_count += 1
                time.sleep(random.uniform(8, 12))
            except Exception as e:
                print(f"❌ 处理第{page}页时发生错误: {str(e)}")
                fail_count += 1
                time.sleep(random.uniform(3, 5))
        
        # 输出停止原因
        print("\n=== 采集结束 ===")
        if empty_page_count >= max_empty_pages:
            print(f"📭 已连续{max_empty_pages}页无数据，停止采集")
        elif fail_count >= max_fail_count:
            print(f"❌ 已连续失败{max_fail_count}次，停止采集")
        elif page > max_pages:
            print(f"📖 已达到最大页数限制{max_pages}页，停止采集")
        else:
            print("✅ 采集正常完成")
            
        print(f"📊 最终结果: 共处理{page-1}页，获取{len(results)}条去重后的视频")
    
    except Exception as e:
        print(f"💥 程序初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # 保存结果到tv文件夹
    if results:
        # 确保tv目录存在
        os.makedirs("tv", exist_ok=True)
        filename = "tv/糖豆.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(results))
        print(f"💾 数据已保存到 '{filename}'，共{len(results)}条去重后的记录")
        
        # 显示前几条结果作为样例
        print("\n📋 前5条结果样例:")
        for i, result in enumerate(results[:5]):
            print(f"  {i+1}. {result}")
    else:
        print("😞 未获取到任何数据")

if __name__ == "__main__":
    print("🚀 开始获取糖豆视频信息...")
    get_tangdou_videos()