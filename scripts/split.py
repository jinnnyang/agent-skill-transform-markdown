# -*- coding: utf-8 -*-
import argparse
import os
from pathlib import Path

try:
    from markdown_splitter import MarkdownSplitter
except ImportError:
    print("错误：无法导入 'MarkdownSplitter'。请确保 markdown_splitter.py 文件与此脚本位于同一目录中。")
    exit(1)

def main():
    """
    主函数，用于解析命令行参数并执行 Markdown 文件拆分。
    """
    # --- 1. 设置命令行参数解析 ---
    parser = argparse.ArgumentParser(
        description="将一个 Markdown 文件拆分成多个基于 AST 的块。",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--filename",
        type=str,
        required=True,
        help="要拆分的 Markdown 文件的路径。"
    )
    parser.add_argument(
        "--size",
        type=int,
        default=2048,
        help="每个块的目标最大字符数。默认值：2048"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        required=True,
        help="用于存放拆分后的 Markdown 块文件的目录。"
    )

    args = parser.parse_args()

    # --- 2. 验证输入文件 ---
    input_path = Path(args.filename)
    if not input_path.is_file():
        print(f"错误：文件未找到 -> {args.filename}")
        return

    # --- 3. 读取文件内容 ---
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            markdown_text = f.read()
    except Exception as e:
        print(f"错误：读取文件时出错 -> {e}")
        return

    # --- 4. 初始化拆分器并执行拆分 ---
    print(f"正在使用 chunk_size={args.size} 拆分文件: {args.filename}...")
    splitter = MarkdownSplitter(chunk_size=args.size)
    documents = splitter.create_documents([markdown_text])
    
    if not documents:
        print("拆分后未生成任何文档块。")
        return

    print(f"文件被成功拆分为 {len(documents)} 个块。")

    # --- 5. 创建输出目录并写入文件 ---
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    base_filename = input_path.stem

    for i, doc in enumerate(documents):
        output_filename = f"{base_filename}-chunk_{i}.md"
        output_filepath = output_path / output_filename
        
        try:
            with open(output_filepath, 'w', encoding='utf-8') as f:
                f.write(doc.page_content)
            print(f"已保存块 {i} -> {output_filepath}")
        except Exception as e:
            print(f"错误：写入文件 {output_filepath} 时出错 -> {e}")

    print("\\n拆分完成！")

if __name__ == "__main__":
    main()
