#!/usr/bin/env python3
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from RandomizerUI.window import RandomizerWindow
# from RandomizerCore.Paths.randomizer_paths import RESOURCE_PATH, RUNNING_FROM_SOURCE
import sys

def interruptHandler(sig, frame):
    sys.exit(0)

# Allow keyboard interrupts
import signal
signal.signal(signal.SIGINT, interruptHandler)


# # Set app id so the custom taskbar icon will show while running from source
# if RUNNING_FROM_SOURCE:
#     from ctypes import windll
#     try:
#         windll.shell32.SetCurrentProcessExplicitAppUserModelID("OctoExpansion_Randomizer")
#     except AttributeError:
#         pass # Ignore for versions of Windows before Windows 7

# build_icon = "icon.ico"
# if sys.platform == "darwin": # mac
#     build_icon = "icon.icns"

app = QApplication([])
app.setStyle('fusion')
# app.setWindowIcon(QtGui.QIcon(os.path.join(RESOURCE_PATH, build_icon)))

m = RandomizerWindow()

# for keyboard interrupts
timer = QTimer()
timer.start(100)
timer.timeout.connect(lambda: None)

sys.exit(app.exec())
