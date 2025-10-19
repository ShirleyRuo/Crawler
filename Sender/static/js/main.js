const CHUNK_SIZE = 2 * 1024 * 1024;
const MAX_PARALLEL = 4;
let currentUploads = new Map();

let currentDeleteFile = null;
let selectedFiles = [];

function deleteFile(filename) {
    currentDeleteFile = filename;
    document.getElementById('deleteFileName').textContent = filename;
    document.getElementById('deleteModal').style.display = 'flex';
    document.getElementById('deletePassword').value = '';
    document.getElementById('deleteMessage').innerHTML = '';
    // 聚焦到密码输入框
    document.getElementById('deletePassword').focus();
}

function closeDeleteModal() {
    document.getElementById('deleteModal').style.display = 'none';
    currentDeleteFile = null;
}

async function confirmDelete() {
    const password = document.getElementById('deletePassword').value;
    const messageDiv = document.getElementById('deleteMessage');
    
    if (!password) {
        messageDiv.innerHTML = '<div class="status error">⚠️ 请输入密码</div>';
        return;
    }

    // 显示验证中状态
    messageDiv.innerHTML = '<div class="status">🔄 验证中...</div>';

    try {
        // 先验证密码
        const verifyResponse = await fetch('/verify-password', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ password: password })
        });
        
        const verifyResult = await verifyResponse.json();
        
        if (verifyResult.success) {
            // 密码正确，执行删除
            const deleteResponse = await fetch(`/delete/${currentDeleteFile}`, { 
                method: 'DELETE' 
            });
            const deleteResult = await deleteResponse.json();
            
            if (deleteResult.success) {
                messageDiv.innerHTML = '<div class="status success">✅ 删除成功</div>';
                setTimeout(() => {
                    closeDeleteModal();
                    loadFiles(); // 刷新文件列表
                    showStatus(`✅ 文件删除成功: ${currentDeleteFile}`, 'success');
                }, 1000);
            } else {
                messageDiv.innerHTML = '<div class="status error">❌ 删除失败: ' + deleteResult.message + '</div>';
            }
        } else {
            messageDiv.innerHTML = '<div class="status error">❌ 密码错误</div>';
            // 清空密码输入框
            document.getElementById('deletePassword').value = '';
            document.getElementById('deletePassword').focus();
        }
    } catch (error) {
        messageDiv.innerHTML = '<div class="status error">❌ 请求失败: ' + error.message + '</div>';
    }
}

document.addEventListener('keydown', function(e) {
    // ESC键关闭模态框
    if (e.key === 'Escape' && document.getElementById('deleteModal').style.display === 'flex') {
        closeDeleteModal();
    }
    // Enter键确认删除
    if (e.key === 'Enter' && document.getElementById('deleteModal').style.display === 'flex') {
        confirmDelete();
    }
});

document.getElementById('deleteModal').addEventListener('click', function(e) {
    if (e.target === this) {
        closeDeleteModal();
    }
});

function getFileIcon(filename) {
    const extension = filename.split('.').pop().toLowerCase();
    
    const iconMap = {
        // 图片文件
        'jpg': '🖼️', 'jpeg': '🖼️', 'png': '🖼️', 'gif': '🖼️', 'bmp': '🖼️',
        'svg': '🖼️', 'webp': '🖼️', 'ico': '🖼️', 'tiff': '🖼️',
        
        // 文档文件
        'pdf': '📕',
        'doc': '📄', 'docx': '📄',
        'ppt': '📊', 'pptx': '📊',
        'xls': '📈', 'xlsx': '📈',
        'txt': '📝', 'rtf': '📝',
        
        // 代码文件
        'html': '🌐', 'htm': '🌐',
        'js': '📜', 'javascript': '📜',
        'css': '🎨',
        'py': '🐍', 'python': '🐍',
        'java': '☕',
        'cpp': '⚙️', 'c': '⚙️', 'h': '⚙️',
        'php': '🐘',
        'json': '🔧', 'xml': '🔧',
        'sql': '🗄️',
        
        // 压缩文件
        'zip': '📦', 'rar': '📦', '7z': '📦', 'tar': '📦', 'gz': '📦',
        
        // 音频文件
        'mp3': '🎵', 'wav': '🎵', 'flac': '🎵', 'aac': '🎵', 'ogg': '🎵',
        'm4a': '🎵', 'wma': '🎵',
        
        // 视频文件
        'mp4': '🎬', 'avi': '🎬', 'mkv': '🎬', 'mov': '🎬', 'wmv': '🎬',
        'flv': '🎬', 'webm': '🎬', 'm4v': '🎬',
        
        // 其他常见文件
        'exe': '⚙️', 'msi': '⚙️',
        'dll': '🔧',
        'ini': '⚙️', 'cfg': '⚙️', 'config': '⚙️',
        'bat': '🖥️', 'sh': '🖥️', 'ps1': '🖥️',
        
        // 默认图标
        'default': '📄'
    };
    
    return iconMap[extension] || iconMap['default'];
}

