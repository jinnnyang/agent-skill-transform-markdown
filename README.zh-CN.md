# transform-markdown 技能

一套强大的工具流，用于对超大型Markdown文档进行拆分、转换和合并，以突破大语言模型（LLM）的上下文窗口限制。本技能支持任何基于LLM的文本操作，如翻译、总结、润色等。

## 何时使用

- 当您需要**翻译、总结或转换**一个体积过大、超出LLM上下文窗口的Markdown文件时。
- 当您想在不破坏Markdown格式的前提下，对文档中的**所有文本内容**进行精细化处理时。
- 当您需要快速**预览一个大型Markdown文件的结构**或只读取其中一小部分内容时。

## 核心概念：拆分-转换-合并 (Split-Transform-Merge)

本技能的核心思想是将一个复杂的大任务分解为三个简单步骤：

1.  **拆分 (Split)**: 使用 `split.py` 将一个巨大的Markdown文件安全地拆分成多个保留了原始格式的小文件块。
2.  **转换 (Transform)**: 使用 `transform.py` 逐个处理这些小文件块。您可以提供自定义的Prompt，让大语言模型（LLM）执行翻译、总结、润色等任何文本任务。
3.  **合并 (Merge)**: 使用 `merge.py` 将所有处理后的小文件块按原始顺序无缝地合并成一个最终的完整文档。

---

## 工作流

### 工作流 1: 完整的大型文档转换流程

这是一个典型的端到端翻译示例，您可以将其应用于任何文本转换任务。

#### **第 1 步: 拆分 (Split)**

首先，使用 `split.py` 将您的大文件（例如 `my_book.md`）拆分成多个小块。

```bash
# 将 my_book.md 拆分成大小约 4000 字符的块，并存入 ./cache/input_chunks/ 目录
python ./.roo/skills/transform-markdown/scripts/split.py --filename "my_book.md" --size 4000 --output-dir "./cache/input_chunks/"
```

#### **第 2 步: 转换 (Transform)**

现在，使用 `transform.py` 对每个小块进行翻译。`--ast-node` 参数是此步骤的关键，它能确保在翻译文本的同时，完美保留所有的Markdown格式（如列表、代码块、表格等）。

```bash
# 使用 --ast-node 模式处理 ./cache/input_chunks/ 目录中的所有文件
# 将翻译后的结果存入 ./cache/output_chunks/
python ./.roo/skills/transform-markdown/scripts/transform.py ^
  --input "./cache/input_chunks/" ^
  --output "./cache/output_chunks/" ^
  --api-key "YOUR_API_KEY" ^
  --base-url "https://api.example.com/v1" ^
  --model-id "gpt-4-turbo" ^
  --prompt-template "./.roo/skills/transform-markdown/references/clean-and-translate.md" ^
  --prompt-arguments "source_lang=English,target_lang=Chinese" ^
  --ast-node
```
*   **提示**: 您可以修改 `references/clean-and-translate.md` 文件来定制您自己的Prompt。

#### **第 3 步: 合并 (Merge)**

最后，使用 `merge.py` 将所有翻译好的小块合并成最终的文档。

```bash
# 合并 ./cache/output_chunks/ 目录中的所有文件，并保存为 my_book_translated.md
python ./.roo/skills/transform-markdown/scripts/merge.py --input-dir "./cache/output_chunks/" --filename "my_book_translated.md"
```

---

### 工作流 2: 探查与局部读取

在处理一个未知的超大文件前，使用 `read.py` 可以帮您节省大量时间和Token。

#### **选项 1: 生成大纲**

使用 `--outline` 参数快速预览整个文档的标题结构和每个章节的行数范围。

```bash
python ./.roo/skills/transform-markdown/scripts/read.py --filename "my_very_large_document.md" --outline
```

**示例输出:**
```
--- 文件大纲 ---
- (行: 32) 杭州中德企业信用服务有限公司投资价值评估报告
  - (行: 34) 执行摘要
  - (行: 42) 一、公司基本情况
    - (行: 44) 1.1 工商信息
    - (行: 57) 1.2 央行备案资质
    - (行: 68) 1.3 股权结构
  - (行: 77) 二、企业征信行业分析
```

#### **选项 2: 读取指定范围**

在了解大纲后，使用 `--range` 参数只读取您感兴趣的部分。

```bash
# 只读取第 160 到 300 行的内容
python ./.roo/skills/transform-markdown/scripts/read.py --filename "my_very_large_document.md" --range 160-300
```

---

## 安装说明

本技能是自包含的，不需要通过 `pip` 安装任何外部 Python 包。所有必需的模块都已包含在技能的 `scripts/` 目录中。

您只需要一个标准的 Python 3 环境即可运行这些脚本。

---

## 核心脚本概览

-   `markdown_parser.py`: **核心引擎**。一个强大的、从头构建的Markdown解析器和渲染器，为所有其他脚本提供AST（抽象语法树）处理能力。
-   `split.py`: **拆分器**。将一个大型Markdown文件安全地拆分成多个保留格式的小文件块。
-   `transform.py`: **转换器**。调用LLM对文件或文件块进行“原始”或“AST节点”模式的文本转换。
-   `merge.py`: **合并器**。将多个文件块按正确顺序无缝地合并成一个单一的Markdown文档。
-   `read.py`: **阅读器**。用于高效地生成大型Markdown文件的大纲或读取指定行范围。
-   `openai.py`: 一个无外部依赖的轻量级OpenAI API客户端。
