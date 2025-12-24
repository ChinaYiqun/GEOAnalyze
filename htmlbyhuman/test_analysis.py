# analyze_competitor_for_lenovo_keyboard.py
import os
import re
import json
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# ======================
# 配置你的 OpenRouter 凭据
# ======================
API_KEY = "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"
BASE_URL = "https://openrouter.ai/api/v1"
MODEL = "qwen/qwen3-32b"


def extract_seo_elements(html_content):
    """从 HTML 中提取对大模型可见性 & SEO 关键的内容"""
    soup = BeautifulSoup(html_content, 'html.parser')

    # 移除干扰元素
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
        "h2": h2s[:6],  # 取前6个 H2
        "intro": intro,
        "conclusion": conclusion,
        "alt_texts": alt_texts[:5],
        "word_count": len(visible_text.split())
    }


def call_openrouter_qwen(prompt):
    """调用 OpenRouter 的 Qwen3-32B 模型"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "HTTP-Referer": "https://your-site.com",  # OpenRouter 要求（可填任意）
        "X-Title": "Lenovo Keyboard SEO Analysis",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.4,
        "max_tokens": 1500
    }

    response = requests.post(
        f"{BASE_URL}/chat/completions",
        headers=headers,
        json=payload,
        timeout=90
    )

    if response.status_code != 200:
        raise RuntimeError(f"OpenRouter API Error ({response.status_code}): {response.text}")

    data = response.json()
    return data["choices"][0]["message"]["content"]


def generate_analysis_prompt(extracted, filename):
    brand_guess = re.sub(r'[^a-zA-Z]', '', filename.replace('.html', '')).capitalize() or "UnknownBrand"

    prompt = f"""你是一位精通 SEO 与大模型内容分发机制的数字营销专家。以下是从一个竞品键盘品牌（推测为 {brand_guess}）网页中提取的关键内容：

【页面标题】
{extracted['title']}

【Meta 描述】
{extracted['meta_description']}

【H1 标题】
{"；".join(extracted['h1']) if extracted['h1'] else "无"}

【H2 小标题（节选）】
{"；".join(extracted['h2'])}

【首段内容（约前600字符）】
{extracted['intro']}

【结尾总结（约后300字符）】
{extracted['conclusion']}

【图片 Alt 文本示例】
{"；".join(extracted['alt_texts'])}

【字数估算】
约 {extracted['word_count']} 词

请基于以上信息，完成以下任务：

1. 分析该页面为何可能在大模型（如 AI 搜索、RAG 系统）中获得高可见性？重点关注：
   - 是否清晰回答了用户问题（如“手感如何？”“适合打游戏吗？”）
   - 是否包含结构化内容（对比表格、参数列表、步骤指南）
   - 是否覆盖多种搜索意图（信息型、评测型、交易型）

2. 为【联想（Lenovo）键盘】产品制定一套内容优化策略，用于撰写高曝光的：
   - 官网产品页
   - 第三方媒体软文
   - 用户评论/评测帖

具体建议需包括：
✅ 推荐标题模板（含核心关键词如“联想键盘”“ThinkPad 键盘”）
✅ 首段必须包含的关键词与用户痛点（如“静音”“回弹手感”“防泼溅”）
✅ 内容结构建议（例如：H2 小标题应包含哪些长尾词）
✅ 应加入哪些高价值模块（如“vs 罗技 MX Keys 对比”、“程序员实测一周”）
✅ Meta Description 与图片 Alt 标签示例
✅ 如何设计内链锚文本（如链接到“联想笔记本键盘更换指南”）

要求：语言简洁、可执行、避免空泛理论，直接给出可复用的文案框架。
"""
    return prompt


def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    html_files = [f for f in os.listdir(current_dir) if f.endswith('.html')]

    if not html_files:
        print("❌ 未找到 .html 文件，请将竞品网页保存到本目录。")
        return

    print(f"🔍 发现 {len(html_files)} 个竞品 HTML 文件，开始分析...\n")

    all_reports = []

    for i, filename in enumerate(html_files, 1):
        print(f"[{i}/{len(html_files)}] 处理: {filename}")
        filepath = os.path.join(current_dir, filename)

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                html = f.read()
        except UnicodeDecodeError:
            with open(filepath, 'r', encoding='gbk') as f:
                html = f.read()

        extracted = extract_seo_elements(html)
        prompt = generate_analysis_prompt(extracted, filename)

        try:
            print("   → 调用 Qwen3-32B 分析中...")
            analysis = call_openrouter_qwen(prompt)
            all_reports.append({
                "source_file": filename,
                "analysis": analysis
            })
            print("   ✅ 分析完成\n")
        except Exception as e:
            print(f"   ❌ 失败: {str(e)}\n")
            continue

    # 保存报告
    output_path = os.path.join(current_dir, "lenovo_keyboard_visibility_strategy.md")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# 联想键盘大模型可见性提升策略报告\n\n")
        f.write("> 基于对竞品网页的 HTML 内容分析，由 Qwen3-32B 生成的可执行建议\n\n")
        for report in all_reports:
            f.write(f"## 来源文件: `{report['source_file']}`\n\n")
            f.write(report["analysis"])
            f.write("\n\n---\n\n")

    print(f"✅ 报告已生成: {output_path}")
    print("\n🎯 下一步行动建议：")
    print("- 优先实施“标题+首段+H2”关键词布局")
    print("- 创建 3-5 篇深度评测/对比软文（参考报告中的模板）")
    print("- 优化官网产品页的 Meta 与 Alt 标签")


if __name__ == "__main__":
    main()