document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeModal();
    }
});

function switchTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
    document.getElementById(tabName).classList.add('active');
    event.target.classList.add('active');
    
    if (tabName === 'download') loadFiles();
}

document.getElementById('fileInput').addEventListener('change', handleFileSelect);

const dropArea = document.getElementById('dropArea');
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

['dragenter', 'dragover'].forEach(eventName => {
    dropArea.addEventListener(eventName, () => dropArea.style.background = '#e3f2fd', false);
});

['dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, () => dropArea.style.background = '#f8f9fa', false);
});

dropArea.addEventListener('drop', handleDrop, false);

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    handleFiles(files);
}

function handleFileSelect(e) {
    const files = e.target.files;
    handleFiles(files);
}

function handleFiles(files) {
    if (files.length === 0) return;
    
    selectedFiles = selectedFiles.concat(Array.from(files));
    
    showStatus(`已选择 ${files.length} 个文件，总共 ${selectedFiles.length} 个文件待上传`, 'success');
    
    displaySelectedFilesInStatus(selectedFiles);
}

function displaySelectedFilesInStatus(files) {
    const statusMessage = document.getElementById('statusMessage');
    const fileList = files.map((file, index) => {
        const icon = getFileIcon(file.name);
        return `
        <div style="font-size: 0.9em; margin: 5px 0; padding: 5px; background: #f5f5f5; border-radius: 4px; display: flex; justify-content: space-between; align-items: center;">
            <span>${icon} ${file.name} <span style="color: #666;">(${formatFileSize(file.size)})</span></span>
            <button onclick="removeFile(${index})" style="background: #ff6b6b; color: white; border: none; border-radius: 3px; padding: 2px 6px; font-size: 0.8em;">移除</button>
        </div>`
    }).join('');

    statusMessage.innerHTML = `
        <div style="margin: 10px 0;">
            <h4>已选择 ${files.length} 个文件：</h4>
            ${fileList}
            <div style="margin-top: 10px;">
                <button onclick="uploadFileOptimized()" class="success" style="margin-right: 10px;">🚀 开始上传</button>
                <button onclick="clearSelectedFiles()" class="danger">❌ 清空文件列表</button>
            </div>
        </div>
    `;
}

function removeFile(index) {
    if (index >= 0 && index < selectedFiles.length) {
        selectedFiles.splice(index, 1);
        displaySelectedFilesInStatus(selectedFiles);
        showStatus(`已移除文件，剩余 ${selectedFiles.length} 个文件`, 'info');
    }
}

function clearSelectedFiles() {
    selectedFiles = [];
    document.getElementById('fileInput').value = '';
    document.getElementById('statusMessage').innerHTML = '';
    showStatus('已清除所有选中的文件', 'info');
}

let uploadStartTime = null;
let uploadedBytes = 0;

async function uploadFileOptimized() {
    if (selectedFiles.length === 0) {
        showStatus('请先选择文件', 'error');
        return;
    }
    
    document.getElementById('statusMessage').innerHTML = '';
    
    showStatus(`开始上传 ${selectedFiles.length} 个文件...`, 'success');
    
    try {
        const filesToUpload = [...selectedFiles];
        
        selectedFiles = [];
        document.getElementById('fileInput').value = '';
        
        for (let file of filesToUpload) {
            await uploadFileWithChunks(file);
        }
        
        showStatus(`所有文件上传完成!`, 'success');
        
    } catch (error) {
        console.error('上传过程中出错:', error);
        showStatus(`上传失败: ${error.message}`, 'error');
    }
}

