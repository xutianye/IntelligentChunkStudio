"""
Intelligent Chunk Studio - AI Service
FastAPI 入口
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi import UploadFile, File

from models.data_models import (
    ParseRequest, ParseResponse, ParsedDocumentDTO,
    ChunkGenerateRequest, ChunkGenerateResponse, ChunkDTO
)
from services.markdown_parser import parse_markdown, to_dict

app = FastAPI(title="AI Service", version="1.0.0")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "AI Service is running", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/api/document/parse", response_model=ParseResponse)
async def parse_document(request: ParseRequest):
    """
    解析 Markdown 文档
    """
    if not request.content or not request.content.strip():
        return ParseResponse(code=1001, message="文件内容为空", data=None)

    if len(request.content) > 1_000_000:  # 1MB
        return ParseResponse(code=1003, message="文件内容过长（超过 1MB）", data=None)

    try:
        parsed = parse_markdown(request.content, request.file_name)
        result = to_dict(parsed)

        # 转换为 Pydantic 模型
        tree = _build_tree_dto(result['tree'])
        metadata = result['metadata']

        data = ParsedDocumentDTO(
            id=result['id'],
            file_name=result['file_name'],
            raw_content=result['raw_content'],
            total_lines=result['total_lines'],
            total_tokens=result['total_tokens'],
            title=result['title'],
            tree=tree,
            metadata={
                "created_at": metadata['created_at'],
                "char_count": metadata['char_count'],
                "word_count": metadata['word_count'],
                "token_count": metadata['token_count'],
                "heading_count": metadata['heading_count'],
                "paragraph_count": metadata['paragraph_count']
            }
        )

        return ParseResponse(code=0, message="success", data=data)
    except Exception as e:
        return ParseResponse(code=1004, message=f"Markdown 解析失败: {str(e)}", data=None)


@app.post("/api/document/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    上传 Markdown 文件并解析
    """
    if not file.filename:
        return ParseResponse(code=1005, message="文件名无效", data=None)

    # 检查文件类型
    if not file.filename.endswith(('.md', '.txt', '.markdown')):
        return ParseResponse(code=1002, message="文件格式不支持（非 .md/.txt/.markdown）", data=None)

    try:
        content = await file.read()
        text = content.decode('utf-8')

        request = ParseRequest(content=text, file_name=file.filename)
        return await parse_document(request)
    except Exception as e:
        return ParseResponse(code=1004, message=f"文件读取失败: {str(e)}", data=None)


@app.post("/api/chunk/generate", response_model=ChunkGenerateResponse)
async def generate_chunks(request: ChunkGenerateRequest):
    """
    生成 Chunk（待实现语义切片）
    """
    # TODO: 实现语义切片算法
    return ChunkGenerateResponse(
        document_id=request.document_id,
        chunks=[],
        total_count=0
    )


@app.post("/api/embedding")
async def generate_embedding(texts: list[str]):
    """
    生成文本向量
    """
    # TODO: 实现 Embedding
    return {"embeddings": []}


def _build_tree_dto(nodes: list) -> list:
    """将字典转换为 DocumentNodeDTO"""
    from models.data_models import DocumentNodeDTO

    result = []
    for node in nodes:
        children = _build_tree_dto(node.get('children', [])) if node.get('children') else []
        result.append(DocumentNodeDTO(
            id=node['id'],
            level=node['level'],
            title=node['title'],
            content=node['content'],
            content_type=node['content_type'],
            path=node['path'],
            start_line=node['start_line'],
            end_line=node['end_line'],
            children=children
        ))
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)