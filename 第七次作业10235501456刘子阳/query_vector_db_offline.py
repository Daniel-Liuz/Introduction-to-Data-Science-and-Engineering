import os
import argparse
from typing import List

# 导入必要的模块
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import FakeEmbeddings


# 设置默认路径（使用英文路径避免中文字符问题）
DEFAULT_DB_FAISS_PATH = "./vectorstore/db_faiss"


def format_document_content(doc_content: str) -> str:
    """
    格式化文档内容，使其更易读
    """
    # 移除多余的空白字符
    content = doc_content.strip()
    
    # 如果内容包含数据预览部分，保留前几行
    if "数据预览:" in content:
        lines = content.split('\n')
        formatted_lines = []
        data_preview_found = False
        
        for line in lines:
            if line.startswith("数据预览:"):
                data_preview_found = True
                formatted_lines.append("\n" + "="*50)
                formatted_lines.append("数据预览:")
                formatted_lines.append("="*50)
            elif data_preview_found and len(line.strip()) == 0:
                # 跳过数据预览后的空行
                continue
            elif data_preview_found and line.startswith(("="*30, "-"*30)):
                # 跳过分隔线
                continue
            else:
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    return content


def search_similar_documents(vector_store, query: str, k: int = 5) -> List[Document]:
    """
    在向量数据库中搜索相似文档
    """
    # 执行相似性搜索
    docs = vector_store.similarity_search(query, k=k)
    return docs


def load_vector_store(db_path: str):
    """
    加载向量数据库（使用FakeEmbeddings避免网络问题）
    """
    print("正在加载向量数据库...")
    
    # 使用FakeEmbeddings避免网络连接问题
    embeddings = FakeEmbeddings(size=768)
    
    # 检查数据库路径是否存在
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"向量数据库路径不存在: {db_path}")
    
    # 检查必需的FAISS文件是否存在
    index_file = os.path.join(db_path, "index.faiss")
    pkl_file = os.path.join(db_path, "index.pkl")
    
    if not os.path.exists(index_file):
        raise FileNotFoundError(f"FAISS索引文件不存在: {index_file}")
    
    if not os.path.exists(pkl_file):
        raise FileNotFoundError(f"FAISS pickle文件不存在: {pkl_file}")
    
    # 加载向量数据库
    vector_store = FAISS.load_local(db_path, embeddings, allow_dangerous_deserialization=True)
    print(f"向量数据库加载成功: {db_path}")
    return vector_store


def interactive_query(vector_store):
    """
    提供交互式查询界面
    """
    print("\n" + "="*60)
    print("欢迎使用高校学科排名问答系统 (离线版)")
    print("="*60)
    print("您可以询问关于各高校学科排名的问题，例如：")
    print("- 计算机科学专业排名前十的高校有哪些？")
    print("- 清华大学在哪些学科上表现突出？")
    print("- 农业科学领域有哪些优秀高校？")
    print("- 哪些高校的物理学专业排名较高？")
    print("- 输入 'quit' 或 'exit' 退出系统")
    print("="*60)
    
    while True:
        try:
            # 获取用户输入
            query = input("\n请输入您的问题: ").strip()
            
            # 检查退出条件
            if query.lower() in ['quit', 'exit', '退出']:
                print("感谢使用高校学科排名问答系统！")
                break
            
            # 检查空输入
            if not query:
                print("请输入有效问题。")
                continue
            
            print(f"\n正在搜索关于 '{query}' 的相关信息...")
            
            # 搜索相似文档
            similar_docs = search_similar_documents(vector_store, query, k=3)
            
            # 显示结果
            if similar_docs:
                print(f"\n找到 {len(similar_docs)} 个相关结果:\n")
                for i, doc in enumerate(similar_docs, 1):
                    print(f"--- 结果 {i} ---")
                    formatted_content = format_document_content(doc.page_content)
                    print(formatted_content)
                    print(f"来源: {doc.metadata.get('source', '未知')}")
                    print(f"学科: {doc.metadata.get('subject', '未知')}")
                    print()
            else:
                print("未找到相关结果，请尝试重新表述问题。")
                
        except KeyboardInterrupt:
            print("\n\n程序被用户中断。")
            break
        except Exception as e:
            print(f"查询过程中发生错误: {str(e)}")


def main():
    parser = argparse.ArgumentParser(description="查询向量数据库 (离线版本)")
    parser.add_argument("--db_path", default=DEFAULT_DB_FAISS_PATH, help="向量数据库路径")
    
    args = parser.parse_args()
    
    try:
        # 加载向量数据库
        vector_store = load_vector_store(args.db_path)
        
        # 启动交互式查询
        interactive_query(vector_store)
        
    except FileNotFoundError as e:
        print(f"错误: {e}")
        print("请确保向量数据库已创建，或者检查数据库路径是否正确。")
    except Exception as e:
        print(f"加载向量数据库时发生错误: {str(e)}")


if __name__ == "__main__":
    main()