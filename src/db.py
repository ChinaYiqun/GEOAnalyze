import pymysql
from pymysql.err import OperationalError, ProgrammingError, InterfaceError

def connect_mysql_and_manage_table():
    """
    主函数：连接数据库 + 建表 + 插入样例数据
    返回：数据库连接对象（成功）/ None（失败）
    """
    # 数据库连接配置
    db_config = {
        "host": "rm-2ze9gpdcg0c0j8b4k0o.mysql.rds.aliyuncs.com",
        "port": 3306,
        "user": "wangyq68",
        "password": "Ai123456!",
        "database": "ai_lens",
        "charset": "utf8mb4",
        "connect_timeout": 10
    }

    conn = None
    cursor = None  # 单独声明游标变量，避免finally中引用未定义的变量
    try:
        # 建立数据库连接
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()
        print(" 数据库连接成功！")
        return conn

    except OperationalError as e:
        print(f" 连接失败：{e}")
        print("可能原因：IP/端口错误、用户名/密码错误、数据库不存在、服务器防火墙限制等")
    except ProgrammingError as e:
        print(f" SQL执行/删表/建表错误：{e}")
        print("可能原因：SQL语法错误、JSON类型不兼容（MySQL < 5.7）、用户无删表/建表权限")
    except InterfaceError as e:
        print(f" 数据库接口错误：{e}")
    except Exception as e:
        print(f" 未知错误：{e}")
    finally:
        # 关闭游标（连接返回给调用方）
        if cursor:
            try:
                cursor.close()
            except Exception as e:
                print(f"关闭游标失败：{e}")
    return None



db_conn = connect_mysql_and_manage_table()

