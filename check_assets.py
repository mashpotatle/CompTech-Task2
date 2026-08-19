import os
import sys

sys.path.insert(0, r"c:\Users\Mashe\CompTech-Task2")

import pygame

from TheTwilightZone.assets.player_model import create_player_sprite
from TheTwilightZone.assets.fish_model import create_fish_sprite
from TheTwilightZone.assets.med_kit_model import create_med_kit_sprite
from TheTwilightZone.assets.o2_tank_model import create_oxygen_tank_sprite
from TheTwilightZone.assets.silt_cloud_model import create_silt_cloud_sprite
from TheTwilightZone.assets.spiky_plant_model import create_spiky_plant_sprite
from TheTwilightZone.assets.thermal_vent_model import create_thermal_vent_sprite

sprites = [
    create_player_sprite(),
    create_fish_sprite(),
    create_med_kit_sprite(),
    create_oxygen_tank_sprite(),
    create_silt_cloud_sprite(),
    create_spiky_plant_sprite(),
    create_thermal_vent_sprite(),
]

print('pygame', pygame.__version__)
for idx, surface in enumerate(sprites, 1):
    print(idx, surface.get_size())
print('ASSET_CHECK_OK')
