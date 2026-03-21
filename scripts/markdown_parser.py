# -*- coding: utf-8 -*-
"""
A comprehensive Markdown parser that converts Markdown text into a detailed
Abstract Syntax Tree (AST) and can render it back to a Markdown string.
"""
import re
from typing import List, Optional, Dict, Any

try:
    import yaml
except ImportError:
    yaml = None

# region AST Node Definitions

class Node:
    """Base class for all AST nodes."""
    def __init__(self, node_type: str, children: Optional[List['Node']] = None):
        self.type = node_type
        self.children = children if children is not None else []
        self.parent: Optional[Node] = None
        for child in self.children:
            child.parent = self

    def __repr__(self):
        # Provides a more informative representation for debugging
        content_preview = str(getattr(self, 'text', ''))[:20] or str(getattr(self, 'level', ''))
        return f"{self.__class__.__name__}('{content_preview}...', {len(self.children)} children)"

class Block(Node):
    """Base class for block-level elements."""
    pass

class Root(Block):
    """The root node of the document."""
    def __init__(self, children: List[Block], metadata: Optional[Dict[str, Any]] = None):
        super().__init__('root', children)
        self.metadata = metadata if metadata is not None else {}

class Heading(Block):
    """Represents a heading, e.g., # My Title."""
    def __init__(self, level: int, children: List['Inline']):
        super().__init__('heading', children)
        self.level = level

class Paragraph(Block):
    """Represents a paragraph of text."""
    def __init__(self, children: List['Inline']):
        super().__init__('paragraph', children)

class CodeBlock(Block):
    """Represents a fenced code block or an inline code snippet."""
    def __init__(self, text: str, lang: Optional[str] = None):
        super().__init__('code_block')
        self.text = text
        self.lang = lang # None for inline code, str for fenced block

class BlockQuote(Block):
    """Represents a blockquote, e.g., > Some quote."""
    def __init__(self, children: List[Block]):
        super().__init__('block_quote', children)

class MarkdownList(Block):
    """Represents an ordered or unordered list."""
    def __init__(self, ordered: bool, children: List['ListItem']):
        super().__init__('markdown_list', children)
        self.ordered = ordered

class ListItem(Block):
    """Represents an item in a list."""
    def __init__(self, children: List[Block]):
        super().__init__('list_item', children)

class Table(Block):
    """Represents a GFM table."""
    def __init__(self, children: List[Node], alignments: List[str]):
        super().__init__('table', children)
        self.alignments = alignments

class TableHeader(Block):
    def __init__(self, children: List['TableRow']):
        super().__init__('table_header', children)

class TableBody(Block):
    def __init__(self, children: List['TableRow']):
        super().__init__('table_body', children)

class TableRow(Block):
    def __init__(self, children: List['TableCell']):
        super().__init__('table_row', children)

class TableCell(Block):
    def __init__(self, children: List['Inline']):
        super().__init__('table_cell', children)

class Inline(Node):
    """Base class for inline-level elements."""
    pass

class Text(Inline):
    def __init__(self, text: str):
        super().__init__('text')
        self.text = text

class Bold(Inline):
    def __init__(self, children: List[Inline]):
        super().__init__('bold', children)

class Italic(Inline):
    def __init__(self, children: List[Inline]):
        super().__init__('italic', children)

class Link(Inline):
    def __init__(self, url: str, children: List[Inline], title: Optional[str] = None):
        super().__init__('link', children)
        self.url = url
        self.title = title

class Image(Inline):
    def __init__(self, src: str, alt: str, title: Optional[str] = None):
        super().__init__('image')
        self.src = src
        self.alt = alt
        self.title = title

# endregion

# region Markdown Parser

