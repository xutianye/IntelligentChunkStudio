"""
Markdown 文档解析服务
将 Markdown 文本解析为结构化文档树
"""

import re
import uuid
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class DocumentNode:
    """文档节点"""
    id: str
    level: int  # 标题级别 1-6，0 表示非标题内容
    title: str
    content: str
    content_type: str  # heading/paragraph/list/code/quote/table
    path: str
    start_line: int
    end_line: int
    children: List['DocumentNode'] = field(default_factory=list)


@dataclass
class ParsedDocument:
    """解析结果"""
    id: str
    file_name: str
    raw_content: str
    total_lines: int
    total_tokens: int
    title: str
    tree: List[DocumentNode]
    metadata: dict


def estimate_tokens(text: str) -> int:
    """
    估算 token 数量
    - 中文：1 字 ≈ 1.5 tokens
    - 英文：1 词 ≈ 1.3 tokens
    """
    chinese = len(re.findall(r'[一-鿿]', text))
    english = len(re.findall(r'[a-zA-Z]+', text))
    others = len(text) - chinese - english * 0.5

    return int(chinese * 1.5 + english * 1.3 + others)


def parse_markdown(content: str, file_name: str = "untitled.md") -> ParsedDocument:
    """
    解析 Markdown 文本为结构化文档树

    Args:
        content: Markdown 文本内容
        file_name: 文件名

    Returns:
        ParsedDocument: 解析结果
    """
    lines = content.split('\n')
    nodes = []
    doc_id = f"doc_{uuid.uuid4().hex[:8]}"

    # 第一步：逐行解析，构建节点列表
    i = 0
    while i < len(lines):
        line = lines[i]
        line_num = i + 1

        # 跳过空行
        if not line.strip():
            i += 1
            continue

        # 标题行
        if match := re.match(r'^(#{1,6})\s+(.+)$', line):
            level = len(match.group(1))
            title = match.group(2).strip()

            # 收集标题下的内容
            content_lines = []
            j = i + 1
            while j < len(lines):
                next_line = lines[j]
                # 遇到同级或更高级标题，停止
                if next_line.strip() and re.match(rf'^#{{{level},6}}\s+', next_line):
                    break
                # 遇到更低级的标题，停止
                if next_line.strip() and re.match(r'^(#{1,6})\s+', next_line):
                    next_level = len(re.match(r'^(#{1,6})', next_line).group(1))
                    if next_level <= level:
                        break
                content_lines.append(next_line)
                j += 1

            node_content = '\n'.join(content_lines).strip()

            node = DocumentNode(
                id=f"node_{uuid.uuid4().hex[:8]}",
                level=level,
                title=title,
                content=node_content,
                content_type="heading",
                path=title,
                start_line=line_num,
                end_line=i + len(content_lines) if content_lines else line_num,
                children=[]
            )
            nodes.append(node)
            i = j
            continue

        # 代码块
        if line.strip().startswith('```'):
            lang = line.strip()[3:] if len(line.strip()) > 3 else ""
            code_lines = []
            j = i + 1
            while j < len(lines) and not lines[j].strip().endswith('```'):
                code_lines.append(lines[j])
                j += 1

            node = DocumentNode(
                id=f"node_{uuid.uuid4().hex[:8]}",
                level=0,
                title="",
                content='\n'.join(code_lines),
                content_type="code",
                path="",
                start_line=line_num,
                end_line=j + 1 if j < len(lines) else line_num,
                children=[]
            )
            nodes.append(node)
            i = j + 1 if j < len(lines) else j + 1
            continue

        # 引用块
        if line.strip().startswith('>'):
            quote_lines = []
            while i < len(lines) and (lines[i].strip().startswith('>') or not lines[i].strip()):
                if lines[i].strip().startswith('>'):
                    quote_lines.append(lines[i].strip()[1:].strip())
                i += 1

            node = DocumentNode(
                id=f"node_{uuid.uuid4().hex[:8]}",
                level=0,
                title="",
                content='\n'.join(quote_lines),
                content_type="quote",
                path="",
                start_line=line_num,
                end_line=i,
                children=[]
            )
            nodes.append(node)
            continue

        # 列表项
        if re.match(r'^[\s]*[-*+]\s+', line) or re.match(r'^[\s]*\d+\.\s+', line):
            list_lines = []
            while i < len(lines) and (re.match(r'^[\s]*[-*+]\s+', lines[i]) or
                                      re.match(r'^[\s]*\d+\.\s+', lines[i])):
                list_lines.append(lines[i].strip())
                i += 1

            node = DocumentNode(
                id=f"node_{uuid.uuid4().hex[:8]}",
                level=0,
                title="",
                content='\n'.join(list_lines),
                content_type="list",
                path="",
                start_line=line_num,
                end_line=i,
                children=[]
            )
            nodes.append(node)
            continue

        # 表格
        if '|' in line:
            table_lines = []
            while i < len(lines) and '|' in lines[i]:
                table_lines.append(lines[i])
                i += 1

            node = DocumentNode(
                id=f"node_{uuid.uuid4().hex[:8]}",
                level=0,
                title="",
                content='\n'.join(table_lines),
                content_type="table",
                path="",
                start_line=line_num,
                end_line=i,
                children=[]
            )
            nodes.append(node)
            continue

        # 普通段落
        para_lines = []
        while i < len(lines) and lines[i].strip() and \
                not re.match(r'^#{1,6}\s+', lines[i]) and \
                not lines[i].strip().startswith('```') and \
                not lines[i].strip().startswith('>'):
            para_lines.append(lines[i])
            i += 1

        if para_lines:
            node = DocumentNode(
                id=f"node_{uuid.uuid4().hex[:8]}",
                level=0,
                title="",
                content='\n'.join(para_lines),
                content_type="paragraph",
                path="",
                start_line=line_num,
                end_line=i,
                children=[]
            )
            nodes.append(node)

    # 第二步：通过标题层级构建树形结构
    tree = _build_tree(nodes)

    # 第三步：更新 path
    _update_paths(tree)

    # 第四步：提取文档标题（第一个 H1）
    doc_title = ""
    if nodes and nodes[0].level == 1:
        doc_title = nodes[0].title

    # 第五步：计算 metadata
    all_content = content.replace('#', '').strip()
    metadata = {
        "created_at": datetime.now().isoformat(),
        "char_count": len(content),
        "word_count": len(re.findall(r'[一-鿿]|[a-zA-Z]+', content)),
        "token_count": estimate_tokens(content),
        "heading_count": len([n for n in nodes if n.content_type == 'heading']),
        "paragraph_count": len([n for n in nodes if n.content_type == 'paragraph'])
    }

    return ParsedDocument(
        id=doc_id,
        file_name=file_name,
        raw_content=content,
        total_lines=len(lines),
        total_tokens=estimate_tokens(content),
        title=doc_title,
        tree=tree,
        metadata=metadata
    )


