document.addEventListener('DOMContentLoaded', function() {
    // 获取 DOM 元素
    const uploadForm = document.getElementById('uploadForm');
    const fileInput = document.getElementById('fileInput');
    const uploadStatus = document.getElementById('uploadStatus');
    const resultsArea = document.getElementById('resultsArea');

    // HTML 转义函数，用于安全地显示来自服务器的文本
    function escapeHTML(str) {
        if (typeof str !== 'string') return '';
        return str.replace(/[&<>"']/g, function (match) {
            return {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#39;'
            }[match];
        });
    }

    // 新的对照预览函数
    function fetchAndShowComparisonPreview(originalFilename, markdownFilename, listItemElement) {
        let previewArea = listItemElement.querySelector('.comparison-preview-area');
        
        // 如果 previewArea 不存在，则创建它
        if (!previewArea) {
            previewArea = document.createElement('div');
            previewArea.className = 'comparison-preview-area';
            previewArea.style.display = 'none'; // Initially hidden, will be shown by button click
            previewArea.style.marginTop = '10px';
            previewArea.style.border = '1px solid #eee';
            previewArea.style.padding = '10px';

            previewArea.innerHTML = `
                <div style="display: flex; justify-content: space-between;">
                    <h4 style="margin-top:0;">原始文档预览 (DOCX)</h4>
                    <h4 style="margin-top:0;">Markdown 预览</h4>
                </div>
                <div style="display: flex; justify-content: space-between; gap: 10px;">
                    <div class="original-preview-pane" style="width: 49%; border: 1px solid #ccc; padding: 5px; height: 400px; overflow-y: auto; background-color: #f9f9f9;">
                        正在加载原始预览...
                    </div>
                    <div class="markdown-preview-pane" style="width: 49%; border: 1px solid #ccc; padding: 5px; height: 400px; overflow-y: auto; background-color: #f9f9f9;">
                        正在加载 Markdown 预览...
                    </div>
                </div>
            `;
            listItemElement.appendChild(previewArea);
        }

        const originalPane = previewArea.querySelector('.original-preview-pane');
        const markdownPane = previewArea.querySelector('.markdown-preview-pane');

        // Toggle display (this part is handled by the button's new onclick logic)
        // previewArea.style.display = previewArea.style.display === 'none' ? 'block' : 'none';
        // if (previewArea.style.display === 'none') {
        //     return; // If hiding, don't fetch
        // }

        originalPane.innerHTML = '正在加载原始预览...';
        markdownPane.innerHTML = '正在加载 Markdown 预览...';

        // Original Document Pane Logic
        originalPane.innerHTML = '正在加载原始预览...'; // Set initial loading message

        if (originalFilename.toLowerCase().endsWith('.docx')) {
            fetch(`/preview_docx/${encodeURIComponent(originalFilename)}`)
                .then(response => {
                    if (!response.ok) {
                        return response.json().then(errData => {
                            throw new Error(errData.error || `服务器错误: ${response.status}`);
                        }).catch(() => {
                            throw new Error(`服务器响应错误: ${response.status} ${response.statusText}`);
                        });
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.html_content) {
                        originalPane.innerHTML = data.html_content;
                    } else if (data.error) {
                        originalPane.innerHTML = `<p class="error-message">DOCX 预览失败: ${escapeHTML(data.error)}</p>`;
                    } else {
                        originalPane.innerHTML = `<p class="error-message">DOCX 预览返回了非预期的响应格式。</p>`;
                    }
                })
                .catch(error => {
                    console.error('获取 DOCX 预览失败:', error);
                    originalPane.innerHTML = `<p class="error-message">DOCX 预览请求失败: ${escapeHTML(error.message)}</p>`;
                });
        } else if (originalFilename.toLowerCase().endsWith('.pdf')) {
            originalPane.innerHTML = ''; // Clear loading message
            const iframe = document.createElement('iframe');
            iframe.src = `/preview_pdf/${encodeURIComponent(originalFilename)}`;
            iframe.style.width = '100%';
            iframe.style.height = '100%';
            iframe.style.border = 'none';
            iframe.title = `原始 PDF 预览: ${escapeHTML(originalFilename)}`;
            
            // Fallback content or error handling for iframe
            iframe.onload = function() {
                // You could check if the content loaded is actually a PDF, 
                // but it's tricky due to cross-origin restrictions if src is from a different domain.
                // For same-origin, you might inspect iframe.contentDocument.contentType
                // However, for simple cases, successful load implies the server sent something.
                // If server sent an error page with 200 OK, that would show in iframe.
                // Errors like 404 from server for the PDF src will usually leave iframe blank or show browser error.
                console.log("PDF iframe loaded.");
            };
            iframe.onerror = function() {
                // This onerror on iframe itself is not very reliable for content errors (like 404s)
                console.error('PDF iframe 加载时发生错误。');
                originalPane.innerHTML = `<p class="error-message">无法加载 PDF 预览。文件可能不存在或浏览器不支持内嵌 PDF。</p>`;
            };
            
            originalPane.appendChild(iframe);
        } else {
            originalPane.innerHTML = `<p>原始文档预览不支持此文件类型 (${escapeHTML(originalFilename.split('.').pop())})。</p><p>仅支持 .docx 和 .pdf 文件预览。</p>`;
        }

        // Fetch and Render Markdown Preview
        fetch(`/download/${encodeURIComponent(markdownFilename)}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`获取 Markdown 失败: ${response.status} ${response.statusText}`);
                }
                return response.text();
            })
            .then(markdownText => {
                if (typeof marked === 'undefined') {
                    console.error('Marked.js 库未加载。');
                    markdownPane.innerHTML = '<p class="error-message">Markdown 预览库加载失败。</p>';
                    return;
                }
                try {
                    const htmlContent = marked.parse(markdownText);
                    markdownPane.innerHTML = htmlContent; // marked.parse output is generally safe for preview
                } catch (e) {
                    console.error('Markdown 解析错误:', e);
                    markdownPane.innerHTML = `<p class="error-message">Markdown 内容解析时发生错误: ${escapeHTML(e.message)}</p>`;
                }
            })
            .catch(error => {
                console.error('获取 Markdown 预览失败:', error);
                markdownPane.innerHTML = `<p class="error-message">Markdown 预览失败: ${escapeHTML(error.message)}</p>`;
            });
    }


    // 添加表单提交事件监听器
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(event) {
            event.preventDefault(); // 阻止表单的默认提价行为

            // 清空之前的状态和结果
            uploadStatus.innerHTML = '正在准备上传，请稍候...'; // 1. Initial Click
            resultsArea.innerHTML = '<p>处理流程已启动...</p>'; // Neutral message for results area

            const files = fileInput.files;

            // 检查是否有文件被选择
            if (files.length === 0) {
                resultsArea.innerHTML = '<p class="error-message">请至少选择一个文件。</p>';
                return;
            }

            // 创建 FormData 对象
            const formData = new FormData();
            for (let i = 0; i < files.length; i++) {
                formData.append('files[]', files[i]); // 'files[]' 必须与后端 Flask 期望的名称一致
            }

            uploadStatus.innerHTML = '正在连接服务器并发送文件...'; // 2. Before fetch Call

            // 执行异步上传
            fetch('/upload', { // URL 对应 Flask 中的上传路由
                method: 'POST',
                body: formData
            })
            .then(response => {
                uploadStatus.innerHTML = '文件已发送，服务器处理中，这可能需要一些时间...'; // 3. After fetch initiated
                if (!response.ok) {
                    // 如果 HTTP 状态码不是 2xx，尝试解析错误信息
                    return response.json().then(errData => {
                        // 优先使用后端在 JSON 中明确提供的错误信息
                        throw new Error(errData.error || `服务器返回错误: ${response.status}`);
                    }).catch(() => {
                        // 如果无法从 JSON 中解析错误，或者 JSON 本身就是问题，则抛出通用 HTTP 错误
                        throw new Error(`服务器响应错误: ${response.status} ${response.statusText}`);
                    });
                }
                return response.json(); // 解析 JSON 响应体
            })
            .then(data => {
                uploadStatus.innerHTML = '处理完毕，正在准备结果...'; // 4. After response.json()
                resultsArea.innerHTML = ''; // 清空之前的 "正在准备..." 或错误信息

                if (Array.isArray(data) && data.length > 0) {
                    const ul = document.createElement('ul');
                    ul.className = 'results-list';

                    data.forEach(item => {
                        const li = document.createElement('li');
                        li.className = 'result-item';
                        
                        let content = `<strong>${escapeHTML(item.original_filename)}:</strong> `;
                        if (item.status === 'success') {
                            content += `<span class="status-success">处理成功。</span> `;
                            if (item.processed_filename) {
                                const downloadLink = document.createElement('a');
                                downloadLink.href = `/download/${encodeURIComponent(item.processed_filename)}`;
                                downloadLink.textContent = `下载 ${escapeHTML(item.processed_filename)}`;
                                downloadLink.className = 'download-link';
                                downloadLink.setAttribute('download', item.processed_filename); // 建议浏览器下载

                                const downloadLink = document.createElement('a');
                                downloadLink.href = `/download/${encodeURIComponent(item.processed_filename)}`;
                                downloadLink.textContent = `下载 ${escapeHTML(item.processed_filename)}`;
                                downloadLink.className = 'download-link';
                                downloadLink.setAttribute('download', item.processed_filename);
                                li.appendChild(downloadLink); // Append link

                                li.appendChild(document.createTextNode(' ')); // Add a space

                                const comparisonPreviewButton = document.createElement('button');
                                comparisonPreviewButton.textContent = '对照预览';
                                comparisonPreviewButton.className = 'comparison-preview-button';
                                
                                // Create the preview area structure but keep it hidden initially
                                // This structure will be appended to 'li' when the button is first clicked and area needs to be shown.
                                // Or, create it here and append to li, then toggle display. Let's do the latter for simplicity.
                                
                                let previewArea = li.querySelector('.comparison-preview-area');
                                if (!previewArea) { // Create if not exists (e.g. if li content is cleared and rebuilt)
                                    previewArea = document.createElement('div');
                                    previewArea.className = 'comparison-preview-area';
                                    previewArea.style.display = 'none'; // Initially hidden
                                    previewArea.style.marginTop = '10px';
                                    previewArea.style.border = '1px solid #eee';
                                    previewArea.style.padding = '10px';
                                    previewArea.innerHTML = `
                                        <div style="display: flex; justify-content: space-between;">
                                            <h4 style="margin-top:0;">原始文档预览 (DOCX)</h4>
                                            <h4 style="margin-top:0;">Markdown 预览</h4>
                                        </div>
                                        <div style="display: flex; justify-content: space-between; gap: 10px;">
                                            <div class="original-preview-pane" style="width: 49%; border: 1px solid #ccc; padding: 5px; height: 400px; overflow-y: auto; background-color: #f9f9f9;"></div>
                                            <div class="markdown-preview-pane" style="width: 49%; border: 1px solid #ccc; padding: 5px; height: 400px; overflow-y: auto; background-color: #f9f9f9;"></div>
                                        </div>
                                    `;
                                    // li.appendChild(previewArea); // Append it after all other content in li
                                }


                                comparisonPreviewButton.onclick = (function(origFname, mdFname, currentLi, area) {
                                    return function() {
                                        const isVisible = area.style.display !== 'none';
                                        area.style.display = isVisible ? 'none' : 'block';
                                        if (!isVisible) { 
                                            fetchAndShowComparisonPreview(origFname, mdFname, currentLi);
                                        }
                                    };
                                })(item.original_filename, item.processed_filename, li, previewArea);
                                
                                li.appendChild(comparisonPreviewButton); // Append button
                                li.appendChild(previewArea); // Append the (initially hidden) preview area

                            } else {
                                const noDownloadSpan = document.createElement('span');
                                noDownloadSpan.textContent = `Markdown 内容已生成 (但未提供下载链接)。`;
                                li.appendChild(noDownloadSpan);
                            }
                        } else { // item.status !== 'success'
                            const errorSpan = document.createElement('span');
                            errorSpan.className = 'status-error';
                            errorSpan.textContent = `处理失败。 原因: ${escapeHTML(item.message || '未知错误')}`;
                            li.appendChild(errorSpan);
                        }
                        // li.innerHTML = content; // Avoid using innerHTML to preserve event listeners

                        ul.appendChild(li);
                    });
                    resultsArea.appendChild(ul);
                    uploadStatus.innerHTML = '处理完成！'; // 5. On Successful Completion (after results are rendered)
                } else if (data.error) { // 处理整体上传错误（如果后端这样返回）
                     resultsArea.innerHTML = `<p class="error-message">处理失败: ${escapeHTML(data.error)}</p>`;
                     uploadStatus.innerHTML = '处理失败。'; // More specific status
                } else if (Array.isArray(data) && data.length === 0) {
                    resultsArea.innerHTML = '<p>已上传，但未返回任何处理结果。可能是所有文件都无法处理。</p>';
                    uploadStatus.innerHTML = '处理完成，但无有效结果。'; // More specific status
                }
                 else {
                    resultsArea.innerHTML = '<p>未收到有效的处理结果或返回了非预期的格式。</p>';
                    uploadStatus.innerHTML = '处理完成，但响应格式不正确。'; // More specific status
                }
            })
            .catch(error => {
                console.error('上传或处理过程中发生错误:', error);
                uploadStatus.innerHTML = '上传或处理过程中发生错误。'; // 6. On Error
                resultsArea.innerHTML = `<p class="error-message">错误详情: ${escapeHTML(error.message)}</p>`;
            });
        });
    } else {
        console.error('上传表单 (uploadForm) 未在 DOM 中找到。');
    }
});
// End of script.js - test modification
