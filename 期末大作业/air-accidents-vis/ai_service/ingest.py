import os
import psycopg2
import faiss
import numpy as np
import pickle
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import torch
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"💻 当前使用的计算设备: {device.upper()}")
# --- 路径配置 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EMBEDDING_PATH = os.path.join(BASE_DIR, "models", "bge-m3")
VECTOR_DB_DIR = os.path.join(BASE_DIR, "vector_db")
INDEX_PATH = os.path.join(VECTOR_DB_DIR, "accidents.index")
MAPPING_PATH = os.path.join(VECTOR_DB_DIR, "mapping.pkl")

# 数据库配置
DB_CONFIG = {
    "dbname": "aviation_safety",
    "user": "postgres",
    "password": "1234", 
    "host": "localhost",
    "port": "5432"
}

def ingest_data():
    if not os.path.exists(VECTOR_DB_DIR):
        os.makedirs(VECTOR_DB_DIR)

    print("⏳ 正在加载 BGE-M3 模型...")
    embed_model = SentenceTransformer(EMBEDDING_PATH)
    embed_model.max_seq_length = 512
    print("⏳ 正在从 PostgreSQL 读取数据...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # 使用你定义的 DetailURL 作为唯一标识
        query = """
            SELECT 
                "Date", "Location", "Type", "Owner/operator", "Fatalities", "Narrative", "DetailURL"
            FROM asn_incidents 
            WHERE "Narrative" IS NOT NULL AND "Narrative" != ''
        """
        cur.execute(query)
        rows = cur.fetchall()
        conn.close()
        print(f"✅ 成功提取 {len(rows)} 条数据")
    except Exception as e:
        print(f"❌ 数据库读取失败: {e}")
        return

    descriptions = []
    metadata = [] 
    
    print("⏳ 正在生成向量 (RAG Knowledge Base)...")
    for row in tqdm(rows):
        date, loc, type_, operator, fatal, narrative, detail_url = row
        
        # --- 增加：物理截断描述内容，建议限制在 500 个字符左右 ---
        # 既保证了核心信息（事故原因通常在开头），又避免了超长文本拖慢速度
        short_narrative = (narrative[:500] + '...') if narrative and len(narrative) > 500 else (narrative or "")
        
        # 使用截断后的文本构建 chunk
        text_chunk = f"时间: {date}, 飞机: {type_}, 运营商: {operator}, 地点: {loc}, 描述: {short_narrative}"
        
        descriptions.append(text_chunk)
        metadata.append({
            "pk": detail_url,
            "date": str(date),
            "type": type_,
            "narrative": short_narrative # 存储截断后的内容，节省 mapping.pkl 的空间
        })

    # 批量 Embedding
    embeddings = embed_model.encode(descriptions, batch_size=32, show_progress_bar=True, normalize_embeddings=True)

    # 构建 FAISS 索引
    print("⏳ 正在构建索引...")
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension) 
    index.add(embeddings.astype('float32'))

    # 持久化存储
    print(f"💾 正在保存至 {VECTOR_DB_DIR}...")
    faiss.write_index(index, INDEX_PATH)
    with open(MAPPING_PATH, 'wb') as f:
        pickle.dump(metadata, f)

    print("🎉 向量数据库构建成功！")

if __name__ == "__main__":
    ingest_data()