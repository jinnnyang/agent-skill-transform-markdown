# -*- coding: utf-8 -*-
import json
from typing import List, Dict, Optional

# 确保 markdown_parser.py 在 Python 路径中
try:
    from .markdown_parser import MarkdownParser, MarkdownRenderer, Node, Root, Block
except ImportError:
    # 如果直接运行此文件进行测试，则需要下面的相对路径导入
    try:
        from markdown_parser import MarkdownParser, MarkdownRenderer, Node, Root, Block
    except ImportError:
        print("错误：无法导入 'markdown_parser'。请确保 markdown_parser.py 文件与此脚本位于同一目录中。")
        # 提供一个虚拟的类，以便在导入失败时程序不会立即崩溃
        class Node: pass
        class Root(Node): pass
        class Block(Node): pass
        class MarkdownParser:
            def parse(self, text): raise NotImplementedError("markdown_parser.py 未找到")
        class MarkdownRenderer:
            def render(self, node): raise NotImplementedError("markdown_parser.py 未找到")


class Document:
    """
    一个简单的文档对象，用于存储切分后的文本块。
    """
    def __init__(self, page_content: str, metadata: Optional[Dict] = None, lookup_str: str = "", lookup_index: int = 0):
        self.page_content = page_content
        self.metadata = metadata or {}
        self.lookup_str = lookup_str
        self.lookup_index = lookup_index

    def __repr__(self) -> str:
        # 使用 repr(self.page_content) 来正确显示换行符
        return (
            f"Document(page_content={repr(self.page_content)}, "
            f"lookup_str='{self.lookup_str}', "
            f"metadata={self.metadata}, "
            f"lookup_index={self.lookup_index})"
        )

class MarkdownSplitter:
    """
    一个基于 Markdown AST 的智能文本分割器。
    它将 Markdown 文本解析为 AST，然后根据块级节点进行分割，以确保块的完整性。
    """
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200, enable_oversize: bool = True):
        if chunk_size <= 0:
            raise ValueError("chunk_size 必须是正整数。")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap # 保留接口，未来可用于实现重叠逻辑
        self.enable_oversize = enable_oversize
        self._parser = MarkdownParser()
        self._renderer = MarkdownRenderer()

    def create_documents(self, texts: List[str]) -> List[Document]:
        """
        将一个 Markdown 文本列表切分为 Document 对象列表。
        """
        all_docs = []
        for text in texts:
            if not text.strip():
                continue
            
            # 1. 解析 Markdown 文本为 AST
            original_root = self._parser.parse(text)
            
            # 2. 根据 AST 节点进行拆分，得到节点“桶”的列表
            node_buckets = self._split_ast(original_root.children)
            
            # 3. 将每个“桶”渲染回 Markdown 文本
            for i, bucket in enumerate(node_buckets):
                # 为每个块创建一个新的 Root 节点，并附上原始的元数据
                new_root = Root(children=bucket, metadata=original_root.metadata)
                chunk_content = self._renderer.render(new_root)
                
                if chunk_content.strip():
                    all_docs.append(Document(
                        page_content=chunk_content,
                        metadata=original_root.metadata,
                        lookup_index=i
                    ))
        return all_docs

    def _get_node_length(self, node: Block) -> int:
        """计算单个块级节点渲染后的文本长度。"""
        # 临时渲染单个节点以获取其长度
        temp_root = Root(children=[node])
        # 渲染并计算字符数
        return len(self._renderer.render(temp_root))

    def _split_ast(self, nodes: List[Block]) -> List[List[Block]]:
        """
        核心拆分逻辑：接收一组块级节点，返回一个“桶”列表，每个桶是一个节点列表。
        """
        buckets: List[List[Block]] = []
        current_bucket: List[Block] = []
        current_length = 0

        for node in nodes:
            node_length = self._get_node_length(node)
            
            # --- Case 1: 节点本身就太大 ---
            if node_length > self.chunk_size:
                # 如果当前桶有内容，先保存
                if current_bucket:
                    buckets.append(current_bucket)
                    current_bucket = []
                    current_length = 0
                
                # 如果允许超大块，则该节点单独成一个桶
                if self.enable_oversize:
                    buckets.append([node])
                else:
                    # 如果不允许，可以抛出错误或进行更细粒度的拆分（当前为跳过）
                    # 注意：真正的字符级拆分会破坏 Markdown 结构，这里选择跳过
                    print(f"警告：节点类型 {node.node_type} 内容过长 ({node_length} > {self.chunk_size}) 且 enable_oversize=False，已跳过。")
                continue

            # --- Case 2: 尝试将节点加入当前桶 ---
            separator_length = 2 # 两个换行符
            if current_length + node_length + separator_length <= self.chunk_size:
                current_bucket.append(node)
                current_length += node_length + separator_length
            else:
                # 当前桶已满，保存它
                if current_bucket:
                    buckets.append(current_bucket)
                
                # 用当前节点开启一个新桶
                current_bucket = [node]
                current_length = node_length

        # 不要忘记最后一个桶
        if current_bucket:
            buckets.append(current_bucket)

        return buckets

# ================= 示例使用 =================
if __name__ == "__main__":
    import sys
    
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')

    markdown_text_complex = """---
title: "My Document"
author: "John Doe"
---

# Document Title

This is the first paragraph under H1. It contains some introductory text.

## H2 Title: Features

- Feature 1
- Feature 2
- Feature 3

This is a paragraph after the list.

### H3 Title: Details

This paragraph under H3 explains the details. This content should ideally stay with the H3 title.

```python
# This is a code block
# It should be treated as a single unit
for i in range(5):
    print(f"Hello, AST! {i}")
```

Another paragraph, back at the H2 level.

## H2 Title: About

> This is a blockquote.
> It contains multiple lines and should not be split.

| Header 1 | Header 2 | Header 3 |
| :--- | :---: | ---: |
| Cell 1.1 | Cell 1.2 | Cell 1.3 |
| Cell 2.1 | Cell 2.2 | Cell 2.3 |

This is the final paragraph.
"""
    print("--- 示例：复杂结构分割 (chunk_size=400) ---")
    print("--- Input Markdown Text ---")
    print(markdown_text_complex)
    
    # 使用新的分割器
    markdown_splitter = MarkdownSplitter(chunk_size=400, enable_oversize=True)
    docs = markdown_splitter.create_documents([markdown_text_complex])

    print("\\n" + "="*50 + "\\n")
    print("--- Split Result (List[Document]) ---")
    print("[")
    for doc in docs:
        print(f"  --- Chunk --- (Metadata: {doc.metadata})")
        print(doc.page_content)
    print("]")
