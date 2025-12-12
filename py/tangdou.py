import requests
import json
from urllib.parse import urljoin
import sys
import warnings

def main():
    # 抑制InsecureRequestWarning警告
    warnings.filterwarnings("ignore", category=requests.packages.urllib3.exceptions.InsecureRequestWarning)
    
    # 获取页码参数，默认为1
    pg = sys.argv[1] if len(sys.argv) > 1 else '1'
    
    # API接口URL
    api_url = f"https://api-h5.tangdou.com/mtangdou/home/feed?page={pg}&num=&uuid="
    
    # 发送请求
    try:
        response = requests.get(api_url, verify=False)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(json.dumps({"data": {"list": []}}))
        return
    
    # 解析JSON
    data = response.json()
    
    # 检查是否请求成功
    if data.get("code") != 0 or "data" not in data:
        print(json.dumps({"data": {"list": []}}))
        return
    
    # 转换数据格式
    video_list = []
    for item in data["data"]:
        cover = item.get("cover", "")
        if not cover.startswith(("http://", "https://")):
            cover = urljoin("https://www.tangdou.com", cover)
        
        video_item = {
            "vod_id": str(item.get("vid", "")),
            "vod_name": item.get("title", ""),
            "vod_pic": cover,
            "vod_content": "沧海笑内置",
            "vod_play_url": f"https://www.tangdou.com/play/?vid={item.get('vid', '')}"
        }
        video_list.append(video_item)
    
    result = {
        "data": {
            "list": video_list
        }
    }
    
    print(json.dumps(result, ensure_ascii=False, separators=(',', ':')))

if __name__ == "__main__":
    main()