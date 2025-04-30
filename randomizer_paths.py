from pathlib import Path
import appdirs
import platform

try:
    from sys import _MEIPASS
    ROOT_PATH = Path(_MEIPASS)
    RUNNING_FROM_SOURCE = False
    if platform.system() == 'Darwin': # mac
        userdata_path = Path(appdirs.user_data_dir('randomizer', 'Splatoon 3 Randomizer'))
        if not userdata_path.exists():
            userdata_path.mkdir(parents=True, exist_ok=True)
        SETTINGS_PATH = userdata_path / 'settings.txt'
        LOGS_PATH = userdata_path / 'log.txt'
    else:
        SETTINGS_PATH = ROOT_PATH / 'settings.txt'
        LOGS_PATH = ROOT_PATH / 'log.txt'
except ImportError:
    RUNNING_FROM_SOURCE = True
    ROOT_PATH = Path(__file__).parent.absolute()
    SETTINGS_PATH = ROOT_PATH / 'settings.txt'
    LOGS_PATH = ROOT_PATH / 'log.txt'

DATA_PATH = ROOT_PATH / 'RandomizerCore' / 'Data'
RESOURCE_PATH = ROOT_PATH / 'RandomizerUI' / 'Resources'
