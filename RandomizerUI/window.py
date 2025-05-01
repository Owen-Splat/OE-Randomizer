from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QMainWindow, QLabel, QLineEdit, QPushButton, QGroupBox, QProgressBar,
    QCheckBox, QComboBox, QSpacerItem, QHBoxLayout, QVBoxLayout, QWidget, QFileDialog, QSizePolicy)
from RandomizerCore.metro import Metro_Process
from randomizer_paths import SETTINGS_PATH, LOGS_PATH
from pathlib import Path
import random, string, yaml


class RandomizerWindow(QMainWindow):
    def __init__(self) -> None:
        super(RandomizerWindow, self).__init__()
        self.ui = Ui_RandomizerWindow()
        self.ui.setupUi(self)
        self.loadSettings()
        self.show()


    def browseButtonClicked(self, line) -> None:
        """Handles setting the RomFS and Output directories"""

        dir = QFileDialog.getExistingDirectory(self, "Select Folder")
        if dir == '': # dont override any existing path if the user canceled the QFileDialog
            return
        line.setText(str(Path(dir)))


    def createSeed(self, write_line=False) -> str:
        """Creates a random 32-length string of ascii letters that will be used as the seeding for the randomizer
        
        Eventually this will be updated to use adjectives and OE character names
        
        Parameters
        ----------
        line : QLineEdit | None
            If a QLineEdit is provided, the seed is written to it"""

        seed = ''.join(random.choices(string.ascii_letters, k=32))
        if write_line:
            self.ui.seed_line.setText(seed)
        return seed


    def randomize(self) -> None:
        """:)"""

        valid = self.validatePaths()
        if not valid:
            return

        seed = self.ui.seed_line.text()
        if not seed:
            seed = self.createSeed()

        settings = self.getSettings()
        settings["Seed"] = seed

        rando_window = WorkWindow(self, settings)
        rando_window.show()


    def validatePaths(self) -> bool:
        """Validates the romfs path as well as checking if the output path exists"""

        romfs_path = Path(self.ui.base_line.text())
        if Path(romfs_path / "romfs").exists():
            romfs_path = romfs_path / "romfs"
        romfs_valid = Path(romfs_path / "Pack" / "Mush.release.pack").is_file()

        # dlc_path = Path(self.ui.dlc_line.text())
        # if Path(dlc_path / "romfs").exists():
        #     dlc_path = dlc_path / "romfs"
        # dlc_valid = Path(dlc_path / "Layout" / "OctBackBtn_00.Nin_NX_NVN.szs").is_file()

        out_path = Path(self.ui.out_line.text())
        output_valid = out_path.exists()

        self.ui.base_line.setStyleSheet('')
        # self.ui.dlc_line.setStyleSheet('')
        self.ui.out_line.setStyleSheet('')
        if all((romfs_valid, output_valid)):
            return True

        red = "background-color: red;"
        green = "background-color: green;"

        if not romfs_valid:
            self.ui.base_line.setStyleSheet(red)
        else:
            self.ui.base_line.setStyleSheet(green)

        # if not dlc_valid:
        #     self.ui.dlc_line.setStyleSheet(red)
        # else:
        #     self.ui.dlc_line.setStyleSheet(green)

        if not output_valid:
            self.ui.out_line.setStyleSheet(red)
        else:
            self.ui.out_line.setStyleSheet(green)

        return False


    def getSettings(self) -> dict:
        settings = {}
        settings['Base_RomFS_Path'] = self.ui.base_line.text()
        # settings['DLC_Path'] = self.ui.dlc_line.text()
        settings['Output_Path'] = self.ui.out_line.text()
        settings['Seed'] = self.ui.seed_line.text()
        for check in self.findChildren(QCheckBox):
            check: QCheckBox
            settings[check.text()] = check.isChecked()
        for box in self.findChildren(QComboBox):
            box: QComboBox
            setting_name = box.currentText().split(':')[0]
            choice = box.currentText().split(':')[1].strip()
            settings[setting_name] = choice
        return settings


    def saveSettings(self) -> None:
        settings = self.getSettings()
        with open(SETTINGS_PATH, 'w') as f:
            yaml.dump(settings, f, sort_keys=False)


    def loadSettings(self) -> None:
        if not SETTINGS_PATH.exists():
            return
        with open(SETTINGS_PATH, 'r') as f:
            settings = yaml.safe_load(f)

        if 'Base_RomFS_Path' in settings:
            self.ui.base_line.setText(settings['Base_RomFS_Path'])
        # if 'DLC_Path' in settings:
        #     self.ui.dlc_line.setText(settings['DLC_Path'])
        if 'Output_Path' in settings:
            self.ui.out_line.setText(settings['Output_Path'])
        if 'Seed' in settings:
            self.ui.seed_line.setText(settings['Seed'])
        for check in self.findChildren(QCheckBox):
            check: QCheckBox
            if check.text() in settings:
                check.setChecked(settings[check.text()])
        for box in self.findChildren(QComboBox):
            box: QComboBox
            setting_name = box.currentText().split(':')[0]
            if setting_name in settings:
                index = box.findText(f"{setting_name}:  {settings[setting_name]}")
                if index == -1:
                    index = 0
                box.setCurrentIndex(index)


    def closeEvent(self, event) -> None:
        self.saveSettings()
        return super().closeEvent(event)