class MarkdownParser:
    """Parses Markdown text into an Abstract Syntax Tree (AST)."""
    def __init__(self):
        # A robust, scanner-based regex for inline elements using named groups.
        # Order is critical: Image before Link, Bold before Italic.
        inline_patterns = [
            r'(?P<image>!\[(?P<image_alt>[^\]]*)\]\((?P<image_src>[^\s\)]+)(?:\s+"(?P<image_title>[^"]*)")?\))',
            r'(?P<link>\[(?P<link_text>.+?)\]\((?P<link_url>[^\s\)]+)(?:\s+"(?P<link_title>[^"]*)")?\))',
            r'(?P<bold>\*\*(?P<bold_text>.+?)\*\*)',
            r'(?P<italic>\*(?P<italic_text>.+?)\*)',
            r'(?P<inline_code>`(?P<inline_code_text>.+?)`)'
        ]
        self.master_inline_regex = re.compile('|'.join(inline_patterns))

    def parse(self, text: str) -> Root:
        metadata, content = self._parse_front_matter(text)
        content = content.replace('\r\n', '\n').strip()
        block_nodes = self._parse_blocks(content)
        for block in block_nodes:
            self._parse_inlines_recursive(block)
        return Root(block_nodes, metadata)

    def _parse_front_matter(self, text: str) -> tuple[Dict[str, Any], str]:
        if not text.startswith('---'):
            return {}, text
        match = re.match(r'^---\s*\n(.*?)\n---\s*\n?(.*)', text, re.DOTALL)
        if not match:
            return {}, text
        front_matter_str, content = match.groups()
        if yaml is None:
            raise ImportError("PyYAML is required to parse front matter. Please install it using 'pip install PyYAML'.")
        try:
            metadata = yaml.safe_load(front_matter_str)
            return metadata or {}, content
        except yaml.YAMLError:
            return {}, text

    def _parse_blocks(self, text: str) -> List[Block]:
        lines = text.split('\n')
        blocks = []
        i = 0
        while i < len(lines):
            line = lines[i]
            
            if not line.strip():
                i += 1
                continue

            # Headings
            match = re.match(r'^(#{1,6})\s+(.*)', line)
            if match:
                blocks.append(Heading(len(match.group(1)), [Text(match.group(2).strip())]))
                i += 1
                continue

            # Code Blocks
            if line.strip().startswith('```'):
                lang = line.strip()[3:]
                i += 1
                code_lines = []
                while i < len(lines) and not lines[i].strip() == '```':
                    code_lines.append(lines[i])
                    i += 1
                blocks.append(CodeBlock('\n'.join(code_lines), lang))
                i += 1
                continue

            # Tables
            if '|' in line and i + 1 < len(lines) and re.match(r'^\s*\|?.*--.*\|?\s*$', lines[i+1]):
                header_line = lines[i]
                align_line = lines[i+1]
                
                aligns = [a.strip() for a in align_line.split('|') if a.strip()]
                alignments = []
                for align in aligns:
                    starts_with_colon = align.startswith(':')
                    ends_with_colon = align.endswith(':')
                    if starts_with_colon and ends_with_colon:
                        alignments.append('center')
                    elif ends_with_colon:
                        alignments.append('right')
                    elif starts_with_colon:
                        alignments.append('left')
                    else:
                        alignments.append('default')

                header_cells = self._parse_table_row(header_line)
                header = TableHeader([TableRow(header_cells)])
                
                body_rows = []
                i += 2
                while i < len(lines) and '|' in lines[i]:
                    body_rows.append(TableRow(self._parse_table_row(lines[i])))
                    i += 1
                body = TableBody(body_rows)
                blocks.append(Table([header, body], alignments))
                continue

            # Lists
            list_match = re.match(r'^(\s*)(\*|\-|\+|\d+\.)\s+(.*)', line)
            if list_match:
                initial_indent_len = len(list_match.group(1))
                is_ordered = list_match.group(2).rstrip('.').isdigit()
                list_items = []
                
                while i < len(lines):
                    current_line = lines[i]
                    item_match = re.match(r'^(\s*)(\*|\-|\+|\d+\.)\s+(.*)', current_line)
                    if not item_match or len(item_match.group(1)) != initial_indent_len:
                        break
                    
                    item_content_lines = [item_match.group(3)]
                    i += 1
                    while i < len(lines) and lines[i].strip() and not re.match(r'^(\s*)(\*|\-|\+|\d+\.)\s+', lines[i]):
                        item_content_lines.append(lines[i].strip())
                        i += 1
                    
                    item_paragraph = Paragraph([Text('\n'.join(item_content_lines))])
                    list_items.append(ListItem([item_paragraph]))
                
                blocks.append(MarkdownList(is_ordered, list_items))
                continue

            # Paragraphs
            para_lines = [line]
            i += 1
            while (i < len(lines) and lines[i].strip() and 
                   not re.match(r'^(#{1,6}\s|```|\|.*\||(\s*)(\*|\-|\+|\d+\.)\s+)', lines[i])):
                para_lines.append(lines[i])
                i += 1
            blocks.append(Paragraph([Text('\n'.join(para_lines))]))
            continue
            
        return blocks

    def _parse_table_row(self, line: str) -> List[TableCell]:
        line = line.strip()
        if line.startswith('|'): line = line[1:]
        if line.endswith('|'): line = line[:-1]
        return [TableCell([Text(cell.strip())]) for cell in line.split('|')]

    def _parse_inlines_recursive(self, node: Node):
        if isinstance(node, (Paragraph, Heading, TableCell)):
            if len(node.children) == 1 and isinstance(node.children[0], Text):
                raw_text = node.children[0].text
                node.children = self._parse_inlines(raw_text)
                for child in node.children: child.parent = node
        for child in node.children:
            self._parse_inlines_recursive(child)

    def _parse_inlines(self, text: str) -> List[Inline]:
        """A robust inline parser using a scanner approach."""
        nodes = []
        last_pos = 0
        for match in self.master_inline_regex.finditer(text):
            start = match.start()
            if start > last_pos:
                nodes.append(Text(text[last_pos:start]))
            
            last_pos = match.end()
            groups = match.groupdict()
            
            if groups.get('image') is not None:
                nodes.append(Image(alt=groups['image_alt'], src=groups['image_src'], title=groups['image_title']))
            elif groups.get('link') is not None:
                link_children = self._parse_inlines(groups['link_text'])
                nodes.append(Link(url=groups['link_url'], children=link_children, title=groups['link_title']))
            elif groups.get('bold') is not None:
                bold_children = self._parse_inlines(groups['bold_text'])
                nodes.append(Bold(children=bold_children))
            elif groups.get('italic') is not None:
                italic_children = self._parse_inlines(groups['italic_text'])
                nodes.append(Italic(children=italic_children))
            elif groups.get('inline_code') is not None:
                nodes.append(CodeBlock(text=groups['inline_code_text']))

        if last_pos < len(text):
            nodes.append(Text(text[last_pos:]))
            
        return nodes