function clearUploads() {
    const progressArea = document.getElementById('progressArea');
    progressArea.innerHTML = '';
    showStatus('已清除上传进度', 'info');
}

async function uploadFileWithChunks(file) {
    const totalChunks = Math.ceil(file.size / CHUNK_SIZE);
    const fileId = generateFileId();
    
    currentUploads.set(fileId, {
        file: file,
        uploadedChunks: 0,
        totalChunks: totalChunks,
        startTime: Date.now(),
        lastUpdateTime: Date.now(),
        lastUploadedBytes: 0,
        uploadedBytes: 0
    });

    createProgressBar(fileId, file.name, totalChunks);

    const chunks = Array.from({length: totalChunks}, (_, i) => i);
    const parallelGroups = [];
    
    for (let i = 0; i < chunks.length; i += MAX_PARALLEL) {
        const chunkGroup = chunks.slice(i, i + MAX_PARALLEL);
        parallelGroups.push(chunkGroup);
    }
    
    for (let group of parallelGroups) {
        const promises = group.map(chunkIndex => 
            uploadChunk(file, chunkIndex, totalChunks, fileId)
        );
        
        try {
            await Promise.all(promises);
            updateProgress(fileId, group.length);
        } catch (error) {
            showStatus(`分块上传失败: ${error.message}`, 'error');
            return;
        }
    }
    
    try {
        await completeUpload(fileId, file.name);
        showStatus(`✅ 文件上传完成: ${file.name}`, 'success');
        currentUploads.delete(fileId);
    } catch (error) {
        showStatus(`❌ 文件合并失败: ${error.message}`, 'error');
    }
}

async function uploadChunk(file, chunkIndex, totalChunks, fileId) {
    const start = chunkIndex * CHUNK_SIZE;
    const end = Math.min(start + CHUNK_SIZE, file.size);
    const chunk = file.slice(start, end);
    
    const formData = new FormData();
    formData.append('chunk', chunk);
    formData.append('chunk_index', chunkIndex);
    formData.append('total_chunks', totalChunks);
    formData.append('file_id', fileId);
    formData.append('file_name', file.name);
    
    try {
        const response = await fetch('/upload_chunk', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const result = await response.json();
        
        // 更新已上传字节数
        const uploadInfo = currentUploads.get(fileId);
        if (uploadInfo) {
            uploadInfo.uploadedBytes += chunk.size;
        }
        
        return result;
    } catch (error) {
        console.error(`分块 ${chunkIndex} 上传失败:`, error);
        throw error;
    }
}

async function completeUpload(fileId, fileName) {
    const response = await fetch('/complete_upload', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            file_id: fileId,
            file_name: fileName
        })
    });
    
    if (!response.ok) {
        throw new Error('合并文件失败');
    }
    
    return await response.json();
}

function createProgressBar(fileId, fileName, totalChunks) {
    const progressArea = document.getElementById('progressArea');
    const progressItem = document.createElement('div');
    progressItem.className = 'progress-item';
    progressItem.id = `progress-${fileId}`;
    progressItem.innerHTML = `
        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
            <div>
                <strong>${fileName}</strong>
                <div style="font-size: 0.9em; color: #666;">
                    大小: ${formatFileSize(currentUploads.get(fileId).file.size)} | 
                    速度: <span id="speed-${fileId}">计算中...</span>
                </div>
            </div>
            <div>
                <span id="progress-percent-${fileId}" style="font-weight: bold;">0%</span>
            </div>
        </div>
        <div class="progress-bar">
            <div id="progress-fill-${fileId}" class="progress-fill" style="width: 0%"></div>
        </div>
        <div style="font-size: 0.8em; color: #666; margin-top: 5px;">
            剩余时间: <span id="eta-${fileId}">计算中...</span>
        </div>
    `;
    progressArea.appendChild(progressItem);
}

