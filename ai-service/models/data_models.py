"""
数据模型
"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class DocumentNodeDTO(BaseModel):
    """文档节点 DTO"""
    id: str
    level: int
    title: str
    content: str
    content_type: str
    path: str
    start_line: int
    end_line: int
    children: List['DocumentNodeDTO'] = []


class DocumentMetadataDTO(BaseModel):
    """文档元信息"""
    created_at: str
    char_count: int
    word_count: int
    token_count: int
    heading_count: int
    paragraph_count: int


class ParsedDocumentDTO(BaseModel):
    """解析结果 DTO"""
    id: str
    file_name: str
    raw_content: str
    total_lines: int
    total_tokens: int
    title: str
    tree: List[DocumentNodeDTO]
    metadata: DocumentMetadataDTO

    class Config:
        from_attributes = True


class ChunkDTO(BaseModel):
    """Chunk DTO"""
    chunk_id: str
    title: str
    content: str
    path: str
    parent_id: str = ""
    level: int = 0
    token_count: int = 0
    quality_score: int = 0
    issues: List[str] = []


class ChunkGenerateRequest(BaseModel):
    """切片请求"""
    document_id: str
    content: str
    file_name: str = "untitled.md"
    max_tokens: int = 400
    overlap: int = 50


class ChunkGenerateResponse(BaseModel):
    """切片响应"""
    document_id: str
    chunks: List[ChunkDTO]
    total_count: int


class ParseRequest(BaseModel):
    """解析请求"""
    content: str
    file_name: str = "untitled.md"


class ParseResponse(BaseModel):
    """解析响应"""
    code: int = 0
    message: str = "success"
    data: Optional[ParsedDocumentDTO] = None


class ErrorResponse(BaseModel):
    """错误响应"""
    code: int
    message: str
    data: Optional[dict] = None