# ✈️ 全球航空事故数据可视化与智能分析平台
# Global Aviation Accident Data Visualization & Intelligent Analysis Platform

> 基于 React + Node.js + Python (RAG AI) 的全栈数据可视化与智能分析系统。

![Project Status](https://img.shields.io/badge/Status-Completed-success)
![License](https://img.shields.io/badge/License-MIT-blue)

## 📂 提交文件清单 (File Manifest)

本仓库包含了期末大作业的所有交付物，目录结构说明如下：

| 文件/目录名 | 说明 |
| :--- | :--- |
| **`air-accidents-vis/`** | **项目源代码**（包含前端、后端、AI微服务及爬虫脚本） |
| `全球航空事故数据可视化与智能分析平台.md` | 项目实验报告 (Markdown 版本) |
| `期末大作业报告.pdf` | 项目实验报告 (PDF 正式版本) |
| `期末大作业汇报PPT.pptx` | 期末汇报演示文稿 |

---

## 📖 项目简介

本项目旨在构建一个集数据采集、清洗、存储、可视化与智能问答于一体的综合性平台。数据源自 **Aviation Safety Network (ASN)**，涵盖了 2021-2025 年间发生的 **30,000+** 条航空事故记录。

通过引入 **检索增强生成 (RAG)** 技术，系统实现了一个能够理解自然语言的 **AI 智能助手**，用户不仅可以通过交互式地图查看事故分布，还能直接询问事故成因，实现了从“看数据”到“问数据”的转变。

### ✨ 核心功能
* **🌍 交互式全球地图**：基于 Leaflet 绘制真实大圆航线（Great Circle Route），支持时空多维筛选。
* **🤖 RAG AI 智能助手**：集成 DeepSeek-R1-7B 本地大模型与 FAISS 向量库，提供基于事实的事故问答。
* **📊 多维数据看板**：基于 ECharts 展示年度趋势、机型分布、国家排行等统计信息。
* **🕸️ 全链路数据工程**：包含高并发爬虫、地理坐标模糊匹配补全及自动化 ETL 脚本。

---

## 🛠️ 技术架构

本项目采用 **微服务架构**，将业务逻辑与 AI 计算分离：

* **前端 (Frontend)**: React 18, Vite, Leaflet, ECharts
* **业务后端 (Gateway)**: Node.js, Express (Port 3001)
* **AI 微服务 (AI Service)**: Python, FastAPI, LangChain, FAISS, PyTorch (Port 8000)
* **数据存储 (Storage)**: PostgreSQL (结构化), FAISS (向量索引)
* **模型 (Models)**: BGE-M3 (Embedding), DeepSeek-R1-Distill-Qwen-7B (LLM)

---

## 🚀 快速启动 (Deployment)

请按照以下顺序启动各模块。

### 1. 环境准备
* **Node.js**: v18+
* **Python**: 3.10+ (建议使用 Conda 环境)
* **PostgreSQL**: 12+ (需预先创建数据库)
* **GPU**: 建议配备 NVIDIA 显卡 (8GB+ 显存) 以获得最佳 AI 体验

### 2. 数据工程 (初始化数据)
```bash
cd air-accidents-vis/airportdata

# 1. 爬取数据 & 2. 清洗数据与补全坐标
python getData_Mul.py
python append_coords.py
python transform.py

# 3. 导入 PostgreSQL 数据库
python import_to_db.py
```
### 3.启动AI微服务
```bash
cd ../ai_service

# 1. 安装依赖
pip install -r requirements.txt

# 2. 构建向量知识库 (首次运行需执行)
python ingest.py

# 3. 启动 FastAPI 服务 (Port: 8000)
python app.py
```

### 4.启动业务后端
```bash
cd ../backend

# 1. 安装依赖
npm install

# 2. 启动 Express 服务 (Port: 3001)
npm start
```

### 5.启动前端应用
```bash
cd ..  # 回到 air-accidents-vis 根目录

# 1. 安装依赖
npm install

# 2. 启动开发服务器 (Port: 3000)
npm run dev
```



