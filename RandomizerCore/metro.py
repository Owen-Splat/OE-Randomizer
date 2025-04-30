from PySide6.QtCore import QThread, Signal
import RandomizerCore.Tools.zs_tools as zs_tools
import RandomizerCore.Tools.nisasyst as nisasyst
from randomizer_paths import DATA_PATH
import random, oead, yaml, traceback, shutil
from pathlib import Path

class Metro_Process(QThread):
    error = Signal(str)
    is_done = Signal()
    thread_active = True


    def __init__(self, parent, settings) -> None:
        QThread.__init__(self, parent)
        self.base_path = Path(settings['Base_Path'])
        self.dlc_path = Path(settings['DLC_Path'])
        self.root_out_path = Path(settings['Output_Path']) / str(settings['Seed'])
        self.seed = settings['Seed']
        del settings['Base_Path']
        del settings['DLC_Path']
        del settings['Output_Path']
        del settings['Seed']
        self.settings = settings

        # remove old files first if they exist
        if self.root_out_path.exists():
            shutil.rmtree(self.root_out_path)

        # now update the output path to match platform formatting
        # rainbow expansion looks like it uses both base game and oe romfs for console
        # just base game romfs worked for side order mods, so I will need to test on console to see if oe romfs is needed
        if settings['Platform'] == "Console":
            match settings['Region']:
                case 'EU':
                    title_id = "0100f8f0000a2000"
                case 'JP':
                    title_id = "01003c700009c000"
                case 'US':
                    title_id = "01003bc0000a0000"
            self.out_path = self.root_out_path / "atmosphere" / "contents" / title_id
            self.out_path = self.out_path / "romfs"
        else:
            self.out_path = self.root_out_path / "romfs"


    def run(self) -> None:
        """Automatically called when this thread is started"""

        try:
            self.makeMod()
        except Exception:
            er = traceback.format_exc()
            print(er)
            self.error.emit(er)
        finally: # regardless if there was an error or not, we want to tell the progress window that this thread has finished
            if not self.thread_active and self.root_out_path.exists():
                shutil.rmtree(self.root_out_path)
            self.is_done.emit()


    def stop(self):
        """Tells this thread to stop and skip over all remaining work. Files will also be deleted"""

        self.thread_active = False


    def makeMod(self):
        # set seed before we start any random generation
        random.seed(self.seed)

        # read data
        with open(self.base_path / 'Pack' / 'Mush.release.pack', 'rb') as f:
            sarc_data = zs_tools.SARC(data=f.read(), compressed=False)

        # read map info data
        info_file = 'Mush/Octa2DMapInfo.byml'
        container = nisasyst.NisasystContainer(info_file, bytes(sarc_data.writer.files[info_file]))
        map_data = zs_tools.BYAML(data=container.data, compressed=False)

        self.defineLevels(map_data)

        # edit data
        if self.settings['Weapons'] or self.settings['Levels'] or self.settings['Thangs']:
            self.editLevels(map_data)

        # write map info data
        container.data = bytes(map_data.repack())
        sarc_data.writer.files[info_file] = container.repack()

        # randomize music and ink color
        info_file = 'Mush/MapInfo.release.byml'
        map_data = zs_tools.BYAML(data=sarc_data.writer.files[info_file], compressed=False)
        self.randomizeAesthetics(map_data)
        sarc_data.writer.files[info_file] = map_data.repack()
        self.writeFile('Pack', 'Mush.release.pack', sarc_data.repack())

        self.editMapObjs()


    def defineLevels(self, map_data: zs_tools.BYAML) -> None:
        """Makes a list of map names and randomizes levels"""

        # grab valid level names from the map info data
        self.map_names = {map['UIID'].v: map['MapName'] for map in map_data.info
                    if map['UIID'].v < 84}
        if len(self.map_names) != 84:
            raise IndexError(f"Not enough maps found. Total found: {len(self.map_names)}")

        if not self.settings['Levels'] and not self.settings['Thangs']:
            return

        with open(DATA_PATH / 'StageList.yml', 'r') as f:
            stages: dict = yaml.safe_load(f)

        ids = list(range(80))

        # define empty lines
        lines = []
        for i in range(10):
            lines.append([])
        line_level_counts = [8, 15, 13, 9, 12, 8, 6, 6, 4, 3]

        # shuffle levels
        for i, line in enumerate(lines):
            while len(line) < line_level_counts[i] - 1: # leave an empty space in each line for the thangs
                if not self.settings['Thangs']:
                    i2 = len(line)
                    if stages[list(stages.keys())[i]][i2] in [80, 81, 82, 83]:
                        line.append(stages[list(stages.keys())[i]][i2])
                        continue
                new_id = random.choice(ids)
                line.append(new_id)
                ids.remove(new_id)

        # now select random lines for the thangs
        if self.settings['Thangs']:
            lines_with_thangs = []
            line_nums = list(range(10))
            for i in range(4):
                line_num = random.choice(line_nums)
                while line_num in lines_with_thangs:
                    line_num = random.choice(line_nums)
                lines_with_thangs.append(line_num)
                line_nums.remove(line_num)
            for i, line in enumerate(lines_with_thangs):
                thang = 80 + i
                if random.random() >= 0.5:
                    lines[line].append(thang)
                else:
                    lines[line].insert(0, thang)

        # finish shuffling levels
        for i, line in enumerate(lines):
            while len(line) < line_level_counts[i]:
                new_id = random.choice(ids)
                line.append(new_id)
                ids.remove(new_id)

        # now compare the vanilla and new lines to make a dictionary mapping of old and new IDs
        self.stages = {}
        for i, (k,v) in enumerate(stages.items()):
            for i2, id in enumerate(v):
                self.stages[id] = lines[i][i2]


    def editLevels(self, map_data: zs_tools.BYAML) -> None:
        """Randomizes weapons and level locations depending on user settings"""

        if not self.thread_active:
            return

        # get weapon data if needed
        if self.settings['Weapons']:
            with open(DATA_PATH / 'Weapons.yml', 'r') as f:
                weapons = yaml.safe_load(f)
            first_weapons = {}
            for map in map_data.info:
                if map['MapName'] in list(self.map_names.values()):
                    first_weapons[map['MapName']] = {'Main': map['MainA'], 'Sub': map['SubA']}

        self.maps_to_add_special = {}

        for map in map_data.info:
            if map['UIID'].v > 83:
                continue

            new_map = self.map_names[self.stages[map['UIID'].v]]
            map['MapName'] = new_map

            # save myself credits when testing lol
            map['Admission'] = oead.S32(0)

            if not self.settings['Weapons']:
                continue

            # check if new level is an infinite special level
            vspecial = first_weapons[new_map]['Main'] in ('Jetpack', 'AquaBall')
            if vspecial:
                map['MainA'] = first_weapons[new_map]['Main']
                map['SubA'] = '-'
                map['MainB'] = '-'
                map['SubB'] = '-'
                map['MainC'] = '-'
                map['SubC'] = '-'
                continue

            # 5% chance for a special per stage
            if random.randint(0, 19) == random.choice(list(range(20))):
                map['MainA'] = random.choice(('Jetpack', 'AquaBall'))
                map['SubA'] = '-'
                map['MainB'] = '-'
                map['SubB'] = '-'
                map['MainC'] = '-'
                map['SubB'] = '-'
                self.maps_to_add_special[new_map] = map['MainA']
                continue

            # if not a special level, make the first weapon vanilla and randomize the next 2
            no_dups = list(weapons['Main_Weapons']).copy()
            mainB = no_dups.pop(no_dups.index(random.choice(no_dups)))
            mainC = no_dups.pop(no_dups.index(random.choice(no_dups)))
            map['MainA'] = first_weapons[new_map]['Main']
            map['MainB'] = mainB
            map['MainC'] = mainC
            map['SubA'] = first_weapons[new_map]['Sub']
            map['SubB'] = random.choice(weapons['Sub_Weapons'])
            map['SubC'] = random.choice(weapons['Sub_Weapons'])
            if map['RewardB'] == oead.S32(0):
                map['RewardB'] = oead.S32(int(map['RewardA']) + 100)
            if map['RewardC'] == oead.S32(0):
                map['RewardC'] = oead.S32(int(map['RewardB']) + 200)


    def randomizeAesthetics(self, map_data) -> None:
        """Randomizes music and ink color depending on user settings"""

        musics = set()
        colors = set()
        for map in map_data.info:
            if 'BGMType' in map:
                musics.add(map['BGMType'])
            if 'FixTeamColor' in map:
                colors.add(map['FixTeamColor'])
        
        musics = list(musics)
        random.shuffle(musics)
        colors = list(colors)
        random.shuffle(colors)
        for map in map_data.info:
            map['BGMType'] = random.choice(musics)
            map['FixTeamColor'] = random.choice(colors)


    def editMapObjs(self) -> None:
        """Edits maps to add/remove stuff as necessary"""

        with open(self.base_path / 'Pack' / 'Map.pack', 'rb') as f:
            sarc_data = zs_tools.SARC(data=f.read(), compressed=False)

        for k,map in self.map_names.items():
            # read file & object list
            try:
                map_sarc_name = f"Map/{map}.szs"
                map_sarc = zs_tools.SARC(data=sarc_data.writer.files[map_sarc_name], compressed=True)
                info_file = f"{map}.byaml"
                map_data = zs_tools.BYAML(data=map_sarc.writer.files[info_file], compressed=False)
            except KeyError:
                print('Map object not found:', map)
                continue

            if self.settings['Enemy Ink Is Lava']:
                map_data.info['Objs'].append(self.makeSuddenDeathObj())
            if map in self.maps_to_add_special:
                map_data.info['Objs'].append(self.makeSpecialSetterObj(self.maps_to_add_special[map]))

            map_sarc.writer.files[info_file] = map_data.repack()
            sarc_data.writer.files[map_sarc_name] = map_sarc.repack()

        self.writeFile('Pack', 'Map.pack', sarc_data.repack())


    def makeSuddenDeathObj(self) -> dict:
        """Returns a new object to be added to maps that need the Enemy Ink Is Lava challenge"""

        obj = {}
        obj['Id'] = 'PatchSuddenDeath'
        obj['IsLinkDest'] = False
        obj['LayerConfigName'] = 'Cmn'
        obj['Links'] = {}
        obj['ModelName'] = None
        obj['Rotate'] = {'X': oead.F32(0.0), 'Y': oead.F32(0.0), 'Z': oead.F32(0.0)}
        obj['Scale'] = {'X': oead.F32(1.0), 'Y': oead.F32(1.0), 'Z': oead.F32(1.0)}
        obj['Team'] = oead.S32(2)
        obj['Translate'] = {'X': oead.F32(0.0), 'Y': oead.F32(0.0), 'Z': oead.F32(0.0)}
        obj['UnitConfigName'] = 'DamageSuddenDeathObjOcta'
        return obj


    def makeSpecialSetterObj(self, special: str) -> dict:
        """Returns a new object to be added to maps that need an infinite special modifier"""

        obj = {}
        obj['Id'] = 'PatchSpecialSetter'
        obj['IsLinkDest'] = False
        obj['LayerConfigName'] = 'Cmn'
        obj['Links'] = {}
        obj['ModelName'] = None
        obj['Rotate'] = {'X': oead.F32(0.0), 'Y': oead.F32(0.0), 'Z': oead.F32(0.0)}
        obj['Scale'] = {'X': oead.F32(1.0), 'Y': oead.F32(1.0), 'Z': oead.F32(1.0)}
        obj['Team'] = oead.S32(2)
        obj['Translate'] = {'X': oead.F32(0.0), 'Y': oead.F32(0.0), 'Z': oead.F32(0.0)}
        obj['Type'] = oead.S32(0 if special=='Jetpack' else 1)
        obj['UnitConfigName'] = 'AlwaysSpecialSetterOcta'
        return obj


    def writeFile(self, path: str, name: str, data: bytes):
        """ Creates parent folders and writes the file
        
        Parameters
        ----------
        path : str
            The path of the file, relative to the RomFS
        name : str
            The name of the file to write to
        data : bytes
            The raw data to write to the file
        """

        full_out_path = self.out_path / path
        full_out_path.mkdir(parents=True, exist_ok=True)
        with open(full_out_path / name, "wb") as f:
            f.write(data)
