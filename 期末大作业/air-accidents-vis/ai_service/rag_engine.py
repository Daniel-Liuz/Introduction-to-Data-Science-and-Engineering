import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# --- 路径配置 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EMBEDDING_PATH = os.path.join(BASE_DIR, "models", "bge-m3")
LLM_PATH = os.path.join(BASE_DIR, "models", "deepseek-ai", "DeepSeek-R1-Distill-Qwen-1.5B")
FAISS_PATH = os.path.join(BASE_DIR, "vector_db", "accidents.index")

class AIEngine:
    def __init__(self):
        print("⏳ 正在加载 Embedding 模型...")
        self.embed_model = SentenceTransformer(EMBEDDING_PATH)
        
        print("⏳ 正在加载 LLM (可能需要一点时间)...")
        # 1.5B 模型较小，可以用 float16 跑
        self.tokenizer = AutoTokenizer.from_pretrained(LLM_PATH)
        self.llm = AutoModelForCausalLM.from_pretrained(
            LLM_PATH, 
            torch_dtype=torch.float16, 
            device_map="auto" # 如果有显卡会自动用，没显卡用 CPU
        )
        
        print("⏳ 正在加载向量数据库...")
        if os.path.exists(FAISS_PATH):
            self.index = faiss.read_index(FAISS_PATH)
            # 这里还需要加载对应的文本数据（通常需要一个 mapping 文件，简单起见假设我们只检索ID）
            # 实际项目中，你需要把 accident_id 和 index 对应起来
        else:
            self.index = None
            print("⚠️ 未找到向量库，请先运行 ingest.py")

        print("✅ AI 引擎初始化完成！")

    def get_embedding(self, text):
        return self.embed_model.encode([text])[0]

    def search(self, query, top_k=3):
        if not self.index:
            return []
        
        vector = self.get_embedding(query)
        # FAISS 需要二维数组
        vector = np.array([vector]).astype('float32')
        distances, indices = self.index.search(vector, top_k)
        
        # 这里返回的是索引 ID，你需要回数据库查具体内容，或者在构建索引时把内容也存了
        # 为了演示简单，我们假设我们有一个 look_up 函数
        return indices[0]

    def generate_answer(self, query, context):
        # 构造 Prompt
        prompt = f"""
        你是一个航空安全专家。基于以下已知信息回答用户问题。如果无法从信息中得到答案，请说明。
        
        【已知信息】：
        {context}
        
        【用户问题】：
        {query}
        
        【回答】：
        """
        
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.llm.device)
        attention_mask = inputs.get("attention_mask")
        with torch.no_grad():
            outputs = self.llm.generate(
            inputs.input_ids, 
            attention_mask=attention_mask, # 传入这个参数
            pad_token_id=self.tokenizer.eos_token_id, # 明确指定停止符
            max_new_tokens=512,
            temperature=0.6,
            top_p=0.9,
            do_sample=True # 允许采样
            )
    
            
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        # 简单截取回答部分（根据实际模型输出调整）
        return response.split("【回答】：")[-1]

# 单例模式
engine = AIEngine()