# endregion

# region Markdown Renderer

class MarkdownRenderer:
    """Renders an AST back into a Markdown string."""
    def render(self, node: Node) -> str:
        method_name = f'render_{node.type}'
        method = getattr(self, method_name, self.render_default)
        return method(node)

    def _render_children(self, node: Node, separator: str = '') -> str:
        return separator.join([self.render(child) for child in node.children])

    def render_default(self, node: Node) -> str:
        return self._render_children(node)

    def render_root(self, node: Root) -> str:
        front_matter = ""
        if node.metadata:
            if yaml is None:
                raise ImportError("PyYAML is required to render front matter. Please install it using 'pip install PyYAML'.")
            yaml_str = yaml.dump(node.metadata, default_flow_style=False, allow_unicode=True, sort_keys=False).strip()
            front_matter = f"---\n{yaml_str}\n---\n\n"
        content = self._render_children(node, separator='\n\n')
        return front_matter + content

    def render_heading(self, node: Heading) -> str:
        return f"{'#' * node.level} {self._render_children(node)}"

    def render_paragraph(self, node: Paragraph) -> str:
        return self._render_children(node)

    def render_code_block(self, node: CodeBlock) -> str:
        return f"```{node.lang or ''}\n{node.text}\n```" if node.lang is not None else f"`{node.text}`"

    def render_markdown_list(self, node: MarkdownList) -> str:
        output = []
        for i, item in enumerate(node.children):
            marker = f"{i + 1}." if node.ordered else "*"
            rendered_item = self.render(item).lstrip()
            output.append(f"{marker} {rendered_item}")
        return '\n'.join(output)

    def render_list_item(self, node: ListItem) -> str:
        return self._render_children(node, separator='\n')

    def render_table(self, node: Table) -> str:
        header = self.render(node.children[0])
        align_map = {'left': ':---', 'center': ':---:', 'right': '---:', 'default': '---'}
        align_line_parts = [align_map.get(align, '---') for align in node.alignments]
        align_line = '|' + '|'.join(align_line_parts) + '|'
        body = self.render(node.children[1])
        return f"{header}\n{align_line}\n{body}"

    def render_table_header(self, node: TableHeader) -> str:
        return self._render_children(node)

    def render_table_body(self, node: TableBody) -> str:
        return self._render_children(node, separator='\n')

    def render_table_row(self, node: TableRow) -> str:
        return '| ' + ' | '.join(self.render(cell) for cell in node.children) + ' |'

    def render_table_cell(self, node: TableCell) -> str:
        return self._render_children(node)

    def render_text(self, node: Text) -> str:
        return node.text

    def render_bold(self, node: Bold) -> str:
        return f"**{self._render_children(node)}**"

    def render_italic(self, node: Italic) -> str:
        return f"*{self._render_children(node)}*"

    def render_link(self, node: Link) -> str:
        title_part = f' "{node.title}"' if node.title else ''
        return f"[{self._render_children(node)}]({node.url}{title_part})"

    def render_image(self, node: Image) -> str:
        title_part = f' "{node.title}"' if node.title else ''
        return f"![{node.alt}]({node.src}{title_part})"

# endregion

if __name__ == '__main__':
    markdown_input = """---
title: "My Awesome Document"
author: "John Doe"
tags: [markdown, parser]
---

# Main Title

This is a paragraph with **bold text** and an *italicized* word.
It also includes a [link to Google](https://www.google.com "Google's Homepage").

- An unordered list item.
- Another item.

1. An ordered list item.
2. And another one.

## A Sub-heading

Here is a table:

| Header 1 | Header 2 | Header 3 |
|:---|:---:|---:|
| Left-aligned | `code` | Right-aligned |
| cell 2.1 | cell 2.2 | ![img](src) |

And a code block:
```python
def hello():
    # This is a comment
    print("Hello, World!")
```
"""
    print("--- Input Markdown ---")
    print(markdown_input)
    
    parser = MarkdownParser()
    ast = parser.parse(markdown_input)

    # Modify the AST: Change "bold text" to "very important text"
    first_paragraph = next((node for node in ast.children if isinstance(node, Paragraph)), None)
    if first_paragraph:
        bold_node = next((node for node in first_paragraph.children if isinstance(node, Bold)), None)
        if bold_node and bold_node.children and isinstance(bold_node.children[0], Text):
            bold_node.children[0].text = "very important text"

    renderer = MarkdownRenderer()
    new_markdown = renderer.render(ast)

    print("\n--- Rendered Markdown (after modification) ---")
    print(new_markdown)
    
    print("\n--- Verification: Running the script should now succeed with correct output. ---")
