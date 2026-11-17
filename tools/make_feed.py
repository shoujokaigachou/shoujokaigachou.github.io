#!/usr/bin/env python3
"""Pinterest自動投稿用のRSSを作る。毎朝GitHub Actionsが実行する。
feed-data.json の並び順に、start_date から1日 per_day 枚ずつ公開済みにする。
skip に入れた番号（手動で投稿済みのもの）は飛ばす。
  python3 tools/make_feed.py            # 今日の日付で作る
  python3 tools/make_feed.py 2026-12-01 # 日付を指定して確認する
"""
import json
import os
import sys
from datetime import date, datetime, time, timedelta, timezone
from email.utils import format_datetime
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JST = timezone(timedelta(hours=9))


def main():
    cfg = json.load(open(os.path.join(ROOT, "feed-config.json")))
    items = [x for x in json.load(open(os.path.join(ROOT, "feed-data.json"))) if x["no"] not in cfg["skip"]]
    today = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else datetime.now(JST).date()
    start = date.fromisoformat(cfg["start_date"])
    base = cfg["base_url"]
    released = []
    for i, x in enumerate(items):
        d = start + timedelta(days=i // cfg["per_day"])
        if d <= today:
            # 同じ日の中でも並び順どおりに出るよう、1枚ごとに1分ずらす
            released.append((datetime.combine(d, time(6, i % cfg["per_day"]), JST), x))

    def write(name, title, rows):
        out = ['<?xml version="1.0" encoding="UTF-8"?>', '<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/">', "<channel>",
               f"<title>{escape(title)}</title>", f"<link>{base}/</link>",
               "<description>Strange Girls' Sketchbook. Hand-drawn by a 10-year-old.</description>",
               "<language>en</language>"]
        for d, x in reversed(rows):  # 新しい順に並べる
            link = f'{base}/w/{x["no"]}.html'
            pub = format_datetime(d)
            out += ["<item>", f'<title>{escape(x["title"])}</title>', f"<link>{link}</link>",
                    f'<guid isPermaLink="true">{link}</guid>',
                    f'<description>{escape(x["description"])}</description>',
                    f'<enclosure url="{base}/img/{x["no"]}.jpg" length="{x["bytes"]}" type="image/jpeg"/>',
                    f'<media:content url="{base}/img/{x["no"]}.jpg" type="image/jpeg" medium="image"/>',
                    f"<pubDate>{pub}</pubDate>", "</item>"]
        out += ["</channel>", "</rss>", ""]
        with open(os.path.join(ROOT, name), "w", encoding="utf-8") as f:
            f.write("\n".join(out))

    write("feed.xml", "少女怪画帖 | Strange Girls' Sketchbook", released)
    left = len(items) - len(released)
    print(f"{today}: 公開済み {len(released)} / 全 {len(items)}（残り {left}枚・約{-(-left // cfg['per_day'])}日分）")


if __name__ == "__main__":
    main()
