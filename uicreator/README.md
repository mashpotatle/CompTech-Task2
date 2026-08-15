# The Twilight Zone — UI Creator

A small visual editor for laying out menu/HUD widgets with exact pixel
dimensions, instead of guessing coordinates by hand. It exports JSON that
the game loads directly via `TheTwilightZone/ui/layout.py`.

## Run

```bash
python uicreator/main.py
```

No extra dependencies — it only uses the standard library `tkinter`.

## Usage

- Drag on the empty canvas to create a new widget rectangle.
- Click a widget to select it; drag its corner handles to resize, or drag
  its body to move it.
- Use the right panel to rename it, set its `type` (`button`, `panel`,
  `label`, `toggle`, `slider`, `circle`), set display `text`, or type exact
  `X`/`Y`/`W`/`H` numbers, then click **Apply**.
- Set **Screen name** (e.g. `main_menu`) and click **Save** — this writes
  `TheTwilightZone/data/ui/<screen name>.json`.
- **Load...** re-opens an existing layout file by screen name.

The canvas is fixed at 1024x768 to match the game's window
(`SCREEN_WIDTH`/`SCREEN_HEIGHT` in `TheTwilightZone/settings.py`), so
whatever you see on the canvas is exactly what will render in-game.

## Using a layout in code

```python
from ui.layout import load_layout

layout = self.layout  # or load_layout("main_menu")
rect = layout.rect("btn_play", default=pygame.Rect(120, 220, 220, 54))
text = layout.get("btn_play", "text", "-> Play")
```

`MainMenu` in `ui/menus.py` already does this for its buttons and settings
panel as a working example — follow the same pattern for `PauseMenu`,
`EndlessRunConfirmation`, the HUD, and the death screen.
