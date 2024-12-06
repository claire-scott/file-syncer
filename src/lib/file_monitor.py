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
        
    def on_moved(self, event):
        """Called when a file or directory is moved or renamed"""
        if event.is_directory:
            return
            
        try:
            # Get relative paths for both source and destination
            src_rel_path = os.path.relpath(event.src_path, self.source_folder)
            dest_rel_path = os.path.relpath(event.dest_path, self.source_folder)
            
            # Check cooldown
            current_time = time.time()
            if src_rel_path in self.cooldown and current_time - self.cooldown[src_rel_path] < self.cooldown_time:
                return
            self.cooldown[src_rel_path] = current_time
            
            # Check if either path should be excluded
            if self.app.sync_engine and self.app.sync_engine.should_exclude_file(event.src_path):
                self.app.log_message(f"Ignored rename: {src_rel_path} (matches exclusion pattern)", 'ignored')
                return
                
            # Handle the rename by deleting the old file and copying the new one
            self.app.log_message(f"File renamed: {src_rel_path} → {dest_rel_path}", 'changed')
            self.app.handle_file_deletion(src_rel_path)
            self.app.handle_file_change(dest_rel_path, 'created')
            
        except Exception as e:
            self.app.log_message(f"Error handling rename: {str(e)}", 'error')
            logging.error(f"Error handling rename: {str(e)}", exc_info=True)
    
    def on_created(self, event):
        """Called when a file or directory is created"""
        if event.is_directory:
            return
            
        try:
            rel_path = os.path.relpath(event.src_path, self.source_folder)
            
            # Check cooldown
            current_time = time.time()
            if rel_path in self.cooldown and current_time - self.cooldown[rel_path] < self.cooldown_time:
                return
            self.cooldown[rel_path] = current_time
            
            # Check if file should be ignored
            if self.app.sync_engine and self.app.sync_engine.should_exclude_file(event.src_path):
                self.app.log_message(f"Ignored new file: {rel_path} (matches exclusion pattern)", 'ignored')
                return
                
            self.app.log_message(f"New file detected: {rel_path}", 'new_file')
            self.app.handle_file_change(rel_path, 'created')
            
        except Exception as e:
            self.app.log_message(f"Error handling new file: {str(e)}", 'error')
            logging.error(f"Error handling new file: {str(e)}", exc_info=True)
    
    def on_modified(self, event):
        """Called when a file is modified"""
        if event.is_directory:
            return
            
        try:
            rel_path = os.path.relpath(event.src_path, self.source_folder)
            
            # Check cooldown
            current_time = time.time()
            if rel_path in self.cooldown and current_time - self.cooldown[rel_path] < self.cooldown_time:
                return
            self.cooldown[rel_path] = current_time
            
            # Check if file should be ignored
            if self.app.sync_engine and self.app.sync_engine.should_exclude_file(event.src_path):
                self.app.log_message(f"Ignored change: {rel_path} (matches exclusion pattern)", 'ignored')
                return
                
            self.app.log_message(f"File changed: {rel_path}", 'changed')
            self.app.handle_file_change(rel_path, 'modified')
            
        except Exception as e:
            self.app.log_message(f"Error handling change: {str(e)}", 'error')
            logging.error(f"Error handling change: {str(e)}", exc_info=True)
    
    def on_deleted(self, event):
        """Called when a file is deleted"""
        if event.is_directory:
            return
            
        try:
            rel_path = os.path.relpath(event.src_path, self.source_folder)
            
            # Check cooldown
            current_time = time.time()
            if rel_path in self.cooldown and current_time - self.cooldown[rel_path] < self.cooldown_time:
                return
            self.cooldown[rel_path] = current_time
            
            # Check if file should be ignored
            if self.app.sync_engine and self.app.sync_engine.should_exclude_file(event.src_path):
                self.app.log_message(f"Ignored deletion: {rel_path} (matches exclusion pattern)", 'ignored')
                return
                
            self.app.log_message(f"File deleted: {rel_path}", 'deleted')
            self.app.handle_file_deletion(rel_path)
            
        except Exception as e:
            self.app.log_message(f"Error handling deletion: {str(e)}", 'error')
            logging.error(f"Error handling deletion: {str(e)}", exc_info=True)

class FileMonitor:
    def __init__(self, app):
        self.app = app
        self.observer = None
        self.event_handler = None
        
    def start(self, folder):
        if not folder:
            self.app.log_message("Please select the source folder first!", 'error')
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
