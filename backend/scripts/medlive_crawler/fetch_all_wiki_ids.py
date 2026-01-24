"""
获取医脉通所有疾病的 wiki_id
"""
import httpx
import re
import json
import time
from typing import List, Set

# Cookie 需要定期更新
COOKIE = "Hm_lvt_62d92d99f7c1e7a31a11759de376479f=1769004987; HMACCOUNT=56C35BF8E24E5BB6; ymt_pk_id=e738b79d24d848ed; mrauth=Ug0CUw9VXTDc3rDU2IjVuN4%3D; PHPSESSID=ST-3194918-hVWqe09x4w6oxlIAfd7f-cas; _pk_ref.3.a971=%5B%22%22%2C%22%22%2C1769091133%2C%22https%3A%2F%2Fcn.bing.com%2F%22%5D; _pk_ses.3.a971=*; ymtinfo=eyJ1aWQiOiI2OTM3NzY5IiwicmVzb3VyY2UiOiJ3ZWIiLCJleHRfdmVyc2lvbiI6IjEiLCJhcHBfbmFtZSI6Im1lZGxpdmUifQ%3D%3D; _pk_id.3.a971=e738b79d24d848ed.1769004987.4.1769091404.1769084134.; Hm_lpvt_62d92d99f7c1e7a31a11759de376479f=1769091404; XSRF-TOKEN=eyJpdiI6IkFUN3lIY2VwdVZ6alo2ZURzWmtFQUE9PSIsInZhbHVlIjoiZEpQN1JqcUpkMkpzRVd5aU9TOUdWWStDdGVzZWs1YjZLdHVkc1h2OW9PYkFsa0R3bWlXQTBsb1BXdWRCbGtBdnk1YmNCTUhyQVo0SjlOVkhKQ2FjUnc9PSIsIm1hYyI6IjBjNWMwNGUwMTk5NGU3YjM3NDg3OGRjZjk1Njk3YzdhMzIyNDMwMThhN2QzNGRmOTE5YzU2Y2FkYTU5ODQzM2IifQ%3D%3D; oncologist_session=eyJpdiI6IkhCTlZMXC9NeEdMYjZVU1Y0S1habG5RPT0iLCJ2YWx1ZSI6IkRWTFUxdmhJRGw3RXUrc05JdDJcL3ErbTZGZjNhalwvaURidzNMbmRpWHlaZCtQZFArRjg2WlJXWUpOK0Zwc0NTNFVKYWxJMEdMaFlyNCtWbTJ6RzRSS3c9PSIsIm1hYyI6ImU4N2VlMmVlN2MzODdkZmVjMzc3ZGFhZjhiNzhjZGU2YTQ1MTYyMzBhMjk1MzlmMjUyYjA0NmJhM2NlM2FlYTMifQ%3D%3D"

def fetch_all_wiki_ids() -> List[str]:
    """获取所有疾病的 wiki_id"""
    wiki_ids: Set[str] = set()

    client = httpx.Client(follow_redirects=True, timeout=30, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Cookie": COOKIE,
        "Referer": "https://yzy.medlive.cn/pc/allWiki",
        "X-Requested-With": "XMLHttpRequest",
    })

    page = 0
    while True:
        try:
            # 请求下一页数据
            resp = client.get(f"https://yzy.medlive.cn/pc/nextWikiList?page={page}")

            if resp.status_code != 200:
                print(f"  ✗ HTTP {resp.status_code}")
                break

            data = resp.json()

            if not data.get("success"):
                print(f"  ✗ API 返回失败")
                break

            html = data.get("html", "")

            # 解析 HTML 中的 wiki_id
            # 格式: jumpWiki('1234')
            found_ids = re.findall(r"jumpWiki\(['\"](\d+)['\"]\)", html)

            if not found_ids:
                print(f"  第 {page} 页: 没有找到 wiki_id")
                break

            before_count = len(wiki_ids)
            wiki_ids.update(found_ids)
            new_count = len(wiki_ids) - before_count

            print(f"  第 {page} 页: +{new_count} 个 (累计 {len(wiki_ids)})")

            # 检查是否还有下一页
            if not data.get("is_next"):
                print(f"  已到最后一页")
                break

            page += 1
            time.sleep(0.5)  # 避免请求过快

        except Exception as e:
            print(f"  ✗ 错误: {e}")
            break

    client.close()
    return sorted(list(wiki_ids), key=int)


if __name__ == "__main__":
    print("开始获取所有疾病 wiki_id...")
    wiki_ids = fetch_all_wiki_ids()

    print(f"\n总共获取 {len(wiki_ids)} 个疾病")
    print(f"ID 范围: {wiki_ids[0]} - {wiki_ids[-1]}")

    # 保存到文件
    output_file = "wiki_ids.txt"
    with open(output_file, "w") as f:
        for wiki_id in wiki_ids:
            f.write(f"{wiki_id}\n")

    print(f"\n已保存到 {output_file}")

    # 保存 JSON 格式
    json_file = "wiki_ids.json"
    with open(json_file, "w") as f:
        json.dump(wiki_ids, f, indent=2)

    print(f"已保存到 {json_file}")
