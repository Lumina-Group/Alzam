import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import asyncio
import os
import sys
import threading
import logging
from pathlib import Path

# 必要なライブラリをインポート
try:
    import aiofiles
    from AQE.transport import SecureTransport
    from AQE.configuration import ConfigurationManager
    # encryption_utils からの関数インポート
    from encryption_utils import encrypt_file, decrypt_file, ConfigurationManagerWithKey
except ImportError as e:
    print(f"Error: Required library not found: {e}", file=sys.stderr)
    print("Please ensure all required libraries are correctly installed.", file=sys.stderr)
    sys.exit(1)

# ロギング設定
def setup_logging(config_file="config.ini"):
    log_level_str = "INFO"  # デフォルト
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                for line in f:
                    if line.strip().lower().startswith("log_level"):
                        level = line.split('=')[1].strip().upper()
                        if level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
                            log_level_str = level
                        break
        except Exception:
            pass  # エラー時はデフォルトを使用
    
    log_level = getattr(logging, log_level_str, logging.INFO)
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

# モダンなスタイルを設定するクラス
class ModernStyle:
    def __init__(self, root):
        self.style = ttk.Style()
        
        # カラーパレット
        self.bg_color = "#2E3440"  # ダークブルーグレー
        self.fg_color = "#ECEFF4"  # ライトグレー
        self.accent_color = "#88C0D0"  # ライトブルー
        self.button_bg = "#5E81AC"  # ブルー
        self.button_fg = "#ECEFF4"  # ライトグレー
        self.input_bg = "#3B4252"  # ダークグレー
        self.input_fg = "#E5E9F0"  # ライトグレー
        self.error_color = "#BF616A"  # レッド
        self.success_color = "#A3BE8C"  # グリーン
        
        # ルートウィンドウの設定
        root.configure(bg=self.bg_color)
        
        # スタイルの設定
        self.style.configure("TFrame", background=self.bg_color)
        self.style.configure("TLabel", background=self.bg_color, foreground=self.fg_color, font=("Helvetica", 10))
        self.style.configure("TButton", 
                          background=self.button_bg, 
                          foreground=self.button_fg, 
                          font=("Helvetica", 10, "bold"),
                          padding=10,
                          relief="flat")
        self.style.map("TButton",
                    background=[('active', self.accent_color)],
                    foreground=[('active', self.button_fg)])
        
        self.style.configure("Header.TLabel", 
                          font=("Helvetica", 16, "bold"), 
                          background=self.bg_color, 
                          foreground=self.accent_color)
        
        self.style.configure("Status.TLabel", 
                          font=("Helvetica", 9), 
                          background=self.bg_color)
        
        self.style.configure("Success.Status.TLabel", 
                          foreground=self.success_color)
        
        self.style.configure("Error.Status.TLabel", 
                          foreground=self.error_color)
        
        # コンボボックスと入力フィールドのスタイル
        self.style.map('TCombobox', 
                    fieldbackground=[('readonly', self.input_bg)],
                    selectbackground=[('readonly', self.button_bg)],
                    selectforeground=[('readonly', self.button_fg)])
        
        # プログレスバーのスタイル
        self.style.configure("TProgressbar", 
                          background=self.accent_color, 
                          troughcolor=self.input_bg,
                          borderwidth=0,
                          thickness=10)

