import tkinter as tk
from lib.ui import SyncerUI
from lib.sync_engine import SyncEngine
from lib.file_monitor import FileMonitor
from lib.config_manager import ConfigManager
import sys
import logging
import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr),  # Log to stderr
        logging.FileHandler(  # Also log to a daily rotating file
            f'syncer_{datetime.datetime.now().strftime("%Y%m%d")}.log'
        )
    ]
)

class MessageHandler:
    def __init__(self):
        self.ui = None
        self.sync_engine = None
            
    def set_ui(self, ui):
        self.ui = ui
            
    def set_sync_engine(self, sync_engine):
        self.sync_engine = sync_engine
            
    def log_message(self, message, message_type='info'):
        # Always log to UI
        if self.ui:
            self.ui.log_message(message, message_type)
            
        # Log errors and warnings to stderr and file
        if message_type == 'error':
            logging.error(message)
        elif message_type == 'ignored':
            logging.warning(message)
        else:
            logging.info(message)
            
    def handle_file_change(self, rel_path, event_type):
        if self.ui and self.ui.auto_sync_var.get():
            self.ui.sync_single_file(rel_path)
            
    def handle_file_deletion(self, rel_path):
        if self.ui and self.ui.auto_sync_var.get() and self.ui.delete_files_var.get():
            self.ui.delete_single_file(rel_path)

def handle_exception(exc_type, exc_value, exc_traceback):
    """Handle uncaught exceptions by logging them"""
    if issubclass(exc_type, KeyboardInterrupt):
        # Call the default handler for KeyboardInterrupt
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
        
    logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

def main():
    # Set up global exception handler
    sys.excepthook = handle_exception
    
    try:
        root = tk.Tk()
        
        # Create instances of all components
        config_manager = ConfigManager()
        
        # Create message handler
        message_handler = MessageHandler()
        
        # Create sync engine and set it in message handler
        sync_engine = SyncEngine(message_handler)
        message_handler.set_sync_engine(sync_engine)
        
        # Create file monitor
        file_monitor = FileMonitor(message_handler)
        
        # Create UI with all required components
        ui = SyncerUI(root, sync_engine, file_monitor, config_manager)
        
        # Set UI reference in message handler
        message_handler.set_ui(ui)
        
        logging.info("Application started successfully")
        root.mainloop()
        
    except Exception as e:
        logging.error(f"Failed to start application: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
