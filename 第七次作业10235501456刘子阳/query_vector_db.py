import os
import argparse
import pandas as pd
from typing import List

# 导入必要的库
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain.chains import RetrievalQA
from langchain_community.llms import HuggingFacePipeline


# 设置默认路径
DEFAULT_DB_FAISS_PATH = r"d:\DataEngineering\第七次作业10235501456刘子阳\vectorstore\db_faiss"
DEFAULT_EMBEDDING = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def load_vector_store(db_path: str, embedding_model: str):
    """
    加载已创建的向量数据库
    """
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"向量数据库路径 {db_path} 不存在")
    
    print(f"正在加载向量数据库: {db_path}")
    embeddings = HuggingFaceEmbeddings(model_name=embedding_model)
    vector_store = FAISS.load_local(db_path, embeddings, allow_dangerous_deserialization=True)
    print("向量数据库加载成功")
    return vector_store


def search_similar_documents(vector_store, query: str, k: int = 4):
    """
    搜索相似文档
    """
    print(f"正在搜索与 '{query}' 相关的文档...")
    docs = vector_store.similarity_search(query, k=k)
    return docs


def format_document_content(doc: Document) -> str:
    """
    格式化文档内容以便显示
    """
    content = f"来源: {doc.metadata.get('source', '未知')}\n"
    if 'subject' in doc.metadata:
        content += f"学科: {doc.metadata['subject']}\n"
    if 'file_type' in doc.metadata:
        content += f"文件类型: {doc.metadata['file_type']}\n"
    content += f"内容:\n{doc.page_content}\n"
    content += "-" * 50 + "\n"
    return content


def interactive_query(vector_store):
    """
    交互式查询界面
    """
    print("\n" + "="*60)
    print("欢迎使用高校学科排名问答系统")
    print("="*60)
    print("输入您的问题，系统将根据知识库内容回答")
    print("输入 'quit' 或 'exit' 退出系统")
    print("="*60)
    
    while True:
        try:
            query = input("\n请输入您的问题: ").strip()
            
            if query.lower() in ['quit', 'exit', '退出']:
                print("感谢使用，再见！")
                break
            
            if not query:
                continue
                
            # 搜索相关文档
            docs = search_similar_documents(vector_store, query, k=4)
            
            print(f"\n找到 {len(docs)} 个相关文档:")
            print("="*60)
            
            for i, doc in enumerate(docs, 1):
                print(f"\n【相关文档 {i}】")
                print(format_document_content(doc))
                
        except KeyboardInterrupt:
            print("\n\n程序被用户中断")
            break
        except Exception as e:
            print(f"查询过程中发生错误: {str(e)}")


def main():
    parser = argparse.ArgumentParser(description="查询向量数据库")
    parser.add_argument("--db_path", default=DEFAULT_DB_FAISS_PATH, help="向量数据库路径")
    parser.add_argument("--embedding", default=DEFAULT_EMBEDDING, help="嵌入模型名称")
    parser.add_argument("--query", help="直接查询的问题")
    
    args = parser.parse_args()
    
    try:
        # 加载向量数据库
        vector_store = load_vector_store(args.db_path, args.embedding)
        
        if args.query:
            # 直接查询模式
            docs = search_similar_documents(vector_store, args.query, k=4)
            print(f"查询: {args.query}")
            print(f"找到 {len(docs)} 个相关文档:")
            for i, doc in enumerate(docs, 1):
                print(f"\n【相关文档 {i}】")
                print(format_document_content(doc))
        else:
            # 交互式查询模式
            interactive_query(vector_store)
            
    except Exception as e:
        print(f"程序执行出错: {str(e)}")


if __name__ == "__main__":
    main()