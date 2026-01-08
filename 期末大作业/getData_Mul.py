import requests
import csv
import time
import random 
from bs4 import BeautifulSoup
import concurrent.futures
import re
import json
import urllib3

YEARS       = range(2025, 2026)  # 2025
BATCH_SIZE  = 500
CSV_PATH    = "asn_details_25.csv"
MAX_RETRIES = 5
USER_AGENTS = [# 设定模拟用户代理
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    " (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15"
    " (KHTML, like Gecko) Version/16.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:117.0) Gecko/20100101 Firefox/117.0",
]
ACCEPT_LANGS = ["en-US,en;q=0.9", "en-GB,en;q=0.8", "zh-CN,zh;q=0.9,en;q=0.8"]
HEADERS_BASE = {#设定来源页
    "Referer": "https://asn.flightsafety.org/database/"
}
BASE_LIST   = "https://asn.flightsafety.org/database/dblist.php"
BASE_DETAIL = "https://asn.flightsafety.org"
MAX_WORKERS = 8
href_re = re.compile(r'href="([^"]+)"')

session = requests.Session()#创建会话对象，从而支持持久的链接
session.verify = False  # 忽略SSL验证
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning) # 屏蔽掉红色安全警告
session.proxies = {#添加代理
    "http": "http://127.0.0.1:7897",
    "https": "http://127.0.0.1:7897"
}

def build_headers():# 身份伪装，随机选择UA和语言
    headers = HEADERS_BASE.copy()
    headers["User-Agent"] = random.choice(USER_AGENTS)
    headers["Accept-Language"] = random.choice(ACCEPT_LANGS)
    return headers

def safe_get(url, params=None):#智能重试与指数退避
    for attempt in range(1, MAX_RETRIES + 1):
        headers = build_headers()
        resp = session.get(url, params=params, headers=headers, timeout=10)
        if resp.status_code == 200:
            return resp
        # 遇到明显的反爬状态码，做指数退避
        # 403 禁止访问，429 请求过多，5xx 服务器错误，这些都有可能是反爬状态码
        if resp.status_code in (403, 429) or 500 <= resp.status_code < 600:
            wait = 2 ** attempt + random.random()
            print(f"[WARN] {url} → {resp.status_code}, retry in {wait:.1f}s")
            time.sleep(wait)
            continue
        resp.raise_for_status()
    # 最后一次不成功就报错
    resp.raise_for_status()

def random_delay():
    time.sleep(random.uniform(0.5, 2.0))

def fetch_page_hrefs(year, page):

    url = f"https://asn.flightsafety.org/asndb/year/{year}/{page}"
    print(f"[LIST] Fetching page {page}: {url}")
    resp = safe_get(url)
    soup = BeautifulSoup(resp.text, "html.parser")

    hrefs = []
    for a in soup.select("tr.list span.nobr a"):
        href = a.get("href")
        if href:
            hrefs.append(href)
    print(f"[LIST] Year={year}, page={page}, got {len(hrefs)} links")
    return hrefs

def fetch_list_batch(year, start, length=BATCH_SIZE):

    draw = 1 + start // length
    payload = {
        "Year":   year,
        "draw":   draw,
        "start":  start,
        "length": length
    }
    headers = build_headers()
    headers.update({
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "application/json, text/javascript, */*; q=0.01"
    })

    resp = session.post(BASE_LIST, data=payload, headers=headers, timeout=10)
    '''
    print(f"\n[DEBUG] status={resp.status_code}, headers={resp.headers.get('Content-Type')}")
    print("[DEBUG] raw text head:\n", resp.text[:200].replace("\n"," "), "\n…\n")
    '''
    resp.raise_for_status()
    text = resp.content.decode("utf-8-sig")
    j = json.loads(text)

    hrefs = []
    for row in j.get("data", []):
        m = href_re.search(row[1])
        if m:
            hrefs.append(m.group(1))

    print(f"[LIST] Year={year}, start={start}, got {len(hrefs)} hrefs")
    return hrefs

