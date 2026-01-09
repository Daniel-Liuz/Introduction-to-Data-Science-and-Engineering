import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import pickle 

# --- 路径配置 ---
# 1. 获取当前脚本所在目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. 强行把 Python 的工作目录切换到 ai_service 文件夹
os.chdir(BASE_DIR)

# 3. 使用相对路径 (Relative Path)
EMBEDDING_PATH = "models/bge-m3"  
LLM_PATH = "models/deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"
FAISS_PATH = "vector_db/accidents.index" 
MAPPING_PATH = "vector_db/mapping.pkl"

class AIEngine:
    def __init__(self):
        print("⏳ [1/3] 正在加载 Embedding 模型...")
        self.embed_model = SentenceTransformer(EMBEDDING_PATH, device="cuda" if torch.cuda.is_available() else "cpu")
        
        print("⏳ [2/3] 正在加载 LLM (1.5B)...")
        self.tokenizer = AutoTokenizer.from_pretrained(LLM_PATH)
        self.llm = AutoModelForCausalLM.from_pretrained(
            LLM_PATH, 
            torch_dtype=torch.float16, 
            device_map="auto"
        )
        
        print(f"⏳ [3/3] 正在加载向量数据库: {FAISS_PATH}")
        self.index = None
        self.metadata = []
        
        # ⚠️ 这里增加了详细的路径检查
        if os.path.exists(FAISS_PATH) and os.path.exists(MAPPING_PATH):
            try:
                self.index = faiss.read_index(FAISS_PATH)
                with open(MAPPING_PATH, 'rb') as f:
                    self.metadata = pickle.load(f)
                print(f"✅ 向量库加载成功，包含 {self.index.ntotal} 条记录")
            except Exception as e:
                print(f"❌ 加载向量库文件出错: {e}")
        else:
            print(f"❌ 未找到向量库文件！\n请检查: {FAISS_PATH}")
            print("请先运行 ingest.py 生成数据。")

    def search(self, query, top_k=3):
        """
        语义搜索：将问题转向量 -> 在 FAISS 搜相似向量 -> 返回对应的元数据
        """
        if not self.index:
            return []
        
        # 1. 向量化问题
        query_vec = self.embed_model.encode([query], normalize_embeddings=True)
        query_vec = np.array(query_vec).astype('float32')
        
        # 2. 搜索
        distances, indices = self.index.search(query_vec, top_k)
        
        # 3. 提取结果 (将 ID 转换为具体的文本字典)
        results = []
        for idx in indices[0]:
            if idx != -1 and idx < len(self.metadata):
                results.append(self.metadata[idx])
        
        return results

    def generate_answer(self, query, retrieved_docs):
        """
        RAG 生成：Context + Question -> LLM -> Answer
        """
        # 构造上下文文本
        context_str = ""
        for i, doc in enumerate(retrieved_docs):
            # 安全获取字段，防止 None 报错
            date = doc.get('date', 'Unknown')
            type_ = doc.get('type', 'Unknown')
            narrative = doc.get('narrative', '')
            context_str += f"【事故记录 {i+1}】\n时间: {date}\n机型: {type_}\n详情: {narrative}\n\n"

        # 构造 Prompt
        prompt = f"""<|im_start|>system
你是一个专业的航空安全分析师。请根据下面提供的【事故记录】来回答用户的【问题】。
如果记录中没有答案，请使用你的通用知识回答，并明确说明。回答要用中文，并且要简洁、专业。
<|im_end|>
<|im_start|>user
【事故记录】：
{context_str}

【问题】：
{query}
<|im_end|>
<|im_start|>assistant
"""
        
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.llm.device)
        attention_mask = inputs.get("attention_mask")
        
        with torch.no_grad():
            outputs = self.llm.generate(
                inputs.input_ids, 
                attention_mask=attention_mask,
                pad_token_id=self.tokenizer.eos_token_id, 
                max_new_tokens=512,
                temperature=0.6,
                top_p=0.9,
                do_sample=True
            )
            
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # 清理掉 Prompt 部分，只保留回答
        if "assistant\n" in response:
            return response.split("assistant\n")[-1]
        return response

# 单例
engine = AIEngine()