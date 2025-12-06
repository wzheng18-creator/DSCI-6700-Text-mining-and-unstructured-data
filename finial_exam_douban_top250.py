# 1. 拿到页面代码
# 2. 编写正则，提取数据
# 3. 保存数据（JSON + CSV）

import requests
import re
import json
import csv
import time


def build_urls():
    """构造所有分页 URL"""
    urls = []
    for start in range(0, 250, 25):  # 0,25,50,...,225
        url = f"https://movie.douban.com/top250?start={start}&filter="
        urls.append(url)
    return urls


def get_html(url, headers):
    """请求单个页面，返回 HTML 字符串"""
    resp = requests.get(url, headers=headers)
    resp.encoding = "utf-8"
    return resp.text


def parse_page(content, obj):
    """
    用正则解析一页 HTML
    返回：当前页面的电影列表（list[dict]）
    """
    movies = []

    result = obj.finditer(content)
    for i in result:
        # 基础字段
        name = i.group("name").strip()
        year_field = i.group("year").strip()
        country_field = i.group("country").strip()
        sort_field = i.group("sort").strip()
        score = i.group("score").strip()
        num = i.group("num").strip()
        D_raw = i.group("D").strip()

        # ====== 年份：提取所有 4 位数字，取最后一个 ======
        years = re.findall(r"\d{4}", year_field)
        year = years[-1] if years else ""

        # ====== 国家：只取主要的 ======
        country = country_field.split()[0]

        # ====== 影片类型：只取第一个 ======
        types = sort_field.split()[0]

        # ====== 导演：中文名 + 英文数量统计 ======
        # 提取中文导演名
        names_cn = re.findall(r'[\u4e00-\u9fa5·]+', D_raw)
        # 提取英文导演名（只用于计数）
        english_names = re.findall(r"[A-Za-z][A-Za-z ]+[A-Za-z]", D_raw)

        name_en = 0
        if len(names_cn) == 0:
            # 没有中文名（比如：Chris Columbus）
            D1 = D_raw
            D2 = ""
            name_en = len(english_names)
        elif len(names_cn) == 1:
            D1 = names_cn[0]
            D2 = ""
        else:
            D1 = names_cn[0]
            D2 = names_cn[1]  # 只取前两个

        Sum_D = len(names_cn) + name_en

        movie = {
            "name": name,
            "D1": D1,
            "D2": D2,
            "Sum_director": Sum_D,
            "year": year,
            "country": country,
            "types": types,
            "score": score,
            "num": num,
        }

        movies.append(movie)

    return movies


def save_json(filename, data):
    """保存为 JSON 文件"""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"已保存 JSON 文件：{filename}")


def save_csv(filename, data):
    """从 list[dict] 直接保存为 CSV 文件"""
    fieldnames = ["name", "D1", "D2", "Sum_director",
                  "year", "country", "types", "score", "num"]

    with open(filename, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

    print(f"已保存 CSV 文件：{filename}")


def main():

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/116.0.5845.97 Safari/537.36 Core/1.116.569.400 QQBrowser/19.7.6765.400"
        )
    }

    obj = re.compile(
        r'<div class="item">.*?'
        r'<span class="title">(?P<name>.*?)</span>.*?'
        r'<p.*?>.*?'
        r'导演:(?P<D>.*?)&nbsp.*?<br>'
        r'(?P<year>.*?)&nbsp;/&nbsp;(?P<country>.*?)&nbsp;/&nbsp;(?P<sort>.*?)</p>'
        r'.*?<span class="rating_num" property="v:average">(?P<score>.*?)</span>'
        r'.*?<span>(?P<num>.*?)人评价</span>',
        re.S
    )

    urls = build_urls()
    all_movies = []

    for url in urls:
        print("正在爬取：", url)
        html = get_html(url, headers)
        page_movies = parse_page(html, obj)
        all_movies.extend(page_movies)   # 把这一页的电影加到总列表中

        print(f"当前总共爬取到 {len(all_movies)} 条电影记录")
        time.sleep(1)  # 避免过于频繁请求

    # 打印第一条做一下检查
    if all_movies:
        print("示例数据：", all_movies[0])

    # 保存 JSON
    json_filename = "top250.json"
    save_json(json_filename, all_movies)

    # 保存 CSV
    csv_filename = "top250.csv"
    save_csv(csv_filename, all_movies)



if __name__ == "__main__":
    main()
