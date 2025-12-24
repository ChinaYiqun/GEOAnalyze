from src.db import db_conn
from src.analysis.dwd_fact_brand_mentions import get_top_keyboard_brand
from src.analysis.dwd_fact_citations import get_citations_by_brand
from src.analysis.dwd_fact_citations import sample_urls_by_source
from src.crawler.crawler4aiScript import crawl_urls


if __name__ == "__main__":
    # 执行主逻辑，提取日期内的所有top-3数据
    top_brand = get_top_keyboard_brand(db_conn,"2025-12-17")

    citations = get_citations_by_brand(db_conn, brand=top_brand, category="keyboard")

    # 每个类型采样5个URL
    sampled_urls = sample_urls_by_source(citations, urls_per_type=5)

    saved_files = crawl_urls(sampled_urls, output_dir="./crawlhtml")
    # 查看结果
    for stype, paths in saved_files.items():
        print(f"\n{stype} saved {len(paths)} files:")
        for p in paths:
            print(f"  - {p}")
    # to do list
    # # Step 5: Analyze with LLM
    # analysis_results = analyze_html_pages(html_paths)
    #
    # # Step 6: Generate recommendations for Lenovo
    # recommendations = generate_recommendations(analysis_results, target_brand="Lenovo")
    #
    # # Save final report
    # with open("./data/output/lenovo_keyboard_ai_exposure_recommendation.md", "w") as f:
    #     f.write(recommendations)
    #
    # logger.info("Pipeline completed. Report saved.")