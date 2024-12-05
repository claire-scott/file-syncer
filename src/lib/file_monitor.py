from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
import time
import logging

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
                logging.debug(f"Skipping duplicate event for {rel_path} (cooldown)")
                return
            self.cooldown[rel_path] = current_time
            
            # Check if file should be ignored
            if self.app.sync_engine and self.app.sync_engine.should_exclude(
                event.src_path,
                self.source_folder,
                self.app.sync_engine.read_gitignore(self.source_folder),
                [p.strip() for p in self.app.ui.exclusions_text.get("1.0", "end").split('\n') if p.strip()]
            ):
                self.app.log_message(f"Ignored change: {rel_path} (matches exclusion pattern)", 'ignored')
                logging.info(f"Ignored file system event for {rel_path} (excluded)")
                return
            
            if event.event_type == 'created':
                self.app.log_message(f"New file detected: {rel_path}", 'new_file')
                logging.info(f"New file created: {rel_path}")
                self.app.handle_file_change(rel_path, event.event_type)
            elif event.event_type == 'modified':
                self.app.log_message(f"File changed: {rel_path}", 'changed')
                logging.info(f"File modified: {rel_path}")
                self.app.handle_file_change(rel_path, event.event_type)
            elif event.event_type == 'deleted':
                self.app.log_message(f"File deleted: {rel_path}", 'deleted')
                logging.info(f"File deleted: {rel_path}")
                self.app.handle_file_deletion(rel_path)
        except Exception as e:
            error_msg = f"Error handling change for {event.src_path}: {str(e)}"
            self.app.log_message(error_msg, 'error')
            logging.error(error_msg, exc_info=True)

class FileMonitor:
    def __init__(self, app):
        self.app = app
        self.observer = None
        self.event_handler = None
        
    def start(self, folder):
        if not folder:
            error_msg = "Please select the source folder first!"
            self.app.log_message(error_msg, 'error')
            logging.error(error_msg)
            return False
            
        try:
            logging.info(f"Starting file system monitor for {folder}")
            self.observer = Observer()
            self.event_handler = FolderChangeHandler(self.app, folder)
            self.observer.schedule(self.event_handler, folder, recursive=True)
            self.observer.start()
            self.app.log_message("Started monitoring for changes", 'info')
            logging.info("File system monitor started successfully")
            return True
        except Exception as e:
            error_msg = f"Error starting monitoring: {str(e)}"
            self.app.log_message(error_msg, 'error')
            logging.error(error_msg, exc_info=True)
            return False
            
    def stop(self):
        if self.observer:
            try:
                logging.info("Stopping file system monitor")
                self.observer.stop()
                self.observer.join()
                self.observer = None
                self.event_handler = None
                self.app.log_message("Stopped monitoring for changes", 'info')
                logging.info("File system monitor stopped successfully")
            except Exception as e:
                error_msg = f"Error stopping monitor: {str(e)}"
                self.app.log_message(error_msg, 'error')
                logging.error(error_msg, exc_info=True)
