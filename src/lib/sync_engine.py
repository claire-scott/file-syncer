import os
import shutil
import fnmatch
from pathlib import Path

class SyncEngine:
    def __init__(self, app):
        self.app = app
        
    def read_gitignore(self, folder):
        gitignore_path = os.path.join(folder, '.gitignore')
        patterns = []
        if os.path.exists(gitignore_path):
            with open(gitignore_path, 'r') as f:
                patterns = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        return patterns
        
    def should_exclude(self, path, base_path, gitignore_patterns, additional_patterns):
        relative_path = os.path.relpath(path, base_path)
        
        # Check additional exclusions
        for pattern in additional_patterns:
            if fnmatch.fnmatch(relative_path, pattern):
                return True
                
        # Check gitignore patterns
        for pattern in gitignore_patterns:
            if fnmatch.fnmatch(relative_path, pattern):
                return True
                
        return False
        
    def get_all_files(self, folder, gitignore_patterns, additional_patterns):
        files = set()
        for root, _, filenames in os.walk(folder):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                if not self.should_exclude(file_path, folder, gitignore_patterns, additional_patterns):
                    rel_path = os.path.relpath(file_path, folder)
                    files.add(rel_path)
        return files
        
    def sync_single_file(self, source_folder, target_folder, rel_path, gitignore_patterns, additional_patterns):
        try:
            source_file = os.path.join(source_folder, rel_path)
            target_file = os.path.join(target_folder, rel_path)
            
            if not self.should_exclude(source_file, source_folder, gitignore_patterns, additional_patterns):
                os.makedirs(os.path.dirname(target_file), exist_ok=True)
                shutil.copy2(source_file, target_file)
                return True
        except Exception as e:
            self.app.log_message(f"Error syncing {rel_path}: {str(e)}")
            return False
            
    def delete_single_file(self, target_folder, rel_path):
        try:
            target_file = os.path.join(target_folder, rel_path)
            if os.path.exists(target_file):
                os.remove(target_file)
                
                # Clean up empty directories
                dir_path = os.path.dirname(target_file)
                while dir_path != target_folder:
                    if len(os.listdir(dir_path)) == 0:
                        os.rmdir(dir_path)
                    dir_path = os.path.dirname(dir_path)
                return True
        except Exception as e:
            self.app.log_message(f"Error deleting {rel_path}: {str(e)}")
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
            
            # Calculate total operations
            total_operations = len(files_to_copy) + len(files_to_delete)
            if total_operations == 0:
                return 0, 0  # No changes needed
            
            completed_operations = 0
            copied_count = 0
            deleted_count = 0
            
            # Copy files
            for rel_path in files_to_copy:
                if cancel_check and cancel_check():
                    break
                    
                if trial_run:
                    self.app.log_message(f"Would copy: {rel_path}")
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
                        break
                        
                    if trial_run:
                        self.app.log_message(f"Would delete: {rel_path}")
                        deleted_count += 1
                    else:
                        if self.delete_single_file(target_folder, rel_path):
                            deleted_count += 1
                    
                    completed_operations += 1
                    if progress_callback:
                        progress_callback((completed_operations / total_operations) * 100)
            
            return copied_count, deleted_count
            
        except Exception as e:
            self.app.log_message(f"Error during sync: {str(e)}")
            return 0, 0
