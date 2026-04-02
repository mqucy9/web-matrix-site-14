import os
import sys
import json
import random
import re
import uuid
import glob
from datetime import datetime
from pathlib import Path
import google.generativeai as genai

POSTS_DIR = "posts"
CONFIG_FILE = "site_config.json"
ADS_FILE = "ads.json"
POSTS_PER_PAGE = 15
MIN_WORDS = 650
MIN_CHARS = 1200


def load_json(path, default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return default


def default_config(repo_name: str):
    repo_id_match = re.search(r"\d+", repo_name or "")
    repo_id = int(repo_id_match.group()) if repo_id_match else 1

    if 1 <= repo_id <= 20:
        return {
            "site_name": f"Gold Intelligence #{repo_id:02d}",
            "niche": "XAUUSD / Gold trading",
            "theme_color": "#fbbf24",
            "primary_keywords": [
                "gold price forecast 2026",
                "XAUUSD outlook",
                "gold trading strategy",
                "gold inflation hedge",
                "gold macro view 2026"
            ],
            "long_tail_keywords": [
                "how to hedge with gold in 2026",
                "best time to buy gold 2026",
                "gold macro analysis 2026",
                "gold swing trading signals",
                "gold seasonality 2026"
            ],
            "language": "zh",
            "word_count_min": MIN_WORDS
        }
    elif 21 <= repo_id <= 35:
        return {
            "site_name": f"Enterprise AI #{repo_id:02d}",
            "niche": "Enterprise AI / Automation",
            "theme_color": "#3b82f6",
            "primary_keywords": [
                "enterprise ai",
                "rag架构",
                "ai自动化",
                "大模型治理",
                "llm风控"
            ],
            "long_tail_keywords": [
                "企业如何部署LLM",
                "rag向量检索最佳实践",
                "ai自动化降本案例",
                "llm安全合规2026",
                "国产大模型选型2026"
            ],
            "language": "zh",
            "word_count_min": MIN_WORDS
        }
    else:
        return {
            "site_name": f"Cyber Defense #{repo_id:02d}",
            "niche": "Cybersecurity & Zero Trust",
            "theme_color": "#ef4444",
            "primary_keywords": [
                "zero trust",
                "ransomware防御",
                "身份安全",
                "云安全",
                "威胁情报"
            ],
            "long_tail_keywords": [
                "零信任落地指南2026",
                "中小企业防勒索方案",
                "云安全合规2026",
                "SOC自动化威胁狩猎",
                "安全运营成熟度2026"
            ],
            "language": "zh",
            "word_count_min": MIN_WORDS
        }


def generate_ads(cfg: dict, repo_id: int) -> dict:
    palette = cfg.get("theme_color", "#3b82f6")
    coupon = f"{repo_id:02d}-{uuid.uuid4().hex[:6]}".upper()
    header = (
        f"<div class='ad' style='margin:16px 0;padding:14px;border:1px dashed {palette};"
        f"border-radius:10px;background:linear-gradient(120deg,{palette}1A,#0d1117);'>"
        f"<strong>赞助推荐</strong>: {cfg['site_name']} 精选资源，券码 {coupon}</div>"
    )
    mid = (
        f"<div class='ad' style='margin:18px 0;padding:14px;border:1px solid {palette};"
        "border-radius:12px;background:#111827;'>"
        f"获取最新 {cfg['niche']} 白皮书，立即试用。</div>"
    )
    footer = (
        f"<div class='ad' style='margin:20px 0;padding:14px;border:1px dashed {palette};"
        "border-radius:12px;background:#0b1220;">"
        "长按收藏，订阅每日更新。</div>"
    )
    return {"header": header, "mid": mid, "footer": footer}


def insert_mid_ad(html: str, mid_ad: str) -> str:
    if not mid_ad:
        return html
    split = re.split(r"(</h2>)", html, maxsplit=1)
    if len(split) == 3:
        return split[0] + split[1] + mid_ad + split[2]
    split = re.split(r"(</p>)", html, maxsplit=2)
    if len(split) >= 3:
        return split[0] + split[1] + mid_ad + "".join(split[2:])
    return html + mid_ad


def effective_chars(html: str) -> int:
    plain = re.sub(r"<[^>]+>", " ", html)
    return len(plain.replace(" ", ""))


def run():
    api_key = os.environ.get("AI_API_KEY") or os.environ.get("GEMINI_API_KEY")
    repo_full_name = os.environ.get("GITHUB_REPOSITORY", "user/site-01")
    repo_name = repo_full_name.split("/")[-1]

    if not api_key:
        print("Missing AI_API_KEY / GEMINI_API_KEY.")
        sys.exit(1)

    cfg = default_config(repo_name)
    cfg.update(load_json(CONFIG_FILE, {}))

    repo_id_match = re.search(r"\d+", repo_name or "")
    repo_id = int(repo_id_match.group()) if repo_id_match else 1

    ads_override = load_json(ADS_FILE, {})
    ads = generate_ads(cfg, repo_id)
    ads.update(ads_override)

    persona = random.choice(["行业分析师", "资深架构师", "策略顾问", "研究员", "投研总监", "SOC领班"])
    primary_kw = random.choice(cfg["primary_keywords"])
    long_tail_kw = random.choice(cfg["long_tail_keywords"])
    kw_pool = cfg["primary_keywords"] + cfg["long_tail_keywords"]
    kw_pack = ", ".join(random.sample(kw_pool, k=min(5, len(kw_pool))))

    unique_session = uuid.uuid4().hex[:8]
    prompt = f"""
用{cfg['language']}写一篇原创长文，至少 {cfg.get('word_count_min', MIN_WORDS)} 个词，主题：{cfg['niche']}。
角色：{persona}。
主关键词：{primary_kw}；长尾词：{long_tail_kw}；热词包：{kw_pack}。
结构：H1(含主关键词)、执行摘要、3-5 个 H2 小节、FAQ(3问3答)、结论；自然嵌入关键词；附 155-160 字符 META 描述，前缀写 META:
使用 <h1><h2><h3><p><ul><li> HTML；不要代码块。
结合 {datetime.now().strftime('%Y-%m-%d')} 最新趋势，引用具体案例或数据，确保与历史不同。
"""

    genai.configure(api_key=api_key)
    article_html = ""
    for model_name in ["gemini-1.5-flash-latest", "gemini-1.5-flash"]:
        try:
            model = genai.GenerativeModel(model_name)
            resp = model.generate_content(prompt, generation_config={"temperature": 0.95})
            if resp.text:
                article_html = resp.text.replace("```html", "").replace("```", "").strip()
                break
        except Exception as e:
            print(f"model {model_name} failed: {e}")
            continue

    if effective_chars(article_html) < MIN_CHARS:
        print("Generated content too short; abort to protect SEO.")
        sys.exit(0)

    Path(POSTS_DIR).mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    meta_info = (
        f"<div class=\"meta\" style=\"color:{cfg['theme_color']}; font-size:13px; "
        f"margin-bottom:15px; font-family:monospace;\">"
        f"PUBLISHED: {datetime.now().strftime('%Y-%m-%d %H:%M')} // SESSION: {unique_session}"
        "</div>"
    )

    post_body = ads["header"] + insert_mid_ad(article_html, ads["mid"]) + ads["footer"]
    post_html = f'<article class="post-item" style="margin-bottom:80px;">{meta_info}{post_body}</article>'
    post_path = Path(POSTS_DIR) / f"{timestamp}-{unique_session}.html"
    post_path.write_text(post_html, encoding="utf-8")

    all_posts = sorted(glob.glob(f"{POSTS_DIR}/*.html"), reverse=True)
    total_pages = (len(all_posts) + POSTS_PER_PAGE - 1) // POSTS_PER_PAGE

    for page_idx in range(1, total_pages + 1):
        start = (page_idx - 1) * POSTS_PER_PAGE
        end = start + POSTS_PER_PAGE
        page_posts_files = all_posts[start:end]
        combined = ""
        for pf in page_posts_files:
            combined += Path(pf).read_text(encoding="utf-8") + '<hr style="border:0; border-top:1px solid #30363d; margin:50px 0;">'

        nav_html = '<div class="pagination" style="margin-top:40px; display:flex; gap:10px; flex-wrap:wrap;">'
        for i in range(1, total_pages + 1):
            target = "index.html" if i == 1 else f"page{i}.html"
            active = f"background:{cfg['theme_color']}; color:#000;" if i == page_idx else "background:#30363d; color:#c9d1d9;"
            nav_html += f'<a href="{target}" style="padding:8px 16px; border-radius:4px; text-decoration:none; font-weight:bold; {active}">Page {i}</a>'
        nav_html += '</div>'

        page_title = f"{cfg['site_name']} - Page {page_idx}"
        meta_desc = f"Latest {cfg['niche']} insights with {primary_kw} and {long_tail_kw}."
        full_html = f"""<!DOCTYPE html>
<html lang=\"zh\">
<head>
  <meta charset=\"UTF-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
  <title>{page_title}</title>
  <meta name=\"description\" content=\"{meta_desc}\">
  <style>
    body{{font-family:'Inter',system-ui,sans-serif; background:#0d1117; color:#c9d1d9; line-height:1.8; padding:20px;}}
    .container{{max-width:880px; margin:0 auto; background:#161b22; padding:40px; border-radius:12px; border-top:6px solid {cfg['theme_color']}; box-shadow:0 15px 35px rgba(0,0,0,0.4);}}
    h1,h2,h3{{color:#f0f6fc; margin-top:1.4em;}}
    .meta{{letter-spacing:1px;}}
    a{{transition:0.3s;}} a:hover{{opacity:0.8;}}
    .ad{{margin:24px 0; padding:12px; background:#111827; border:1px dashed #6b7280; border-radius:8px;}}
  </style>
</head>
<body>
  <div class=\"container\">
    <header style=\"text-align:center; margin-bottom:40px;\">
      <div style=\"color:{cfg['theme_color']}; font-weight:bold; letter-spacing:4px; font-size:14px;\">{cfg['site_name'].upper()}</div>
      <h1 style=\"margin:12px 0 0;\">{cfg['niche']}</h1>
    </header>
    {ads['header']}
    {combined}
    {ads['footer']}
    {nav_html}
  </div>
</body>
</html>"""
        fname = Path("index.html") if page_idx == 1 else Path(f"page{page_idx}.html")
        fname.write_text(full_html, encoding="utf-8")


if __name__ == "__main__":
    run()
