import tkinter as tk
import platform
import ctypes
from gui import SEMHybridEngineApp

if __name__ == "__main__":
    if platform.system() == "Windows":
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1) # Windows 8.1+
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware() # Windows Vista+
            except Exception:
                pass
                
    root = tk.Tk()
    app = SEMHybridEngineApp(root)
    root.mainloop()