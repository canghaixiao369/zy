# -*- coding: utf-8 -*-
import base64
import sys
import time
import json
import requests
import re
from bs4 import BeautifulSoup

sys.path.append('..')
from base.spider import Spider

class Spider(Spider):

    def getName(self):
        return "IPTV345"

    def init(self, extend):
        self.extend = extend
        try:
            self.extendDict = json.loads(extend)
        except:
            self.extendDict = {}
        proxy = self.extendDict.get('proxy')
        if proxy:
            self.proxy = proxy
            self.is_proxy = True
        else:
            self.is_proxy = False

    # 壳子直播入口：返回纯 m3u 文本
    def liveContent(self, url):
        channel_list = ["#EXTM3U"]
        base_url = "https://iptv345.com/"
        fenlei = ["央视,ys", "卫视,ws", "综合,itv", "体育,ty", "电影,movie", "其他,other"]

        for group in fenlei:
            try:
                group_name, group_id = group.split(",")
                api_url = f"{base_url.rstrip('/')}/?tid={group_id}"
                rsp = self.fetch(api_url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Referer': base_url
                }, timeout=15)
                soup = BeautifulSoup(rsp.text, 'html.parser')
                ul_tag = soup.find('ul', {
                    'data-role': 'listview',
                    'data-inset': 'true',
                    'data-divider-theme': 'a'
                })
                if not ul_tag:
                    continue
                for li in ul_tag.find_all('li'):
                    a_tag = li.find('a')
                    if not a_tag:
                        continue
                    channel_path = a_tag.get('href', '').strip()
                    if not channel_path:
                        continue
                    full_url = requests.compat.urljoin(base_url, channel_path)
                    name = a_tag.text.strip()
                    entry = (f'#EXTINF:-1 tvg-id="{name}" tvg-name="{name}" '
                             f'tvg-logo="https://logo.doube.eu.org/{name}.png" '
                             f'group-title="{group_name}",{name}\n'
                             f'{full_url}')
                    channel_list.append(entry)
            except Exception as e:
                print(f"[{group}] 抓取失败: {e}")
                continue
        return '\n'.join(channel_list)

    # 代理 m3u8
    def proxyM3u8(self, params):
        pid = params['pid']
        a, b, c = pid.split(',')
        timestamp = int(time.time() - 1620000000)
        t = timestamp
        m3u8_text = (f'#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-TARGETDURATION:8\n'
                     f'#EXT-X-MEDIA-SEQUENCE:{timestamp}\n')
        for i in range(10):
            url = (f'https://ntd-tgc.cdn.hinet.net/live/pool/{a}/litv-pc/{a}-avc1_6000000={b}-mp4a_134000_zho={c}'
                   f'-begin={t}0000000-dur=80000000-seq={timestamp}.ts')
            if self.is_proxy:
                url = f'http://127.0.0.1:9978/proxy?do=py&type=ts&url={self.b64encode(url)}'
            m3u8_text += f'#EXTINF:8,\n{url}\n'
            timestamp += 1
            t += 8
        return [200, 'application/vnd.apple.mpegurl', m3u8_text]

    # 代理 ts
    def get_ts(self, params):
        url = self.b64decode(params['url'])
        rsp = self.fetch(url, stream=True, timeout=15)
        return [206, 'video/MP2T', rsp.content, {'Cache-Control': 'no-cache'}]

    # base64 工具
    def b64encode(self, data):
        return base64.b64encode(data.encode('utf-8')).decode('utf-8')

    def b64decode(self, data):
        return base64.b64decode(data.encode('utf-8')).decode('utf-8')

    # 壳子规范其它接口
    def localProxy(self, params):
        if params.get('type') == 'm3u8':
            return self.proxyM3u8(params)
        if params.get('type') == 'ts':
            return self.get_ts(params)
        return [302, 'text/plain', None, {'Location': 'https://sf1-cdn-tos.huoshanstatic.com/obj/media-fe/xgplayer_doc_video/mp4/xgplayer-demo-720p.mp4'}]

    def homeContent(self, filter): return {}
    def homeVideoContent(self): return {}
    def categoryContent(self, tid, pg, filter, extend): return {}
    def detailContent(self, ids): return {}
    def searchContent(self, key, quick, pg='1'): return {}
    def isVideoFormat(self, url): pass
    def manualVideoCheck(self): pass
    def destroy(self): return ''
