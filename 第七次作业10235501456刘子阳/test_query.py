import os
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import FakeEmbeddings

# 设置路径
DB_FAISS_PATH = "./vectorstore/db_faiss"

def test_query():
    """
    测试查询功能
    """
    print("正在加载向量数据库...")
    
    # 使用FakeEmbeddings避免网络连接问题
    embeddings = FakeEmbeddings(size=768)
    
    # 检查数据库路径是否存在
    if not os.path.exists(DB_FAISS_PATH):
        print(f"错误: 向量数据库路径不存在: {DB_FAISS_PATH}")
        return
    
    # 加载向量数据库
    vector_store = FAISS.load_local(DB_FAISS_PATH, embeddings, allow_dangerous_deserialization=True)
    print("向量数据库加载成功!")
    
    # 测试查询
    test_queries = [
        "计算机科学专业排名前十的高校有哪些？",
        "清华大学在哪些学科上表现突出？",
        "农业科学领域有哪些优秀高校？"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"查询: {query}")
        print('='*60)
        
        # 执行相似性搜索
        docs = vector_store.similarity_search(query, k=2)
        
        if docs:
            print(f"找到 {len(docs)} 个相关结果:\n")
            for i, doc in enumerate(docs, 1):
                print(f"--- 结果 {i} ---")
                print(f"内容预览: {doc.page_content[:300]}...")
                print(f"来源: {doc.metadata.get('source', '未知')}")
                print(f"学科: {doc.metadata.get('subject', '未知')}")
                print()
        else:
            print("未找到相关结果。")

if __name__ == "__main__":
    test_query()