function updateProgress(fileId, chunksUploaded) {
    const uploadInfo = currentUploads.get(fileId);
    if (!uploadInfo) return;
    
    uploadInfo.uploadedChunks += chunksUploaded;
    const percent = (uploadInfo.uploadedChunks / uploadInfo.totalChunks) * 100;
    
    // 计算上传速度
    const now = Date.now();
    const timeElapsed = (now - uploadInfo.startTime) / 1000; // 转换为秒
    const currentSpeed = uploadInfo.uploadedBytes / timeElapsed; // 字节/秒
    
    // 计算剩余时间
    const remainingBytes = uploadInfo.file.size - uploadInfo.uploadedBytes;
    const eta = currentSpeed > 0 ? remainingBytes / currentSpeed : 0;
    
    // 更新进度条
    const progressFill = document.getElementById(`progress-fill-${fileId}`);
    const progressPercent = document.getElementById(`progress-percent-${fileId}`);
    const speedElement = document.getElementById(`speed-${fileId}`);
    //const uploadedElement = document.getElementById(`uploaded-${fileId}`);
    const etaElement = document.getElementById(`eta-${fileId}`);
    
    if (progressFill) {
        progressFill.style.width = percent + '%';
        progressPercent.textContent = Math.round(percent) + '%';
        speedElement.textContent = formatSpeed(currentSpeed);
        //uploadedElement.textContent = formatFileSize(uploadInfo.uploadedBytes);
        etaElement.textContent = formatTime(eta);
    }
}

function formatSpeed(bytesPerSecond) {
    if (bytesPerSecond >= 1024 * 1024) {
        return (bytesPerSecond / (1024 * 1024)).toFixed(2) + ' MB/s';
    } else if (bytesPerSecond >= 1024) {
        return (bytesPerSecond / 1024).toFixed(2) + ' KB/s';
    } else {
        return bytesPerSecond.toFixed(0) + ' B/s';
    }
}
function formatTime(seconds) {
    if (seconds < 60) {
        return Math.ceil(seconds) + '秒';
    } else if (seconds < 3600) {
        const minutes = Math.floor(seconds / 60);
        const secs = Math.ceil(seconds % 60);
        return `${minutes}分${secs}秒`;
    } else {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        return `${hours}时${minutes}分`;
    }
}

function generateFileId() {
    return 'file_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function showStatus(message, type) {
    const statusDiv = document.getElementById('statusMessage');
    statusDiv.innerHTML = `<div class="status ${type}">${message}</div>`;
    setTimeout(() => {
        if (statusDiv.innerHTML.includes(message)) {
            statusDiv.innerHTML = '';
        }
    }, 5000);
}

function clearUploads() {
    document.getElementById('progressArea').innerHTML = '';
    document.getElementById('fileInput').value = '';
    showStatus('已清空上传进度', 'success');
}