# メインアプリケーションクラス
class CryptoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AQE 暗号化ツール")
        self.root.geometry("650x550")
        self.root.resizable(True, True)
        
        # モダンなスタイルを適用
        self.style = ModernStyle(root)
        
        # メインフレーム
        self.main_frame = ttk.Frame(root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # ヘッダー
        header_label = ttk.Label(self.main_frame, text="AQE 暗号化/復号化ツール", style="Header.TLabel")
        header_label.pack(pady=(0, 20))
        
        # 操作モード選択
        mode_frame = ttk.Frame(self.main_frame)
        mode_frame.pack(fill=tk.X, pady=10)
        
        mode_label = ttk.Label(mode_frame, text="操作モード:")
        mode_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.mode_var = tk.StringVar(value="encrypt")
        mode_encrypt = ttk.Radiobutton(mode_frame, text="暗号化", variable=self.mode_var, value="encrypt")
        mode_encrypt.pack(side=tk.LEFT, padx=10)
        
        mode_decrypt = ttk.Radiobutton(mode_frame, text="復号化", variable=self.mode_var, value="decrypt")
        mode_decrypt.pack(side=tk.LEFT, padx=10)
        
        # ファイル選択フレーム - 入力ファイル
        input_frame = ttk.Frame(self.main_frame)
        input_frame.pack(fill=tk.X, pady=10)
        
        input_label = ttk.Label(input_frame, text="入力ファイル:")
        input_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.input_var = tk.StringVar()
        input_entry = ttk.Entry(input_frame, textvariable=self.input_var, width=40)
        input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        input_button = ttk.Button(input_frame, text="参照...", command=self.browse_input)
        input_button.pack(side=tk.LEFT)
        
        # ファイル選択フレーム - 出力ファイル
        output_frame = ttk.Frame(self.main_frame)
        output_frame.pack(fill=tk.X, pady=10)
        
        output_label = ttk.Label(output_frame, text="出力ファイル:")
        output_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.output_var = tk.StringVar()
        output_entry = ttk.Entry(output_frame, textvariable=self.output_var, width=40)
        output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        output_button = ttk.Button(output_frame, text="参照...", command=self.browse_output)
        output_button.pack(side=tk.LEFT)
        
        # 設定ファイル選択
        config_frame = ttk.Frame(self.main_frame)
        config_frame.pack(fill=tk.X, pady=10)
        
        config_label = ttk.Label(config_frame, text="設定ファイル:")
        config_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.config_var = tk.StringVar(value="config.ini")
        config_entry = ttk.Entry(config_frame, textvariable=self.config_var, width=40)
        config_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        config_button = ttk.Button(config_frame, text="参照...", command=self.browse_config)
        config_button.pack(side=tk.LEFT)
        
        # 詳細オプションを表示するためのフレーム（折りたたみ可能）
        self.show_details = tk.BooleanVar(value=False)
        details_check = ttk.Checkbutton(self.main_frame, text="詳細設定を表示", variable=self.show_details, 
                                      command=self.toggle_details)
        details_check.pack(anchor=tk.W, pady=10)
        
        # 詳細設定フレーム（初期状態では非表示）
        self.details_frame = ttk.Frame(self.main_frame)
        
        # ログレベル設定
        log_frame = ttk.Frame(self.details_frame)
        log_frame.pack(fill=tk.X, pady=5)
        
        log_label = ttk.Label(log_frame, text="ログレベル:")
        log_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.log_level_var = tk.StringVar(value="INFO")
        log_combo = ttk.Combobox(log_frame, textvariable=self.log_level_var, 
                               values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                               state="readonly", width=15)
        log_combo.pack(side=tk.LEFT)
        
        # 進行状況表示用のプログレスバー
        progress_frame = ttk.Frame(self.main_frame)
        progress_frame.pack(fill=tk.X, pady=10)
        
        self.progress = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, length=100, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=5)
        
        # ステータスメッセージ表示用のラベル
        self.status_var = tk.StringVar(value="準備完了")
        self.status_label = ttk.Label(progress_frame, textvariable=self.status_var, style="Status.TLabel")
        self.status_label.pack(anchor=tk.W, pady=5)
        
        # ログメッセージを表示するテキストウィジェット
        log_label = ttk.Label(self.main_frame, text="ログメッセージ:")
        log_label.pack(anchor=tk.W, pady=(10, 5))
        
        log_frame = ttk.Frame(self.main_frame)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = tk.Text(log_frame, height=8, bg=self.style.input_bg, fg=self.style.input_fg,
                              wrap=tk.WORD, font=("Consolas", 9))
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # 実行ボタン
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(fill=tk.X, pady=20)
        
        cancel_button = ttk.Button(button_frame, text="キャンセル", command=self.cancel_operation)
        cancel_button.pack(side=tk.LEFT, padx=(0, 10))
        
        execute_button = ttk.Button(button_frame, text="実行", command=self.execute_operation)
        execute_button.pack(side=tk.RIGHT)
        
        # カスタムロギングハンドラー
        self.log_handler = LogTextHandler(self.log_text)
        self.log_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self.log_handler.setFormatter(formatter)
        logger.addHandler(self.log_handler)
        
        # タスク管理用の変数
        self.current_task = None
        
        # 初期設定の読み込み
        self.load_initial_config()
    
    def toggle_details(self):
        if self.show_details.get():
            self.details_frame.pack(fill=tk.X, pady=10, after=self.main_frame.children.get('!checkbutton', None))
        else:
            self.details_frame.pack_forget()
    
    def load_initial_config(self):
        # config.ini があれば読み込み
        config_path = "config.ini"
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    for line in f:
                        if line.strip().lower().startswith("log_level"):
                            level = line.split('=')[1].strip().upper()
                            if level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
                                self.log_level_var.set(level)
                                break
            except Exception as e:
                logger.warning(f"設定ファイルの読み込みに失敗しました: {e}")
    
    def browse_input(self):
        file_path = filedialog.askopenfilename(title="入力ファイルを選択")
        if file_path:
            self.input_var.set(file_path)
            # 出力ファイル名を自動設定
            if not self.output_var.get():
                output_path = ""
                if self.mode_var.get() == "encrypt":
                    output_path = f"{file_path}.encrypted"
                else:
                    output_path = os.path.splitext(file_path)[0] + ".decrypted"
                self.output_var.set(output_path)
    
    def browse_output(self):
        file_path = filedialog.asksaveasfilename(title="出力ファイルを選択")
        if file_path:
            self.output_var.set(file_path)
    
    def browse_config(self):
        file_path = filedialog.askopenfilename(title="設定ファイルを選択", 
                                            filetypes=[("INI files", "*.ini"), ("All files", "*.*")])
        if file_path:
            self.config_var.set(file_path)
    
    def update_status(self, message, is_error=False):
        self.status_var.set(message)
        style = "Error.Status.TLabel" if is_error else "Status.TLabel"
        self.status_label.configure(style=style)
        logger.info(message) if not is_error else logger.error(message)
    
    def cancel_operation(self):
        if self.current_task and self.current_task.is_alive():
            # 現在のタスクをキャンセルする
            # Note: 実際のキャンセル処理は実装次第
            self.update_status("処理をキャンセルしています...")
        else:
            self.root.destroy()
    
    def validate_inputs(self):
        input_path = self.input_var.get()
        output_path = self.output_var.get()
        config_path = self.config_var.get()
        
        if not input_path:
            self.update_status("入力ファイルを指定してください", True)
            return False
        
        if not os.path.exists(input_path):
            self.update_status(f"入力ファイルが見つかりません: {input_path}", True)
            return False
        
        if not output_path:
            self.update_status("出力ファイルを指定してください", True)
            return False
        
        if os.path.abspath(input_path) == os.path.abspath(output_path):
            self.update_status("入力と出力のファイルパスが同じです", True)
            return False
        
        if os.path.exists(output_path):
            result = messagebox.askokcancel("警告", f"出力ファイル {output_path} は既に存在します。上書きしますか？")
            if not result:
                return False
        
        if config_path and not os.path.exists(config_path):
            result = messagebox.askokcancel("警告", 
                                          f"設定ファイル {config_path} が見つかりません。デフォルト設定で続行しますか？")
            if not result:
                return False
        
        return True
    
    def execute_operation(self):
        if not self.validate_inputs():
            return
        
        # UI要素を無効化
        for widget in self.main_frame.winfo_children():
            if isinstance(widget, (ttk.Button, ttk.Entry, ttk.Radiobutton, ttk.Checkbutton, ttk.Combobox)):
                widget.configure(state="disabled")
        
        # プログレスバーの開始
        self.progress.start()
        
        mode = self.mode_var.get()
        input_path = self.input_var.get()
        output_path = self.output_var.get()
        config_path = self.config_var.get()
        
        # ログレベルの設定
        log_level = getattr(logging, self.log_level_var.get(), logging.INFO)
        logger.setLevel(log_level)
        self.log_handler.setLevel(log_level)
        
        self.update_status(f"{'暗号化' if mode == 'encrypt' else '復号化'}を開始しています...")
        
        # スレッドで実行
        self.current_task = threading.Thread(
            target=self.process_file,
            args=(mode, input_path, output_path, config_path)
        )
        self.current_task.daemon = True
        self.current_task.start()
    
    def process_file(self, mode, input_path, output_path, config_path):
        try:
            # asyncio イベントループの作成と実行
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = False
            if mode == "encrypt":
                result = loop.run_until_complete(encrypt_file(input_path, output_path, config_path))
            else:
                result = loop.run_until_complete(decrypt_file(input_path, output_path, config_path))
            
            # UI更新は別のスレッドで行う必要がある
            self.root.after(0, self.complete_operation, result)
            
        except Exception as e:
            self.root.after(0, self.complete_operation, False, str(e))
    
    def complete_operation(self, success, error_message=None):
        # プログレスバーの停止
        self.progress.stop()
        
        # UI要素を有効化
        for widget in self.main_frame.winfo_children():
            if isinstance(widget, (ttk.Button, ttk.Entry, ttk.Radiobutton, ttk.Checkbutton, ttk.Combobox)):
                widget.configure(state="normal")
        
        if success:
            self.update_status("処理が正常に完了しました。", False)
            messagebox.showinfo("成功", "ファイル処理が正常に完了しました。")
        else:
            error_msg = error_message if error_message else "処理中にエラーが発生しました。"
            self.update_status(error_msg, True)
            messagebox.showerror("エラー", error_msg)

# カスタムログハンドラークラス - Tkinterのテキストウィジェットにログを出力
class LogTextHandler(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget
    
    def emit(self, record):
        msg = self.format(record)
        
        def append():
            self.text_widget.configure(state="normal")
            self.text_widget.insert(tk.END, msg + "\n")
            self.text_widget.see(tk.END)  # 自動スクロール
            self.text_widget.configure(state="disabled")
        
        # GUIスレッドで実行
        self.text_widget.after(0, append)

# メイン関数
def main():
    root = tk.Tk()
    app = CryptoApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()