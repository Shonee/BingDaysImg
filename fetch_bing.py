#!/usr/bin/env python3
"""
必应每日壁纸自动获取与页面生成工具

功能：
1. 从必应 API 获取每日壁纸信息
2. 按月存储壁纸数据到 data/YYYY-MM.json
3. 生成 index.html 首页和 archives/YYYY-MM.html 归档页面
4. 生成 README.md
"""

import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError

# ===== 配置 =====
BING_API = "https://cn.bing.com/HPImageArchive.aspx?format=js&idx=0&n=1&mkt=zh-CN"
BING_BASE = "https://cn.bing.com"
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
ARCHIVE_DIR = BASE_DIR / "archives"
MAX_RETRIES = 3


def fetch_json(url, retries=MAX_RETRIES):
    """带重试的 JSON 请求"""
    for i in range(retries):
        try:
            req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (URLError, Exception) as e:
            if i == retries - 1:
                raise
            print(f"⚠️ 请求失败: {e}, 第 {i+1}/{retries} 次重试...")
            time.sleep(2 ** i)


def fetch_today_wallpaper():
    """获取今日必应壁纸数据"""
    print("正在获取今日必应壁纸...")
    data = fetch_json(BING_API)
    if not data or "images" not in data or not data["images"]:
        raise Exception("未能获取到有效的壁纸数据")

    image = data["images"][0]
    # startdate 格式: 20260701, 实际展示日期需要 +1 天
    raw_date = image["startdate"]
    date_obj = datetime.strptime(raw_date, "%Y%m%d") + timedelta(days=1)
    date_str = date_obj.strftime("%Y-%m-%d")

    wallpaper = {
        "date": date_str,
        "title": image.get("title", ""),
        "copyright": image.get("copyright", ""),
        "copyrightlink": image.get("copyrightlink", ""),
        "imageUrl": f"{BING_BASE}{image['urlbase']}_1920x1080.jpg",
        "downloadUrl4k": f"{BING_BASE}{image['urlbase']}_UHD.jpg",
    }
    print(f"📸 获取到壁纸: {wallpaper['title']} ({wallpaper['date']})")
    return wallpaper


def load_month_data(month_key):
    """读取某月的壁纸数据"""
    file = DATA_DIR / f"{month_key}.json"
    if file.exists():
        return json.loads(file.read_text(encoding="utf-8"))
    return []


def save_month_data(month_key, data):
    """保存某月的壁纸数据"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    data.sort(key=lambda x: x["date"], reverse=True)
    file = DATA_DIR / f"{month_key}.json"
    file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def get_all_data():
    """读取所有月份数据"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    all_data = []
    for f in sorted(DATA_DIR.glob("*.json"), reverse=True):
        month_data = json.loads(f.read_text(encoding="utf-8"))
        all_data.extend(month_data)
    all_data.sort(key=lambda x: x["date"], reverse=True)
    return all_data


