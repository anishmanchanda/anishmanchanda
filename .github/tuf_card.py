#!/usr/bin/env python3
"""Render a takeUforward profile as an SVG card (heatmap + stats). Stdlib only.

Usage: python tuf_card.py <username> [out.svg]
The profile page is server-rendered, so the stats and heatmap cells are in the HTML.
If takeUforward changes its markup, the parse fails loudly instead of writing a blank card.
"""
import datetime as dt
import html
import re
import sys
import urllib.request

LEVEL_COLORS = ["#1b2130", "#1e3a8a", "#1d4ed8", "#2563eb", "#60a5fa"]
CELL, GAP = 11, 3


def fetch(user):
    req = urllib.request.Request(
        f"https://takeuforward.org/profile/{user}", headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf8", "ignore")


def parse(page):
    cells = re.findall(
        r'level-(\d)\)[^"]*"\s+aria-label="(\d\d)-(\d\d)-(\d{4}): (\d+) submissions?"', page
    )
    days = {dt.date(int(y), int(m), int(d)): (int(lv), int(n)) for lv, d, m, y, n in cells}
    stats = dict(
        (label, value)
        for value, label in re.findall(
            r'consistencyStatValue">([^<]+)</span><span class="[^"]*consistencyStatLabel">([^<]+)<', page
        )
    )
    glance = dict(
        re.findall(r'glanceLabel">([^<]+)</span><span class="[^"]*glanceValue">(?:<[^>]+>)*([^<]+)<', page)
    )
    if not days or not stats:
        raise SystemExit("parse failed: takeUforward markup may have changed")
    return days, stats, glance


def render(user, days, stats, glance):
    first, last = min(days), max(days)
    start = first - dt.timedelta(days=(first.weekday() + 1) % 7)  # Sunday-first columns
    weeks = (last - start).days // 7 + 1
    left, top = 24, 116
    width = left * 2 + weeks * (CELL + GAP)
    height = top + 7 * (CELL + GAP) + 44
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<style>text{font-family:-apple-system,Segoe UI,Helvetica,Arial,sans-serif;fill:#c9d1d9}'
        '.h{font-size:15px;font-weight:600}.s{font-size:22px;font-weight:700}.l{font-size:11px;fill:#8b949e}</style>',
        f'<rect width="{width}" height="{height}" rx="12" fill="#0d1117" stroke="#30363d"/>',
        f'<text class="h" x="{left}" y="30">takeUforward · @{html.escape(user)}</text>',
    ]
    items = [(stats.get(k, "–"), k) for k in ("Contributions • 12 mos", "Active days", "Best streak")]
    for i, (v, k) in enumerate(items):
        x = left + i * 150
        out += [f'<text class="s" x="{x}" y="62">{html.escape(v)}</text>',
                f'<text class="l" x="{x}" y="80">{html.escape(k)}</text>']
    seen_month = None
    for d in sorted(days):
        w, wd = (d - start).days // 7, (d.weekday() + 1) % 7
        x, y = left + w * (CELL + GAP), top + wd * (CELL + GAP)
        lv, n = days[d]
        out.append(
            f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{LEVEL_COLORS[lv]}">'
            f'<title>{d.isoformat()}: {n} submissions</title></rect>'
        )
        if d.day <= 7 and wd == 0 and seen_month != d.month:
            seen_month = d.month
            out.append(f'<text class="l" x="{x}" y="{top - 8}">{d.strftime("%b")}</text>')
    out.append(f'<text class="l" x="{left}" y="{height - 14}">Updated {dt.date.today().isoformat()} · data from takeuforward.org</text>')
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    user = sys.argv[1] if len(sys.argv) > 1 else "anishmanchanda"
    path = sys.argv[2] if len(sys.argv) > 2 else "tuf-card.svg"
    days, stats, glance = parse(fetch(user))
    open(path, "w").write(render(user, days, stats, glance))
    print(f"wrote {path}: {len(days)} days, stats={stats}")
