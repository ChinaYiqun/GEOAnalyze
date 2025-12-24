import asyncio
from src.db import db_conn
from src.analysis.dwd_fact_brand_mentions import get_top_keyboard_brand
from src.analysis.dwd_fact_citations import get_citations_by_brand
from src.analysis.dwd_fact_citations import sample_urls_by_source
from src.analysis.dwd_fact_citations import sample_urls_by_domain
from src.crawler.crawler4aiScript import crawl_urls
from src.crawler.crawler4aiScript import analyze_reddit_pages

if __name__ == "__main__":
    # 执行主逻辑
    top_brand = get_top_keyboard_brand(db_conn,"2025-12-17")

    citations = get_citations_by_brand(db_conn, brand=top_brand, category="keyboard")

    sampled_urls = sample_urls_by_domain(citations, urls_per_type=10)

    reddit_urls = sampled_urls['reddit.com']

    # Step 4: 【关键】使用 asyncio.run 调用异步分析函数
    print("\n🔍 开始爬取并分析 Reddit 帖子...")
    results = asyncio.run(
        analyze_reddit_pages(reddit_urls, output_dir="./reddit_analysis")
    )