def get_archive_months():
    """获取已有的月份列表"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    months = [f.stem for f in DATA_DIR.glob("*.json")]
    months.sort(reverse=True)
    return months


# ===== 页面生成 =====

def generate_index_html(all_data, archive_months):
    """生成首页 index.html"""
    latest = all_data[0]
    current_month = datetime.now().strftime("%Y-%m")
    monthly = [w for w in all_data if w["date"].startswith(current_month)]
    others = [w for w in monthly if w["date"] != latest["date"]]

    # 归档链接
    archive_links = "\n".join(
        f'            <a href="./archives/{m}.html">{m}</a>' for m in archive_months
    )

    # 卡片网格
    cards = ""
    for i, w in enumerate(others):
        cards += f'''<div class="card" onclick="openLightbox({i})">
<img src="{w['imageUrl']}" alt="{w['title']}" loading="lazy">
<div class="overlay"><span class="card-title">{w['title']}</span>
<span class="card-date">{w['date']}</span></div></div>'''

    # 版权信息
    if latest.get("copyrightlink"):
        copyright_html = f'<a href="{latest["copyrightlink"]}" target="_blank">{latest["copyright"]}</a>'
    else:
        copyright_html = latest["copyright"]

    # lightbox 数据
    items_json = json.dumps(
        [{"url": w["downloadUrl4k"], "title": w["title"], "date": w["date"], "cr": w["copyright"]}
         for w in others], ensure_ascii=False
    )

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Bing Daily Wallpaper</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#0a0a0a;color:#e4e4e7}}
a{{color:#a1a1aa;text-decoration:none}}a:hover{{color:#fafafa}}
.hero{{position:relative;width:100%;height:100vh;min-height:500px;overflow:hidden}}
.hero img{{width:100%;height:100%;object-fit:cover}}
.hero .gradient{{position:absolute;inset:0;background:linear-gradient(0deg,rgba(10,10,10,.95) 0%,rgba(10,10,10,.4) 40%,transparent 70%)}}
.hero .content{{position:absolute;bottom:0;left:0;right:0;padding:48px clamp(24px,5vw,80px)}}
.hero .content h1{{font-size:clamp(1.8rem,4vw,3rem);font-weight:700;color:#fafafa;margin-bottom:8px}}
.hero .content .meta{{display:flex;align-items:center;gap:16px;flex-wrap:wrap;margin-bottom:16px}}
.hero .content .date{{font-size:.9rem;color:#a1a1aa}}
.hero .content .copyright{{font-size:.85rem;color:#71717a}}
.hero .content .copyright a{{color:#71717a}}.hero .content .copyright a:hover{{color:#a1a1aa}}
.hero .content .btn{{display:inline-flex;align-items:center;gap:8px;padding:12px 28px;background:#fafafa;color:#0a0a0a;border-radius:8px;font-size:.9rem;font-weight:500;text-decoration:none;transition:all .2s}}
.hero .content .btn:hover{{background:#d4d4d8;transform:translateY(-1px)}}
.section{{max-width:1400px;margin:0 auto;padding:60px clamp(16px,4vw,48px)}}
.section-header{{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:32px}}
.section-header h2{{font-size:1.3rem;font-weight:600;color:#e4e4e7}}
.section-header .count{{font-size:.85rem;color:#52525b}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px}}
.card{{position:relative;border-radius:10px;overflow:hidden;cursor:pointer;opacity:0;transform:translateY(20px);transition:opacity .5s,transform .5s}}
.card.visible{{opacity:1;transform:translateY(0)}}
.card img{{width:100%;display:block;transition:transform .4s}}
.card:hover img{{transform:scale(1.05)}}
.card .overlay{{position:absolute;inset:0;background:linear-gradient(0deg,rgba(10,10,10,.8) 0%,transparent 50%);display:flex;flex-direction:column;justify-content:flex-end;padding:16px;opacity:0;transition:opacity .3s}}
.card:hover .overlay{{opacity:1}}
.card .overlay .card-title{{font-size:.95rem;font-weight:500;color:#fafafa}}
.card .overlay .card-date{{font-size:.8rem;color:#a1a1aa;margin-top:4px}}
.archives{{margin-top:40px}}
.archives h3{{font-size:1rem;color:#71717a;margin-bottom:16px}}
.archives .links{{display:flex;flex-wrap:wrap;gap:8px}}
.archives .links a{{padding:6px 16px;background:#18181b;border:1px solid #27272a;border-radius:6px;color:#a1a1aa;font-size:.85rem;transition:all .2s}}
.archives .links a:hover{{background:#27272a;color:#fafafa;border-color:#3f3f46}}
.footer{{text-align:center;padding:40px 20px;color:#3f3f46;font-size:.75rem;border-top:1px solid #18181b;margin-top:60px}}
.lightbox{{display:none;position:fixed;inset:0;z-index:1000;background:rgba(0,0,0,.92);backdrop-filter:blur(8px);align-items:center;justify-content:center;cursor:zoom-out}}
.lightbox.active{{display:flex}}
.lightbox img{{max-width:92vw;max-height:88vh;object-fit:contain;border-radius:4px}}
.lightbox .lb-info{{position:absolute;bottom:24px;left:50%;transform:translateX(-50%);text-align:center}}
.lightbox .lb-info .lb-title{{font-size:1rem;color:#fafafa;margin-bottom:4px}}
.lightbox .lb-info .lb-meta{{font-size:.8rem;color:#71717a}}
.lightbox .lb-close{{position:absolute;top:24px;right:24px;width:40px;height:40px;background:#18181b;border:1px solid #27272a;border-radius:50%;color:#a1a1aa;font-size:1.2rem;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all .2s}}
.lightbox .lb-close:hover{{background:#27272a;color:#fafafa}}
.lightbox .lb-download{{position:absolute;top:24px;right:80px;padding:8px 20px;background:#fafafa;color:#0a0a0a;border-radius:6px;font-size:.85rem;font-weight:500;text-decoration:none;transition:all .2s}}
.lightbox .lb-download:hover{{background:#d4d4d8}}
.lightbox .lb-nav{{position:absolute;top:50%;transform:translateY(-50%);width:48px;height:48px;background:rgba(24,24,27,.7);border:1px solid #3f3f46;border-radius:50%;color:#a1a1aa;font-size:1.4rem;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all .2s}}
.lightbox .lb-nav:hover{{background:#27272a;color:#fafafa}}
.lightbox .lb-prev{{left:20px}}.lightbox .lb-next{{right:20px}}
@media(max-width:640px){{.hero{{min-height:70vh}}.grid{{grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:10px}}.card .overlay{{opacity:1;background:linear-gradient(0deg,rgba(10,10,10,.7) 0%,transparent 40%)}}.lightbox .lb-nav{{width:40px;height:40px;font-size:1.1rem}}.lightbox .lb-prev{{left:8px}}.lightbox .lb-next{{right:8px}}}}
</style>
</head>
<body>
<div class="hero">
<img src="{latest['imageUrl']}" alt="{latest['title']}" width="1920" height="1080">
<div class="gradient"></div>
<div class="content">
<h1>{latest['title']}</h1>
<div class="meta">
<span class="date">{latest['date']}</span>
<span class="copyright">{copyright_html}</span>
</div>
<a class="btn" href="{latest['downloadUrl4k']}" target="_blank" rel="noopener">⬇ 下载 4K</a>
</div>
</div>
<div class="section">
<div class="section-header">
<h2>{current_month} 月壁纸</h2>
<span class="count">{len(monthly)} 张</span>
</div>
<div class="grid">{cards}</div>
<div class="archives">
<h3>历史归档</h3>
<div class="links">
{archive_links}
</div>
</div>
</div>
<div class="footer">GitHub Actions 每天自动更新 · 壁纸版权归微软及原作者所有</div>
<div class="lightbox" id="lightbox" onclick="closeLightbox()">
<button class="lb-close" onclick="closeLightbox()">&times;</button>
<a class="lb-download" id="lb-download" href="#" target="_blank" onclick="event.stopPropagation()">查看原图</a>
<button class="lb-nav lb-prev" onclick="event.stopPropagation();navigate(-1)">&#8249;</button>
<button class="lb-nav lb-next" onclick="event.stopPropagation();navigate(1)">&#8250;</button>
<img id="lb-img" src="" alt="">
<div class="lb-info"><div class="lb-title" id="lb-title"></div><div class="lb-meta" id="lb-meta"></div></div>
</div>
<script>
const items={items_json};
let currentIndex=0;
function openLightbox(i){{currentIndex=i;const w=items[i];document.getElementById('lb-img').src=w.url;document.getElementById('lb-title').textContent=w.title;document.getElementById('lb-meta').textContent=w.date+' · '+w.cr;document.getElementById('lb-download').href=w.url;document.getElementById('lightbox').classList.add('active');document.body.style.overflow='hidden';}}
function navigate(d){{currentIndex=(currentIndex+d+items.length)%items.length;const w=items[currentIndex];document.getElementById('lb-img').src=w.url;document.getElementById('lb-title').textContent=w.title;document.getElementById('lb-meta').textContent=w.date+' · '+w.cr;document.getElementById('lb-download').href=w.url;}}
function closeLightbox(){{document.getElementById('lightbox').classList.remove('active');document.body.style.overflow='';}}
document.addEventListener('keydown',e=>{{if(e.key==='Escape')closeLightbox();if(e.key==='ArrowLeft')navigate(-1);if(e.key==='ArrowRight')navigate(1);}});
const observer=new IntersectionObserver(entries=>{{entries.forEach(e=>{{if(e.isIntersecting){{e.target.classList.add('visible');observer.unobserve(e.target);}}}});}},{{threshold:0.1}});
document.querySelectorAll('.card').forEach(c=>observer.observe(c));
</script>
</body>
</html>'''


def generate_archive_html(month_key, wallpapers):
    """生成月度归档页面"""
    title = f"{month_key} 必应壁纸"

    cards = ""
    for i, w in enumerate(wallpapers):
        cards += f'''<div class="card" onclick="openLightbox({i})">
<img src="{w['imageUrl']}" alt="{w['title']}" loading="lazy">
<div class="overlay"><span class="card-title">{w['title']}</span>
<span class="card-date">{w['date']}</span></div></div>'''

    items_json = json.dumps(
        [{"url": w["downloadUrl4k"], "title": w["title"], "date": w["date"], "cr": w["copyright"]}
         for w in wallpapers], ensure_ascii=False
    )

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#0a0a0a;color:#e4e4e7}}
a{{color:#a1a1aa;text-decoration:none}}a:hover{{color:#fafafa}}
.nav{{padding:20px clamp(16px,4vw,48px);max-width:1400px;margin:0 auto}}
.nav a{{font-size:.85rem;color:#52525b;transition:color .2s}}.nav a:hover{{color:#fafafa}}
.section{{max-width:1400px;margin:0 auto;padding:0 clamp(16px,4vw,48px) 60px}}
.section h1{{font-size:clamp(1.5rem,3vw,2rem);font-weight:700;color:#fafafa;margin-bottom:8px}}
.section .count{{font-size:.85rem;color:#52525b;margin-bottom:32px;display:block}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px}}
.card{{position:relative;border-radius:10px;overflow:hidden;cursor:pointer;opacity:0;transform:translateY(20px);transition:opacity .5s,transform .5s}}
.card.visible{{opacity:1;transform:translateY(0)}}
.card img{{width:100%;display:block;transition:transform .4s}}
.card:hover img{{transform:scale(1.05)}}
.card .overlay{{position:absolute;inset:0;background:linear-gradient(0deg,rgba(10,10,10,.8) 0%,transparent 50%);display:flex;flex-direction:column;justify-content:flex-end;padding:16px;opacity:0;transition:opacity .3s}}
.card:hover .overlay{{opacity:1}}
.card .overlay .card-title{{font-size:.95rem;font-weight:500;color:#fafafa}}
.card .overlay .card-date{{font-size:.8rem;color:#a1a1aa;margin-top:4px}}
.lightbox{{display:none;position:fixed;inset:0;z-index:1000;background:rgba(0,0,0,.92);backdrop-filter:blur(8px);align-items:center;justify-content:center;cursor:zoom-out}}
.lightbox.active{{display:flex}}
.lightbox img{{max-width:92vw;max-height:88vh;object-fit:contain;border-radius:4px}}
.lightbox .lb-info{{position:absolute;bottom:24px;left:50%;transform:translateX(-50%);text-align:center}}
.lightbox .lb-info .lb-title{{font-size:1rem;color:#fafafa;margin-bottom:4px}}
.lightbox .lb-info .lb-meta{{font-size:.8rem;color:#71717a}}
.lightbox .lb-close{{position:absolute;top:24px;right:24px;width:40px;height:40px;background:#18181b;border:1px solid #27272a;border-radius:50%;color:#a1a1aa;font-size:1.2rem;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all .2s}}
.lightbox .lb-close:hover{{background:#27272a;color:#fafafa}}
.lightbox .lb-download{{position:absolute;top:24px;right:80px;padding:8px 20px;background:#fafafa;color:#0a0a0a;border-radius:6px;font-size:.85rem;font-weight:500;text-decoration:none;transition:all .2s}}
.lightbox .lb-download:hover{{background:#d4d4d8}}
.lightbox .lb-nav{{position:absolute;top:50%;transform:translateY(-50%);width:48px;height:48px;background:rgba(24,24,27,.7);border:1px solid #3f3f46;border-radius:50%;color:#a1a1aa;font-size:1.4rem;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all .2s}}
.lightbox .lb-nav:hover{{background:#27272a;color:#fafafa}}
.lightbox .lb-prev{{left:20px}}.lightbox .lb-next{{right:20px}}
@media(max-width:640px){{.grid{{grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:10px}}.card .overlay{{opacity:1;background:linear-gradient(0deg,rgba(10,10,10,.7) 0%,transparent 40%)}}.lightbox .lb-nav{{width:40px;height:40px}}.lightbox .lb-prev{{left:8px}}.lightbox .lb-next{{right:8px}}}}
</style>
</head>
<body>
<div class="nav"><a href="../index.html">&larr; 返回首页</a></div>
<div class="section">
<h1>{title}</h1>
<span class="count">{len(wallpapers)} 张壁纸</span>
<div class="grid">{cards}</div>
</div>
<div class="lightbox" id="lightbox" onclick="closeLightbox()">
<button class="lb-close" onclick="closeLightbox()">&times;</button>
<a class="lb-download" id="lb-download" href="#" target="_blank" onclick="event.stopPropagation()">查看原图</a>
<button class="lb-nav lb-prev" onclick="event.stopPropagation();navigate(-1)">&#8249;</button>
<button class="lb-nav lb-next" onclick="event.stopPropagation();navigate(1)">&#8250;</button>
<img id="lb-img" src="" alt="">
<div class="lb-info"><div class="lb-title" id="lb-title"></div><div class="lb-meta" id="lb-meta"></div></div>
</div>
<script>
const items={items_json};
let currentIndex=0;
function openLightbox(i){{currentIndex=i;const w=items[i];document.getElementById('lb-img').src=w.url;document.getElementById('lb-title').textContent=w.title;document.getElementById('lb-meta').textContent=w.date+' · '+w.cr;document.getElementById('lb-download').href=w.url;document.getElementById('lightbox').classList.add('active');document.body.style.overflow='hidden';}}
function navigate(d){{currentIndex=(currentIndex+d+items.length)%items.length;const w=items[currentIndex];document.getElementById('lb-img').src=w.url;document.getElementById('lb-title').textContent=w.title;document.getElementById('lb-meta').textContent=w.date+' · '+w.cr;document.getElementById('lb-download').href=w.url;}}
function closeLightbox(){{document.getElementById('lightbox').classList.remove('active');document.body.style.overflow='';}}
document.addEventListener('keydown',e=>{{if(e.key==='Escape')closeLightbox();if(e.key==='ArrowLeft')navigate(-1);if(e.key==='ArrowRight')navigate(1);}});
const observer=new IntersectionObserver(entries=>{{entries.forEach(e=>{{if(e.isIntersecting){{e.target.classList.add('visible');observer.unobserve(e.target);}}}});}},{{threshold:0.1}});
document.querySelectorAll('.card').forEach(c=>observer.observe(c));
</script>
</body>
</html>'''


def generate_readme(all_data, archive_months):
    """生成 README.md"""
    latest = all_data[0]
    current_month = datetime.now().strftime("%Y-%m")
    monthly = [w for w in all_data if w["date"].startswith(current_month)]

    md = "# Bing Wallpaper\n\n"
    md += "## 今日壁纸\n\n"
    md += f"**{latest['title']}** ({latest['date']})\n\n"
    md += f"![{latest['title']}]({latest['imageUrl']})\n\n"
    md += f"{latest['copyright']}\n\n"
    md += f"🔗 [下载 4K 高清版本]({latest['downloadUrl4k']})\n\n"

    md += f"## {current_month} 月壁纸 ({len(monthly)} 张)\n\n"
    md += "| 日期 | 标题 | 4K 下载 |\n"
    md += "|------|------|--------|\n"
    for w in monthly:
        md += f"| {w['date']} | {w['title']} | [下载]({w['downloadUrl4k']}) |\n"

    md += "\n## 历史归档\n\n"
    md += " · ".join(f"[{m}](./archives/{m}.html)" for m in archive_months)
    md += "\n\n## 关于\n\n"
    md += "🤖 本项目使用 GitHub Actions 每天自动获取必应壁纸并更新\n\n"
    md += "📸 所有壁纸版权归微软及原作者所有\n"
    return md


def generate_all_pages():
    """生成所有页面"""
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    archive_months = get_archive_months()
    all_data = get_all_data()

    if not all_data:
        print("⚠️ 没有数据，跳过页面生成")
        return

    # 生成首页
    index_html = generate_index_html(all_data, archive_months)
    (BASE_DIR / "index.html").write_text(index_html, encoding="utf-8")
    print("✅ index.html 已生成")

    # 生成 README
    readme = generate_readme(all_data, archive_months)
    (BASE_DIR / "README.md").write_text(readme, encoding="utf-8")
    print("✅ README.md 已生成")

    # 生成归档页面
    for month in archive_months:
        month_data = load_month_data(month)
        html = generate_archive_html(month, month_data)
        (ARCHIVE_DIR / f"{month}.html").write_text(html, encoding="utf-8")
    print(f"✅ {len(archive_months)} 个归档页面已生成")


def main():
    """主入口"""
    try:
        print("🚀 开始获取今日必应壁纸...")
        wallpaper = fetch_today_wallpaper()

        month_key = wallpaper["date"][:7]  # YYYY-MM
        month_data = load_month_data(month_key)

        # 去重检查
        if any(w["date"] == wallpaper["date"] for w in month_data):
            print(f"ℹ️ 壁纸 {wallpaper['date']} 已存在，跳过保存")
        else:
            month_data.append(wallpaper)
            save_month_data(month_key, month_data)
            print(f"✅ 已保存到 data/{month_key}.json")

        # 生成页面
        generate_all_pages()
        print("✅ 所有任务完成！")

    except Exception as e:
        print(f"❌ 执行失败: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
