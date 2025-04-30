from pathlib import Path
import appdirs, sys

if getattr(sys, "frozen", False):
    RUNNING_FROM_SOURCE = False
    ROOT_PATH = Path(sys.executable).parent
    if sys.platform == 'darwin': # mac
        userdata_path = Path(appdirs.user_data_dir('randomizer', 'Splatoon 3 Randomizer'))
        if not userdata_path.exists():
            userdata_path.mkdir(parents=True, exist_ok=True)
        SETTINGS_PATH = userdata_path / 'settings.txt'
        LOGS_PATH = userdata_path / 'log.txt'
    else:
        SETTINGS_PATH = Path('.') / 'settings.txt'
        LOGS_PATH = Path('.') / 'log.txt'
else:
    RUNNING_FROM_SOURCE = True
    ROOT_PATH = Path(sys.argv[0]).parent.absolute()
    SETTINGS_PATH = ROOT_PATH / 'settings.txt'
    LOGS_PATH = ROOT_PATH / 'log.txt'

DATA_PATH = ROOT_PATH / 'RandomizerCore' / 'Data'
RESOURCE_PATH = ROOT_PATH / 'RandomizerUI' / 'Resources'