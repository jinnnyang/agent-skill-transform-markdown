# -*- coding: utf-8 -*-
import argparse
import os
import re
from pathlib import Path

try:
    from markdown_parser import MarkdownParser, MarkdownRenderer, Root, Block
except ImportError:
    print("错误：无法导入 'markdown_parser'。请确保 markdown_parser.py 文件与此脚本位于同一目录中。")
    exit(1)

def find_and_sort_chunks(directory: Path, base_filename: str) -> list[Path]:
    """
    在目录中查找所有相关的块文件并按数字顺序排序。
    例如：[base-chunk_0.md, base-chunk_1.md, base-chunk_3.md]
    """
    pattern = re.compile(rf"{re.escape(base_filename)}-chunk_(\d+)\.md$")
    
    found_files = []
    for f in directory.iterdir():
        if f.is_file():
            match = pattern.match(f.name)
            if match:
                chunk_num = int(match.group(1))
                found_files.append((chunk_num, f))
    
    # 按块编号排序
    found_files.sort(key=lambda x: x[0])
    
    return [f for _, f in found_files]

def main():
    """
    主函数，用于解析命令行参数并执行 Markdown 文件合并。
    """
    # --- 1. 设置命令行参数解析 ---
    parser = argparse.ArgumentParser(
        description="将一个目录中的多个 Markdown 块文件合并成一个单一的 Markdown 文档。",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        required=True,
        help="包含拆分后的 Markdown 块文件的目录。"
    )
    parser.add_argument(
        "--filename",
        type=str,
        required=True,
        help="合并后输出的 Markdown 文件的完整路径。"
    )
    # --size 参数在合并时不需要，因此不添加

    args = parser.parse_args()

    # --- 2. 验证输入目录 ---
    input_dir = Path(args.input_dir)
    if not input_dir.is_dir():
        print(f"错误：输入目录未找到 -> {args.input_dir}")
        return

    # --- 3. 查找并排序块文件 ---
    # 从目录中的文件自动推断出基础文件名
    base_filename = None
    chunk_pattern = re.compile(r"^(.*)-chunk_(\d+)\.md$")
    for f in input_dir.iterdir():
        if f.is_file():
            match = chunk_pattern.match(f.name)
            if match:
                base_filename = match.group(1)
                print(f"自动检测到块文件基础名称: '{base_filename}'")
                break  # 找到后即退出循环

    if not base_filename:
        print(f"错误：在目录 '{input_dir}' 中未找到任何 '...-chunk_*.md' 格式的文件。")
        return

    chunk_files = find_and_sort_chunks(input_dir, base_filename)

    if not chunk_files:
        # 这种情况在找到 base_filename 后应该很少发生，但作为安全检查
        print(f"错误：在目录 '{input_dir}' 中未找到任何 '{base_filename}-chunk_*.md' 文件。")
        return
    
    output_file = Path(args.filename)
        
    print(f"找到了 {len(chunk_files)} 个块文件，将按顺序合并。")

    # --- 4. 初始化解析器、渲染器和数据容器 ---
    parser = MarkdownParser()
    renderer = MarkdownRenderer()
    
    final_metadata = None
    all_blocks: list[Block] = []

    # --- 5. 逐个解析文件并合并内容 ---
    for i, chunk_file in enumerate(chunk_files):
        print(f"正在处理: {chunk_file.name}...")
        try:
            with open(chunk_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析块文件内容
            root = parser.parse(content)
            
            # 只保留第一个文件的元数据
            if i == 0:
                final_metadata = root.metadata
                print("  -> 已保留元数据。")

            # 添加所有块级节点
            if root.children:
                all_blocks.extend(root.children)

        except Exception as e:
            print(f"错误：处理文件 {chunk_file} 时出错 -> {e}")
            return

    # --- 6. 创建最终的 AST 并渲染 ---
    if not all_blocks:
        print("警告：所有文件中都没有找到可合并的内容。")
        final_content = ""
    else:
        final_root = Root(children=all_blocks, metadata=final_metadata)
        final_content = renderer.render(final_root)

    # --- 7. 写入最终的合并文件 ---
    output_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(final_content)
        print(f"\\n合并成功！已将所有内容写入 -> {output_file}")
    except Exception as e:
        print(f"\\n错误：写入最终文件 {output_file} 时出错 -> {e}")


if __name__ == "__main__":
    main()
