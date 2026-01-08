import pandas as pd
import mysql.connector
import os

# --- 数据库连接配置 ---
DB_CONFIG = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': 'Lzy225678!',  
    'database': 'sci_data_analysis' 
}


CSV_FOLDER_PATH = './csv_files' 


def import_csv_to_mysql(file_path, discipline_name, connection):
    print(f"正在导入文件: {file_path} (学科: {discipline_name})...")
    try:
        df = pd.read_csv(
        file_path,
        skipinitialspace=True,
        skiprows=[0, 1],
        header=None,
        encoding='latin-1' 
    )
        # 检查DataFrame是否为空，避免在空DataFrame上调用.drop()
        if not df.empty:
            df = df.drop(df.tail(1).index) # 删除最后一行


    # 重新命名列，确保与数据库表字段对应
        df.columns = [
        'ranking', # 现在第一列是排名
        'institution_name',
        'country_region',
        'web_of_science_documents',
        'cites',
        'cites_per_paper',
        'top_papers'
    ]
        
        # 筛选出我们需要导入的列，并添加discipline列
        df_to_insert = df[[
            'ranking',
            'institution_name',
            'country_region',
            'web_of_science_documents',
            'cites',
            'cites_per_paper',
            'top_papers'
        ]].copy()
        df_to_insert['discipline'] = discipline_name

        df_to_insert = df_to_insert.fillna('')


        # 重新排列列顺序以匹配数据库表
        df_to_insert = df_to_insert[[
            'discipline',
            'ranking',
            'institution_name',
            'country_region',
            'web_of_science_documents',
            'cites',
            'cites_per_paper',
            'top_papers'
        ]]

        # 将DataFrame数据转换为列表的元组，以便于批量插入
        records_to_insert = [tuple(row) for row in df_to_insert.to_numpy()]

        cursor = connection.cursor()
        
        # 构建插入语句
        sql_insert = """
        INSERT INTO institution_performance (
            discipline,
            ranking,  -- <-- 新增这一行
            institution_name,
            country_region,
            web_of_science_documents,
            cites,
            cites_per_paper,
            top_papers
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) -- <-- 占位符数量也需要是 8 个
        """
        
        # 批量插入数据
        if records_to_insert:
            cursor.executemany(sql_insert, records_to_insert)
            connection.commit()
            print(f"成功导入 {len(records_to_insert)} 条记录到数据库。")
        else:
            print(f"文件 {file_path} 没有可导入的数据。")

    except pd.errors.EmptyDataError:
        print(f"文件 {file_path} 是空的，跳过。")
    except pd.errors.ParserError as e:
        print(f"解析文件 {file_path} 错误: {e}")
    except Exception as e:
        print(f"导入文件 {file_path} 时发生错误: {e}")
        connection.rollback() 
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()

def main():
    try:
        # 连接到MySQL数据库
        conn = mysql.connector.connect(**DB_CONFIG)
        if conn.is_connected():
            print("成功连接到MySQL数据库。")
        
        # 遍历CSV文件夹中的所有文件
        for filename in os.listdir(CSV_FOLDER_PATH):
            if filename.endswith('.csv'):
                file_path = os.path.join(CSV_FOLDER_PATH, filename)
                # 从文件名中提取学科名称（去除.csv后缀）
                discipline_name = os.path.splitext(filename)[0]
                import_csv_to_mysql(file_path, discipline_name, conn)

    except mysql.connector.Error as err:
        print(f"数据库连接错误: {err}")
    except Exception as e:
        print(f"发生未预期错误: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()
            print("数据库连接已关闭。")

if __name__ == "__main__":
    main()

