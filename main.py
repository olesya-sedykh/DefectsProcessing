from PyQt5.QtWidgets import QApplication
import sys
import os

plugins_path = os.path.join(sys.prefix, 'Lib', 'site-packages', 'PyQt5', 'Qt5', 'plugins')
os.environ['QT_PLUGIN_PATH'] = plugins_path

sys.path.append('./backend')
sys.path.append('./frontend')

from frontend.MainScreen import MainScreen

if __name__ == "__main__":
    App = QApplication(sys.argv)
    window = MainScreen()
    # App.aboutToQuit.connect(window.clear_temp_folder)
    window.clear_temp_folder()
    window.show()
    sys.exit(App.exec())