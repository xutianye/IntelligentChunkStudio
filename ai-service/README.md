# AI Service - Intelligent Chunk Studio

Python AI 服务，负责文档解析、语义切片、Embedding 生成。

## 技术栈

- FastAPI
- sentence-transformers (BGE-M3)
- pgvector

## 安装

```bash
pip install -r requirements.txt
```

## 运行

```bash
uvicorn app:app --reload --port 8000
```

## API 文档

启动后访问：http://localhost:8000/docs

## 目录结构

```
ai-service/
├── app.py              # FastAPI 入口
├── services/           # 业务服务
│   └── markdown_parser.py
├── models/             # 数据模型
├── requirements.txt
└── README.md
```