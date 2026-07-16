import sys
import traceback

if __name__ == "__main__":
    sys.path.append(r"a:\Nexa\nexashield-app\modules")
    
    def custom_excepthook(exc_type, exc_value, exc_traceback):
        with open("crash_log.txt", "w") as f:
            traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

    sys.excepthook = custom_excepthook

    try:
        from PyQt6.QtWidgets import QApplication
        from main import NexaShieldApp
        
        app = QApplication(sys.argv)
        window = NexaShieldApp()
        window.show()
        
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(4000, app.quit)
        
        sys.exit(app.exec())
    except Exception as e:
        with open("crash_log.txt", "w") as f:
            traceback.print_exc(file=f)
