"""A tiny visual UI layout editor for The Twilight Zone.

Draw rectangles at exact pixel positions/sizes (matching the game's fixed
1024x768 window), name them, and save them as JSON to
`TheTwilightZone/data/ui/<screen>.json`. The game loads that JSON via
`ui.layout.load_layout()` so widget positions can be tuned visually instead
of guessing pixel numbers in code.

Run:
    python uicreator/main.py
"""

from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, simpledialog
from typing import Any

DATA_DIR = (Path(__file__).resolve().parents[1] / "TheTwilightZone" / "data" / "ui").resolve()

WIDGET_TYPES = ["button", "panel", "label", "toggle", "slider", "circle"]

GRID_STEP = 20
HANDLE_SIZE = 8


class Widget:
    def __init__(self, widget_id: str, kind: str, x: int, y: int, w: int, h: int, text: str = ""):
        self.id = widget_id
        self.type = kind
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.text = text

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "x": self.x,
            "y": self.y,
            "w": self.w,
            "h": self.h,
            "text": self.text,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Widget":
        return cls(
            data.get("id", "widget"),
            data.get("type", "button"),
            int(data.get("x", 0)),
            int(data.get("y", 0)),
            int(data.get("w", 100)),
            int(data.get("h", 40)),
            data.get("text", ""),
        )

    def handles(self) -> dict[str, tuple[int, int]]:
        return {
            "nw": (self.x, self.y),
            "ne": (self.x + self.w, self.y),
            "sw": (self.x, self.y + self.h),
            "se": (self.x + self.w, self.y + self.h),
        }

    def hit_handle(self, px: int, py: int) -> str | None:
        for name, (hx, hy) in self.handles().items():
            if abs(px - hx) <= HANDLE_SIZE and abs(py - hy) <= HANDLE_SIZE:
                return name
        return None

    def contains(self, px: int, py: int) -> bool:
        return self.x <= px <= self.x + self.w and self.y <= py <= self.y + self.h


class UICreatorApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("The Twilight Zone — UI Creator")

        self.reference_width = 1024
        self.reference_height = 768
        self.screen_name = "main_menu"
        self.widgets: list[Widget] = []
        self.selected: Widget | None = None
        self.next_id = 1

        self.drag_mode: str | None = None  # "create" | "move" | "resize"
        self.drag_handle: str | None = None
        self.drag_start = (0, 0)
        self.drag_origin = (0, 0, 0, 0)
        self.draft_start = (0, 0)

        self._build_ui()
        self._redraw()

    # ---------- UI construction ----------

    def _build_ui(self) -> None:
        toolbar = tk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        tk.Button(toolbar, text="New", command=self.new_layout).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Button(toolbar, text="Load...", command=self.load_layout_dialog).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Button(toolbar, text="Save", command=self.save_layout).pack(side=tk.LEFT, padx=2, pady=2)

        tk.Label(toolbar, text="Screen name:").pack(side=tk.LEFT, padx=(12, 2))
        self.screen_name_var = tk.StringVar(value=self.screen_name)
        tk.Entry(toolbar, textvariable=self.screen_name_var, width=16).pack(side=tk.LEFT)

        body = tk.Frame(self.root)
        body.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(
            body,
            width=self.reference_width,
            height=self.reference_height,
            bg="#0d1318",
            highlightthickness=1,
            highlightbackground="#3e4c56",
        )
        self.canvas.pack(side=tk.LEFT, padx=8, pady=8)
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.root.bind("<Delete>", self._on_delete_key)
        self.root.bind("<BackSpace>", self._on_delete_key)

        panel = tk.Frame(body, width=260)
        panel.pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=8)

        tk.Label(panel, text="Widgets").pack(anchor="w")
        self.listbox = tk.Listbox(panel, height=14)
        self.listbox.pack(fill=tk.X)
        self.listbox.bind("<<ListboxSelect>>", self._on_list_select)

        form = tk.Frame(panel)
        form.pack(fill=tk.X, pady=(12, 0))

        self.id_var = tk.StringVar()
        self.type_var = tk.StringVar(value=WIDGET_TYPES[0])
        self.text_var = tk.StringVar()
        self.x_var = tk.StringVar()
        self.y_var = tk.StringVar()
        self.w_var = tk.StringVar()
        self.h_var = tk.StringVar()

        self._labeled_entry(form, "ID", self.id_var, 0)
        self._labeled_option(form, "Type", self.type_var, WIDGET_TYPES, 1)
        self._labeled_entry(form, "Text", self.text_var, 2)
        self._labeled_entry(form, "X", self.x_var, 3)
        self._labeled_entry(form, "Y", self.y_var, 4)
        self._labeled_entry(form, "W", self.w_var, 5)
        self._labeled_entry(form, "H", self.h_var, 6)

        tk.Button(form, text="Apply", command=self._apply_fields).grid(row=7, column=0, pady=6)
        tk.Button(form, text="Delete", command=self._delete_selected).grid(row=7, column=1, pady=6)

        tk.Label(panel, text="Drag on the canvas to add a widget.\nDrag corners to resize, body to move.", justify="left", fg="#888").pack(
            anchor="w", pady=(12, 0)
        )

    def _labeled_entry(self, parent, label, var, row):
        tk.Label(parent, text=label).grid(row=row, column=0, sticky="w")
        tk.Entry(parent, textvariable=var, width=14).grid(row=row, column=1, sticky="w")

    def _labeled_option(self, parent, label, var, options, row):
        tk.Label(parent, text=label).grid(row=row, column=0, sticky="w")
        tk.OptionMenu(parent, var, *options).grid(row=row, column=1, sticky="w")

    # ---------- canvas rendering ----------

    def _redraw(self) -> None:
        self.canvas.delete("all")
        for gx in range(0, self.reference_width, GRID_STEP):
            color = "#2c3a44" if gx % (GRID_STEP * 5) == 0 else "#1a232a"
            self.canvas.create_line(gx, 0, gx, self.reference_height, fill=color)
        for gy in range(0, self.reference_height, GRID_STEP):
            color = "#2c3a44" if gy % (GRID_STEP * 5) == 0 else "#1a232a"
            self.canvas.create_line(0, gy, self.reference_width, gy, fill=color)

        for widget in self.widgets:
            self._draw_widget(widget)

        self._refresh_list()

    def _draw_widget(self, widget: Widget) -> None:
        selected = widget is self.selected
        outline = "#5ad1c4" if selected else "#c8c8c8"
        self.canvas.create_rectangle(
            widget.x, widget.y, widget.x + widget.w, widget.y + widget.h, outline=outline, width=2
        )
        label = f"{widget.id} ({widget.x},{widget.y} {widget.w}x{widget.h})"
        self.canvas.create_text(widget.x + 4, widget.y + 4, anchor="nw", fill=outline, text=label, font=("Segoe UI", 8))
        if widget.text:
            self.canvas.create_text(
                widget.x + widget.w / 2, widget.y + widget.h / 2, fill="#ffffff", text=widget.text, font=("Segoe UI", 10)
            )
        if selected:
            for hx, hy in widget.handles().values():
                self.canvas.create_rectangle(
                    hx - HANDLE_SIZE / 2, hy - HANDLE_SIZE / 2, hx + HANDLE_SIZE / 2, hy + HANDLE_SIZE / 2,
                    fill="#5ad1c4", outline="",
                )

    def _refresh_list(self) -> None:
        self.listbox.delete(0, tk.END)
        for widget in self.widgets:
            self.listbox.insert(tk.END, widget.id)
        if self.selected in self.widgets:
            self.listbox.selection_set(self.widgets.index(self.selected))
            self._fill_fields(self.selected)

    def _fill_fields(self, widget: Widget) -> None:
        self.id_var.set(widget.id)
        self.type_var.set(widget.type)
        self.text_var.set(widget.text)
        self.x_var.set(str(widget.x))
        self.y_var.set(str(widget.y))
        self.w_var.set(str(widget.w))
        self.h_var.set(str(widget.h))

    # ---------- mouse handling ----------

    def _widget_at(self, px: int, py: int) -> Widget | None:
        for widget in reversed(self.widgets):
            if widget.contains(px, py):
                return widget
        return None

    def _on_press(self, event) -> None:
        x, y = event.x, event.y
        if self.selected is not None:
            handle = self.selected.hit_handle(x, y)
            if handle:
                self.drag_mode = "resize"
                self.drag_handle = handle
                self.drag_start = (x, y)
                self.drag_origin = (self.selected.x, self.selected.y, self.selected.w, self.selected.h)
                return

        widget = self._widget_at(x, y)
        if widget is not None:
            self.selected = widget
            self.drag_mode = "move"
            self.drag_start = (x, y)
            self.drag_origin = (widget.x, widget.y, widget.w, widget.h)
            self._redraw()
            return

        self.selected = None
        self.drag_mode = "create"
        self.draft_start = (x, y)
        self._redraw()

    def _on_drag(self, event) -> None:
        x, y = event.x, event.y
        if self.drag_mode == "create":
            self._redraw()
            sx, sy = self.draft_start
            self.canvas.create_rectangle(sx, sy, x, y, outline="#f4b942", dash=(4, 2))
        elif self.drag_mode == "move" and self.selected is not None:
            dx = x - self.drag_start[0]
            dy = y - self.drag_start[1]
            ox, oy, ow, oh = self.drag_origin
            self.selected.x = max(0, ox + dx)
            self.selected.y = max(0, oy + dy)
            self._redraw()
        elif self.drag_mode == "resize" and self.selected is not None:
            self._apply_resize(x, y)
            self._redraw()

    def _apply_resize(self, x: int, y: int) -> None:
        ox, oy, ow, oh = self.drag_origin
        widget = self.selected
        if widget is None:
            return
        if "e" in self.drag_handle:
            widget.w = max(GRID_STEP, x - ox)
        if "s" in self.drag_handle:
            widget.h = max(GRID_STEP, y - oy)
        if "w" in self.drag_handle:
            new_x = min(x, ox + ow - GRID_STEP)
            widget.w = ox + ow - new_x
            widget.x = new_x
        if "n" in self.drag_handle:
            new_y = min(y, oy + oh - GRID_STEP)
            widget.h = oy + oh - new_y
            widget.y = new_y

    def _on_release(self, event) -> None:
        if self.drag_mode == "create":
            sx, sy = self.draft_start
            x, y = event.x, event.y
            x0, x1 = sorted((sx, x))
            y0, y1 = sorted((sy, y))
            if x1 - x0 >= GRID_STEP and y1 - y0 >= GRID_STEP:
                widget = Widget(f"widget_{self.next_id}", "button", x0, y0, x1 - x0, y1 - y0)
                self.next_id += 1
                self.widgets.append(widget)
                self.selected = widget
        self.drag_mode = None
        self.drag_handle = None
        self._redraw()

    def _on_delete_key(self, event) -> None:
        self._delete_selected()

    def _on_list_select(self, event) -> None:
        selection = self.listbox.curselection()
        if not selection:
            return
        self.selected = self.widgets[selection[0]]
        self._redraw()

    # ---------- properties panel ----------

    def _apply_fields(self) -> None:
        if self.selected is None:
            return
        try:
            new_id = self.id_var.get().strip() or self.selected.id
            self.selected.id = new_id
            self.selected.type = self.type_var.get()
            self.selected.text = self.text_var.get()
            self.selected.x = int(self.x_var.get())
            self.selected.y = int(self.y_var.get())
            self.selected.w = max(1, int(self.w_var.get()))
            self.selected.h = max(1, int(self.h_var.get()))
        except ValueError:
            messagebox.showerror("Invalid value", "X, Y, W and H must be whole numbers.")
            return
        self._redraw()

    def _delete_selected(self) -> None:
        if self.selected is None:
            return
        self.widgets.remove(self.selected)
        self.selected = None
        self._redraw()

    # ---------- file operations ----------

    def new_layout(self) -> None:
        if self.widgets and not messagebox.askyesno("New layout", "Discard current widgets?"):
            return
        self.widgets = []
        self.selected = None
        self.next_id = 1
        self._redraw()

    def save_layout(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        name = self.screen_name_var.get().strip() or "screen"
        path = DATA_DIR / f"{name}.json"
        data = {
            "screen": name,
            "reference_width": self.reference_width,
            "reference_height": self.reference_height,
            "widgets": [w.to_dict() for w in self.widgets],
        }
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
        messagebox.showinfo("Saved", f"Saved to {path}")

    def load_layout_dialog(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        name = simpledialog.askstring(
            "Load layout", "Screen name (file in data/ui/ without .json):", initialvalue=self.screen_name_var.get()
        )
        if not name:
            return
        path = DATA_DIR / f"{name}.json"
        if not path.exists():
            messagebox.showerror("Not found", f"No layout file at {path}")
            return
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        self.screen_name_var.set(name)
        self.reference_width = data.get("reference_width", 1024)
        self.reference_height = data.get("reference_height", 768)
        self.widgets = [Widget.from_dict(w) for w in data.get("widgets", [])]
        self.selected = None
        self.next_id = len(self.widgets) + 1
        self._redraw()


def main() -> None:
    root = tk.Tk()
    UICreatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
