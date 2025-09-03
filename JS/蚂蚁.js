var rule = {
    title: '蚂蚁视频',
    host: 'https://www.xmyxjx.com',
    url: '/vodshow/fyclass--------fypage---.html',
    searchUrl: 'vodsearch/**----------fypage---.html',
    searchable: 2,//是否启用全局搜索,
    quickSearch: 0,//是否启用快速搜索,
    filterable: 0,//是否启用分类筛选,
    headers: {
                'User-Agent':'MOBILE_UA', // "Cookie":"searchneed=ok"
            },
    编码: 'utf-8',
    timeout: 5000,
    class_name:'电影&电视剧&综艺&动漫',
 class_url:'1&2&3&4',
  tab_exclude: '*',
  tab_rename:{'':''},
    play_parse: true,
     lazy: `js:
    let html = request(input);
    let hconf = html.match(/r player_.*?=(.*?)</)[1];
    let json = JSON5.parse(hconf);
    let url = json.url;
    if (json.encrypt == '1') {
      url = unescape(url);
    } else if (json.encrypt == '2') {
      url = unescape(base64Decode(url));
    }
    if (/\\.(m3u8|mp4|m4a|mp3)/.test(url)) {
      input = {
        parse: 0,
        jx: 0,
        url: url,
      };
    } else {
      input;
    }`,
    limit: 6,
    double: true,
    推荐: '*',
    一级: '.col-lg-2.col-sm-3;a&&title;img&&data-original;.note.text-bg-r&&Text;a&&href',
    二级: $js.toString(() => {
        VOD = {};
        let html = request(input);
        VOD.vod_name = pdfh(html, ".text-overflow&&Text");
        VOD.vod_pic = pd(html, "img&&data-original");
        VOD.vod_year = pdfh(html, ".info.clearfix&&li:eq(6)&&Text");
        VOD.vod_area = pdfh(html, ".info.clearfix&&li:eq(4)&&Text");
        VOD.type_name = pdfh(html, ".module-info-tag-link:eq(2)&&Text");
        VOD.vod_actor = pdfh(html, ".info.clearfix&&li:eq(0)&&Text");
        VOD.vod_director = pdfh(html, ".info.clearfix&&li:eq(3)&&Text");
        VOD.vod_remarks = "";
        VOD.vod_content = pdfh(html, ".vod-content&&Text");
        let playFrom = [];
        let playUrl = [];
        let tabs = pdfa(html, ".gico.wolong");
        tabs.forEach((it, index) => {
            playFrom.push(pdfh(it, 'a&&Text'));
            let playTag = ".playlist&&ul:eq(" + index + ") li";
            let tags = pdfa(html, playTag);
            let mapUrl = tags.map((tag) => {
                let title = pdfh(tag, "a&&Text").trim();
                let purl = pdfh(tag, "a&&href");
                return title + "$" + rule.host + urlencode(purl);
            });
            playUrl.push(mapUrl.join("#"))
        });
        VOD.vod_play_from = playFrom.join("$$$");
        VOD.vod_play_url = playUrl.join("$$$");
    }),
    搜索:'.details-info-min.col-md-12;a&&title;img&&data-original;.col-xs-12.text&&Text;a&&href',
        }