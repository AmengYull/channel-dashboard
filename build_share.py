"""Build a fully self-contained share.html for WorkBuddy sharing.
- Inlines data.js (all data)
- Inlines echarts.min.js (~1MB, zero external dependency)
- Auto-updates date stamps from actual data
- Zero CDN calls, zero local file references
"""
import os
import re
import sys
from datetime import datetime

BASE = sys.argv[1] if len(sys.argv) > 1 else r"F:\Work\2026-05-24-10-39-23\dashboard"

# Read dashboard.html
with open(os.path.join(BASE, "dashboard.html"), "r", encoding="utf-8") as f:
    html = f.read()

# Read data.js
data_js_path = os.path.join(BASE, "data.js")
with open(data_js_path, "r", encoding="utf-8") as f:
    data_js = f.read()

# Read echarts.min.js (inline to avoid CDN blocking in WorkBuddy sandbox)
with open(os.path.join(BASE, "lib", "echarts.min.js"), "r", encoding="utf-8") as f:
    echarts_js = f.read()

# --- Auto-detect latest date from data.js ---
# DAILY labels format: ["5.1", ..., "5.24"]
dates = re.findall(r'"(\d+\.\d+)"', data_js)
latest = None
for d in dates:
    # Normalize for comparison: "5.24" -> "0524"
    parts = d.split('.')
    norm = f'{int(parts[0]):02d}{int(parts[1]):02d}'
    if latest is None or norm > latest[1]:
        latest = (d, norm)

if latest:
    latest_str = latest[0]  # e.g. "5.24"
else:
    latest_str = "unknown"

if latest:
    # Only replace dates in end-date contexts (after "~", "截止", "更新时间")
    # Do NOT touch start dates like "数据周期：5.1"
    patterns = [
        (r'(~\s*)\d+\.\d+', r'\g<1>' + latest_str),           # ~ 5.XX
        (r'(统计截止：)\d+\.\d+', r'\g<1>' + latest_str),      # 统计截止：5.XX
        (r'(更新时间：)\d+\.\d+', r'\g<1>' + latest_str),      # 更新时间：5.XX
        (r'(~ )\d+\.\d+(\s*\|)', r'\g<1>' + latest_str + r'\2'),  # in stat period range
    ]
    for pat, repl in patterns:
        html, n = re.subn(pat, repl, html)
        if n > 0:
            print(f"  Replaced '{pat}' x{n}")
    print(f"  Date auto-updated: latest data = {latest_str}")
else:
    print(f"  Warning: could not detect latest date from data.js")

# 1. Replace echarts: local lib + CDN fallback → fully inline
old_echarts = '''<script src="lib/echarts.min.js"></script>
<script>if(typeof echarts==='undefined'){document.write('<script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"><\\/script>');}</script>'''
new_echarts = f'<script>\n{echarts_js}\n</script>'
html = html.replace(old_echarts, new_echarts)

# 2. Replace external data.js with inline script
old_data = '<script src="data.js"></script>'
new_data = f'<script>\n{data_js}\n</script>'
html = html.replace(old_data, new_data)

# Write share.html
share_path = os.path.join(BASE, "share.html")
with open(share_path, "w", encoding="utf-8") as f:
    f.write(html)

size_kb = round(os.path.getsize(share_path) / 1024, 1)
print(f"Done: {share_path} ({size_kb} KB)")
print(f"  - data.js inlined ({round(len(data_js)/1024, 1)} KB)")
print(f"  - echarts.min.js inlined ({round(len(echarts_js)/1024, 1)} KB)")
print(f"  - Zero external dependencies")
print(f"  - Stats date: {latest_str}")
