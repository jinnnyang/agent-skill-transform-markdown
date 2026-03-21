# Transform Markdown Skill

A powerful toolchain for splitting, transforming, and merging very large Markdown documents that exceed the context window limitations of Large Language Models (LLMs). This skill supports any text-based transformation, such as translation, summarization, or proofreading, powered by an LLM.

## When to Use This Skill

- When you need to **translate, summarize, or transform** a Markdown file that is too large to be processed by an LLM in a single pass.
- When you want to apply fine-grained processing to **all text content** within a document while preserving its original Markdown formatting.
- When you need to quickly **preview the structure** of a large Markdown file or read only a small portion of it.

## Core Concept: Split-Transform-Merge

The core methodology of this skill is to break down a large, complex task into three manageable steps:

1.  **Split**: Use `split.py` to safely break a large Markdown file into smaller chunks that respect the original formatting.
2.  **Transform**: Use `transform.py` to process each small chunk individually. You can provide a custom prompt to have an LLM perform any text-based task, such as translation, summarization, or rephrasing.
3.  **Merge**: Use `merge.py` to seamlessly reassemble the processed chunks back into a single, final document in the correct order.

---

## Workflows

### Workflow 1: Full Transformation of a Large Document

This example demonstrates a typical end-to-end process for translating a large document. This workflow can be adapted for any text transformation task.

#### **Step 1: Split**

First, use `split.py` to break your large file (e.g., `my_book.md`) into smaller pieces.

```bash
# Split my_book.md into chunks of approximately 4000 characters
# and store them in the ./cache/input_chunks/ directory.
python ./.roo/skills/transform-markdown/scripts/split.py --filename "my_book.md" --size 4000 --output-dir "./cache/input_chunks/"
```

#### **Step 2: Transform**

Next, use `transform.py` to process each chunk. The `--ast-node` parameter is crucial here, as it ensures that all Markdown formatting (lists, code blocks, tables, etc.) is perfectly preserved while the text content is being transformed.

```bash
# Process all files in ./cache/input_chunks/ using the --ast-node mode.
# The transformed results will be saved in ./cache/output_chunks/.
python ./.roo/skills/transform-markdown/scripts/transform.py \
  --input "./cache/input_chunks/" \
  --output "./cache/output_chunks/" \
  --api-key "YOUR_API_KEY" \
  --base-url "https://api.example.com/v1" \
  --model-id "gpt-4-turbo" \
  --prompt-template "./.roo/skills/transform-markdown/references/clean-and-translate.md" \
  --prompt-arguments "source_lang=English,target_lang=Chinese" \
  --ast-node
```
*   **Tip**: You can customize the transformation by editing the prompt file located at `references/clean-and-translate.md`.

#### **Step 3: Merge**

Finally, use `merge.py` to combine the translated chunks into the final document.

```bash
# Merge all files from ./cache/output_chunks/ into a single file named my_book_translated.md.
python ./.roo/skills/transform-markdown/scripts/merge.py --input-dir "./cache/output_chunks/" --filename "my_book_translated.md"
```

---

### Workflow 2: Exploration and Partial Reading

Before processing an unfamiliar large file, you can use `read.py` to save time and tokens.

#### **Option 1: Generate an Outline**

Use the `--outline` flag to quickly get an overview of the document's heading structure and the line numbers for each section.

```bash
python ./.roo/skills/transform-markdown/scripts/read.py --filename "my_very_large_document.md" --outline
```

**Example Output:**
```
--- File Outline ---
- (Line: 32) Investment Value Assessment Report for Hangzhou Sino-German Credit Service Co., Ltd.
  - (Line: 34) Executive Summary
  - (Line: 42) I. Company Basics
    - (Line: 44) 1.1 Business Information
    - (Line: 57) 1.2 Central Bank Filing Qualification
    - (Line: 68) 1.3 Shareholding Structure
  - (Line: 77) II. Analysis of the Enterprise Credit Reporting Industry
```

#### **Option 2: Read a Specific Range**

Once you have the outline, use the `--range` flag to read only the parts you are interested in.

```bash
# Read only the content from line 160 to 300.
python ./.roo/skills/transform-markdown/scripts/read.py --filename "my_very_large_document.md" --range 160-300
```

---

## Installation

This skill is self-contained and does not require any external Python packages to be installed via pip. All necessary modules are included within the skill's `scripts/` directory.

You only need a standard Python 3 environment to run the scripts.

---

## Core Scripts Overview

-   `markdown_parser.py`: The **core engine**. A powerful, from-scratch Markdown parser and renderer that provides Abstract Syntax Tree (AST) processing capabilities for all other scripts.
-   `split.py`: The **Splitter**. Safely splits a large Markdown file into multiple smaller chunks while preserving formatting.
-   `transform.py`: The **Transformer**. Invokes an LLM to perform text transformations on files or chunks in either "raw" or "AST node" mode.
-   `merge.py`: The **Merger**. Seamlessly merges multiple file chunks back into a single Markdown document in the correct order.
-   `read.py`: The **Reader**. Used to efficiently generate an outline or read a specific range of lines from a large Markdown file.
-   `openai.py`: A lightweight, dependency-free OpenAI API client.
