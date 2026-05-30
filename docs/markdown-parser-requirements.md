# Intelligent Chunk Studio v1.0 - Markdown 解析模块需求文档

## 1. 概述

### 1.1 模块名称
**Markdown Document Parser**（Markdown 文档解析器）

### 1.2 模块定位
v1.0 MVP 核心模块，负责将 Markdown 文档解析为结构化数据，为后续切片提供基础。

### 1.3 设计目标
- 输入：Markdown 文本
- 输出：结构化文档树 + 原始内容
- 支持标题层级识别、段落分割、语义边界检测

---

## 2. 功能需求

### 2.1 支持的 Markdown 语法

| 语法元素 | 必须支持 | 说明 |
|---------|---------|-----|
| 标题 H1~H6 | ✅ | 按 `#` 数量识别层级 |
| 段落 | ✅ | 连续文本为一个段落 |
| 列表（无序） | ✅ | `-` 和 `*` 开头 |
| 列表（有序） | ✅ | `1.` `2.` 开头 |
| 代码块 | ✅ | ``` 和 ``` 包裹 |
| 行内代码 | ✅ | `` ` `` 包裹 |
| 链接 | ✅ | `[text](url)` |
| 图片 | ✅ | `![alt](url)` |
| 引用 | ✅ | `>` 开头 |
| 分割线 | ✅ | `---` |
| 表格 | ✅ | Markdown 表格语法 |
| 粗体/斜体 | ✅ | `**bold**` `*italic*` |

### 2.2 解析能力

#### 2.2.1 标题树构建
```markdown
# 第一章
## 第一节
### 小节
```
识别结果：
```
- level: 1, title: "第一章", children: [...]
- level: 2, title: "第一节", children: [...]
- level: 3, title: "小节", children: [...]
```

#### 2.2.2 内容归属
- 标题下的内容归属于该标题，直到遇到同级或更高级标题
- 列表项、引用、代码块等作为段落的子元素处理

#### 2.2.3 元信息提取
每个节点需要提取：
| 字段 | 类型 | 说明 |
|-----|------|-----|
| id | string | 唯一标识，格式 `node_{uuid}` |
| level | int | 标题级别 1-6，无内容时为 0 |
| title | string | 标题文本，无标题时为空 |
| content | string | 该节点下的所有文本内容 |
| content_type | string | `heading`/`paragraph`/`list`/`code`/`quote`/`table` |
| path | string | 完整路径，如 "第一章 > 第一节 > 小节" |
| start_line | int | 在原文档中的起始行号 |
| end_line | int | 在原文档中的结束行号 |
| children | array | 子节点列表 |

---

## 3. 数据结构设计

### 3.1 DocumentNode（文档节点）

```typescript
interface DocumentNode {
  id: string;                    // 唯一标识
  level: number;                 // 标题级别 1-6，0 表示非标题内容
  title: string;                 // 标题文本
  content: string;               // 节点内容
  content_type: ContentType;     // 内容类型
  path: string;                  // 完整路径
  start_line: number;           // 起始行号
  end_line: number;             // 结束行号
  children: DocumentNode[];      // 子节点
}

type ContentType = 'heading' | 'paragraph' | 'list' | 'code' | 'quote' | 'table';
```

### 3.2 ParsedDocument（解析结果）

```typescript
interface ParsedDocument {
  id: string;                    // 文档唯一标识
  file_name: string;             // 文件名
  raw_content: string;          // 原始内容
  total_lines: number;          // 总行数
  total_tokens: number;         // 总 token 数估算
  title: string;                 // 文档标题（取第一个 H1）
  tree: DocumentNode[];         // 文档树
  metadata: DocumentMetadata;   // 文档元信息
}

interface DocumentMetadata {
  created_at: string;           // 解析时间
  char_count: number;           // 字符数
  word_count: number;           // 字数（中英文混合估算）
  token_count: number;          // token 数估算
  heading_count: number;        // 标题数量
  paragraph_count: number;      // 段落数量
}
```

---

## 4. 算法设计

### 4.1 解析流程

```
Markdown 文本
    ↓
行号标记（记录每行起始位置）
    ↓
逐行解析，识别语法元素
    ↓
构建节点列表
    ↓
通过标题层级构建树形结构
    ↓
内容归属计算
    ↓
元信息统计
    ↓
