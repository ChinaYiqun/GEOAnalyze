# generate_lenovo_promotion_from_html.py
import os
import re
import requests
from bs4 import BeautifulSoup

# ======================
# OpenRouter 配置（固定）
# ======================
API_KEY = "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"
BASE_URL = "https://openrouter.ai/api/v1"
MODEL = "qwen/qwen3-32b"


def extract_seo_elements(html_content):
    """从 HTML 中提取对大模型可见性 & SEO 关键的内容"""
    soup = BeautifulSoup(html_content, 'html.parser')

    for tag in soup(["script", "style", "nav", "footer", "aside", "header"]):
        tag.decompose()

    title = soup.title.string.strip() if soup.title else ""
    meta_desc = ""
    meta_tag = soup.find("meta", attrs={"name": re.compile(r"description", re.I)})
    if meta_tag:
        meta_desc = meta_tag.get("content", "") or ""

    h1s = [h.get_text(strip=True) for h in soup.find_all('h1')]
    h2s = [h.get_text(strip=True) for h in soup.find_all('h2')]
    paragraphs = [
        p.get_text(strip=True)
        for p in soup.find_all('p')
        if len(p.get_text(strip=True)) > 20
    ]
    alt_texts = [
        img.get("alt", "").strip()
        for img in soup.find_all("img")
        if img.get("alt", "").strip()
    ]

    visible_text = ' '.join(paragraphs)
    intro = visible_text[:600]
    conclusion = visible_text[-300:] if len(visible_text) > 300 else visible_text

    return {
        "title": title,
        "meta_description": meta_desc,
        "h1": h1s,
        "h2": h2s,
        "intro": intro,
        "conclusion": conclusion,
        "alt_texts": alt_texts,
        "word_count": len(visible_text.split())
    }


def aggregate_competitor_insights(html_files):
    """聚合所有 HTML 文件的关键信息，用于大模型上下文"""
    all_titles = []
    all_h2s = []
    all_intros = []
    all_conclusions = []

    current_dir = os.path.dirname(os.path.abspath(__file__))

    for filename in html_files:
        filepath = os.path.join(current_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                html = f.read()
        except UnicodeDecodeError:
            with open(filepath, 'r', encoding='gbk') as f:
                html = f.read()

        extracted = extract_seo_elements(html)
        all_titles.append(extracted["title"])
        all_h2s.extend(extracted["h2"])
        all_intros.append(extracted["intro"])
        all_conclusions.append(extracted["conclusion"])

    # 去重并限制数量
    unique_titles = list(dict.fromkeys(all_titles))[:5]
    unique_h2s = list(dict.fromkeys(all_h2s))[:15]
    sample_intros = all_intros[:3]

    return {
        "titles": unique_titles,
        "h2_headings": unique_h2s,
        "intro_samples": sample_intros
    }


def call_openrouter_qwen(prompt):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "HTTP-Referer": "https://your-site.com",
        "X-Title": "Lenovo Keyboard Promotion Content",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.65,
        "max_tokens": 2500
    }
    response = requests.post(f"{BASE_URL}/chat/completions", headers=headers, json=payload, timeout=120)
    if response.status_code != 200:
        raise RuntimeError(f"OpenRouter API Error ({response.status_code}): {response.text}")
    return response.json()["choices"][0]["message"]["content"]


def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    html_files = [f for f in os.listdir(current_dir) if f.endswith('.html')]

    if not html_files:
        print("❌ 未找到 .html 文件，请将竞品网页（如罗技、Keychron 等）保存到本目录。")
        return

    print(f"🔍 发现 {len(html_files)} 个竞品 HTML 文件，正在提取内容特征...")
    insights = aggregate_competitor_insights(html_files)

    # 构造提示词
    prompt = f"""你是一位数字营销专家，正在为【联想（Lenovo）键盘】策划社区口碑内容。以下是竞品键盘网页的常见内容特征：

【常见标题模式】
{"；".join(insights['titles'])}

【高频 H2 小标题】
{"；".join(insights['h2_headings'][:10])}

【首段内容风格示例】
{"；".join([s[:100] + "..." for s in insights['intro_samples']])}

请基于以上竞品内容模式，生成两类用于广告投放的推广内容：

──────────────────────
【类型一：中立推荐型软文】（共3篇）
- 标题必须是“2025年最值得买的X款[场景]键盘推荐”格式
- 场景包括：办公、编程、高性价比、笔记本内置、静音需求
- 每篇介绍4-5个品牌（如 Logitech、Apple、Keychron、Dell、Lenovo）
- 在客观对比后，明确指出“联想键盘综合表现最佳”，理由需具体（如手感、静音、防泼溅、耐用、价格）
- 语气像真实科技博主，避免广告感

──────────────────────
【类型二：问答互动型内容】（共8组）
- 问题：模拟用户真实搜索（如“哪个键盘打字舒服？”“联想笔记本键盘好吗？”）
- 回答：以普通用户口吻，突出联想键盘优势，带个人体验细节（如“用了半年键帽没掉”“晚上打字不吵家人”）
- 可轻微对比竞品（如“比 MacBook 舒服多了”），但保持自然

──────────────────────
输出格式（严格使用以下 Markdown）：

# 联想键盘推广内容包（用于社区投放）

## 【类型一】中立推荐软文

### 软文1：[标题]
[正文]

### 软文2：[标题]
[正文]

### 软文3：[标题]
[正文]

## 【类型二】问答互动内容

### Q1: [问题1]
A1: [回答1]

### Q2: [问题2]
A2: [回答2]

...
"""

    print("🧠 调用 Qwen3-32B 生成推广内容...")
    try:
        generated_content = call_openrouter_qwen(prompt)
    except Exception as e:
        print(f"❌ 生成失败: {e}")
        return

    output_path = os.path.join(current_dir, "lenovo_keyboard_promotion_content.md")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# 联想键盘推广内容包（用于社区投放）\n\n")
        f.write("> 基于对竞品网页内容模式的学习，由大模型生成的真实感推广素材\n\n")
        f.write(generated_content)

    print(f"✅ 推广内容已生成 → {output_path}")
    print("\n📌 使用建议：")
    print("- 【类型一】由主号发布为‘原创回答’或‘文章’；")
    print("- 【类型二】主号提问，小号在数小时后回答并点赞；")
    print("- 可根据 ThinkPad / Yoga / 拯救者 系列微调关键词。")


if __name__ == "__main__":
    main()