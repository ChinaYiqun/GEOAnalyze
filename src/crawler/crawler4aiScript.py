# src/crawler/crawler4aiScript.py
import os
import asyncio
from crawl4ai import AsyncWebCrawler
from openai import OpenAI

# === 大模型配置 ===
API_KEY = "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"
BASE_URL = "https://openrouter.ai/api/v1"
MODEL = "qwen/qwen3-32b"  # 强烈推荐纯文本模型；如需多模态可换回 qwen/qwen3-vl-8b-instruct

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

async def _crawl_urls_async(sampled_urls, output_dir="./crawlhtml"):
    """内部异步函数"""
    saved_files = {}

    async with AsyncWebCrawler() as crawler:
        for source_type, url_list in sampled_urls.items():
            print(f"\n🌐 Crawling {len(url_list)} URLs from source type: {source_type}")

            save_dir = os.path.join(output_dir, source_type)
            os.makedirs(save_dir, exist_ok=True)
            saved_files[source_type] = []

            for idx, url in enumerate(url_list, start=1):
                try:
                    print(f"  → ({idx}/{len(url_list)}) {url}")

                    # 执行异步爬取
                    result = await crawler.arun(
                        url=url,
                        word_count_threshold=10,
                        bypass_cache=False,
                        magic=True  # 启用智能内容提取
                    )

                    if result.success and result.markdown:  # v0.7.8 返回 markdown / html
                        # 保存 HTML（也可以保存 markdown）
                        filename = f"page_{idx}.html"
                        filepath = os.path.join(save_dir, filename)

                        with open(filepath, "w", encoding="utf-8") as f:
                            f.write(result.html)  # 或 result.markdown（如果你想要 Markdown）

                        saved_files[source_type].append(filepath)
                        print(f"    ✅ Saved: {filepath}")
                    else:
                        print(f"    ❌ Failed to extract content from: {url}")

                except Exception as e:
                    print(f"    ⚠️ Error on {url}: {e}")
                    continue

    print(f"\n✅ All crawling completed. Files saved under: {os.path.abspath(output_dir)}")
    return saved_files


def crawl_urls(sampled_urls, output_dir="./crawlhtml"):
    """
    同步接口：供 main.py 调用
    """
    return asyncio.run(_crawl_urls_async(sampled_urls, output_dir))

async def analyze_reddit_pages(reddit_urls, output_dir="./reddit_analysis"):
    """
    爬取 reddit_urls 中的每个网页 HTML，并用大模型分析内容

    Args:
        reddit_urls (list): Reddit 帖子 URL 列表
        output_dir (str): 输出目录（保存 HTML 和分析结果）

    Returns:
        list[dict]: 每个元素包含 url, html_path, analysis
    """
    os.makedirs(output_dir, exist_ok=True)
    results = []

    async with AsyncWebCrawler() as crawler:
        for idx, url in enumerate(reddit_urls, start=1):
            print(f"\n🌐 [{idx}/{len(reddit_urls)}] 正在处理: {url}")

            try:
                # Step 1: 爬取页面
                result = await crawler.arun(
                    url=url,
                    word_count_threshold=10,
                    magic=True,  # 启用智能渲染和内容提取
                    bypass_cache=False,
                    timeout=30  # 防止卡死
                )

                if not (result.success and result.html):
                    print(f"  ❌ 爬取失败或无内容: {url}")
                    results.append({
                        "url": url,
                        "html_path": None,
                        "analysis": "❌ 爬取失败：未获取到有效HTML内容"
                    })
                    continue

                # Step 2: 保存 HTML
                safe_filename = f"page_{idx:02d}.html"
                html_path = os.path.join(output_dir, safe_filename)
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(result.html)
                print(f"  ✅ HTML 已保存: {html_path}")

                # Step 3: 用大模型分析（优先使用 markdown，更干净）
                content = (result.markdown or result.html)[:12000]  # 截断防超限

                prompt = f"""
你是一个专业的网络内容分析师。请分析以下从 Reddit 抓取的帖子内容，并以简洁清晰的方式回答：

1. **帖子标题**（如果可识别）
2. **核心讨论主题**
3. **主要观点或建议**（如产品推荐、经验分享等）
4. **是否有争议、广告或低质量内容？**

URL: {url}

抓取内容如下：
{content}
"""

                # 调用大模型
                response = client.chat.completions.create(
                    model=MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=500
                )
                analysis = response.choices[0].message.content.strip()

                # 保存分析结果
                results.append({
                    "url": url,
                    "html_path": html_path,
                    "analysis": analysis
                })
                print(f"  🧠 分析完成")

            except Exception as e:
                error_msg = f"⚠️ 处理异常: {str(e)}"
                print(f"  {error_msg}")
                results.append({
                    "url": url,
                    "html_path": None,
                    "analysis": error_msg
                })

            # 可选：加延迟避免触发反爬
            await asyncio.sleep(1)

    # 保存完整报告
    report_path = os.path.join(output_dir, "analysis_report.json")
    import json
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 全部分析完成！报告已保存至: {os.path.abspath(report_path)}")

    return results