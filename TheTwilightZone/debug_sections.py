import os
os.chdir('C:/Users/Mashe/CompTech-Task2/TheTwilightZone')
from levels.level_manager import LevelManager
from paths import CAVE_SECTIONS_DIR

lm = LevelManager(CAVE_SECTIONS_DIR, ['section_01.json'])
lm.load_initial_section('section_01.json')
for name in ['section_02.json','section_03.json','section_04.json','section_01.json']:
    inst = lm.stitch_next_section(name)
    print(name, '->', [e.element_type for e in inst.section.elements])
