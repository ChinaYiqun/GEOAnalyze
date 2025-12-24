def get_top_keyboard_brand(conn, target_date):
    """
    查询 dwd_fact_brand_mentions 表中指定日期、category='keyboard' 且 is_top3=1 的记录，
    统计各品牌出现次数，返回当天排名第一的品牌名称。

    Args:
        conn (pymysql.Connection): 数据库连接对象
        target_date (str): 业务日期，格式 'YYYY-MM-DD'，对应 stat_date 字段

    Returns:
        str or None: 当天排名第一的品牌名称，若无数据则返回 None
    """
    print(f"Getting top keyboard brands for date: {target_date}...")

    sql = """
        SELECT brand_name, COUNT(*) AS mention_count
        FROM dwd_fact_brand_mentions
        WHERE category = %s
          AND is_top3 = 1
          AND stat_date = %s
        GROUP BY brand_name
        ORDER BY mention_count DESC
        LIMIT 1
    """

    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, ('keyboard', target_date))
            result = cursor.fetchone()

            if result:
                top_brand = result[0]
                return top_brand
            else:
                print(f"⚠️ No keyboard brand found in top3 mentions on {target_date}.")
                return None

    except Exception as e:
        print(f"❌ Error querying top keyboard brand for {target_date}: {e}")
        return None