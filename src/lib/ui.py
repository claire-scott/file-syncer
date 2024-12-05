import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import queue
import threading
import os

class SyncerUI:
    def __init__(self, root, sync_engine, file_monitor, config_manager):
        self.root = root
        self.root.title("Folder Syncer")
        self.root.geometry("800x600")
        
        # Store component references
        self.sync_engine = sync_engine
        self.file_monitor = file_monitor
        self.config_manager = config_manager
        
        # Create main frame with proper grid configuration
        main_frame = ttk.Frame(root)
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure root window grid
        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)
        
        # Create top frame for all controls
        top_frame = ttk.Frame(main_frame, padding="10")
        top_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Create UI components
        self.create_folder_selection(top_frame)
        self.create_exclusions_frame(top_frame)
        self.create_sync_options_frame(top_frame)
        self.create_buttons_frame(top_frame)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(top_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # Output text area
        self.create_output_area(main_frame)
        
        # Configure main_frame grid
        main_frame.grid_rowconfigure(1, weight=1)  # Make output area expand
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Control variables
        self.cancel_sync = False
        self.sync_thread = None
        self.message_queue = queue.Queue()
        self.root.after(100, self.check_message_queue)
        
        # Load saved settings
        self.load_settings()
        
        # Save settings on window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_folder_selection(self, parent):
        # Left folder selection
        ttk.Label(parent, text="Left Folder:").grid(row=0, column=0, sticky=tk.W)
        self.left_folder_var = tk.StringVar()
        self.left_folder_entry = ttk.Entry(parent, textvariable=self.left_folder_var)
        self.left_folder_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(parent, text="Browse", command=lambda: self.browse_folder("left")).grid(row=0, column=2)
        
        # Right folder selection
        ttk.Label(parent, text="Right Folder:").grid(row=1, column=0, sticky=tk.W)
        self.right_folder_var = tk.StringVar()
        self.right_folder_entry = ttk.Entry(parent, textvariable=self.right_folder_var)
        self.right_folder_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(parent, text="Browse", command=lambda: self.browse_folder("right")).grid(row=1, column=2)
        
    def create_exclusions_frame(self, parent):
        exclusions_frame = ttk.LabelFrame(parent, text="Additional Exclusions", padding="5")
        exclusions_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        self.exclusions_text = scrolledtext.ScrolledText(exclusions_frame, height=4)
        self.exclusions_text.pack(fill=tk.X)
        ttk.Label(exclusions_frame, text="Enter patterns to exclude, one per line").pack()
        
    def create_sync_options_frame(self, parent):
        options_frame = ttk.LabelFrame(parent, text="Sync Options", padding="5")
        options_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        self.delete_files_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Delete files in right folder that don't exist in left folder",
                       variable=self.delete_files_var).pack(anchor=tk.W)
        
        # Real-time monitoring options
        monitor_frame = ttk.Frame(options_frame)
        monitor_frame.pack(fill=tk.X, pady=5)
        
        self.monitor_var = tk.BooleanVar(value=False)
        self.monitor_checkbox = ttk.Checkbutton(monitor_frame, text="Monitor for changes",
                                              variable=self.monitor_var, command=self.toggle_monitoring)
        self.monitor_checkbox.pack(side=tk.LEFT)
        
        self.auto_sync_var = tk.BooleanVar(value=True)
        self.auto_sync_checkbox = ttk.Checkbutton(monitor_frame, text="Auto-sync changes",
                                                variable=self.auto_sync_var)
        self.auto_sync_checkbox.pack(side=tk.LEFT, padx=10)
        
        self.monitor_status = ttk.Label(monitor_frame, text="Status: Not monitoring")
        self.monitor_status.pack(side=tk.RIGHT)
        
    def create_buttons_frame(self, parent):
        buttons_frame = ttk.Frame(parent)
        buttons_frame.grid(row=4, column=0, columnspan=3, pady=10)
        
        self.trial_button = ttk.Button(buttons_frame, text="Trial Run", command=lambda: self.start_sync(trial_run=True))
        self.trial_button.pack(side=tk.LEFT, padx=5)
        
        self.sync_button = ttk.Button(buttons_frame, text="Synchronize", command=lambda: self.start_sync(trial_run=False))
        self.sync_button.pack(side=tk.LEFT, padx=5)
        
        self.cancel_button = ttk.Button(buttons_frame, text="Cancel", command=self.cancel_sync_operation, state=tk.DISABLED)
        self.cancel_button.pack(side=tk.LEFT, padx=5)
        
    def create_output_area(self, parent):
        # Create output frame
        output_frame = ttk.LabelFrame(parent, text="Output", padding="5")
        output_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=5)
        
        # Configure output frame grid
        output_frame.grid_rowconfigure(0, weight=1)
        output_frame.grid_columnconfigure(0, weight=1)
        
        # Create scrolled text widget
        self.output_text = scrolledtext.ScrolledText(output_frame)
        self.output_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
    def browse_folder(self, side):
        folder = filedialog.askdirectory()
        if folder:
            if side == "left":
                self.left_folder_var.set(folder)
                if self.monitor_var.get():
                    self.stop_monitoring()
                    self.start_monitoring()
            else:
                self.right_folder_var.set(folder)
                
    def toggle_monitoring(self):
        if self.monitor_var.get():
            self.start_monitoring()
        else:
            self.stop_monitoring()
            
    def start_monitoring(self):
        if self.file_monitor.start(self.left_folder_var.get()):
            self.monitor_status.config(text="Status: Monitoring")
            self.log_message("Started monitoring for changes")
        else:
            self.monitor_var.set(False)
            
    def stop_monitoring(self):
        self.file_monitor.stop()
        self.monitor_status.config(text="Status: Not monitoring")
        self.log_message("Stopped monitoring for changes")
        
    def sync_single_file(self, rel_path):
        gitignore_patterns = self.sync_engine.read_gitignore(self.left_folder_var.get())
        additional_patterns = [p.strip() for p in self.exclusions_text.get("1.0", tk.END).split('\n') if p.strip()]
        
        if self.sync_engine.sync_single_file(self.left_folder_var.get(), self.right_folder_var.get(),
                                           rel_path, gitignore_patterns, additional_patterns):
            self.log_message(f"Auto-synced: {rel_path}")
            
    def delete_single_file(self, rel_path):
        if self.sync_engine.delete_single_file(self.right_folder_var.get(), rel_path):
            self.log_message(f"Auto-deleted: {rel_path}")
            
    def start_sync(self, trial_run=False):
        if self.sync_thread and self.sync_thread.is_alive():
            self.log_message("Sync operation already in progress!")
            return
            
        if not self.left_folder_var.get() or not self.right_folder_var.get():
            self.log_message("Please select both folders first!")
            return
            
        if not os.path.exists(self.left_folder_var.get()) or not os.path.exists(self.right_folder_var.get()):
            self.log_message("One or both folders do not exist!")
            return
            
        self.cancel_sync = False
        self.trial_button.config(state=tk.DISABLED)
        self.sync_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)
        
        self.sync_thread = threading.Thread(
            target=self.perform_sync,
            args=(trial_run,),
            daemon=True
        )
        self.sync_thread.start()
        
    def perform_sync(self, trial_run):
        try:
            mode = "Trial run" if trial_run else "Synchronization"
            self.log_message(f"Starting {mode}")
            
            # Get patterns
            gitignore_patterns = self.sync_engine.read_gitignore(self.left_folder_var.get())
            additional_patterns = [p.strip() for p in self.exclusions_text.get("1.0", tk.END).split('\n') if p.strip()]
            
            self.log_message("Using .gitignore patterns: " + ", ".join(gitignore_patterns))
            self.log_message("Using additional exclusions: " + ", ".join(additional_patterns))
            
            # Perform sync
            copied, deleted = self.sync_engine.sync_folders(
                self.left_folder_var.get(),
                self.right_folder_var.get(),
                gitignore_patterns,
                additional_patterns,
                self.delete_files_var.get(),
                trial_run,
                self.update_progress,
                lambda: self.cancel_sync
            )
            
            if not self.cancel_sync:
                self.log_message(f"{mode} completed!")
                self.log_message(f"Files copied: {copied}")
                self.log_message(f"Files deleted: {deleted}")
                
        finally:
            self.trial_button.config(state=tk.NORMAL)
            self.sync_button.config(state=tk.NORMAL)
            self.cancel_button.config(state=tk.DISABLED)
            self.progress_var.set(0)
            
    def cancel_sync_operation(self):
        self.cancel_sync = True
        self.log_message("Cancelling sync operation...")
        
    def update_progress(self, value):
        self.progress_var.set(value)
        
    def log_message(self, message):
        self.message_queue.put(message)
        
    def check_message_queue(self):
        while not self.message_queue.empty():
            message = self.message_queue.get()
            self.output_text.insert(tk.END, message + "\n")
            self.output_text.see(tk.END)
        self.root.after(100, self.check_message_queue)
        
    def load_settings(self):
        config = self.config_manager.load_config()
        self.left_folder_var.set(config.get('left_folder', ''))
        self.right_folder_var.set(config.get('right_folder', ''))
        self.exclusions_text.delete('1.0', tk.END)
        self.exclusions_text.insert('1.0', config.get('exclusions', ''))
        self.delete_files_var.set(config.get('delete_files', True))
        self.auto_sync_var.set(config.get('auto_sync', True))
        if config.get('monitoring', False):
            self.monitor_var.set(True)
            self.start_monitoring()
            
    def save_settings(self):
        config = {
            'left_folder': self.left_folder_var.get(),
            'right_folder': self.right_folder_var.get(),
            'exclusions': self.exclusions_text.get('1.0', tk.END).strip(),
            'delete_files': self.delete_files_var.get(),
            'monitoring': self.monitor_var.get(),
            'auto_sync': self.auto_sync_var.get()
        }
        self.config_manager.save_config(config)
        
    def on_closing(self):
        self.stop_monitoring()
        self.save_settings()
        self.root.destroy()
