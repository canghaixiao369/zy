import requests
import time
from datetime import datetime
import json


def fetch_tangdou_videos_complete():
    """
    完整获取糖豆广场舞视频数据，模拟加载更多直到无新数据
    """
    base_url = "https://api-h5.tangdou.com/mtangdou/home/feed"
    all_videos = []
    seen_ids = set()
    page_count = 0
    consecutive_empty = 0  # 连续空页计数器
    max_consecutive_empty = 3  # 最大连续空页数
    max_pages = 180  # 最多获取180页

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://www.tangdou.com/',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Origin': 'https://www.tangdou.com',
    }

    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 开始完整获取糖豆广场舞视频数据...")
    print(f"模拟'点击加载更多'行为，最多获取{max_pages}页，或直到无新数据")

    start_time = time.time()

    try:
        while page_count < max_pages and consecutive_empty < max_consecutive_empty:
            page_count += 1
            params = {
                'page': page_count,
                'num': 20,  # 每页数量适中
                'uuid': '',
                'timestamp': int(time.time() * 1000)
            }

            print(f"\n正在获取第 {page_count}/{max_pages} 页...", end=" ")

            try:
                response = requests.get(base_url, params=params, headers=headers, timeout=20)
                response.raise_for_status()
                data = response.json()

                if data.get('code') != 0:
                    print(f"API返回错误: {data.get('msg', '未知错误')}")
                    consecutive_empty += 1
                    continue

                videos = data.get('data', [])

                if not videos:
                    print("本页无数据")
                    consecutive_empty += 1
                    continue

                # 重置连续空页计数器
                consecutive_empty = 0

                page_videos = []
                new_videos_count = 0
                duplicate_count = 0

                for video in videos:
                    video_id = str(video.get('vid', ''))
                    video_title = video.get('title', '').strip()

                    if not video_id or not video_title:
                        continue

                    # 清理标题中的特殊字符
                    video_title = video_title.replace(',', '，').replace('\n', ' ').replace('\r', ' ')

                    # 检查是否重复
                    if video_id in seen_ids:
                        duplicate_count += 1
                        continue

                    # 生成最终URL
                    final_url = f"http://zjk.xozv.top/糖豆.php?id={video_id}"
                    video_record = f"{video_title},{final_url}"

                    page_videos.append(video_record)
                    seen_ids.add(video_id)
                    new_videos_count += 1

                all_videos.extend(page_videos)

                print(f"获取 {len(videos)} 个视频，新增 {new_videos_count} 个，重复 {duplicate_count} 个")
                print(f"当前总计: {len(all_videos)} 个唯一视频")

                # 显示本页前几个新视频标题作为参考
                if page_videos:
                    print("本页新增视频示例:")
                    for i, video in enumerate(page_videos[:3]):
                        title = video.split(',')[0]
                        print(f"  {i + 1}. {title[:50]}{'...' if len(title) > 50 else ''}")

                # 如果本页数据量较少，可能接近末尾
                if len(videos) < params['num']:
                    print(f"注意: 本页数据量({len(videos)})小于请求量({params['num']})，可能接近数据末尾")

            except requests.exceptions.RequestException as e:
                print(f"网络请求失败: {e}")
                consecutive_empty += 1
            except json.JSONDecodeError as e:
                print(f"JSON解析失败: {e}")
                consecutive_empty += 1

            # 延迟控制，避免请求过快
            time.sleep(1.5)

            # 每10页显示一次进度
            if page_count % 10 == 0:
                elapsed = time.time() - start_time
                print(
                    f"\n=== 进度报告: 已获取 {page_count}/{max_pages} 页，{len(all_videos)} 个视频，耗时 {elapsed:.1f} 秒 ===")

        # 退出循环的原因
        if page_count >= max_pages:
            print(f"\n已达到最大页数限制 {max_pages} 页")
        elif consecutive_empty >= max_consecutive_empty:
            print(f"\n连续 {max_consecutive_empty} 页无新数据，停止获取")
        else:
            print("\n数据获取完成")

    except KeyboardInterrupt:
        print(f"\n用户中断，已获取 {len(all_videos)} 个视频")
    except Exception as e:
        print(f"\n获取过程中发生未知错误: {e}")

    end_time = time.time()
    total_time = end_time - start_time

    print(f"\n数据获取完成！")
    print(f"总页数: {page_count}")
    print(f"总视频数: {len(all_videos)}")
    print(f"总耗时: {total_time:.2f} 秒")
    print(f"平均每页: {total_time / page_count:.2f} 秒" if page_count > 0 else "")

    return all_videos


def save_to_txt(videos_list, filename=None):
    """
    将视频列表保存到txt文件
    """
    if not videos_list:
        print("没有数据可保存")
        return

    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"/storage/emulated/0/@内置接口学习/自制接口/zyck/tv/糖豆.txt"

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            # 写入文件头
            f.write(f"# 糖豆广场舞视频数据 - 采集时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# 总视频数: {len(videos_list)}\n")
            f.write("# 格式: 视频标题,视频URL\n")

            for video in videos_list:
                f.write(video + '\n')

        print(f"数据已保存到 {filename}，共 {len(videos_list)} 条记录")

        # 显示统计信息
        print("\n数据统计:")
        print(f"  总视频数: {len(videos_list)}")

        # 显示前几条记录作为示例
        print("\n前5条记录示例:")
        for i, video in enumerate(videos_list[:5]):
            title, url = video.split(',', 1)
            print(f"  {i + 1}. 标题: {title}")
            print(f"     链接: {url}")

    except Exception as e:
        print(f"保存文件时出错: {e}")


def analyze_videos(videos_list):
    """
    简单分析视频数据
    """
    if not videos_list:
        return

    print("\n数据分析:")
    print(f"总视频数量: {len(videos_list)}")

    # 分析标题长度
    title_lengths = [len(video.split(',')[0]) for video in videos_list]
    avg_title_length = sum(title_lengths) / len(title_lengths)
    print(f"平均标题长度: {avg_title_length:.1f} 字符")

    # 找出最长的标题
    longest_idx = title_lengths.index(max(title_lengths))
    longest_title = videos_list[longest_idx].split(',')[0]
    print(f"最长标题: {longest_title[:80]}{'...' if len(longest_title) > 80 else ''}")


# 主程序
if __name__ == "__main__":
    print("糖豆广场舞视频完整采集程序")
    print("=" * 50)

    # 获取所有视频数据
    videos_data = fetch_tangdou_videos_complete()

    # 保存到txt文件
    if videos_data:
        save_to_txt(videos_data)
        analyze_videos(videos_data)
        print("\n程序执行完毕！")
    else:
        print("未获取到任何视频数据")