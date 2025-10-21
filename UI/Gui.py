import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.Crawler import JabVideoCrawler
from src.DataUnit import DownloadPackage
from src.Downloader import Downloader

class DownloadManager:
    def __init__(self):
        self.tasks = []
    
    def add_task(self, identifier : str, url=None):
        """添加任务逻辑"""
        if identifier and not url:
            url = f"https://jable.tv/videos/{identifier.lower()}/"
        crawler = JabVideoCrawler(url)
        package : DownloadPackage = crawler.parse()
        task = {
            'id' : package.id,
            'url' : package.hls_url,
            'status' : package.status,
            'progress' : 0,
            'speed' : '0KB/s',
        }
        downloader = Downloader(package)
        downloader.download()
        
        self.tasks.append(task)
        return task

class DownloadGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("视频下载管理器")
        self.geometry("800x600")
        
        # 初始化组件
        self.download_manager = DownloadManager()
        self.create_widgets()
        self.setup_style()
    
    def setup_style(self):
        style = ttk.Style()
        style.configure("TButton", padding=5)
        style.configure("Treeview", rowheight=25)
    
    def create_widgets(self):
        # 顶部操作面板
        control_frame = ttk.Frame(self)
        control_frame.pack(pady=10, fill=tk.X)
        
        # URL/ID输入区
        input_frame = ttk.LabelFrame(control_frame, text="快速添加任务")
        input_frame.pack(side=tk.LEFT, padx=5)
        
        self.url_entry = ttk.Entry(input_frame, width=40)
        self.url_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(input_frame, text="直接下载", command=self.add_direct_task).pack(side=tk.LEFT)
        
        # 搜索区
        search_frame = ttk.LabelFrame(control_frame, text="影片搜索")
        search_frame.pack(side=tk.LEFT, padx=5)
        
        self.search_entry = ttk.Entry(search_frame, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="搜索", command=self.search_videos).pack(side=tk.LEFT)
        
        # 下载队列
        queue_frame = ttk.LabelFrame(self, text="下载队列")
        queue_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        columns = ('id', 'url', 'status', 'progress', 'speed')
        self.queue_tree = ttk.Treeview(queue_frame, columns=columns, show='headings')
        
        # 配置列
        headers = {
            'id': ('ID', 100),
            'url': ('URL', 300),
            'status': ('状态', 80),
            'progress': ('进度', 80),
            'speed': ('速度', 100)
        }
        
        for col, (text, width) in headers.items():
            self.queue_tree.heading(col, text=text)
            self.queue_tree.column(col, width=width)
        
        self.queue_tree.pack(fill=tk.BOTH, expand=True)
        
        # 进度条
        self.progress = ttk.Progressbar(self, orient=tk.HORIZONTAL, mode='determinate')
        self.progress.pack(fill=tk.X, padx=10, pady=5)
    
    def add_direct_task(self):
        """直接添加任务"""
        identifier = self.url_entry.get().strip()
        if not identifier:
            messagebox.showwarning("警告", "请输入有效的URL或ID")
            return
        
        try:
            task = self.download_manager.add_task(identifier)
            self.update_queue()
            messagebox.showinfo("成功", f"已添加任务: {task['id']}")
        except Exception as e:
            messagebox.showerror("错误", f"添加任务失败: {str(e)}")
    
    def search_videos(self):
        """执行搜索操作"""
        keyword = self.search_entry.get().strip()
        if not keyword:
            messagebox.showwarning("警告", "请输入搜索关键词")
            return
        
        # 模拟搜索逻辑
        search_results = [
            {'id': 'SDDE-123', 'title': '示例视频1', 'url': 'https://example.com/sdde123'},
            {'id': 'ABP-456', 'title': '示例视频2', 'url': 'https://example.com/abp456'}
        ]
        
        if not search_results:
            messagebox.showinfo("提示", "没有找到相关影片")
            return
        
        self.show_search_results(search_results)
    
    def show_search_results(self, results):
        """显示搜索结果窗口（修复版）"""
        result_window = tk.Toplevel(self)
        result_window.title("搜索结果")
        
        # 配置Treeview列（添加高度和边框）
        tree = ttk.Treeview(
            result_window, 
            columns=('id', 'title', 'action'), 
            show='headings',
            height=8  # 设置可见行数
        )
        
        # 显式配置列标题（增加字体大小）
        style = ttk.Style()
        style.configure("Treeview.Heading", font=('微软雅黑', 10, 'bold'))
        
        tree.heading('id', text='ID', anchor=tk.W)
        tree.heading('title', text='标题', anchor=tk.W)
        tree.heading('action', text='操作', anchor=tk.CENTER)
        
        # 调整列宽（重点加大操作列宽度）
        tree.column('id', width=120, anchor=tk.W, stretch=False)
        tree.column('title', width=300, anchor=tk.W)
        tree.column('action', width=100, anchor=tk.CENTER, stretch=False)
        
        # 添加垂直滚动条
        vsb = ttk.Scrollbar(result_window, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        
        # 使用grid布局确保组件自适应
        tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        
        # 配置窗口缩放比例
        result_window.grid_rowconfigure(0, weight=1)
        result_window.grid_columnconfigure(0, weight=1)
        

        # 插入数据时添加特殊标签
        for result in results:
            item = tree.insert('', 'end', 
                            values=(result['id'], result['title'], "下载"),
                            tags=("downloadable",))
        
        # 配置标签样式和事件
        tree.tag_configure("downloadable", foreground="blue", font=('微软雅黑', 9, 'underline'))
        tree.bind("<Button-1>", lambda e: self.on_tree_click(e, tree))
            
        # 绑定窗口关闭事件
        result_window.protocol("WM_DELETE_WINDOW", lambda: self.on_result_close(result_window))

    def on_tree_click(self, event, tree):
        item = tree.identify_row(event.y)
        column = tree.identify_column(event.x)
        
        if item and column == "#3":  # 假设操作列是第三列
            values = tree.item(item, "values")
            result = {'id': values[0], 'title': values[1]}
            self.add_search_task(result)


    def on_result_close(self, window):
        """处理搜索结果窗口关闭"""
        window.destroy()

    
    def add_search_task(self, result):
        """添加搜索到的任务"""
        try:
            task = self.download_manager.add_task(result['id'], result['url'])
            self.update_queue()
            messagebox.showinfo("成功", f"已添加任务: {task['id']}")
        except Exception as e:
            messagebox.showerror("错误", f"添加失败: {str(e)}")
    
    def update_queue(self):
        """更新下载队列显示"""
        self.queue_tree.delete(*self.queue_tree.get_children())
        
        for task in self.download_manager.tasks:
            self.queue_tree.insert('', 'end', values=(
                task['id'],
                task['url'],
                task['status'],
                f"{task['progress']}%",
                task['speed']
            ))

if __name__ == "__main__":
    a = 'https://jable.tv/videos/jufe-589/'
    app = DownloadGUI()
    app.mainloop()