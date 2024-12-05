import tkinter as tk
from lib.ui import SyncerUI
from lib.sync_engine import SyncEngine
from lib.file_monitor import FileMonitor
from lib.config_manager import ConfigManager

def main():
    root = tk.Tk()
    
    # Create instances of all components
    config_manager = ConfigManager()
    
    # Create a message handler class to bridge between components
    class MessageHandler:
        def __init__(self):
            self.ui = None
            
        def set_ui(self, ui):
            self.ui = ui
            
        def log_message(self, message):
            if self.ui:
                self.ui.log_message(message)
    
    # Create message handler
    message_handler = MessageHandler()
    
    # Create components with message handler
    sync_engine = SyncEngine(message_handler)
    file_monitor = FileMonitor(message_handler)
    
    # Create UI with all required components
    ui = SyncerUI(root, sync_engine, file_monitor, config_manager)
    
    # Set UI reference in message handler
    message_handler.set_ui(ui)
    
    root.mainloop()

if __name__ == "__main__":
    main()