function loadFiles() {
    fetch('/files')
        .then(response => response.json())
        .then(data => {
            const fileList = document.getElementById('fileList');
            fileList.innerHTML = '';
            
            if (data.files.length === 0) {
                fileList.innerHTML = '<div class="status">暂无文件</div>';
                return;
            }
            
            data.files.forEach(fileInfo => {
                const fileItem = document.createElement('div');
                const icon = getFileIcon(fileInfo.name);
                fileItem.className = 'file-item';
                fileItem.innerHTML = `
                    <div class="file-item">
                        <div class="file-header">
                            <strong class="file-name" title="${fileInfo.name}">${icon} ${fileInfo.name}</strong>
                            <div class="file-meta">
                                <span class="file-size">${formatFileSize(fileInfo.size)}</span>
                                <span class="file-date">${new Date(fileInfo.modified * 1000).toLocaleString()}</span>
                            </div>
                        </div>
                        <div class="file-actions">
                            <button class="btn-download" onclick="downloadFile('${fileInfo.name}')">
                                <span class="btn-icon">⬇️</span> 下载
                            </button>
                            <button class="btn-delete" onclick="deleteFile('${fileInfo.name}')">
                                <span class="btn-icon">🗑️</span> 删除
                            </button>
                        </div>
                    </div>

                    <style>
                    .file-item {
                        display: flex;
                        flex-direction: column;
                        gap: 12px;
                        padding: 16px;
                        background: #ffffff;
                        border-radius: 8px;
                        margin-bottom: 12px;
                        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
                        transition: all 0.2s ease;
                        border: 1px solid #f0f0f0;
                        max-width: 100%;
                        box-sizing: border-box;
                    }

                    .file-item:hover {
                        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.08);
                        transform: translateY(-1px);
                    }

                    .file-header {
                        width: 100%;
                        min-width: 0; /* 关键：允许容器收缩 */
                    }

                    .file-name {
                        display: block;
                        white-space: nowrap;
                        overflow: hidden;
                        text-overflow: ellipsis;
                        margin-bottom: 6px;
                        font-size: 1rem;
                        color: #333;
                        width: 100%;
                    }

                    .file-meta {
                        display: flex;
                        gap: 12px;
                        color: #666;
                        font-size: 0.85rem;
                        flex-wrap: wrap;
                    }

                    .file-size, .file-date {
                        display: flex;
                        align-items: center;
                        white-space: nowrap;
                    }

                    .file-size::before {
                        content: "📄";
                        margin-right: 4px;
                    }

                    .file-date::before {
                        content: "🕒";
                        margin-right: 4px;
                    }

                    .file-actions {
                        display: flex;
                        gap: 10px;
                        width: 100%;
                    }

                    .btn-download, .btn-delete {
                        flex: 1;
                        padding: 10px 12px;
                        border: none;
                        border-radius: 6px;
                        cursor: pointer;
                        font-size: 0.9rem;
                        min-width: 0;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        gap: 6px;
                        transition: all 0.2s ease;
                    }

                    .btn-download {
                        background: #f0f7ff;
                        color: #007bff;
                        border: 1px solid #d0e3ff;
                    }

                    .btn-delete {
                        background: #fff5f5;
                        color: #dc3545;
                        border: 1px solid #ffd0d7;
                    }

                    .btn-download:hover {
                        background: #007bff;
                        color: white;
                        transform: translateY(-1px);
                        box-shadow: 0 2px 4px rgba(0, 123, 255, 0.2);
                    }

                    .btn-delete:hover {
                        background: #dc3545;
                        color: white;
                        transform: translateY(-1px);
                        box-shadow: 0 2px 4px rgba(220, 53, 69, 0.2);
                    }

                    .btn-icon {
                        font-size: 0.9rem;
                    }

                    /* 响应式设计 */
                    @media (max-width: 480px) {
                        .file-meta {
                            flex-direction: column;
                            gap: 4px;
                        }
                        
                        .file-actions {
                            flex-direction: column;
                        }
                    }

                    /* 确保文件列表容器有适当的宽度限制 */
                    .file-list-container {
                        max-width: 600px; /* 或者根据你的布局调整 */
                        margin: 0 auto;
                    }
                `;
                fileList.appendChild(fileItem);
            });
        })
        .catch(error => {
            document.getElementById('fileList').innerHTML = '<div class="status error">加载失败</div>';
        });
}

function downloadFile(filename) {
    window.open(`/download/${filename}`, '_blank');
    showStatus(`开始下载: ${filename}`, 'success');
}

async function testSpeed() {
    const speedResult = document.getElementById('speedResult');
    speedResult.innerHTML = '🔄 测试中...';
    
    // 生成测试数据 (5MB)
    const testData = new Array(5 * 1024 * 1024).fill(0).map(() => 
        String.fromCharCode(Math.floor(Math.random() * 256))
    ).join('');
    
    const startTime = performance.now();
    
    try {
        const response = await fetch('/speed_test', {
            method: 'POST',
            body: testData,
            headers: {
                'Content-Type': 'application/octet-stream'
            }
        });
        
        const endTime = performance.now();
        const duration = (endTime - startTime) / 1000; // 秒
        const speedMbps = (testData.length * 8 / duration / 1000000).toFixed(2);
        const speedMBs = (testData.length / duration / 1024 / 1024).toFixed(2);
        
        speedResult.innerHTML = `
            <div style="color: #27ae60;">
                ✅ 测试完成<br>
                📊 上传速度: ${speedMbps} Mbps (${speedMBs} MB/s)<br>
                ⏱️ 耗时: ${duration.toFixed(2)} 秒
            </div>
        `;
        
    } catch (error) {
        speedResult.innerHTML = '<div style="color: #e74c3c;">❌ 测试失败</div>';
    }
}

