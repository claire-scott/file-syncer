import tkinter as tk
from lib.ui import SyncerUI
from lib.sync_engine import SyncEngine
from lib.file_monitor import FileMonitor
from lib.config_manager import ConfigManager
import sys
import logging
import datetime
import codecs

# Configure stderr to handle Unicode
if sys.stderr.encoding != 'utf-8':
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr),  # Log to stderr with UTF-8 encoding
        logging.FileHandler(  # Also log to a daily rotating file
            f'syncer_{datetime.datetime.now().strftime("%Y%m%d")}.log',
            encoding='utf-8'
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
        
        # Create UI first
        ui = SyncerUI(root, None, None, config_manager)
        
        # Create components with message handler
        sync_engine = SyncEngine(message_handler)
        file_monitor = FileMonitor(message_handler)
        
        # Update UI with component references
        ui.sync_engine = sync_engine
        ui.file_monitor = file_monitor
        
        # Update message handler with references
        message_handler.set_ui(ui)
        message_handler.set_sync_engine(sync_engine)
        
        # Update sync engine with UI reference
        sync_engine.ui = ui
        
        # Initialize monitoring after all components are set up
        ui.initialize_monitoring()
        
        logging.info("Application started successfully")
        root.mainloop()
        
    except Exception as e:
        logging.error(f"Failed to start application: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
