from PySide6.QtCore import QThread, Signal
import RandomizerCore.Tools.zs_tools as zs_tools
import RandomizerCore.Tools.nisasyst as nisasyst
from randomizer_data import DATA_PATH
import random, oead, yaml, copy, traceback, shutil
from pathlib import Path

class Metro_Process(QThread):
    error = Signal(str)
    is_done = Signal()
    thread_active = True


    def __init__(self, parent, settings) -> None:
        QThread.__init__(self, parent)
        self.base_path = Path(settings['Base_Path'])
        self.dlc_path = Path(settings['DLC_Path'])
        self.out_path = Path(settings['Output_Path']) / str(settings['Seed'])
        self.seed = settings['Seed']
        del settings['Base_Path']
        del settings['DLC_Path']
        del settings['Output_Path']
        del settings['Seed']
        self.settings = settings

        # remove old files first if they exist
        if self.out_path.exists():
            shutil.rmtree(self.out_path)

        # now update the output path to match platform formatting
        if settings['Platform'] == "Console":
            rg = settings['Region']
            title_id = "" # different title ids for the different regions that I'm too lazy to look up right now :)
            self.out_path = self.out_path / "atmosphere" / "contents" / title_id
        self.out_path = self.out_path / "romfs"


    # automatically called when this thread is started
    def run(self) -> None:
        try:
            self.makeMod()
        except Exception:
            er = traceback.format_exc()
            print(er)
            self.error.emit(er)
        finally: # regardless if there was an error or not, we want to tell the progress window that this thread has finished
            self.is_done.emit()


    def makeMod(self):
        # set seed before we start any random generation
        random.seed(self.seed)

        # get weapon data
        with open(DATA_PATH / 'Weapons.yml', 'r') as f:
            weapons = yaml.safe_load(f)

        # read data
        with open(self.base_path / 'Pack' / 'Mush.release.pack', 'rb') as f:
            sarc_data = zs_tools.SARC(data=f.read(), compressed=False)

        # read map data
        info_file = 'Mush/Octa2DMapInfo.byml'
        container = nisasyst.NisasystContainer(info_file, bytes(sarc_data.writer.files[info_file]))
        map_data = zs_tools.BYAML(data=container.data, compressed=False)

        # edit data
        total_maps = [map['MapName'] for map in map_data.info
                    if map['MapName'].endswith('Msn') and
                    not map['MapName'].startswith((
                        'Fld_OctKey',
                        'Fld_OctBoss',
                        'Fld_OctShowdown',
                        'Fld_OctLastBoss',
                        'Fld_OctIntroduction'
                    ))]
        map_names = copy.deepcopy(total_maps)
        random.shuffle(map_names)

        maps_to_add_special = {}
        for map in map_data.info:
            # store the new map to swap this entry to after we use the vanilla data
            if map['MapName'] in total_maps:
                new_map = map_names.pop(0)

            # check if vanilla level is an infinite special level
            vspecial = False
            if map['MainA'] in ('Jetpack', 'AquaBall'):
                vspecial = True

            # edit weapons
            if random.randint(1, 12) == 7:
                map['MainA'] = random.choice(('Jetpack', 'AquaBall'))
                map['SubA'] = '-'
                map['MainB'] = '-'
                map['SubB'] = '-'
                map['MainC'] = '-'
                map['SubB'] = '-'
                special_num = 0 if map['MainA'] == 'Jetpack' else 1
                maps_to_add_special[new_map] = special_num
            else:
                if vspecial and map['MapName'] not in maps_to_add_special:
                    maps_to_add_special[map['MapName']] = -1
                no_dups = copy.deepcopy(weapons['Main_Weapons'])
                mainA = no_dups.pop(random.randrange(0, len(no_dups)))
                mainB = no_dups.pop(random.randrange(0, len(no_dups)))
                mainC = no_dups.pop(random.randrange(0, len(no_dups)))
                map['MainA'] = mainA
                map['MainB'] = mainB
                map['MainC'] = mainC
                map['SubA'] = random.choice(weapons['Sub_Weapons'])
                map['SubB'] = random.choice(weapons['Sub_Weapons'])
                map['SubC'] = random.choice(weapons['Sub_Weapons'])
                if map['RewardB'] == oead.S32(0):
                    map['RewardB'] = oead.S32(int(map['RewardA']) + 100)
                if map['RewardC'] == oead.S32(0):
                    map['RewardC'] = oead.S32(int(map['RewardB']) + 200)

            # save myself credits when testing lol
            map['Admission'] = oead.S32(0)

            # now change the map
            if map['MapName'] in total_maps:
                map['MapName'] = new_map

        # write map data
        container.data = bytes(map_data.repack())
        sarc_data.writer.files[info_file] = container.repack()

        # randomize music and ink color
        info_file = 'Mush/MapInfo.release.byml'
        map_data = zs_tools.BYAML(data=sarc_data.writer.files[info_file], compressed=False)
        self.randomizeAesthetics(map_data)
        sarc_data.writer.files[info_file] = map_data.repack()
        self.writeFile('Pack', 'Mush.release.pack', sarc_data.repack())

        # now we need to edit the object list for the maps that need an actor to activate specials
        for map, special_num in maps_to_add_special.items():
            # read file & object list
            try:
                with open(self.dlc_path / "Map" / f"{map}.szs", 'rb') as f:
                    sarc_data = zs_tools.SARC(data=f.read(), compressed=True)
                info_file = f"{map}.byaml"
                map_data = zs_tools.BYAML(data=sarc_data.writer.files[info_file], compressed=False)
                print(map)
            except FileNotFoundError:
                print('Map object for special not found:', map)
                continue

            # edit object list
            copied_actor = None
            special_setter = -1
            for i, obj in enumerate(map_data.info['Objs']):
                if obj['UnitConfigName'] == 'AlwaysSpecialSetterOcta':
                    copied_actor = dict(obj)
                    special_setter = i
                    break
                if obj['UnitConfigName'] == 'Obj_CheckPointFirstOcta':
                    copied_actor = dict(obj)
                elif obj['UnitConfigName'] == 'Obj_SupplyPointOcta' and copied_actor == None:
                    copied_actor = dict(obj)
            if copied_actor == None: # This means it's a thang or a level we will keep vanilla later anyway
                print('no first checkpoint or weapon supplier', map)
                continue
            if special_setter > -1:
                del map_data.info['Objs'][special_setter]
            if special_num > -1:
                special_obj = {}
                special_obj['Id'] = 'PatchSpecialSetter'
                special_obj['IsLinkDest'] = False
                special_obj['LayerConfigName'] = 'Cmn'
                special_obj['Links'] = {}
                special_obj['ModelName'] = None
                special_obj['Rotate'] = {'X': oead.F32(0.0), 'Y': oead.F32(0.0), 'Z': oead.F32(0.0)}
                special_obj['Scale'] = {'X': oead.F32(1.0), 'Y': oead.F32(1.0), 'Z': oead.F32(1.0)}
                special_obj['Team'] = oead.S32(2)
                special_obj['Translate'] = {'X': oead.F32(0.0), 'Y': oead.F32(0.0), 'Z': oead.F32(0.0)}
                special_obj['Type'] = oead.S32(special_num) # 0=JetPack, 1=Baller, 2=Baller, 3+=None
                special_obj['UnitConfigName'] = 'AlwaysSpecialSetterOcta'
                map_data.info['Objs'].insert(0, special_obj) # add the new object to the obj list

            # write everything
            sarc_data.writer.files[info_file] = map_data.repack()
            self.writeFile('Map', f'{map}.szs', sarc_data.repack())


    def randomizeAesthetics(self, map_data):
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


    # STOP THREAD
    def stop(self):
        self.thread_active = False
