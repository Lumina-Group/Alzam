import sys
import os
import asyncio
import logging
import configparser
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from tkinter.font import Font
import threading

# Setup logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
from encryption_utils import encrypt_file, decrypt_file

class ScrollableFrame(ttk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

class ConfigSection:
    def __init__(self, parent, section_name, options):
        self.frame = ttk.LabelFrame(parent, text=section_name)
        self.section_name = section_name
        self.options = options
        self.entries = {}
        
        for i, (option, value) in enumerate(options.items()):
            ttk.Label(self.frame, text=option).grid(row=i, column=0, sticky="w", padx=5, pady=2)
            entry = ttk.Entry(self.frame, width=30)
            entry.insert(0, value)
            entry.grid(row=i, column=1, padx=5, pady=2)
            self.entries[option] = entry
    
    def get_values(self):
        return {option: entry.get() for option, entry in self.entries.items()}

class CryptoGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Secure File Encryption/Decryption")
        self.root.geometry("900x650")
        
        # Set theme
        style = ttk.Style()
        if 'clam' in style.theme_names():
            style.theme_use('clam')
        
        # Create main notebook
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.file_frame = ttk.Frame(self.notebook)
        self.config_frame = ttk.Frame(self.notebook)
        self.log_frame = ttk.Frame(self.notebook)
        
        self.notebook.add(self.file_frame, text="Encryption/Decryption")
        self.notebook.add(self.config_frame, text="Configuration")
        self.notebook.add(self.log_frame, text="Logs")
        
        self.setup_file_tab()
        self.setup_config_tab()
        self.setup_log_tab()
        
        # Configuration file path
        self.config_file = "config.ini"
        self.load_config()
        
        # Log handler to redirect logs to GUI
        self.log_handler = LogHandler(self.log_text)
        logger.addHandler(self.log_handler)
        
        # Show initial message
        self.update_status("Ready to use. Select a file to encrypt or decrypt.")

    def setup_file_tab(self):
        # File selection frame
        file_select_frame = ttk.LabelFrame(self.file_frame, text="File Selection")
        file_select_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(file_select_frame, text="Input File:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.input_path_var = tk.StringVar()
        ttk.Entry(file_select_frame, textvariable=self.input_path_var, width=50).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(file_select_frame, text="Browse...", command=self.select_input_file).grid(row=0, column=2, padx=5, pady=5)
        
        ttk.Label(file_select_frame, text="Output File:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.output_path_var = tk.StringVar()
        ttk.Entry(file_select_frame, textvariable=self.output_path_var, width=50).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(file_select_frame, text="Browse...", command=self.select_output_file).grid(row=1, column=2, padx=5, pady=5)
        
        # Operation frame
        operation_frame = ttk.LabelFrame(self.file_frame, text="Operation")
        operation_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.operation_var = tk.StringVar(value="encrypt")
        ttk.Radiobutton(operation_frame, text="Encrypt", variable=self.operation_var, value="encrypt").grid(row=0, column=0, padx=20, pady=5)
        ttk.Radiobutton(operation_frame, text="Decrypt", variable=self.operation_var, value="decrypt").grid(row=0, column=1, padx=20, pady=5)
        
        # Action buttons
        action_frame = ttk.Frame(self.file_frame)
        action_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(action_frame, text="Process File", command=self.process_file, style='Accent.TButton').pack(side=tk.RIGHT, padx=5, pady=5)
        
        # Status frame
        status_frame = ttk.LabelFrame(self.file_frame, text="Status")
        status_frame.pack(fill=tk.X, padx=10, pady=10, expand=True)
        
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(status_frame, textvariable=self.status_var, wraplength=500).pack(fill=tk.X, padx=10, pady=10)
        
        self.progress = ttk.Progressbar(status_frame, orient=tk.HORIZONTAL, length=100, mode='indeterminate')
        self.progress.pack(fill=tk.X, padx=10, pady=10)

    def setup_config_tab(self):
        # Create a scrollable frame for configuration
        scroll_container = ScrollableFrame(self.config_frame)
        scroll_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Config controls
        control_frame = ttk.Frame(scroll_container.scrollable_frame)
        control_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(control_frame, text="Save Configuration", command=self.save_config).pack(side=tk.RIGHT, padx=5)
        ttk.Button(control_frame, text="Reload", command=self.load_config).pack(side=tk.RIGHT, padx=5)
        
        # Config sections will be added here when loaded
        self.config_sections_frame = ttk.Frame(scroll_container.scrollable_frame)
        self.config_sections_frame.pack(fill=tk.BOTH, expand=True)
        
    def setup_log_tab(self):
        # Create log display
        self.log_text = scrolledtext.ScrolledText(self.log_frame, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.log_text.config(state=tk.DISABLED)
        
        # Log controls
        log_control_frame = ttk.Frame(self.log_frame)
        log_control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(log_control_frame, text="Clear Logs", command=self.clear_logs).pack(side=tk.RIGHT, padx=5)
        ttk.Button(log_control_frame, text="Save Logs", command=self.save_logs).pack(side=tk.RIGHT, padx=5)

    def load_config(self):
        # Clear existing config sections
        for widget in self.config_sections_frame.winfo_children():
            widget.destroy()
        
        self.config_sections = {}
        
        # Create config parser
        self.config = configparser.ConfigParser()
        
        # Try to load from file, or use default if file doesn't exist
        if os.path.exists(self.config_file):
            try:
                self.config.read(self.config_file)
                self.update_status(f"Configuration loaded from {self.config_file}")
            except Exception as e:
                self.update_status(f"Error loading configuration: {e}")
                self.load_default_config()
        else:
            self.update_status("Configuration file not found. Using default settings.")
            self.load_default_config()
        
        # Create UI for each section
        for section in self.config.sections():
            options = dict(self.config[section])
            section_ui = ConfigSection(self.config_sections_frame, section, options)
            section_ui.frame.pack(fill=tk.X, padx=10, pady=5)
            self.config_sections[section] = section_ui
        
        # Check for shared key
        self.check_key_status()

    def load_default_config(self):
        # Default configuration from the provided example
        self.config['kex'] = {
            'kex_alg': 'Kyber1024',
            'ephemeral_key_lifetime': '3600'
        }
        self.config['signature'] = {
            'sig_alg': 'Dilithium3',
            'sig_verify_timeout': '5'
        }
        self.config['noise'] = {
            'noise_protocol': 'ChaCha20_Poly1305'
        }
        self.config['security'] = {
            'key_rotation_interval': '100',
            'key_rotation_time': '360',
            'max_key_chain_length': '3',
            'max_message_size': '1024',
            'timestamp_window': '300',
            'max_failed_attempts': '5',
            'rate_limit_window': '300',
            'replay_window_size': '64',
            'message_max_age': '3600',
            'key_size': '32'
        }
        self.config['timeouts'] = {
            'handshake_timeout': '30',
            'connection_timeout': '300',
            'cleanup_interval': '300'
        }
        self.config['keys'] = {
            'key_file_perms': '600',
            'key_rotation_check_interval': '60'
        }
        self.config['performance'] = {
            'nonce_cache_size': '1024'
        }

    def save_config(self):
        # Update config from UI
        for section, section_ui in self.config_sections.items():
            values = section_ui.get_values()
            for option, value in values.items():
                self.config[section][option] = value
        
        # Save to file
        try:
            with open(self.config_file, 'w') as f:
                self.config.write(f)
            self.update_status(f"Configuration saved to {self.config_file}")
        except Exception as e:
            self.update_status(f"Error saving configuration: {e}")
            logger.error(f"Failed to save config: {e}")

    def select_input_file(self):
        file_path = filedialog.askopenfilename(title="Select Input File")
        if file_path:
            self.input_path_var.set(file_path)
            # Suggest output path with .enc or without .enc extension
            input_path = file_path
            if self.operation_var.get() == "encrypt":
                output_path = input_path + ".enc"
            else:
                if input_path.endswith(".enc"):
                    output_path = input_path[:-4]
                else:
                    output_path = input_path + ".dec"
            self.output_path_var.set(output_path)

    def select_output_file(self):
        file_path = filedialog.asksaveasfilename(title="Select Output File")
        if file_path:
            self.output_path_var.set(file_path)

    def check_key_status(self):
        if os.path.exists("shared_key.bin"):
            try:
                with open("shared_key.bin", "rb") as f:
                    key_data = f.read()
            except Exception as e:
                print(f"Error: {e}")

    def process_file(self):
        input_path = self.input_path_var.get()
        output_path = self.output_path_var.get()
        operation = self.operation_var.get()
        
        if not input_path or not output_path:
            messagebox.showwarning("Missing Information", "Please select both input and output files.")
            return
        
        if not os.path.exists(input_path):
            messagebox.showwarning("File Error", f"Input file does not exist: {input_path}")
            return
            
        if not os.path.exists("shared_key.bin"):
            messagebox.showwarning("Missing Key", "Shared key not found")
            return
        
        # Save config before processing
        self.save_config()
        
        # Process file
        self.update_status(f"{'Encrypting' if operation == 'encrypt' else 'Decrypting'} file...")
        self.progress.start()
        
        # Run in thread to avoid UI freeze
        def process_thread():
            try:
                result = False
                if operation == "encrypt":
                    result = asyncio.run(encrypt_file(input_path, output_path, self.config_file))
                else:
                    result = asyncio.run(decrypt_file(input_path, output_path, self.config_file))
                
                self.root.after(0, lambda: self.process_complete(result))
            except Exception as e:
                self.root.after(0, lambda: self.process_error(e))
        
        threading.Thread(target=process_thread).start()

    def process_complete(self, success):
        self.progress.stop()
        operation = self.operation_var.get()
        
        if success:
            self.update_status(f"File {'encrypted' if operation == 'encrypt' else 'decrypted'} successfully.")
            messagebox.showinfo("Success", f"File {'encrypted' if operation == 'encrypt' else 'decrypted'} successfully.")
        else:
            self.update_status(f"File {'encryption' if operation == 'encrypt' else 'decryption'} failed.")
            messagebox.showerror("Error", f"File {'encryption' if operation == 'encrypt' else 'decryption'} failed. Check logs for details.")

    def process_error(self, error):
        self.progress.stop()
        self.update_status(f"Error: {error}")
        messagebox.showerror("Error", f"Operation failed: {error}")
        logger.error(f"Operation failed: {error}", exc_info=True)

    def update_status(self, message):
        self.status_var.set(message)
        logger.info(message)

    def clear_logs(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

    def save_logs(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[("Log files", "*.log"), ("All files", "*.*")],
            title="Save Logs"
        )
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    f.write(self.log_text.get(1.0, tk.END))
                messagebox.showinfo("Success", f"Logs saved to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save logs: {e}")

class LogHandler(logging.Handler):
    def __init__(self, text_widget):
        logging.Handler.__init__(self)
        self.text_widget = text_widget
        self.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    def emit(self, record):
        msg = self.format(record) + "\n"
        
        def append():
            self.text_widget.config(state=tk.NORMAL)
            self.text_widget.insert(tk.END, msg)
            self.text_widget.see(tk.END)
            self.text_widget.config(state=tk.DISABLED)
            
        # Schedule to run in the main thread
        self.text_widget.after(0, append)

if __name__ == "__main__":
    root = tk.Tk()
    app = CryptoGUI(root)
    root.mainloop()