返回 ParsedDocument
```

### 4.2 解析规则

#### 4.2.1 标题识别
```python
# 正则匹配
r'^(#{1,6})\s+(.+)$'
# 示例
"# 第一章" → level: 1, title: "第一章"
"## 第一节" → level: 2, title: "第一节"
```

#### 4.2.2 列表识别
```python
# 无序列表
r'^[\s]*[-*+]\s+(.+)$'
# 有序列表
r'^[\s]*\d+\.\s+(.+)$'
```

#### 4.2.3 代码块识别
```python
# 开始标记
r'^```(\w*)$'  # 可选语言标识
# 内容：直到下一个 ``` 或文件结束
# 结束标记
r'^```$'
```

#### 4.2.4 引用块识别
```python
r'^>\s*(.*)$'
# 连续的非空 > 行属于同一引用块
```

### 4.3 树构建算法

```python
def build_tree(nodes: List[DocumentNode]) -> List[DocumentNode]:
    """
    通过标题层级构建树
    核心思路：维护一个栈，栈顶是当前节点的父节点
    """
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
```

### 4.4 Token 估算

```python
def estimate_tokens(text: str) -> int:
    """
    估算 token 数量
    - 中文：1 字 ≈ 1.5 tokens
    - 英文：1 词 ≈ 1.3 tokens
    """
    chinese = len(re.findall(r'[一-鿿]', text))
    english = len(re.findall(r'[a-zA-Z]+', text))
    others = len(text) - chinese - english * 0.5  # 英文占英文单词的一半估算

    return int(chinese * 1.5 + english * 1.3 + others)
```

---

## 5. API 设计

### 5.1 解析接口

```
POST /api/document/parse
```

**请求体：**
```json
{
  "content": "# Markdown 文本内容...",
  "file_name": "员工手册.md"
}
```

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "doc_abc123",
    "file_name": "员工手册.md",
    "raw_content": "...",
    "total_lines": 100,
    "total_tokens": 2500,
    "title": "员工手册",
    "tree": [
      {
        "id": "node_001",
        "level": 1,
        "title": "第一章 总则",
        "content": "...",
        "content_type": "heading",
        "path": "第一章 总则",
        "start_line": 1,
        "end_line": 15,
        "children": [...]
      }
    ],
    "metadata": {
      "created_at": "2026-05-30T10:00:00Z",
      "char_count": 5000,
      "word_count": 3200,
      "token_count": 2500,
      "heading_count": 12,
      "paragraph_count": 25
    }
  }
}
```

### 5.2 文件上传解析接口

```
POST /api/document/upload
Content-Type: multipart/form-data
```

**请求参数：**
| 参数 | 类型 | 必须 | 说明 |
|-----|------|-----|-----|
| file | File | ✅ | Markdown 文件 |
| file_name | string | 否 | 自定义文件名 |

**响应：**
同上 `ParsedDocument` 结构

---

## 6. 错误处理

### 6.1 错误码

| 错误码 | 说明 |
|-------|-----|
| 1001 | 文件内容为空 |
| 1002 | 文件格式不支持（非 .md/.txt/.markdown） |
| 1003 | 文件内容过长（超过 1MB） |
| 1004 | Markdown 解析失败 |
| 1005 | 文件名无效 |

### 6.2 错误响应格式

```json
{
  "code": 1001,
  "message": "文件内容为空",
  "data": null
}
```

---

## 7. 性能要求

| 指标 | 目标 |
|-----|-----|
| 解析速度 | < 100ms（10万字以内） |
| 内存占用 | < 200MB（10万字） |
| 并发支持 | 支持 10 个并发解析请求 |

---

## 8. 测试用例

### 8.1 基础测试

| 用例 | 输入 | 预期输出 |
|-----|-----|--------|
| 空文档 | "" | 返回空 tree，code=1001 |
| 纯标题 | "# 标题" | level=1, title="标题", content="" |
| 标题+段落 | "# 标题\n内容" | level=1, 标题节点 content="内容" |
| 多级标题 | "# 一\n## 1.1\n### 1.1.1" | 正确父子关系 |
| 列表 | "- 项目1\n- 项目2" | content_type="list" |
| 代码块 | "```python\ncode\n```" | content_type="code" |

### 8.2 边界测试

| 用例 | 输入 | 预期 |
|-----|-----|-----|
| 无标题 | "纯文本内容..." | level=0, title="" |
| 标题无内容 | "# 章节\n\n## 小节\n内容" | 跳过空节点 |
| 嵌套列表 | "- 1\n  - 1.1\n    - 1.1.1" | 正确识别层级 |

---

## 9. 后续扩展点

| 功能 | 说明 |
|-----|-----|
| 表格解析 | 支持 Markdown 表格转为结构化数据 |
| 图片提取 | 提取图片 URL 和 alt 文本 |
| 链接提取 | 提取所有外链和锚点 |
| 语义边界检测 | 通过 NLP 识别段落边界 |

---

## 10. 参考资料

- [CommonMark 规范](https://commonmark.org/)
- [Markdown 语法说明](https://www.markdownguide.org/basic-syntax/)
- Dify 切片模式设计
- LangChain MarkdownTextSplitter

---

**文档版本**：v1.0
**创建日期**：2026-05-30
**负责人**：待定