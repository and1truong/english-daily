#!/usr/bin/env python3
"""Render English Daily pages: data/day-NN.json -> day-NN-slug.html + index.html."""
import json, html, sys
from pathlib import Path

BASE = Path(__file__).parent
DATA = BASE / "data"
TOPICS = json.loads((BASE / "topics.json").read_text())
HANDWRITTEN = {1, 2, 3, 4}  # already built by hand

HEAD = """<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Ngày {day} · {title} — English Daily</title>
<link href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:ital,wght@0,400;0,600;0,700;1,400&family=Playfair+Display:wght@600;700&family=JetBrains+Mono&display=swap" rel="stylesheet">
<link rel="stylesheet" href="style.css">
</head>
<body>
<div class="notebook">
"""

def esc(s):
    return html.escape(str(s), quote=False)

def validate(day_json, day):
    errs = []
    scenes = day_json.get("scenes")
    if not isinstance(scenes, list) or not (3 <= len(scenes) <= 7):
        errs.append(f"scenes count {len(scenes) if isinstance(scenes, list) else 'missing'}")
        scenes = []
    total = 0
    for i, sc in enumerate(scenes):
        if not sc.get("vi") or not sc.get("en"):
            errs.append(f"scene {i} missing vi/en title")
        for s in sc.get("sentences", []):
            total += 1
            for k in ("vi", "en", "ipa"):
                if not s.get(k):
                    errs.append(f"scene {i} sentence {total} missing {k}")
    if not (15 <= total <= 30):
        errs.append(f"sentence count {total}")
    if not day_json.get("practice"):
        errs.append("missing practice")
    return errs, total

def render_day(topic, d):
    day = topic["day"]
    emoji = d.get("emoji", "")
    parts = [HEAD.format(day=day, title=esc(topic["vi"]))]
    parts.append(f'  <span class="day-badge">Ngày {day}</span>\n')
    parts.append(f'  <h1>{esc(topic["vi"])} {emoji}</h1>\n')
    parts.append(f'  <div class="subtitle">{esc(topic["en"])}</div>\n\n')
    parts.append(f'  <div class="goal">\n    <b>Tình huống:</b> {esc(topic["scenario"])}\n  </div>\n\n')
    for i, sc in enumerate(d["scenes"], 1):
        parts.append(f'  <div class="scene"><span class="num">{i}</span><span class="t-vi">{esc(sc["vi"])}</span><span class="t-en">{esc(sc["en"])}</span></div>\n\n')
        for s in sc["sentences"]:
            vi = esc(s["vi"])
            if s.get("actor"):
                vi += f' <i>({esc(s["actor"])})</i>'
            parts.append(f'  <div class="s"><div class="vi">{vi}</div><div><div class="en">{esc(s["en"])}</div><div class="ipa">{esc(s["ipa"])}</div>')
            if s.get("note"):
                parts.append(f'<div class="note">{esc(s["note"])}</div>')
            parts.append('</div></div>\n')
    parts.append('\n  <div class="practice">\n    <h2>🪞 Bài tập trước gương</h2>\n    <ol>\n')
    for p in d["practice"]:
        parts.append(f'      <li>{esc(p)}</li>\n')
    parts.append('    </ol>\n    <div class="checks">')
    for c in d.get("checks", []):
        parts.append(f'<span>☐ {esc(c)}</span>')
    parts.append('</div>\n  </div>\n')
    # nav
    prev_t = next((t for t in TOPICS if t["day"] == day - 1), None)
    next_t = next((t for t in TOPICS if t["day"] == day + 1), None)
    parts.append('\n  <div class="nav">\n')
    if prev_t:
        parts.append(f'    <a href="day-{prev_t["day"]:02d}-{prev_t["slug"]}.html">← Ngày {prev_t["day"]}: {esc(prev_t["vi"])}</a>\n')
    else:
        parts.append('    <a href="index.html">← Bản đồ chủ đề</a>\n')
    if next_t:
        parts.append(f'    <a href="day-{next_t["day"]:02d}-{next_t["slug"]}.html">Ngày {next_t["day"]}: {esc(next_t["vi"])} →</a>\n')
    else:
        parts.append('    <a href="index.html">Bản đồ chủ đề →</a>\n')
    parts.append('  </div>\n</div>\n</body>\n</html>\n')
    out = BASE / f'day-{day:02d}-{topic["slug"]}.html'
    out.write_text("".join(parts))
    return out

def render_index():
    done = {t["day"] for t in TOPICS if t.get("done")}
    done |= set(load_days())
    parts = [HEAD.format(day="—", title="Bản đồ chủ đề")]
    parts.append('  <span class="day-badge">English Daily</span>\n')
    parts.append('  <h1>Sổ tay hội thoại tưởng tượng</h1>\n')
    parts.append(f'  <div class="subtitle">{len(TOPICS)} ngày · mỗi ngày một chủ đề · 20–25 câu · suy nghĩ tiếng Việt → câu tiếng Anh tự nhiên → phiên âm IPA</div>\n\n')
    parts.append('  <div class="goal">\n    <b>Cách dùng:</b> chọn chủ đề của ngày → đọc câu tiếng Việt, tự tưởng tượng mình đang nói →\n    nhìn câu tiếng Anh, đọc to theo phiên âm → nói trước gương không nhìn chữ.\n    Ôn lại câu của hôm trước trước khi học chủ đề mới.\n  </div>\n')
    parts.append('  <div class="legend">xanh = đã có bài · mỗi chủ đề là một ngày luyện tập</div>\n')
    max_week = max(t["day"] for t in TOPICS) // 7 + 1
    for week in range(1, max_week + 1):
        wdays = [t for t in TOPICS if (t["day"] - 1) // 7 + 1 == week]
        if not wdays:
            continue
        lo, hi = wdays[0]["day"], wdays[-1]["day"]
        parts.append(f'\n  <div class="group">\n    <h3>Tuần {week} · Ngày {lo}–{hi}</h3>\n    <div class="topics">\n')
        for t in wdays:
            cls = "topic done" if t["day"] in done else "topic"
            parts.append(f'      <span class="{cls}"><a href="day-{t["day"]:02d}-{t["slug"]}.html">{t["day"]} · {esc(t["vi"])}</a></span>\n')
        parts.append('    </div>\n  </div>\n')
    parts.append('\n  <div class="nav">\n    <a href="day-01-sieu-thi.html">Bắt đầu → Ngày 1: Đi siêu thị</a>\n    <span></span>\n  </div>\n</div>\n</body>\n</html>\n')
    (BASE / "index.html").write_text("".join(parts))

def load_days():
    """Collect every day object from data/*.json (single-day files or {"days":[...]} batches)."""
    days = {}
    for f in sorted(DATA.glob("*.json")):
        obj = json.loads(f.read_text())
        for d in (obj.get("days") or [obj]):
            if isinstance(d, dict) and d.get("day"):
                days[int(d["day"])] = d
    return days

def main():
    DATA.mkdir(exist_ok=True)
    failures = []
    rendered = 0
    days = load_days()
    for t in TOPICS:
        if t["day"] in HANDWRITTEN or t["day"] not in days:
            continue
        d = days[t["day"]]
        errs, total = validate(d, t["day"])
        if errs:
            failures.append((t["day"], errs))
            continue
        render_day(t, d)
        rendered += 1
        print(f'rendered day {t["day"]}: {total} câu')
    render_index()
    print(f'\n{rendered} days rendered, index regenerated')
    if failures:
        print('FAILURES:', file=sys.stderr)
        for day, errs in failures:
            print(f'  day {day}: {errs}', file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
