import pandas as pd
from sqlalchemy import create_engine
import os
import glob

# ================= 配置区域 =================
DB_USER = "postgres"       # 数据库用户名
DB_PASS = "1234"  # 数据库密码
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "aviation_safety" # 数据库名

# CSV 文件匹配模式 (匹配 asn_cc_20.csv 到 asn_cc_25.csv)
CSV_PATTERN = "asn_cc_*.csv" 
TABLE_NAME = "asn_incidents"
# ===========================================

def import_data():
    # 1. 建立数据库连接
    connection_str = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(connection_str)
    
    print(f"🔗 正在连接数据库: {DB_NAME}...")

    # 2. 找到所有的 csv 文件
    csv_files = glob.glob(CSV_PATTERN)
    if not csv_files:
        print("❌ 未找到任何匹配的 CSV 文件！请检查文件名。")
        return

    print(f"📂 发现 {len(csv_files)} 个文件待导入: {csv_files}")

    total_rows = 0
    for file in csv_files:
        try:
            print(f"   正在处理: {file} ...")
            # 读取 CSV
            df = pd.read_csv(file)
            
            # 数据清洗：将 Pandas 的 NaN 转换为 None (数据库里的 NULL)
            # 注意：to_sql 通常能自动处理，但为了保险，确保列名匹配
            
            # 写入数据库
            # if_exists='append': 追加模式
            # index=False: 不把 pandas 的索引写入数据库
            df.to_sql(TABLE_NAME, engine, if_exists='append', index=False, method='multi', chunksize=1000)
            
            rows = len(df)
            total_rows += rows
            print(f"   ✅ {file} 导入成功 ({rows} 条)")
            
        except Exception as e:
            print(f"   ❌ {file} 导入失败: {e}")

    print(f"\n🎉 全部完成！共导入 {total_rows} 条数据。")

if __name__ == "__main__":
    import_data()
