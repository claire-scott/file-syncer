import os
import shutil
import fnmatch
from pathlib import Path
import logging
import stat

class SyncEngine:
    def __init__(self, app):
        self.app = app
        
    def read_gitignore(self, folder):
        gitignore_path = os.path.join(folder, '.gitignore')
        patterns = []
        try:
            if os.path.exists(gitignore_path):
                with open(gitignore_path, 'r') as f:
                    patterns = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        except Exception as e:
            self.app.log_message(f"Error reading .gitignore: {str(e)}", 'error')
            logging.error(f"Failed to read .gitignore at {gitignore_path}: {str(e)}")
        return patterns
        
    def should_exclude(self, path, base_path, gitignore_patterns, additional_patterns):
        try:
            relative_path = os.path.relpath(path, base_path)
            
            # Check additional exclusions
            for pattern in additional_patterns:
                if fnmatch.fnmatch(relative_path, pattern):
                    logging.debug(f"File {relative_path} excluded by pattern: {pattern}")
                    return True
                    
            # Check gitignore patterns
            for pattern in gitignore_patterns:
                if fnmatch.fnmatch(relative_path, pattern):
                    logging.debug(f"File {relative_path} excluded by gitignore pattern: {pattern}")
                    return True
                    
            return False
        except Exception as e:
            logging.error(f"Error checking exclusions for {path}: {str(e)}")
            return False

    def handle_readonly(self, func, path, exc_info):
        """Error handler for shutil.rmtree to handle read-only files"""
        if not os.access(path, os.W_OK):
            # Try to change the permission
            os.chmod(path, stat.S_IWUSR)
            # Try the function again
            func(path)
        else:
            raise
            
    def sync_single_file(self, source_folder, target_folder, rel_path, gitignore_patterns, additional_patterns):
        try:
            source_file = os.path.join(source_folder, rel_path)
            target_file = os.path.join(target_folder, rel_path)
            
            if not self.should_exclude(source_file, source_folder, gitignore_patterns, additional_patterns):
                os.makedirs(os.path.dirname(target_file), exist_ok=True)
                
                # Handle read-only target files
                if os.path.exists(target_file) and not os.access(target_file, os.W_OK):
                    os.chmod(target_file, stat.S_IWRITE)
                    
                shutil.copy2(source_file, target_file)
                logging.info(f"Synced file: {rel_path}")
                return True
        except PermissionError as e:
            error_msg = f"Permission denied syncing {rel_path}: {str(e)}"
            self.app.log_message(error_msg, 'error')
            logging.error(error_msg)
            return False
        except Exception as e:
            error_msg = f"Error syncing {rel_path}: {str(e)}"
            self.app.log_message(error_msg, 'error')
            logging.error(error_msg, exc_info=True)
            return False
            
    def delete_single_file(self, target_folder, rel_path):
        try:
            target_path = os.path.join(target_folder, rel_path)
            if os.path.exists(target_path):
                if os.path.isdir(target_path):
                    # Use rmtree for directories with error handler for read-only files
                    shutil.rmtree(target_path, onerror=self.handle_readonly)
                    logging.info(f"Deleted directory: {rel_path}")
                else:
                    # Handle read-only files
                    if not os.access(target_path, os.W_OK):
                        os.chmod(target_path, stat.S_IWRITE)
                    os.remove(target_path)
                    logging.info(f"Deleted file: {rel_path}")
                
                # Clean up empty parent directories
                dir_path = os.path.dirname(target_path)
                while dir_path != target_folder:
                    try:
                        if os.path.exists(dir_path) and len(os.listdir(dir_path)) == 0:
                            # Handle read-only directories
                            if not os.access(dir_path, os.W_OK):
                                os.chmod(dir_path, stat.S_IWRITE)
                            os.rmdir(dir_path)
                            logging.info(f"Removed empty directory: {os.path.relpath(dir_path, target_folder)}")
                        else:
                            break
                    except (PermissionError, OSError) as e:
                        logging.warning(f"Could not remove directory {dir_path}: {str(e)}")
                        break
                    dir_path = os.path.dirname(dir_path)
                return True
        except PermissionError as e:
            error_msg = f"Permission denied deleting {rel_path}: {str(e)}"
            self.app.log_message(error_msg, 'error')
            logging.error(error_msg)
            return False
        except Exception as e:
            error_msg = f"Error deleting {rel_path}: {str(e)}"
            self.app.log_message(error_msg, 'error')
            logging.error(error_msg, exc_info=True)
            return False
            
    def sync_folders(self, source_folder, target_folder, gitignore_patterns, additional_patterns,
                    delete_files=True, trial_run=False, progress_callback=None, cancel_check=None):
        try:
            # Get all files in both directories
            source_files = self.get_all_files(source_folder, gitignore_patterns, additional_patterns)
            target_files = self.get_all_files(target_folder, gitignore_patterns, additional_patterns)
            
            # Files to copy (new or modified)
            files_to_copy = []
            for rel_path in source_files:
                source_file = os.path.join(source_folder, rel_path)
                target_file = os.path.join(target_folder, rel_path)
                
                needs_update = True
                if os.path.exists(target_file):
                    source_mtime = os.path.getmtime(source_file)
                    target_mtime = os.path.getmtime(target_file)
                    needs_update = source_mtime > target_mtime
                
                if needs_update:
                    files_to_copy.append(rel_path)
            
            # Files to delete
            files_to_delete = []
            if delete_files:
                files_to_delete = [f for f in target_files if f not in source_files]
            
            # Log sync operation details
            logging.info(f"Starting {'trial run' if trial_run else 'sync'}")
            logging.info(f"Files to copy: {len(files_to_copy)}")
            logging.info(f"Files to delete: {len(files_to_delete)}")
            
            # Calculate total operations
            total_operations = len(files_to_copy) + len(files_to_delete)
            if total_operations == 0:
                logging.info("No changes needed")
                return 0, 0  # No changes needed
            
            completed_operations = 0
            copied_count = 0
            deleted_count = 0
            
            # Copy files
            for rel_path in files_to_copy:
                if cancel_check and cancel_check():
                    logging.info("Sync operation cancelled by user")
                    break
                    
                if trial_run:
                    logging.info(f"Would copy: {rel_path}")
                    copied_count += 1
                else:
                    if self.sync_single_file(source_folder, target_folder, rel_path,
                                          gitignore_patterns, additional_patterns):
                        copied_count += 1
                
                completed_operations += 1
                if progress_callback:
                    progress_callback((completed_operations / total_operations) * 100)
            
            # Delete files
            if delete_files:
                for rel_path in files_to_delete:
                    if cancel_check and cancel_check():
                        logging.info("Sync operation cancelled by user")
                        break
                        
                    if trial_run:
                        logging.info(f"Would delete: {rel_path}")
                        deleted_count += 1
                    else:
                        if self.delete_single_file(target_folder, rel_path):
                            deleted_count += 1
                    
                    completed_operations += 1
                    if progress_callback:
                        progress_callback((completed_operations / total_operations) * 100)
            
            logging.info(f"Sync completed: {copied_count} copied, {deleted_count} deleted")
            return copied_count, deleted_count
            
        except Exception as e:
            error_msg = f"Error during sync: {str(e)}"
            self.app.log_message(error_msg, 'error')
            logging.error(error_msg, exc_info=True)
            return 0, 0
            
    def get_all_files(self, folder, gitignore_patterns, additional_patterns):
        files = set()
        try:
            for root, _, filenames in os.walk(folder):
                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    if not self.should_exclude(file_path, folder, gitignore_patterns, additional_patterns):
                        rel_path = os.path.relpath(file_path, folder)
                        files.add(rel_path)
        except Exception as e:
            error_msg = f"Error scanning directory {folder}: {str(e)}"
            self.app.log_message(error_msg, 'error')
            logging.error(error_msg, exc_info=True)
        return files
