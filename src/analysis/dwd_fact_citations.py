import random
from collections import defaultdict

def get_citations_by_brand(conn, brand, category="keyboard"):
    """
    根据品牌名称，获取其在 dwd_fact_citations 中的所有引用 URL 及信源类型。

    Args:
        conn (pymysql.Connection): 数据库连接
        brand (str): 品牌名称，如 "Logitech"
        category (str): 品类，默认 "keyboard"

    Returns:
        List[Dict]: 每个元素包含 {'original_url', 'source_type', 'main_domain'}
                    若无数据，返回空列表 []
    """
    print(f"Fetching citations for brand: {brand}, category: {category}...")

    try:
        with conn.cursor() as cursor:
            # Step 1: 获取该品牌在 top3 中的所有 collection_id
            sql_get_ids = """
                SELECT DISTINCT collection_id
                FROM dwd_fact_brand_mentions
                WHERE brand_name = %s
                  AND category = %s
                  AND is_top3 = 1
            """
            cursor.execute(sql_get_ids, (brand, category))
            collection_ids = [row[0] for row in cursor.fetchall()]

            if not collection_ids:
                print(f"⚠️ No collection_id found for brand '{brand}' in top3 mentions.")
                return []

            # Step 2: 用 collection_id 列表查询 citations
            # 注意：MySQL IN 子句不能直接传 list，需动态生成占位符
            format_strings = ','.join(['%s'] * len(collection_ids))
            sql_get_citations = f"""
                SELECT DISTINCT original_url, source_type, main_domain
                FROM dwd_fact_citations
                WHERE collection_id IN ({format_strings})
                  AND original_url IS NOT NULL
                  AND original_url != ''
            """
            cursor.execute(sql_get_citations, collection_ids)
            results = cursor.fetchall()

            # 转为字典列表
            citations = [
                {
                    "original_url": row[0],
                    "source_type": row[1] or "Unknown",
                    "main_domain": row[2]
                }
                for row in results
                if row[0]  # 确保 URL 非空
            ]

            print(f"✅ Found {len(citations)} unique citation URLs for brand '{brand}'.")
            return citations

    except Exception as e:
        print(f"❌ Error fetching citations for brand '{brand}': {e}")
        return []

import random

def sample_urls_by_source(citations, urls_per_type=5):
    """
    按 source_type 分组，并为每组随机采样最多 urls_per_type 个 original_url。

    Args:
        citations (List[Dict]): 每个元素含 'source_type' 和 'original_url'
        urls_per_type (int): 每类最多采样数量，默认 5

    Returns:
        Dict[str, List[str]]: {source_type: [url1, url2, ...]}
    """
    # 按 source_type 分组（自动去重）
    grouped = defaultdict(list)
    seen = set()  # 全局去重，避免同一 URL 出现在多个类型（虽然理论上不会）

    for cit in citations:
        stype = cit.get("source_type", "Unknown")
        url = cit.get("original_url")
        if url and url.startswith(("http://", "https://")) and url not in seen:
            grouped[stype].append(url)
            seen.add(url)

    # 每组随机采样
    sampled = {}
    for stype, urls in grouped.items():
        random.shuffle(urls)  # 随机打乱
        sampled[stype] = urls[:urls_per_type]

    return sampled

def sample_urls_by_domain(citations, urls_per_type=5):
    """
    按 source_type 分组，并为每组随机采样最多 urls_per_type 个 original_url。

    Args:
        citations (List[Dict]): 每个元素含 'main_domain' 和 'original_url'
        urls_per_type (int): 每类最多采样数量，默认 5

    Returns:
        Dict[str, List[str]]: {source_type: [url1, url2, ...]}
    """
    # 按 source_type 分组（自动去重）
    grouped = defaultdict(list)
    seen = set()  # 全局去重，避免同一 URL 出现在多个类型（虽然理论上不会）

    for cit in citations:
        domain = cit.get("main_domain", "Unknown")
        url = cit.get("original_url")
        if url and url.startswith(("http://", "https://")) and url not in seen:
            grouped[domain].append(url)
            seen.add(url)

    # 每组随机采样
    sampled = {}
    for domain, urls in grouped.items():
        random.shuffle(urls)  # 随机打乱
        sampled[domain] = urls[:urls_per_type]

    return sampled
