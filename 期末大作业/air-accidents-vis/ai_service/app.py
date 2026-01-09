from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder # 引入加密器
from pydantic import BaseModel
from rag_engine import engine
import uvicorn
import traceback

app = FastAPI()

class QueryRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat(req: QueryRequest):
    try:
        print(f"🤖 收到前端请求: {req.message}")
        
        # 1. 检索
        related_docs = engine.search(req.message, top_k=3)
        
        # 2. 生成
        answer = engine.generate_answer(req.message, related_docs)
        
        # 3. 🚨 核心修复：清洗 context 数据，确保所有内容都是 JSON 友好的
        # 我们把每一条记录都转成标准的 Python 字典，并确保字段是字符串
        safe_context = []
        for doc in related_docs:
            safe_context.append({
                "pk": str(doc.get("pk", "")),
                "date": str(doc.get("date", "")),
                "type": str(doc.get("type", "")),
                "narrative": str(doc.get("narrative", ""))
            })

        print("✅ AI 回答生成完毕，正在返回结果...")

        # 返回清洗后的数据
        return {
            "answer": str(answer), # 确保回答是字符串
            "context": safe_context 
        }

    except Exception as e:
        print("❌ Python 端发生异常:")
        traceback.print_exc() 
        raise HTTPException(status_code=500, detail=str(e))

# 根路径测试，方便验证服务是否存活
@app.get("/")
async def root():
    return {"status": "AI Service is running", "engine_ready": engine.index is not None}

if __name__ == "__main__":
    print("🚀 启动 FastAPI 服务...")
    uvicorn.run(app, host="127.0.0.1", port=8000)