def extract_narrative(soup):
    cap = soup.find("span", class_="caption", string="Narrative:")
    if not cap:
        return ""
    parts, node = [], cap.next_sibling
    while node:
        # 如果遇到下一个 Sources/Revision block，就停止
        if getattr(node, "name", None) == "div" and "captionhr" in node.get("class", []):
            break
        txt = node.get_text(" ", strip=True) if hasattr(node, "get_text") else node.strip()
        if txt:
            parts.append(txt)
        node = node.next_sibling
    return " ".join(parts).strip()

def parse_detail(path, seq=None):
    url = BASE_DETAIL + path
    tag = f"[DETAIL {seq}]" if seq else "[DETAIL]"
    print(f"{tag} Fetching {url}")
    
    resp = safe_get(url)
    soup = BeautifulSoup(resp.text, "html.parser")

    data = {"DetailURL": url}
    # 通用表格解析
    table = soup.select_one("div#contentcolumnfull table")
    if table:
        for tr in table.select("tr"):
            tds = tr.find_all("td")
            if len(tds) < 2:
                continue
            key = tds[0].get_text(" ", strip=True).rstrip(":")
            val = tds[1].get_text(" ", strip=True)
            data[key] = val

    manufacture_fields = [k for k in data.keys() if 'manufacture' in k.lower() or 'built' in k.lower() or 'year' in k.lower()]
    if manufacture_fields:
        print(f"{tag} Found manufacture-related fields: {manufacture_fields}")
    else:
        print(f"{tag} No manufacture fields found. All fields: {list(data.keys())}")

    data["Narrative"] = extract_narrative(soup)

    # Sources
    src_div = soup.find("div", class_="captionhr", string="Sources:")
    if src_div:
        items = []
        for sib in src_div.next_siblings:
            if getattr(sib, "name", None) == "br":
                continue
            text = ""
            if getattr(sib, "name", None) == "a":
                text = sib.get("href", sib.get_text(strip=True))
            else:
                text = sib.get_text(" ", strip=True)
            if text:
                items.append(text)
        data["Sources"] = " | ".join(items).strip()

    # Revision History
    rev_div = soup.find("div", class_="captionhr", string="Revision history:")
    if rev_div:
        revs = []
        tbl2 = rev_div.find_next("table", class_="updates")
        for row in tbl2.select("tr")[1:]:
            cols = [td.get_text(" ", strip=True) for td in row.select("td")]
            revs.append(" / ".join(cols))
        data["RevisionHistory"] = " | ".join(revs)

    print(f"{tag} Parsed {len(data)-1} fields")
    random_delay()
    return data

def main():
    session.headers.update(build_headers())
    total = 0
    writer = None
    common_fields = [
        "Aircraft damage","Confidence Rating","Date","Departure airport",
        "Destination airport","DetailURL","Engine model","Fatalities","Location","MSN",
        "Narrative","Nature","Other fatalities","Owner/operator","Phase","Registration",
        "RevisionHistory","Sources","Time","Type","Year of manufacture","Category",
    ]
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as csv_file:
        for year in YEARS:
            print(f"\n=== Processing Year {year} ===")

            all_hrefs = []
            page = 1
            while True:
                hrefs = fetch_page_hrefs(year, page)
                if not hrefs:
                    break
                all_hrefs.extend(hrefs)
                page += 1

            print(f"[MAIN] Year {year} total URLs: {len(all_hrefs)}")

            with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
                futures = {
                    pool.submit(parse_detail, href, seq=i+1): href
                    for i, href in enumerate(all_hrefs)
                }
                for fut in concurrent.futures.as_completed(futures):
                    info = None
                    try:
                        info = fut.result()
                    except Exception as e:
                        print(f"[ERROR] parsing {futures[fut]} → {e}")
                        continue

                    if writer is None:
                        cols = list(dict.fromkeys(common_fields + list(info.keys())))
                        writer = csv.DictWriter(
                            csv_file,
                            fieldnames=cols,
                            extrasaction="ignore"
                        )
                        writer.writeheader()

                    writer.writerow(info)
                    total += 1
                    if total % 10 == 0:
                        print(f"[PROGRESS] {total} records written")

    print(f"\n[DONE] All done. Total records: {total}")




if __name__ == "__main__":
    main()