def _build_tree(nodes: List[DocumentNode]) -> List[DocumentNode]:
    """通过标题层级构建树"""
    tree = []
    stack = []

    for node in nodes:
        if node.content_type != 'heading':
            # 非标题节点，加入当前栈顶节点的 children
            if stack:
                stack[-1].children.append(node)
            else:
                tree.append(node)
        else:
            # 标题节点，找父节点
            while stack and stack[-1].level >= node.level:
                stack.pop()

            if stack:
                stack[-1].children.append(node)
            else:
                tree.append(node)

            stack.append(node)

    return tree


def _update_paths(tree: List[DocumentNode], parent_path: str = ""):
    """更新节点的 path"""
    for node in tree:
        if parent_path:
            node.path = f"{parent_path} > {node.title}" if node.title else parent_path
        else:
            node.path = node.title

        if node.children:
            _update_paths(node.children, node.path if node.content_type == 'heading' else parent_path)


def to_dict(doc: ParsedDocument) -> dict:
    """转换为字典格式，便于 JSON 序列化"""
    def node_to_dict(node: DocumentNode) -> dict:
        return {
            "id": node.id,
            "level": node.level,
            "title": node.title,
            "content": node.content,
            "content_type": node.content_type,
            "path": node.path,
            "start_line": node.start_line,
            "end_line": node.end_line,
            "children": [node_to_dict(c) for c in node.children]
        }

    return {
        "id": doc.id,
        "file_name": doc.file_name,
        "raw_content": doc.raw_content,
        "total_lines": doc.total_lines,
        "total_tokens": doc.total_tokens,
        "title": doc.title,
        "tree": [node_to_dict(n) for n in doc.tree],
        "metadata": doc.metadata
    }