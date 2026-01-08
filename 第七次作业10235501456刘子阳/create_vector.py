import os
import argparse
from tqdm import tqdm
import pandas as pd
from typing import List

# 正确的导入方式
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS


# 设置默认路径
DEFAULT_DATA_PATH = r"d:\DataEngineering\第七次作业10235501456刘子阳"
DEFAULT_DB_FAISS_PATH = r"d:\DataEngineering\第七次作业10235501456刘子阳\vectorstore\db_faiss"
DEFAULT_EMBEDDING = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def load_csv_file(file_path: str) -> List[Document]:
    """
    加载CSV文件并将其转换为文档格式，尝试多种编码
    """
    try:
        # 尝试不同的编码方式
        encodings = ["utf-8", "gbk", "gb2312", "latin-1"]
        df = None
        
        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                print(f"使用 {encoding} 编码成功读取 {file_path}")
                break
            except Exception as e:
                if encoding == encodings[-1]:
                    # 如果所有编码都失败，抛出异常
                    raise e
                continue
        
        if df is None:
            raise Exception("无法使用任何编码读取文件")
        
        # 将DataFrame转换为文本描述
        csv_content = f"文件名: {os.path.basename(file_path)}\n"
        csv_content += f"学科名称: {os.path.splitext(os.path.basename(file_path))[0]}\n"
        csv_content += f"数据行数: {len(df)}\n"
        csv_content += f"列名: {', '.join(df.columns.tolist())}\n\n"
        
        # 添加前几行数据作为示例
        csv_content += "数据预览:\n"
        csv_content += df.head(10).to_string(index=False)
        
        # 创建文档对象
        document = Document(
            page_content=csv_content,
            metadata={
                "source": file_path,
                "file_type": "csv",
                "subject": os.path.splitext(os.path.basename(file_path))[0]
            }
        )
        
        return [document]
    except Exception as e:
        print(f"加载CSV文件 {file_path} 失败: {str(e)}")
        return []


def load_pdf_file(file_path: str) -> List[Document]:
    """
    加载PDF文件并将其转换为文档格式
    """
    try:
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        
        # 为每个文档添加元数据
        for doc in documents:
            doc.metadata.update({
                "source": file_path,
                "file_type": "pdf",
                "subject": os.path.splitext(os.path.basename(file_path))[0]
            })
        
        print(f"成功加载PDF文件 {file_path}，共 {len(documents)} 页")
        return documents
    except Exception as e:
        print(f"加载PDF文件 {file_path} 失败: {str(e)}")
        return []


def load_documents_from_csv_directory(data_path: str) -> List[Document]:
    """
    从指定目录加载所有CSV文档
    """
    all_documents = []
    
    # CSV文件路径
    csv_dir = os.path.join(data_path, "csv_files")
    
    if not os.path.exists(csv_dir):
        print(f"错误: CSV目录 {csv_dir} 不存在")
        return []
    
    print(f"开始扫描CSV目录: {csv_dir}")
    
    # 遍历CSV目录
    csv_files = [f for f in os.listdir(csv_dir) if f.endswith('.csv')]
    
    for file in tqdm(csv_files, desc="处理CSV文件"):
        file_path = os.path.join(csv_dir, file)
        print(f"正在处理: {file_path}")
        documents = load_csv_file(file_path)
        if documents:
            all_documents.extend(documents)
            print(f"成功加载文档从 {file_path}")
        else:
            print(f"未能从 {file_path} 加载文档")
    
    print(f"总共从CSV目录加载了 {len(all_documents)} 个文档")
    return all_documents


def load_documents_from_textbook_directory(data_path: str) -> List[Document]:
    """
    从教材与专著目录加载所有PDF文档
    """
    all_documents = []
    
    # 教材与专著目录路径
    textbook_dir = os.path.join(data_path, "教材与专著")
    
    if not os.path.exists(textbook_dir):
        print(f"错误: 教材与专著目录 {textbook_dir} 不存在")
        return []
    
    print(f"开始扫描教材与专著目录: {textbook_dir}")
    
    # 遍历教材与专著目录，只处理PDF文件
    pdf_files = [f for f in os.listdir(textbook_dir) if f.endswith('.pdf')]
    
    for file in tqdm(pdf_files, desc="处理PDF文件"):
        file_path = os.path.join(textbook_dir, file)
        print(f"正在处理: {file_path}")
        documents = load_pdf_file(file_path)
        if documents:
            all_documents.extend(documents)
            print(f"成功加载文档从 {file_path}")
        else:
            print(f"未能从 {file_path} 加载文档")
    
    print(f"总共从教材与专著目录加载了 {len(all_documents)} 个文档")
    return all_documents


def load_documents_from_directory(data_path: str) -> List[Document]:
    """
    从指定目录加载所有文档（CSV和PDF）
    """
    # 加载CSV文档
    csv_documents = load_documents_from_csv_directory(data_path)
    
    # 加载PDF文档
    pdf_documents = load_documents_from_textbook_directory(data_path)
    
    # 合并所有文档
    all_documents = csv_documents + pdf_documents
    
    print(f"总共加载了 {len(all_documents)} 个文档")
    return all_documents


def split_documents(documents: List[Document]) -> List[Document]:
    """
    使用RecursiveCharacterTextSplitter分割文档
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )
    
    split_docs = text_splitter.split_documents(documents)
    print(f"文档分割完成，共得到 {len(split_docs)} 个片段")
    return split_docs


def create_vector_store(documents: List[Document], embedding_model: str, db_path: str):
    """
    创建向量存储
    """
    print(f"正在初始化嵌入模型: {embedding_model}")
    # 使用本地缓存的模型，避免网络下载
    embeddings = HuggingFaceEmbeddings(
        model_name=embedding_model,
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True},
        # 设置本地缓存目录
        cache_folder="./model_cache"
    )
    
    print("正在创建向量数据库...")
    vector_store = FAISS.from_documents(documents, embeddings)
    
    # 使用英文路径避免中文字符问题
    english_db_path = "./vectorstore/db_faiss"
    # 确保保存路径存在
    os.makedirs(english_db_path, exist_ok=True)
    
    # 保存向量数据库
    vector_store.save_local(english_db_path)
    print(f"向量数据库已保存到: {english_db_path}")
    
    return vector_store


def main():
    parser = argparse.ArgumentParser(description="创建用于RAG的向量数据库（处理CSV和PDF文件）")
    parser.add_argument("--data_path", default=DEFAULT_DATA_PATH, help="知识文档所在的目录")
    parser.add_argument("--db_path", default=DEFAULT_DB_FAISS_PATH, help="向量数据库保存目录")
    parser.add_argument("--embedding", default=DEFAULT_EMBEDDING, help="嵌入模型名称")
    
    args = parser.parse_args()
    
    # 检查数据路径是否存在
    if not os.path.exists(args.data_path):
        print(f"错误: 数据路径 {args.data_path} 不存在")
        return
    
    # 加载文档
    print("开始加载文档...")
    documents = load_documents_from_directory(args.data_path)
    
    if not documents:
        print("未找到任何可处理的文档")
        return
    
    # 分割文档
    print("开始分割文档...")
    split_docs = split_documents(documents)
    
    # 创建向量存储
    print("开始创建向量数据库...")
    vector_store = create_vector_store(split_docs, args.embedding, args.db_path)
    
    print("向量数据库创建完成!")


if __name__ == "__main__":
    main()