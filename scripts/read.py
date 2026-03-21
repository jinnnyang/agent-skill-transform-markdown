# -*- coding: utf-8 -*-
import argparse
import sys
import re
from pathlib import Path

def get_outline(file_path: Path):
    """
    通过逐行读取和正则表达式匹配，生成 Markdown 文件的大纲。
    """
    print(f"正在扫描文件: {file_path}...")
    
    # 正则表达式匹配以 '#' 开头的标题行
    heading_pattern = re.compile(r'^(#+)\s+(.*)')
    
    found_headings = False
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            print("\\n--- 文件大纲 ---")
            for line_num, line in enumerate(f, 1):
                match = heading_pattern.match(line)
                if match:
                    found_headings = True
                    level = len(match.group(1))
                    title = match.group(2).strip()
                    
                    indent = "  " * (level - 1)
                    print(f"{indent}- (行: {line_num}) {title}")
        
        if not found_headings:
            print("文件中未找到任何标题。")
            
    except Exception as e:
        print(f"生成大纲时出错: {e}")


def read_range(file_path: Path, line_range: str):
    """
    读取并打印文件的指定行数范围。
    """
    try:
        start_str, end_str = line_range.split('-')
        start_line = int(start_str)
        end_line = int(end_str)
        
        if start_line <= 0 or end_line < start_line:
            raise ValueError("行数范围格式不正确。")

    except ValueError:
        print("错误：范围格式不正确。请使用 '开始行-结束行' 的格式，例如 '123-345'。")
        return

    print(f"--- 从 {file_path} 读取第 {start_line} 到 {end_line} 行 ---")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                if i >= start_line:
                    if i > end_line:
                        break
                    sys.stdout.write(line)
    except Exception as e:
        print(f"读取文件时出错: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="智能读取大型 Markdown 文件，支持生成大纲或读取指定行范围。",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        '--filename',
        type=str,
        required=True,
        help='要读取的 Markdown 文件路径。'
    )
    
    # 创建一个互斥组，--outline 和 --range 不能同时使用
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--outline',
        action='store_true',
        help='生成文件的大纲，显示标题和内容的行数范围。'
    )
    group.add_argument(
        '--range',
        type=str,
        help="要读取的行数范围，格式为 '开始行-结束行' (例如 '100-250')。"
    )

    args = parser.parse_args()
    
    file_path = Path(args.filename)
    if not file_path.is_file():
        print(f"错误：文件未找到 -> {args.filename}")
        sys.exit(1)

    if args.outline:
        get_outline(file_path)
    elif args.range:
        read_range(file_path, args.range)

if __name__ == "__main__":
    main()
