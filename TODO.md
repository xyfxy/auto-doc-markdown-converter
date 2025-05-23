# 项目待办事项：自动化文档清洗与 Markdown 转换工具

根据 `auto_doc_markdown_plan.mdc` 的建议开发步骤，按优先级排列。

## 第一阶段：基础环境与核心文本提取

- [x] **1. 环境搭建**:
  - [x] 创建 Python 虚拟环境。 (用户手动完成)
  - [x] 安装基础库: `python-docx`, `pdfplumber`, `reportlab` (之前用于测试生成PDF，现可选)。 (通过 `requirements.txt`)
  - [x] 初始化 `requirements.txt` 文件。
- [x] **2. DOCX 文本提取模块 (`docx_extractor.py`)**:
  - [x] 实现从 `.docx` 文件中提取所有段落文本的功能。
  - [x] 关注保留段落分隔。
  - [x] 编写初步的单元测试 (在 `/tests/test_docx_extractor.py` 中，使用位于 `/tests/fixtures/` 目录下的 `sample.docx` 文件)。
- [x] **3. PDF 文本提取模块 (`pdf_extractor.py`)**:
  - [x] 实现从文本型 `.pdf` 文件中提取所有文本的功能 (使用 `pdfplumber`)。
  - [x] 关注保留段落分隔。
  - [x] 编写初步的单元测试 (在 `/tests/test_pdf_extractor.py` 中，使用位于 `/tests/fixtures/` 目录下的 `sample.pdf` 文件)。
- [x] **4. 文件处理器模块 (`file_handler.py`)**:
  - [x] 实现文件读取的初步逻辑，根据文件类型调用相应的提取器。
  - [x] 实现文件验证（例如，检查文件扩展名是否为 `.docx` 或 `.pdf`）。

## 第二阶段：LLM 集成与 Markdown 生成

- [ ] **5. LLM 选型与初步测试**:
  - [ ] 确定首选的 LLM API (例如 OpenAI GPT, Anthropic Claude, Google Gemini)。
  - [ ] 获取 API 访问凭证并配置好本地环境（例如设置环境变量）。
  - [ ] 手动或通过简单的脚本测试选定 LLM 对示例文本的标题识别能力，迭代优化 `auto_doc_markdown_plan.mdc` 中建议的提示词。
- [ ] **6. LLM 处理器模块 (`llm_processor.py`)**:
  - [ ] 实现 `analyze_text_with_llm(text: str) -> str` 函数。
  - [ ] 封装对所选 LLM API 的调用。
  - [ ] 集成优化后的提示词，用于识别 H1, H2, H3, H4 标题和段落 (P)。
  - [ ] 处理 LLM API 可能返回的错误。
  - [ ] 编写初步的单元测试 (例如，在 `/tests/test_llm_processor.py` 中，可以使用 mock API 调用或针对预期的 LLM 输出格式进行测试)。
- [ ] **7. Markdown 生成模块 (`markdown_generator.py`)**:
  - [ ] 实现 `generate_markdown_from_labeled_text(labeled_text: str) -> str` 函数。
  - [ ] 将 LLM 返回的带标记文本 (如 "H1: Title", "P: Paragraph") 转换为正确的 Markdown 格式。
  - [ ] 确保段落和标题的顺序得以保留。
  - [ ] 编写初步的单元测试 (例如，在 `/tests/test_markdown_generator.py` 中)。

## 第三阶段：整合、CLI 与完善

- [ ] **8. 主程序与 CLI (`main.py`)**:
  - [ ] 创建 `main.py` 作为程序入口。
  - [ ] 使用 `argparse` 或 `click` 实现命令行界面，允许用户指定输入文件/文件夹和输出文件夹。
  - [ ] 集成 `file_handler.py`, `docx_extractor.py`, `pdf_extractor.py`, `llm_processor.py`, `markdown_generator.py` 的功能，形成完整处理流程。
  - [ ] 实现将最终的 Markdown 内容保存到与输入文件同名（扩展名为 `.md`）的文件中。
- [ ] **9. 错误处理与日志**:
  - [ ] 在所有模块中添加更完善的错误处理 (try-except 块)。
  - [ ] 配置 `logging` 模块，记录程序运行过程中的重要信息和错误。
  - [ ] (可选) 在 `utils.py` 中创建日志配置函数。
- [ ] **10. 输出处理完善 (`file_handler.py` 或 `main.py`)**:
  - [ ] 确保输出文件可以正确保存到用户指定的路径。
  - [ ] 处理文件名冲突等情况（例如，如果输出文件已存在）。
- [ ] **11. README 文档 (`README.md`)**:
  - [ ] 编写项目说明、如何安装依赖、如何运行程序等。

## 第四阶段：测试与迭代优化

- [ ] **12. 完整测试**:
  - [ ] 准备更多样化的测试文档（不同结构、长度、包含特殊字符的 `.docx` 和 `.pdf` 文件）。
  - [ ] 进行端到端测试，覆盖 `main.py` 的主要功能。
  - [ ] 在 `/tests/fixtures/` 目录下存放这些测试文件。
- [ ] **13. 迭代优化**:
  - [ ] 根据测试结果，优化 LLM 提示词以提高标题识别的准确性。
  - [ ] 优化文本提取逻辑，处理边缘情况。
  - [ ] 审阅和重构代码，提高可读性和可维护性。
  - [ ] 考虑性能瓶颈，特别是 LLM API 调用部分（例如，研究批量处理或异步调用的可能性，如果适用）。

---

**如何使用此待办事项列表:**

* 在每个任务前的 `[ ]` 中间添加 `x` (即 `[x]`) 来标记已完成的任务。
* 随着项目的进展，你可以随时添加、修改或重新排列任务。