async function checkTestFile() {
    const fileStatus = document.getElementById('fileStatus');
    const fileDetails = document.getElementById('fileDetails');
    const downloadTestBtn = document.getElementById('downloadTestBtn');
    try {
        const response = await fetch('/check_test_file');
        const data = await response.json();
        
        if (data.exists) {
            fileStatus.innerHTML = '<span style="color: #27ae60;">✅ 测试文件就绪</span>';
            fileDetails.innerHTML = `文件: ${data.filename} | 大小: ${data.size_formatted}`;
            downloadTestBtn.disabled = false;
            downloadTestBtn.textContent = '开始下载速度测试';
        } else {
            fileStatus.innerHTML = '<span style="color: #e74c3c;">❌ ' + data.message + '</span>';
            fileDetails.innerHTML = '请上传一个约20MB的文件作为测试文件，文件名: speed_test_file_20m.bin';
            downloadTestBtn.disabled = true;
            downloadTestBtn.textContent = '测试文件未就绪';
        }
    } catch (error) {
        fileStatus.innerHTML = '<span style="color: #e74c3c;">❌ 检查测试文件失败</span>';
        fileDetails.innerHTML = '无法连接到服务器';
        downloadTestBtn.disabled = true;
    }
}

async function testDownloadSpeed() {
    const downloadSpeedResult = document.getElementById('downloadSpeedResult');
    const downloadTestBtn = document.getElementById('downloadTestBtn');
    
    downloadSpeedResult.innerHTML = '🔄 下载测试中...';
    downloadTestBtn.disabled = true;
    downloadTestBtn.textContent = '测试进行中...';
    
    try {
        // 首先获取文件信息以知道文件大小
        const checkResponse = await fetch('/check_test_file');
        const fileInfo = await checkResponse.json();
        
        if (!fileInfo.exists) {
            throw new Error('测试文件不存在');
        }
        
        const fileSize = fileInfo.size;
        const startTime = performance.now();
        
        // 开始下载测试
        const response = await fetch('/download_test?' + new Date().getTime()); // 添加时间戳避免缓存
        
        if (!response.ok) {
            throw new Error(`下载失败: ${response.status} ${response.statusText}`);
        }
        
        // 读取响应数据（我们不需要实际保存，只需要计算下载时间）
        const blob = await response.blob();
        const endTime = performance.now();
        
        const duration = (endTime - startTime) / 1000; // 转换为秒
        const speedMbps = (fileSize * 8 / duration / 1000000).toFixed(2);
        const speedMBs = (fileSize / duration / 1024 / 1024).toFixed(2);
        
        downloadSpeedResult.innerHTML = `
            <div style="color: #27ae60;">
                ✅ 下载测试完成<br>
                📊 下载速度: ${speedMbps} Mbps (${speedMBs} MB/s)<br>
                ⏱️ 耗时: ${duration.toFixed(2)} 秒<br>
                📁 文件大小: ${fileInfo.size_formatted}
            </div>
        `;
        
    } catch (error) {
        downloadSpeedResult.innerHTML = `
            <div style="color: #e74c3c;">
                ❌ 下载测试失败<br>
                错误: ${error.message}
            </div>
        `;
    } finally {
        downloadTestBtn.disabled = false;
        downloadTestBtn.textContent = '开始下载速度测试';
    }
}

async function testUploadSpeed() {
    const uploadSpeedResult = document.getElementById('uploadSpeedResult');
    uploadSpeedResult.innerHTML = '🔄 测试中...';
    
    // 生成测试数据 (5MB)
    const testData = new Array(5 * 1024 * 1024).fill(0).map(() => 
        String.fromCharCode(Math.floor(Math.random() * 256))
    ).join('');
    
    const startTime = performance.now();
    
    try {
        const response = await fetch('/speed_test', {
            method: 'POST',
            body: testData,
            headers: {
                'Content-Type': 'application/octet-stream'
            }
        });
        
        const endTime = performance.now();
        const duration = (endTime - startTime) / 1000; // 秒
        const speedMbps = (testData.length * 8 / duration / 1000000).toFixed(2);
        const speedMBs = (testData.length / duration / 1024 / 1024).toFixed(2);
        
        uploadSpeedResult.innerHTML = `
            <div style="color: #27ae60;">
                ✅ 测试完成<br>
                📊 上传速度: ${speedMbps} Mbps (${speedMBs} MB/s)<br>
                ⏱️ 耗时: ${duration.toFixed(2)} 秒
            </div>
        `;
        
    } catch (error) {
        uploadSpeedResult.innerHTML = '<div style="color: #e74c3c;">❌ 测试失败</div>';
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        loadFiles();
        checkTestFile();

        setInterval(checkTestFile, 30000);
    });
} else {
    loadFiles();
    checkTestFile();
    setInterval(checkTestFile, 30000);
}