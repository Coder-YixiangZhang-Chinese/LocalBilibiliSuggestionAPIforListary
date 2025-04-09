import requests
from flask import Flask, request, jsonify
import socket
import sys

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0
if is_port_in_use(60000):
    print("服务已经在运行。")
    sys.exit(0)  # 如果端口已经被占用，则退出

app = Flask(__name__)
# 各站搜索建议API接口
BILIBILI_API_URL = "https://s.search.bilibili.com/main/suggest"
TAOBAO_API_URL = "https://suggest.taobao.com/sug"
JD_API_URL = "https://dd-search.jd.com/"
DOUYIN_API_URL = "https://www.douyin.com/aweme/v1/web/search/sug/"
XIAOHONGSHU_API_URL = "https://edith.xiaohongshu.com/api/sns/web/v1/search/recommend"

def get_taobao_suggestions(query):
    params = {
        'code': 'utf-8',
        'q': query
    }
    response = requests.get(TAOBAO_API_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        return [item[0] for item in data.get("result", [])]
    else:
        return []
def get_bilibili_suggestions(query):
    params = {
        'func': 'suggest',
        'suggest_type': 'accurate',
        'sub_type': 'tag',
        'main_ver': 'v1',
        'term': query,  # 用户输入的搜索词
    }
    response = requests.get(BILIBILI_API_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        suggestions = [item['value'] for item in data['result']['tag']]  # 提取建议词
        return suggestions
    else:
        return []
def get_jd_suggestions(query):
    params = {
        'key': query,
        'terminal': 'h5',
    }

    response = requests.get(JD_API_URL, params=params)
    if response.status_code == 200:
        data = response.json()

        suggestions = []
        for item in data:
            keyword = item.get("keyword")
            if 'tag' in item:
                for tag in item['tag']:
                    tag_query = tag.get('tagsearchquery')
                    if tag_query:
                        suggestions.append({'keyword': keyword, 'query': tag_query})
            else:
                suggestions.append({'keyword': keyword})
        
        # 在返回 suggestions 之前，删除列表中的最后一项
        if suggestions:  # 如果 suggestions 不为空
            suggestions.pop()
        
        return suggestions
    else:
        return []
def get_douyin_suggestions(query):
    params = {
        'keyword': query,
        'device_platform': 'webapp',
        'aid': '6383',
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Referer": "https://www.douyin.com/",
        "Accept": "application/json, text/plain, */*",
    }

    response = requests.get(DOUYIN_API_URL, params=params, headers=headers)
    if response.status_code == 200:
        data = response.json()
        suggestions = [item["content"] for item in data.get("sug_list", [])]  # 提取建议词
        return suggestions
    else:
        return []
def get_xiaohongshu_suggestions(query):
    params = {
        'keyword': query
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "zh-CN,zh-TW;q=0.9,zh;q=0.8,en-GB;q=0.7,en;q=0.6",
        "cookie": "abRequestId=2ef87666-ac59-537d-b3ad-cec6cf757ded; webBuild=4.62.2; xsecappid=xhs-pc-web; loadts=1744222925157; a1=1961bc9b165w71w9xfidqfijcwhpc4m3kva21tkzp50000473155; webId=235178c8f753134e9044bcadd1ce93f0; acw_tc=0a50897517442229263708027edb7397f400aaacc75deccef704cbb050269b; web_session=030037a0c5eeba70b57383fc8e204a2ead6983; gid=yjKyDSjDdjTiyjKyDSjDyh9TK2EWyEjCi3fA0uUi3VSExJ28US46qy8884Wqy228yffY2YK8; unread={%22ub%22:%22641be7c5000000001303c66c%22%2C%22ue%22:%2267da42a6000000001d0044ed%22%2C%22uc%22:49}; websectiga=82e85efc5500b609ac1166aaf086ff8aa4261153a448ef0be5b17417e4512f28; sec_poison_id=ad205a50-ae18-4437-95f5-dfc6e0db72b9"
    }

    response = requests.get(XIAOHONGSHU_API_URL, params=params, headers=headers)

    if response.status_code == 200:
        data = response.json()
        # 获取sug_items中的"text"字段
        suggestions = [item["text"] for item in data.get("data", {}).get("sug_items", [])]
        print(suggestions)
        return suggestions
    else:
        return []

#不同平台分别路由
@app.route('/suggest/bilibili', methods=['GET'])
def bilibili_suggestions():
    query = request.args.get('q')  # 获取查询关键词
    if not query:
        return jsonify({"error": "Missing query parameter"}), 400
    
    suggestions = get_bilibili_suggestions(query)
    return jsonify([query, suggestions, [], {"google:suggestsubtypes": [[512] * len(suggestions)]}])

@app.route('/suggest/taobao', methods=['GET'])
def taobao_suggest():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Missing query parameter 'q'"}), 400

    suggestions = get_taobao_suggestions(query)

    subtypes = [[512] for _ in suggestions]

    output = [
        query,
        suggestions,
        [],
        {"google:suggestsubtypes": subtypes}
    ]

    return jsonify(output)

@app.route('/suggest/jd', methods=['GET'])
def jd_suggest():
    query = request.args.get('q')  # 获取查询关键词
    if not query:
        return jsonify({"error": "Missing query parameter"}), 400

    suggestions = get_jd_suggestions(query)

    # 构建最终的建议格式，按照你提供的结构进行返回
    output = [
        query,
        [item['keyword'] for item in suggestions],
        [],  # 如果有更多扩展数据，可以在这里添加
        {"google:suggestsubtypes": [[512] for _ in suggestions]}  # 假设的类型子集
    ]
    return jsonify(output)

@app.route("/suggest/douyin", methods=["GET"])
def douyin_suggest():
    query = request.args.get('q')
    if not query:
        return jsonify({"error": "Missing query parameter"}), 400
    suggestions = get_douyin_suggestions(query)
    
    output = [
        query, 
        suggestions, 
        [], 
        {"google:suggestsubtypes": [[512] for _ in suggestions]}]
    return jsonify(output)

@app.route('/suggest/xiaohongshu', methods=['GET'])
def xiaohongshu_suggest():
    query = request.args.get('q')  # 获取查询参数
    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400

    suggestions = get_xiaohongshu_suggestions(query)
    output = [
        query,
        suggestions,
        [],
        {"google:suggestsubtypes": [[512] for _ in suggestions]}]
    return jsonify(output)

if __name__ == '__main__':
    # 运行Flask服务
    app.run(host='0.0.0.0', port=60000)