class Ui_RandomizerWindow(object):
    def setupUi(self, window: QMainWindow) -> None:
        window.setWindowTitle("Octo Expansion Randomizer v0.1.0")
        widget = QWidget()
        vl = QVBoxLayout()

        label = QLabel("Base RomFS Path", widget)
        label.setFixedWidth(100)
        base_line = QLineEdit(widget)
        button = QPushButton("Browse", widget)
        button.clicked.connect(lambda: window.browseButtonClicked(base_line))
        hl = QHBoxLayout()
        hl.addWidget(label)
        hl.addWidget(base_line)
        hl.addWidget(button)
        vl.addLayout(hl)
        self.base_line = base_line

        # label = QLabel("DLC Path", widget)
        # label.setFixedWidth(100)
        # dlc_line = QLineEdit(widget)
        # button = QPushButton("Browse", widget)
        # button.clicked.connect(lambda: window.browseButtonClicked(dlc_line))
        # hl = QHBoxLayout()
        # hl.addWidget(label)
        # hl.addWidget(dlc_line)
        # hl.addWidget(button)
        # vl.addLayout(hl)
        # self.dlc_line = dlc_line

        label = QLabel("Output Path", widget)
        label.setFixedWidth(100)
        out_line = QLineEdit(widget)
        button = QPushButton("Browse", widget)
        button.clicked.connect(lambda: window.browseButtonClicked(out_line))
        hl = QHBoxLayout()
        hl.addWidget(label)
        hl.addWidget(out_line)
        hl.addWidget(button)
        vl.addLayout(hl)
        self.out_line = out_line

        label = QLabel("Optional Seed", widget)
        label.setFixedWidth(100)
        seed_line = QLineEdit(widget)
        seed_line.setPlaceholderText("Leave blank for random seed")
        button = QPushButton("Generate", widget)
        button.clicked.connect(lambda: window.createSeed(True))
        hl = QHBoxLayout()
        hl.addWidget(label)
        hl.addWidget(seed_line)
        hl.addWidget(button)
        vl.addLayout(hl)
        self.seed_line = seed_line

        group = QGroupBox("Settings", widget)
        group.setAlignment(Qt.AlignmentFlag.AlignCenter)
        group.setStyleSheet("QGroupBox {font-size: 12px; font-weight: bold;}")
        weapon_check = QCheckBox("Weapons", group)
        level_check = QCheckBox("Levels", group)
        thang_box = QComboBox(group)
        thang_box.addItems((
            "Thangs:  Vanilla",
            "Thangs:  Restricted",
            "Thangs:  Anywhere"
        ))
        beatable_check = QCheckBox("First Weapon Vanilla", group)
        lava_check = QCheckBox("Enemy Ink Is Lava", group)
        cutscenes_check = QCheckBox("Skip Cutscenes", group)
        background_check = QCheckBox("Backgrounds", group)
        color_check = QCheckBox("Ink Color", group)
        music_check = QCheckBox("Music", group)
        hl = QHBoxLayout()
        hl.addWidget(weapon_check)
        hl.addSpacerItem(self.createHorizontalSpacer())
        hl.addWidget(level_check)
        hl.addSpacerItem(self.createHorizontalSpacer())
        hl.addWidget(thang_box)
        ovl = QVBoxLayout()
        ovl.addLayout(hl)
        hl = QHBoxLayout()
        hl.addWidget(beatable_check)
        hl.addSpacerItem(self.createHorizontalSpacer())
        hl.addWidget(lava_check)
        hl.addSpacerItem(self.createHorizontalSpacer())
        hl.addWidget(cutscenes_check)
        ovl.addLayout(hl)
        hl = QHBoxLayout()
        hl.addWidget(background_check)
        hl.addSpacerItem(self.createHorizontalSpacer())
        hl.addWidget(color_check)
        hl.addSpacerItem(self.createHorizontalSpacer())
        hl.addWidget(music_check)
        ovl.addLayout(hl)
        group.setLayout(ovl)
        vl.addWidget(group)

        region_box = QComboBox(widget)
        region_box.addItems((
            "Region:  EU",
            "Region:  JP",
            "Region:  US"
        ))
        platform_box = QComboBox(widget)
        platform_box.addItems((
            "Platform:  Console",
            "Platform:  Emulator"
        ))
        button = QPushButton("RANDOMIZE", widget)
        button.setFixedWidth(button.width() * 3 // 2) # floored multiplier of 1.5
        button.clicked.connect(window.randomize)
        hl = QHBoxLayout()
        hl.addWidget(region_box)
        hl.addWidget(platform_box)
        hl.addSpacerItem(self.createHorizontalSpacer())
        hl.addWidget(button)
        vl.addLayout(hl)

        widget.setLayout(vl)
        window.setCentralWidget(widget)

        # make settings all a consistent size
        for box in window.findChildren(QComboBox):
            box.setFixedWidth(150)
        for check in window.findChildren(QCheckBox):
            check.setFixedWidth(150)


    def createHorizontalSpacer(self) -> QSpacerItem:
        return QSpacerItem(1, 1, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)



class WorkWindow(QMainWindow):
    def __init__(self, parent, settings: dict) -> None:
        super(WorkWindow, self).__init__(parent)
        self.ui = Ui_WorkWindow()
        self.ui.setupUi(self)
        self.setWindowTitle(settings['Seed'])
        self.settings = settings
        self.done = False
        self.error = False
        self.cancel = False
        self.startWorkThread()


    def startWorkThread(self) -> None:
        self.work_thread = Metro_Process(self, self.settings)
        self.work_thread.is_done.connect(self.workDone)
        self.work_thread.error.connect(self.workError)
        self.work_thread.start()


    def workError(self, er_message: str) -> None:
        self.error = True
        with open(LOGS_PATH, 'w') as f:
            f.write(f"{self.windowTitle()}")
            f.write(f'\n\n{er_message}')
            f.write(f'\n\n{self.settings}')


    def workDone(self):
        if self.error:
            self.ui.label.setText("Something went wrong! Please report this to GitHub!")
            self.ui.progress.setVisible(False)
            self.done = True
            return
        
        if self.cancel:
            self.done = True
            self.close()
            return
        
        self.ui.label.setText("All done! Check the README for instructions on how to play!")
        self.ui.progress.setVisible(False)
        self.done = True


    # override the window close event to close the randomization thread
    def closeEvent(self, event):
        if self.done:
            event.accept()
        else:
            event.ignore()
            self.cancel = True
            self.ui.label.setText('Canceling...')
            self.work_thread.stop()



class Ui_WorkWindow(object):
    def setupUi(self, window: QMainWindow) -> None:
        self.label = QLabel("Randomizing...", window)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress = QProgressBar(window)
        self.progress.setMaximum(0)
        vl = QVBoxLayout()
        vl.addWidget(self.label)
        vl.addWidget(self.progress)
        window.setMinimumSize(448, 112)
        widget = QWidget(window)
        widget.setLayout(vl)
        window.setCentralWidget(widget)
