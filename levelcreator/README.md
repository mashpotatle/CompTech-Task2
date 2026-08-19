# The Twilight Zone — New Level Creator

This is a replacement level editor for the existing `levelcreator/maker.py`.

## Run

From this folder:

```bash
pip install pygame
python main.py
```

## Features

- New/open/save cave sections
- Compatible with the current level JSON shape:
  - `format_version`
  - `id`
  - `name`
  - `width` / `height`
  - `entry`
  - `exit`
  - `elements`
- Polygon drawing for walls and obstacles
- Placement and selection of:
  - Fish spawns
  - Spiky plants
  - Thermal vents
  - Silt clouds
  - Currents
  - Items
  - Lore fragments
- Inspector for entity-specific properties
- Grid
- Zoom around mouse
- Middle-mouse panning
- Selection, deletion and rotation
- Undo / redo
- Level validation before saving
- Existing section JSON files can be opened

## Controls

- `1` Wall
- `2` Obstacle
- `3` Fish
- `4` Spiky Plant
- `5` Thermal Vent
- `6` Silt Cloud
- `7` Current
- `8` Item
- `9` Lore Fragment
- `E` Entry
- `X` Exit
- `Q` Select
- `Delete` Delete selected
- `R` Rotate selected
- `F` Fit level
- `Ctrl+S` Save
- `Ctrl+O` Open
- `Ctrl+N` New
- `Ctrl+Z` Undo
- `Ctrl+Y` Redo
- Mouse wheel Zoom
- Middle mouse Pan
- Left mouse Place / Select
- Right mouse Finish polygon
- Click an item's `item_type` property to cycle the supported pickup presets:
  `oxygen_tank` and `med_kit`

## Important

The editor deliberately keeps gameplay values in JSON properties. This means the game can tune entity behaviour without requiring the level editor to be rewritten.

The current game repository expects the level files under:

`TheTwilightZone/data/cave_sections/`

You can either save directly there by changing `DATA_DIR`, or copy the generated JSON files into that directory.


## Debugging / logging

The editor now writes detailed logs to:

`levelcreator/logs/level_creator.log`

The log records:
- editor startup
- tool changes
- entity placement
- selection/deletion
- undo/redo
- saves/loads
- validation failures
- exceptions with tracebacks

Useful shortcuts:
- `F4` = Save As / create a new JSON filename
- `Ctrl+N` = New unsaved level
- `Ctrl+S` = Save current level
- `Delete` = Delete selected element
- `Esc` = Cancel inspector editing / clear selection
