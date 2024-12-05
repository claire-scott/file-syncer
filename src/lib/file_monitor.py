from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
import time

class FolderChangeHandler(FileSystemEventHandler):
    def __init__(self, app, source_folder):
        self.app = app
        self.source_folder = source_folder
        self.cooldown = {}
        self.cooldown_time = 1  # seconds
        
    def on_any_event(self, event):
        if event.is_directory:
            return
            
        # Get relative path
        try:
            rel_path = os.path.relpath(event.src_path, self.source_folder)
            
            # Check cooldown to prevent duplicate events
            current_time = time.time()
            if rel_path in self.cooldown and current_time - self.cooldown[rel_path] < self.cooldown_time:
                return
            self.cooldown[rel_path] = current_time
            
            if event.event_type in ['created', 'modified']:
                self.app.log_message(f"Change detected: {rel_path}")
                if self.app.auto_sync_var.get():
                    self.app.sync_single_file(rel_path)
            elif event.event_type == 'deleted':
                self.app.log_message(f"Deletion detected: {rel_path}")
                if self.app.auto_sync_var.get() and self.app.delete_files_var.get():
                    self.app.delete_single_file(rel_path)
        except Exception as e:
            self.app.log_message(f"Error handling change: {str(e)}")

class FileMonitor:
    def __init__(self, app):
        self.app = app
        self.observer = None
        self.event_handler = None
        
    def start(self, folder):
        if not folder:
            self.app.log_message("Please select the source folder first!")
            return False
            
        try:
            self.observer = Observer()
            self.event_handler = FolderChangeHandler(self.app, folder)
            self.observer.schedule(self.event_handler, folder, recursive=True)
            self.observer.start()
            return True
        except Exception as e:
            self.app.log_message(f"Error starting monitoring: {str(e)}")
            return False
            
    def stop(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            self.event_handler = None
