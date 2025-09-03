var rule = {
    title: '大米星球',
    host: 'https://www.gaoyilatex.com/',
    url: '/mo-y9xek/fyclass/fypage',
    searchUrl: '/se-y9xek/**-fypage',
    searchable: 2,//是否启用全局搜索,
    quickSearch: 0,//是否启用快速搜索,
    filterable: 0,//是否启用分类筛选,
    headers: {
                'User-Agent':'MOBILE_UA', // "Cookie":"searchneed=ok"
            },
    timeout: 5000,
    class_please: '.dropdown-box ul li;a&&Text;a&&href;.*/(.*?).html',
    class_name:'电影&电视剧&动漫&综艺',
  class_url:'5738&5749&5758&5767',
  tab_exclude: '*',
    play_parse: true,
    lazy: `js:
            if(/\\.(m3u8|mp4)/.test(input)){
                input = {parse:0,url:input}
            }else{
                if(rule.parse_url.startsWith('json:')){
                    let purl = rule.parse_url.replace('json:','')+input;
                    let html = request(purl);
                    input = {parse:0,url:JSON.parse(html).url}
                }else{
                    input= rule.parse_url+input; 
                }
            `,
    limit: 6,
    推荐: '.stui-vodlist;a&&data-original;a&&title;a&&href',
    double: true,
一级: '.stui-vodlist__thumb.lazyload;a&&title;a&&data-original;h4&&Text;a&&href',
    double: true,
    二级: {
                title: "h4&&Text",
                img: "a&&data-original",
                desc: '.stui-content__detail&&p:eq(1)&&Text;.stui-content__detail&&p:eq(2)&&Text;.stui-content__detail&&p:eq(3)&&Text;.stui-content__detail&&p:eq(4)&&Text;.stui-content__detail&&p:eq(5)&&Text',
                content: ".stui-content__detail&&p:eq(5)&&Text",
                tabs:'js:TABS = ["线路1"]',
                lists: "body&&.btn.btn-primary.btn-primary-ph"
            },
            搜索: '.stui-vodlist&&li;a&&title;a&&data-original;.stui-vodlist__detail&&p:eq(0)&&Text;a&&href',
}