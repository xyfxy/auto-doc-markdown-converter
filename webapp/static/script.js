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

    // 获取并显示 Markdown 文件预览的函数
    function fetchAndShowPreview(filename, listItemElement) {
        // 移除旧的预览（如果存在）
        const oldPreview = listItemElement.querySelector('.preview-container');
        if (oldPreview) {
            oldPreview.remove();
        }

        const previewContainer = document.createElement('div');
        previewContainer.className = 'preview-container';
        previewContainer.textContent = '正在加载预览...';
        listItemElement.appendChild(previewContainer);

        fetch(`/download/${encodeURIComponent(filename)}`) // 使用下载链接获取文件内容
            .then(response => {
                if (!response.ok) {
                    throw new Error(`无法获取预览: ${response.status} ${response.statusText}`);
                }
                return response.text(); // 获取文本内容
            })
            .then(markdownText => {
                // 新的 Markdown 到 HTML 转换逻辑
                if (typeof marked === 'undefined') {
                    console.error('Marked.js 库未加载。');
                    previewContainer.innerHTML = '<p class="error-message">Markdown 预览库加载失败。</p>';
                    return;
                }
                try {
                    const htmlContent = marked.parse(markdownText); // 使用 marked.parse()
                    previewContainer.innerHTML = ''; // 清空 "正在加载预览..."
                    // 为了安全起见，如果marked.parse返回的是不可信内容且需要进一步处理，
                    // 可能需要在这里进行HTML净化 (DOMPurify)，但对于从自己服务器获取的 .md 文件内容，
                    // 通常认为是可信的。
                    const previewContentDiv = document.createElement('div');
                    previewContentDiv.className = 'markdown-preview'; // 可以保留这个类名用于样式
                    previewContentDiv.innerHTML = htmlContent;
                    previewContainer.appendChild(previewContentDiv);
                } catch (e) {
                    console.error('Markdown 解析错误:', e);
                    previewContainer.innerHTML = `<p class="error-message">Markdown 内容解析时发生错误: ${escapeHTML(e.message)}</p>`;
                }
            })
            .catch(error => {
                console.error('获取预览失败:', error);
                previewContainer.innerHTML = `<p class="error-message">预览失败: ${escapeHTML(error.message)}</p>`;
            });
    }

    // 添加表单提交事件监听器
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(event) {
            event.preventDefault(); // 阻止表单的默认提价行为

            // 清空之前的状态和结果
            uploadStatus.innerHTML = '';
            resultsArea.innerHTML = '<p>正在准备上传...</p>';

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

            uploadStatus.innerHTML = '正在上传文件...';

            // 执行异步上传
            fetch('/upload', { // URL 对应 Flask 中的上传路由
                method: 'POST',
                body: formData
            })
            .then(response => {
                uploadStatus.innerHTML = '后端正在处理文件，请稍候...'; // 文件已上传，等待后端处理
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
                uploadStatus.innerHTML = '处理完成！';
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

                                const previewButton = document.createElement('button');
                                previewButton.textContent = '预览 Markdown';
                                previewButton.className = 'preview-button';
                                // 使用闭包确保 filename 在 onclick 时是正确的
                                previewButton.onclick = (function(filename, currentListItem) {
                                    return function() { fetchAndShowPreview(filename, currentListItem); };
                                })(item.processed_filename, li);

                                content += downloadLink.outerHTML + ' ' + previewButton.outerHTML;
                            } else {
                                content += `<span>Markdown 内容已生成 (但未提供下载链接)。</span>`;
                            }
                        } else {
                            content += `<span class="status-error">处理失败。</span> 原因: ${escapeHTML(item.message || '未知错误')}`;
                        }
                        li.innerHTML = content; // 设置 innerHTML 后，之前绑定的 onclick 可能需要重新处理，但这里是直接生成 HTML 字符串
                        
                        // 重新获取按钮并绑定事件（如果 previewButton.onclick 的方式在某些浏览器有问题）
                        // 或者，在创建按钮后，先附加到 li，再通过 li.querySelector 找到按钮并绑定事件。
                        // 当前的闭包方式通常是有效的。

                        ul.appendChild(li);
                    });
                    resultsArea.appendChild(ul);
                } else if (data.error) { // 处理整体上传错误（如果后端这样返回）
                     resultsArea.innerHTML = `<p class="error-message">处理失败: ${escapeHTML(data.error)}</p>`;
                } else if (Array.isArray(data) && data.length === 0) {
                    resultsArea.innerHTML = '<p>已上传，但未返回任何处理结果。可能是所有文件都无法处理。</p>';
                }
                 else {
                    resultsArea.innerHTML = '<p>未收到有效的处理结果或返回了非预期的格式。</p>';
                }
            })
            .catch(error => {
                console.error('上传或处理过程中发生错误:', error);
                uploadStatus.innerHTML = '发生错误。';
                resultsArea.innerHTML = `<p class="error-message">错误: ${escapeHTML(error.message)}</p>`;
            });
        });
    } else {
        console.error('上传表单 (uploadForm) 未在 DOM 中找到。');
    }
});
