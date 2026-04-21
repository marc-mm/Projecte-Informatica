import tkinter as tk
from collections import Counter
from dataclasses import dataclass
import os
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog

import matplotlib.pyplot as plt
from PIL import Image, ImageTk

import airport


@dataclass
class ArrivalFlight:
    flight_id: str
    company: str
    origin_airport: str
    expected_time: str

    @property
    def hour(self):
        try:
            return int(self.expected_time.split(":")[0])
        except (IndexError, ValueError):
            return None


class AirportInterface:
    def __init__(self, root):
        self.root = root
        self.base_dir = Path(__file__).resolve().parent
        self.airport_list = []
        self.arrival_list = []
        self.logo_photo = None
        self.header_canvas = None
        self.scroll_canvas = None
        self.scroll_window_id = None
        self.home_airport_code = self._load_home_airport_code()

        self.colors = {
            "background": "#dff5ff",
            "hero": "#eefcff",
            "surface": "#fbfeff",
            "surface_alt": "#f2fbff",
            "text": "#14324f",
            "muted": "#56748f",
            "border": "#a7d7ef",
            "airport_fill": "#dff3ff",
            "airport_outline": "#7cc7ed",
            "airport_hover": "#ccecff",
            "arrival_fill": "#ebfff5",
            "arrival_outline": "#7dd9ad",
            "arrival_hover": "#d8faea",
            "gold_fill": "#fff9de",
            "gold_outline": "#ebcf73",
            "gold_hover": "#fff1b8",
            "console": "#fcfeff",
        }

        self.airports_status = tk.StringVar(value="Airports loaded: 0")
        self.arrivals_status = tk.StringVar(value="Arrivals loaded: 0")
        self.console_status = tk.StringVar(
            value="Load airports or arrivals to start exploring the data."
        )

        self.root.title("Airport Management System")
        self.root.geometry("1320x860")
        self.root.minsize(1120, 620)
        self.root.configure(bg=self.colors["background"])
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

        self._build_interface()
        self._set_console_text(
            "Airport Management System ready.\n"
            "Use the airport and arrival tiles to load files, inspect data and open plots."
        )

    def _build_interface(self):
        viewport = tk.Frame(self.root, bg=self.colors["background"])
        viewport.grid(row=0, column=0, sticky="nsew")
        viewport.rowconfigure(0, weight=1)
        viewport.columnconfigure(0, weight=1)

        self.scroll_canvas = tk.Canvas(
            viewport,
            bg=self.colors["background"],
            highlightthickness=0,
            bd=0,
        )
        self.scroll_canvas.grid(row=0, column=0, sticky="nsew")

        main_scrollbar = tk.Scrollbar(viewport, orient="vertical", command=self.scroll_canvas.yview)
        main_scrollbar.grid(row=0, column=1, sticky="ns")
        self.scroll_canvas.configure(yscrollcommand=main_scrollbar.set)

        main = tk.Frame(self.scroll_canvas, bg=self.colors["background"], padx=24, pady=24)
        self.scroll_window_id = self.scroll_canvas.create_window((0, 0), window=main, anchor="nw")
        main.bind("<Configure>", self._update_scroll_region)
        self.scroll_canvas.bind("<Configure>", self._resize_scrollable_content)
        self._bind_main_scroll()

        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(3, weight=1)

        self.header_canvas = tk.Canvas(
            main,
            bg=self.colors["background"],
            highlightthickness=0,
            height=170,
        )
        self.header_canvas.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        self.header_canvas.bind("<Configure>", self._render_header)

        status_frame = tk.Frame(main, bg=self.colors["background"])
        status_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 18))
        status_frame.columnconfigure(0, weight=1)
        status_frame.columnconfigure(1, weight=1)
        status_frame.columnconfigure(2, weight=1)

        self._create_status_card(
            status_frame,
            0,
            "Airport dataset",
            self.airports_status,
            self.colors["airport_fill"],
        )
        self._create_status_card(
            status_frame,
            1,
            "Arrival dataset",
            self.arrivals_status,
            self.colors["arrival_fill"],
        )
        self._create_status_card(
            status_frame,
            2,
            "Session",
            self.console_status,
            self.colors["gold_fill"],
        )

        airport_panel = self._create_section_panel(
            main,
            row=2,
            column=0,
            title="Airport tools",
            subtitle="Load, edit and visualize airport information without touching the data module.",
        )
        arrival_panel = self._create_section_panel(
            main,
            row=2,
            column=1,
            title="Arrival tools",
            subtitle="Inspect incoming flights with quick filters and visual summaries.",
        )

        airport_tiles = tk.Frame(airport_panel, bg=self.colors["surface"])
        airport_tiles.pack(fill="both", expand=True)
        airport_tiles.columnconfigure(0, weight=1)
        airport_tiles.columnconfigure(1, weight=1)

        arrival_tiles = tk.Frame(arrival_panel, bg=self.colors["surface"])
        arrival_tiles.pack(fill="both", expand=True)
        arrival_tiles.columnconfigure(0, weight=1)
        arrival_tiles.columnconfigure(1, weight=1)

        self._create_tile(
            airport_tiles,
            0,
            0,
            "Load airports",
            "Import airport coordinates from a text file.",
            self.load_airports,
            self.colors["airport_fill"],
            self.colors["airport_outline"],
            self.colors["airport_hover"],
        )
        self._create_tile(
            airport_tiles,
            0,
            1,
            "Show airports",
            "Open the loaded airport list in a separate window.",
            self.show_airports,
            self.colors["airport_fill"],
            self.colors["airport_outline"],
            self.colors["airport_hover"],
        )
        self._create_tile(
            airport_tiles,
            1,
            0,
            "Set Schengen",
            "Compute the Schengen flag for every loaded airport.",
            self.set_schengen,
            self.colors["airport_fill"],
            self.colors["airport_outline"],
            self.colors["airport_hover"],
        )
        self._create_tile(
            airport_tiles,
            1,
            1,
            "Add airport",
            "Insert a new airport by code and coordinates.",
            self.add_airport,
            self.colors["gold_fill"],
            self.colors["gold_outline"],
            self.colors["gold_hover"],
        )
        self._create_tile(
            airport_tiles,
            2,
            0,
            "Delete airport",
            "Remove an airport by ICAO code from the current list.",
            self.delete_airport,
            self.colors["gold_fill"],
            self.colors["gold_outline"],
            self.colors["gold_hover"],
        )
        self._create_tile(
            airport_tiles,
            2,
            1,
            "Save Schengen",
            "Export only the Schengen airports to a text file.",
            self.save_schengen,
            self.colors["gold_fill"],
            self.colors["gold_outline"],
            self.colors["gold_hover"],
        )
        self._create_tile(
            airport_tiles,
            3,
            0,
            "Plot Schengen split",
            "Open a bar chart with Schengen and non-Schengen counts.",
            self.plot_airports,
            self.colors["arrival_fill"],
            self.colors["arrival_outline"],
            self.colors["arrival_hover"],
        )
        self._create_tile(
            airport_tiles,
            3,
            1,
            "Show map",
            "Open Google Earth with airports and an optional arrival route.",
            self.show_map,
            self.colors["arrival_fill"],
            self.colors["arrival_outline"],
            self.colors["arrival_hover"],
        )

        self._create_tile(
            arrival_tiles,
            0,
            0,
            "Load arrivals",
            "Import arrival flights from a text file such as Arrivals.txt.",
            self.load_arrivals,
            self.colors["arrival_fill"],
            self.colors["arrival_outline"],
            self.colors["arrival_hover"],
        )
        self._create_tile(
            arrival_tiles,
            0,
            1,
            "Show arrivals",
            "Open the arrival list in a separate window.",
            self.show_arrivals,
            self.colors["arrival_fill"],
            self.colors["arrival_outline"],
            self.colors["arrival_hover"],
        )
        self._create_tile(
            arrival_tiles,
            1,
            0,
            "Plot by company",
            "Bar chart of arrivals grouped by airline company.",
            self.plot_arrivals_by_company,
            self.colors["airport_fill"],
            self.colors["airport_outline"],
            self.colors["airport_hover"],
        )
        self._create_tile(
            arrival_tiles,
            1,
            1,
            "Plot by origin",
            "Horizontal ranking of the busiest origin airports.",
            self.plot_arrivals_by_origin,
            self.colors["airport_fill"],
            self.colors["airport_outline"],
            self.colors["airport_hover"],
        )
        self._create_tile(
            arrival_tiles,
            2,
            0,
            "Hourly flow",
            "Line chart of expected arrivals by landing hour.",
            self.plot_arrivals_by_hour,
            self.colors["gold_fill"],
            self.colors["gold_outline"],
            self.colors["gold_hover"],
        )
        self._create_tile(
            arrival_tiles,
            2,
            1,
            "Load bundled files",
            "Quick load Airports.txt and Arrivals.txt from this project folder.",
            self.load_project_files,
            self.colors["gold_fill"],
            self.colors["gold_outline"],
            self.colors["gold_hover"],
        )

        console_panel = tk.Frame(
            main,
            bg=self.colors["surface"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            bd=0,
            padx=18,
            pady=18,
        )
        console_panel.grid(row=3, column=0, columnspan=2, sticky="nsew")
        console_panel.columnconfigure(0, weight=1)
        console_panel.rowconfigure(1, weight=1)

        console_header = tk.Frame(console_panel, bg=self.colors["surface"])
        console_header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        console_header.columnconfigure(0, weight=1)

        tk.Label(
            console_header,
            text="Activity log",
            font=("Trebuchet MS", 15, "bold"),
            fg=self.colors["text"],
            bg=self.colors["surface"],
        ).grid(row=0, column=0, sticky="w")

        tk.Label(
            console_header,
            text="Recent actions and export summaries appear here.",
            font=("Trebuchet MS", 10),
            fg=self.colors["muted"],
            bg=self.colors["surface"],
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))

        text_frame = tk.Frame(
            console_panel,
            bg=self.colors["surface_alt"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            bd=0,
        )
        text_frame.grid(row=1, column=0, sticky="nsew")
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)

        self.text_box = tk.Text(
            text_frame,
            height=20,
            width=120,
            wrap="none",
            bg=self.colors["console"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
            font=("Consolas", 10),
            relief="flat",
            padx=12,
            pady=12,
        )
        self.text_box.grid(row=0, column=0, sticky="nsew")

        y_scroll = tk.Scrollbar(text_frame, command=self.text_box.yview)
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll = tk.Scrollbar(text_frame, orient="horizontal", command=self.text_box.xview)
        x_scroll.grid(row=1, column=0, sticky="ew")
        self.text_box.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

    def _update_scroll_region(self, _event=None):
        if self.scroll_canvas is None:
            return
        self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))

    def _resize_scrollable_content(self, event):
        if self.scroll_canvas is None or self.scroll_window_id is None:
            return
        self.scroll_canvas.itemconfigure(self.scroll_window_id, width=event.width)

    def _bind_main_scroll(self):
        self.root.bind_all("<MouseWheel>", self._on_main_mousewheel, add="+")
        self.root.bind_all("<Button-4>", self._on_main_mousewheel_linux, add="+")
        self.root.bind_all("<Button-5>", self._on_main_mousewheel_linux, add="+")

    def _event_is_from_main_window(self, event):
        try:
            return event.widget.winfo_toplevel() == self.root
        except Exception:
            return False

    def _on_main_mousewheel(self, event):
        if self.scroll_canvas is None or not self._event_is_from_main_window(event):
            return
        if isinstance(event.widget, tk.Text):
            return

        delta_units = int(-event.delta / 120)
        if delta_units == 0 and event.delta:
            delta_units = -1 if event.delta > 0 else 1
        if delta_units:
            self.scroll_canvas.yview_scroll(delta_units, "units")

    def _on_main_mousewheel_linux(self, event):
        if self.scroll_canvas is None or not self._event_is_from_main_window(event):
            return
        if isinstance(event.widget, tk.Text):
            return

        if event.num == 4:
            self.scroll_canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.scroll_canvas.yview_scroll(1, "units")

    def _render_header(self, event=None):
        if not self.header_canvas:
            return

        canvas = self.header_canvas
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        if width <= 1 or height <= 1:
            return

        canvas.delete("all")
        self._draw_rounded_rectangle(
            canvas,
            8,
            8,
            width - 8,
            height - 8,
            34,
            fill=self.colors["hero"],
            outline=self.colors["border"],
            border_width=2,
        )

        if self.logo_photo is None:
            self._load_logo()

        if self.logo_photo is not None:
            canvas.create_image(92, height // 2, image=self.logo_photo)

        canvas.create_text(
            190,
            58,
            anchor="w",
            text="AIRPORT MANAGEMENT SYSTEM",
            fill=self.colors["text"],
            font=("Trebuchet MS", 24, "bold"),
        )
        canvas.create_text(
            190,
            94,
            anchor="w",
            text="Airports, arrivals and visual insights in one streamlined interface.",
            fill=self.colors["muted"],
            font=("Trebuchet MS", 12),
        )
        canvas.create_text(
            190,
            126,
            anchor="w",
            text="Rounded action tiles, built-in file loading and quick plotting tools.",
            fill=self.colors["muted"],
            font=("Trebuchet MS", 11),
        )

    def _load_logo(self):
        for logo_name in ("eetac.png", "eetac_logo_bgless.png"):
            logo_path = self.base_dir / logo_name
            if not logo_path.exists():
                continue
            try:
                logo_image = Image.open(logo_path)
                logo_image = logo_image.resize((132, 72), Image.Resampling.LANCZOS)
                self.logo_photo = ImageTk.PhotoImage(logo_image)
                return
            except Exception:
                self.logo_photo = None
        self.logo_photo = None

    def _load_home_airport_code(self):
        terminals_path = self.base_dir / "Terminals.txt"
        try:
            with open(terminals_path, "r", encoding="utf-8") as file:
                first_line = file.readline().strip()
                if first_line:
                    return first_line.split()[0].upper()
        except Exception:
            pass
        return "LEBL"

    def _create_status_card(self, parent, column, title, variable, bg_color):
        card = tk.Frame(
            parent,
            bg=bg_color,
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            bd=0,
            padx=16,
            pady=14,
        )
        card.grid(row=0, column=column, sticky="ew", padx=6)
        tk.Label(
            card,
            text=title,
            font=("Trebuchet MS", 10, "bold"),
            bg=bg_color,
            fg=self.colors["muted"],
        ).pack(anchor="w")
        tk.Label(
            card,
            textvariable=variable,
            font=("Trebuchet MS", 12, "bold"),
            bg=bg_color,
            fg=self.colors["text"],
            wraplength=260,
            justify="left",
        ).pack(anchor="w", pady=(6, 0))

    def _create_section_panel(self, parent, row, column, title, subtitle):
        panel = tk.Frame(
            parent,
            bg=self.colors["surface"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            bd=0,
            padx=18,
            pady=18,
        )
        panel.grid(row=row, column=column, sticky="nsew", padx=6, pady=(0, 18))
        panel.columnconfigure(0, weight=1)

        tk.Label(
            panel,
            text=title,
            font=("Trebuchet MS", 16, "bold"),
            fg=self.colors["text"],
            bg=self.colors["surface"],
        ).pack(anchor="w")
        tk.Label(
            panel,
            text=subtitle,
            font=("Trebuchet MS", 10),
            fg=self.colors["muted"],
            bg=self.colors["surface"],
            wraplength=470,
            justify="left",
        ).pack(anchor="w", pady=(4, 14))

        return panel

    def _create_tile(self, parent, row, column, title, subtitle, command, fill, outline, hover_fill):
        tile = tk.Canvas(
            parent,
            bg=self.colors["surface"],
            width=245,
            height=100,
            highlightthickness=0,
            bd=0,
            relief="flat",
            cursor="hand2",
        )
        tile.grid(row=row, column=column, padx=8, pady=8, sticky="nsew")
        tile.bind("<Configure>", lambda event: self._draw_tile(tile, title, subtitle, fill, outline))

        def handle_enter(_event):
            tile.configure(bg=self.colors["surface"])
            self._draw_tile(tile, title, subtitle, hover_fill, outline)

        def handle_leave(_event):
            tile.configure(bg=self.colors["surface"])
            self._draw_tile(tile, title, subtitle, fill, outline)

        for sequence in ("<Button-1>", "<Return>", "<space>"):
            tile.bind(sequence, lambda _event: command())

        tile.bind("<Enter>", handle_enter)
        tile.bind("<Leave>", handle_leave)

    def _draw_tile(self, tile, title, subtitle, fill, outline):
        width = tile.winfo_width()
        height = tile.winfo_height()
        if width <= 1 or height <= 1:
            return

        tile.delete("all")
        self._draw_rounded_rectangle(
            tile,
            5,
            5,
            width - 5,
            height - 5,
            26,
            fill=fill,
            outline=outline,
            border_width=1.5,
        )
        tile.create_oval(width - 64, 18, width - 28, 54, fill="#ffffff", outline="")
        tile.create_text(
            22,
            28,
            anchor="w",
            text=title,
            fill=self.colors["text"],
            font=("Trebuchet MS", 12, "bold"),
        )
        tile.create_text(
            22,
            56,
            anchor="w",
            text=subtitle,
            fill=self.colors["muted"],
            font=("Trebuchet MS", 9),
            width=width - 95,
        )
        tile.create_text(
            width - 46,
            36,
            text=">",
            fill=self.colors["text"],
            font=("Trebuchet MS", 16, "bold"),
        )

    def _draw_rounded_rectangle(
        self,
        canvas,
        x1,
        y1,
        x2,
        y2,
        radius,
        fill,
        outline,
        border_width=1,
    ):
        points = [
            x1 + radius,
            y1,
            x2 - radius,
            y1,
            x2,
            y1,
            x2,
            y1 + radius,
            x2,
            y2 - radius,
            x2,
            y2,
            x2 - radius,
            y2,
            x1 + radius,
            y2,
            x1,
            y2,
            x1,
            y2 - radius,
            x1,
            y1 + radius,
            x1,
            y1,
        ]
        return canvas.create_polygon(
            points,
            smooth=True,
            fill=fill,
            outline=outline,
            width=border_width,
        )

    def _set_console_text(self, message):
        self.text_box.delete("1.0", tk.END)
        self.text_box.insert(tk.END, message)

    def write_console(self, message):
        self._set_console_text(message)

    def _open_text_window(self, title, subtitle, content):
        window = tk.Toplevel(self.root)
        window.title(title)
        window.geometry("980x680")
        window.minsize(780, 520)
        window.configure(bg=self.colors["background"])
        window.transient(self.root)

        container = tk.Frame(window, bg=self.colors["background"])
        container.pack(fill="both", expand=True, padx=20, pady=20)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(1, weight=1)

        header = tk.Frame(
            container,
            bg=self.colors["surface"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            bd=0,
            padx=18,
            pady=16,
        )
        header.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        tk.Label(
            header,
            text=title,
            font=("Trebuchet MS", 16, "bold"),
            bg=self.colors["surface"],
            fg=self.colors["text"],
        ).pack(anchor="w")
        tk.Label(
            header,
            text=subtitle,
            font=("Trebuchet MS", 10),
            bg=self.colors["surface"],
            fg=self.colors["muted"],
        ).pack(anchor="w", pady=(4, 0))

        body = tk.Frame(
            container,
            bg=self.colors["surface"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            bd=0,
        )
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(0, weight=1)
        body.rowconfigure(0, weight=1)

        text_widget = tk.Text(
            body,
            wrap="none",
            bg=self.colors["console"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
            font=("Consolas", 10),
            relief="flat",
            padx=14,
            pady=14,
        )
        text_widget.grid(row=0, column=0, sticky="nsew")

        y_scroll = tk.Scrollbar(body, command=text_widget.yview)
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll = tk.Scrollbar(body, orient="horizontal", command=text_widget.xview)
        x_scroll.grid(row=1, column=0, sticky="ew")
        text_widget.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        text_widget.insert("1.0", content)
        text_widget.configure(state="disabled")

    def _update_status_labels(self):
        self.airports_status.set(f"Airports loaded: {len(self.airport_list)}")
        self.arrivals_status.set(f"Arrivals loaded: {len(self.arrival_list)}")

    def _require_airports(self):
        if self.airport_list:
            return True
        messagebox.showwarning("No airport data", "Please load airport data first.")
        return False

    def _require_arrivals(self):
        if self.arrival_list:
            return True
        messagebox.showwarning("No arrival data", "Please load arrival data first.")
        return False

    def _airport_lookup(self, include_project_airports=False):
        lookup = {item.code.upper(): item for item in self.airport_list}
        if include_project_airports:
            bundled_airports_path = self.base_dir / "Airports.txt"
            if bundled_airports_path.exists():
                try:
                    for item in airport.LoadAirports(str(bundled_airports_path)):
                        lookup.setdefault(item.code.upper(), item)
                except Exception:
                    pass
        return lookup

    def _format_airport_rows(self):
        lines = [
            f"{'CODE':<8}{'LATITUDE':<16}{'LONGITUDE':<16}{'SCHENGEN':<12}",
            "-" * 52,
        ]
        for aero in self.airport_list:
            schengen_state = airport.IsSchengenAirport(aero.code)
            lines.append(
                f"{aero.code:<8}{aero.latitude:<16.6f}{aero.longitude:<16.6f}{str(schengen_state):<12}"
            )
        return "\n".join(lines)

    def _format_arrival_rows(self):
        lines = [
            f"{'ID':<12}{'COMPANY':<14}{'ORIGIN':<12}{'ETA':<8}",
            "-" * 46,
        ]
        for arrival in self.arrival_list:
            lines.append(
                f"{arrival.flight_id:<12}{arrival.company:<14}{arrival.origin_airport:<12}{arrival.expected_time:<8}"
            )
        return "\n".join(lines)

    def _load_arrivals_from_file(self, filepath):
        arrivals = []
        with open(filepath, "r", encoding="utf-8") as file:
            for index, line in enumerate(file):
                if index == 0 or not line.strip():
                    continue
                parts = line.split()
                if len(parts) < 4:
                    raise ValueError(f"Invalid arrival row: {line.strip()}")
                flight_id = parts[0]
                origin_airport = parts[1]
                expected_time = parts[2]
                company = " ".join(parts[3:])
                arrivals.append(
                    ArrivalFlight(
                        flight_id=flight_id,
                        company=company,
                        origin_airport=origin_airport,
                        expected_time=expected_time,
                    )
                )
        return arrivals

    def load_project_files(self):
        try:
            airports_path = self.base_dir / "Airports.txt"
            arrivals_path = self.base_dir / "Arrivals.txt"

            if airports_path.exists():
                self.airport_list = airport.LoadAirports(str(airports_path))
            if arrivals_path.exists():
                self.arrival_list = self._load_arrivals_from_file(arrivals_path)

            self._update_status_labels()
            self.console_status.set("Bundled project files loaded.")
            self._set_console_text(
                "Bundled files loaded from the project folder.\n"
                f"Airports: {len(self.airport_list)}\n"
                f"Arrivals: {len(self.arrival_list)}"
            )
        except Exception as exc:
            messagebox.showerror("Load error", f"Could not load bundled files.\nDetails: {exc}")

    def load_airports(self):
        try:
            filepath = filedialog.askopenfilename(
                title="Select airports file",
                initialdir=self.base_dir,
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            )
            if not filepath:
                return

            self.airport_list = airport.LoadAirports(filepath)
            self._update_status_labels()
            self.console_status.set("Airport dataset loaded successfully.")
            self._set_console_text(f"Successfully loaded {len(self.airport_list)} airports from:\n{filepath}")
            messagebox.showinfo("Success", "Airports loaded successfully.")
        except Exception as exc:
            messagebox.showerror("Load error", f"Could not load airport file.\nDetails: {exc}")

    def show_airports(self):
        if not self._require_airports():
            return

        content = self._format_airport_rows()
        self.console_status.set("Airport list opened in a separate window.")
        self._set_console_text(
            f"Opened airport list window.\nRows displayed: {len(self.airport_list)}"
        )
        self._open_text_window(
            "Loaded airports",
            "Current airport dataset with coordinates and Schengen classification.",
            content,
        )

    def show_data(self):
        self.show_airports()

    def set_schengen(self):
        if not self._require_airports():
            return

        try:
            for aero in self.airport_list:
                airport.SetSchengen(aero)
            schengen_count = sum(1 for aero in self.airport_list if aero.Schengen)
            self.console_status.set("Schengen flags updated.")
            self._set_console_text(
                "Schengen attributes updated for the loaded airport dataset.\n"
                f"Schengen airports: {schengen_count}\n"
                f"Non-Schengen airports: {len(self.airport_list) - schengen_count}"
            )
            messagebox.showinfo("Success", "Schengen attributes updated.")
        except Exception as exc:
            messagebox.showerror("Error", f"Could not update Schengen data.\nDetails: {exc}")

    def add_airport(self):
        code = simpledialog.askstring("New airport", "Enter ICAO code (for example, LEBL):")
        if not code:
            return

        latitude = simpledialog.askfloat("Latitude", "Enter latitude in decimal degrees:")
        if latitude is None:
            return

        longitude = simpledialog.askfloat("Longitude", "Enter longitude in decimal degrees:")
        if longitude is None:
            return

        normalized_code = code.strip().upper()
        if any(item.code == normalized_code for item in self.airport_list):
            messagebox.showwarning("Duplicate airport", "That airport code is already loaded.")
            return

        new_airport = airport.Airport(normalized_code, latitude, longitude)
        airport.AddAirport(self.airport_list, new_airport)
        airport.SetSchengen(new_airport)
        self._update_status_labels()
        self.console_status.set("Airport added to the working dataset.")
        self._set_console_text(
            "Airport added successfully.\n"
            f"Code: {new_airport.code}\n"
            f"Latitude: {new_airport.latitude:.6f}\n"
            f"Longitude: {new_airport.longitude:.6f}\n"
            f"Schengen: {new_airport.Schengen}"
        )

    def delete_airport(self):
        if not self._require_airports():
            return

        code = simpledialog.askstring("Delete airport", "Enter ICAO code to delete:")
        if not code:
            return

        normalized_code = code.strip().upper()
        updated_airports = airport.RemoveAirport(self.airport_list, normalized_code)
        if updated_airports is None:
            messagebox.showerror("Airport not found", "The selected airport is not in the current list.")
            return

        self.airport_list = updated_airports
        self._update_status_labels()
        self.console_status.set("Airport removed from the working dataset.")
        self._set_console_text(f"Airport {normalized_code} removed successfully.")

    def save_schengen(self):
        if not self._require_airports():
            return

        try:
            filepath = filedialog.asksaveasfilename(
                title="Save Schengen airports",
                initialdir=self.base_dir,
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            )
            if not filepath:
                return

            with open(filepath, "w", encoding="utf-8") as file:
                file.write("CODE LAT LON\n")
                for current_airport in self.airport_list:
                    if airport.IsSchengenAirport(current_airport.code):
                        file.write(
                            f"{current_airport.code} "
                            f"{current_airport.latitude} "
                            f"{current_airport.longitude}\n"
                        )
            self.console_status.set("Schengen export saved.")
            self._set_console_text(f"Schengen airports saved to:\n{filepath}")
            messagebox.showinfo("Success", "Schengen airport file saved successfully.")
        except Exception as exc:
            messagebox.showerror("Save error", f"Could not save the file.\nDetails: {exc}")

    def plot_airports(self):
        if not self._require_airports():
            return

        try:
            airport.PlotAirports(self.airport_list)
            self.console_status.set("Airport chart opened.")
        except Exception as exc:
            messagebox.showerror("Plot error", f"Could not generate the airport chart.\nDetails: {exc}")

    def show_map(self):
        if not self._require_airports():
            return

        try:
            lookup = self._airport_lookup(include_project_airports=True)
            selected_arrival = None
            route_note = "No arrival route highlighted."

            if self.arrival_list:
                wants_route = messagebox.askyesno(
                    "Arrival route",
                    "Do you want to draw the route of one loaded arrival on the map?",
                )
                if wants_route:
                    flight_id = simpledialog.askstring(
                        "Arrival route",
                        "Enter the arrival flight ID to highlight (for example, ECMKV):",
                    )
                    if flight_id:
                        normalized_id = flight_id.strip().upper()
                        selected_arrival = next(
                            (
                                item
                                for item in self.arrival_list
                                if item.flight_id.upper() == normalized_id
                            ),
                            None,
                        )
                        if selected_arrival is None:
                            messagebox.showwarning(
                                "Arrival not found",
                                "That arrival ID is not loaded. The map will open without a route.",
                            )

            filename = self.base_dir / "interface_show_map.kml"
            with open(filename, "w", encoding="utf-8") as file:
                file.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                file.write('<kml xmlns="http://www.opengis.net/kml/2.2">\n')
                file.write("<Document>\n")
                file.write("  <name>Airport Interface Map</name>\n")
                file.write("  <Style id=\"schengen\">\n")
                file.write("    <IconStyle><scale>1.1</scale><Icon><href>http://maps.google.com/mapfiles/kml/paddle/grn-circle.png</href></Icon></IconStyle>\n")
                file.write("  </Style>\n")
                file.write("  <Style id=\"non_schengen\">\n")
                file.write("    <IconStyle><scale>1.1</scale><Icon><href>http://maps.google.com/mapfiles/kml/paddle/red-circle.png</href></Icon></IconStyle>\n")
                file.write("  </Style>\n")
                file.write("  <Style id=\"route_origin\">\n")
                file.write("    <IconStyle><scale>1.2</scale><Icon><href>http://maps.google.com/mapfiles/kml/paddle/blu-circle.png</href></Icon></IconStyle>\n")
                file.write("  </Style>\n")
                file.write("  <Style id=\"route_destination\">\n")
                file.write("    <IconStyle><scale>1.2</scale><Icon><href>http://maps.google.com/mapfiles/kml/paddle/ylw-circle.png</href></Icon></IconStyle>\n")
                file.write("  </Style>\n")
                file.write("  <Style id=\"route_line\">\n")
                file.write("    <LineStyle><color>ffffa500</color><width>4</width></LineStyle>\n")
                file.write("  </Style>\n")

                for current_airport in self.airport_list:
                    airport_code = current_airport.code.upper()
                    is_schengen = airport.IsSchengenAirport(airport_code)
                    description = (
                        f"Schengen: {is_schengen}\n"
                        f"Latitude: {current_airport.latitude:.6f}\n"
                        f"Longitude: {current_airport.longitude:.6f}"
                    )
                    file.write("  <Placemark>\n")
                    file.write(f"    <name>{airport_code}</name>\n")
                    file.write(f"    <description>{description}</description>\n")
                    file.write(
                        f"    <styleUrl>#{'schengen' if is_schengen else 'non_schengen'}</styleUrl>\n"
                    )
                    file.write("    <Point>\n")
                    file.write(
                        f"      <coordinates>{current_airport.longitude},{current_airport.latitude},0</coordinates>\n"
                    )
                    file.write("    </Point>\n")
                    file.write("  </Placemark>\n")

                if selected_arrival is not None:
                    origin_airport = lookup.get(selected_arrival.origin_airport.upper())
                    destination_airport = lookup.get(self.home_airport_code)
                    if origin_airport and destination_airport:
                        route_note = (
                            f"Highlighted arrival {selected_arrival.flight_id}: "
                            f"{selected_arrival.origin_airport} -> {self.home_airport_code}"
                        )
                        file.write("  <Placemark>\n")
                        file.write(
                            f"    <name>{selected_arrival.flight_id} route</name>\n"
                        )
                        file.write(
                            f"    <description>{selected_arrival.company} arriving at {selected_arrival.expected_time}</description>\n"
                        )
                        file.write("    <styleUrl>#route_line</styleUrl>\n")
                        file.write("    <LineString>\n")
                        file.write("      <tessellate>1</tessellate>\n")
                        file.write(
                            "      <coordinates>"
                            f"{origin_airport.longitude},{origin_airport.latitude},0 "
                            f"{destination_airport.longitude},{destination_airport.latitude},0"
                            "</coordinates>\n"
                        )
                        file.write("    </LineString>\n")
                        file.write("  </Placemark>\n")

                        file.write("  <Placemark>\n")
                        file.write(
                            f"    <name>{selected_arrival.origin_airport} origin</name>\n"
                        )
                        file.write(
                            f"    <description>Origin of flight {selected_arrival.flight_id}</description>\n"
                        )
                        file.write("    <styleUrl>#route_origin</styleUrl>\n")
                        file.write("    <Point>\n")
                        file.write(
                            f"      <coordinates>{origin_airport.longitude},{origin_airport.latitude},0</coordinates>\n"
                        )
                        file.write("    </Point>\n")
                        file.write("  </Placemark>\n")

                        file.write("  <Placemark>\n")
                        file.write(
                            f"    <name>{self.home_airport_code} destination</name>\n"
                        )
                        file.write(
                            f"    <description>Destination airport for highlighted arrival {selected_arrival.flight_id}</description>\n"
                        )
                        file.write("    <styleUrl>#route_destination</styleUrl>\n")
                        file.write("    <Point>\n")
                        file.write(
                            f"      <coordinates>{destination_airport.longitude},{destination_airport.latitude},0</coordinates>\n"
                        )
                        file.write("    </Point>\n")
                        file.write("  </Placemark>\n")
                    elif selected_arrival is not None:
                        route_note = (
                            f"Route for {selected_arrival.flight_id} could not be drawn "
                            "because some airport coordinates were not available."
                        )
                        messagebox.showwarning(
                            "Missing route coordinates",
                            "The selected arrival was found, but its origin or destination coordinates are missing.",
                        )

                file.write("</Document>\n")
                file.write("</kml>\n")

            os.startfile(filename)
            self.console_status.set("Google Earth map opened.")
            self._set_console_text(
                "Map exported to Google Earth.\n"
                f"Airports shown: {len(self.airport_list)}\n"
                f"{route_note}\n"
                f"KML file: {filename}"
            )
        except Exception as exc:
            messagebox.showerror("Map error", f"Could not generate the KML map.\nDetails: {exc}")

    def load_arrivals(self):
        try:
            filepath = filedialog.askopenfilename(
                title="Select arrivals file",
                initialdir=self.base_dir,
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            )
            if not filepath:
                return

            self.arrival_list = self._load_arrivals_from_file(filepath)
            self._update_status_labels()
            self.console_status.set("Arrival dataset loaded successfully.")
            self._set_console_text(f"Successfully loaded {len(self.arrival_list)} arrivals from:\n{filepath}")
            messagebox.showinfo("Success", "Arrival flights loaded successfully.")
        except Exception as exc:
            messagebox.showerror("Load error", f"Could not load arrival file.\nDetails: {exc}")

    def show_arrivals(self):
        if not self._require_arrivals():
            return

        content = self._format_arrival_rows()
        self.console_status.set("Arrival list opened in a separate window.")
        self._set_console_text(
            f"Opened arrival list window.\nRows displayed: {len(self.arrival_list)}"
        )
        self._open_text_window(
            "Loaded arrivals",
            "Flight id, company, origin airport and expected landing time.",
            content,
        )

    def plot_arrivals_by_company(self):
        if not self._require_arrivals():
            return

        company_counter = Counter(arrival.company for arrival in self.arrival_list)
        labels, values = zip(*company_counter.most_common(10))

        plt.figure("Arrivals by company", figsize=(10, 6))
        plt.bar(labels, values, color="#6cc8f2", edgecolor="#2d7ea2")
        plt.title("Arrivals per airline company")
        plt.xlabel("Company")
        plt.ylabel("Flights")
        plt.grid(axis="y", alpha=0.25)
        plt.tight_layout()
        plt.show()
        self.console_status.set("Company arrivals chart opened.")

    def plot_arrivals_by_origin(self):
        if not self._require_arrivals():
            return

        origin_counter = Counter(arrival.origin_airport for arrival in self.arrival_list)
        labels, values = zip(*origin_counter.most_common(10))

        plt.figure("Arrivals by origin", figsize=(10, 6))
        plt.barh(labels[::-1], values[::-1], color="#7fd9ab", edgecolor="#3c936c")
        plt.title("Top origin airports for arrivals")
        plt.xlabel("Flights")
        plt.ylabel("Origin airport")
        plt.grid(axis="x", alpha=0.25)
        plt.tight_layout()
        plt.show()
        self.console_status.set("Origin arrivals chart opened.")

    def plot_arrivals_by_hour(self):
        if not self._require_arrivals():
            return

        hour_counter = Counter(arrival.hour for arrival in self.arrival_list if arrival.hour is not None)
        hours = list(range(24))
        values = [hour_counter.get(hour, 0) for hour in hours]

        plt.figure("Arrival flow by hour", figsize=(11, 6))
        plt.plot(hours, values, color="#3d8dd8", marker="o", linewidth=2.5)
        plt.fill_between(hours, values, color="#bfe9ff", alpha=0.6)
        plt.title("Expected arrivals by landing hour")
        plt.xlabel("Hour of day")
        plt.ylabel("Flights")
        plt.xticks(hours, [f"{hour:02d}:00" for hour in hours], rotation=45)
        plt.grid(alpha=0.25)
        plt.tight_layout()
        plt.show()
        self.console_status.set("Hourly arrival flow chart opened.")


if __name__ == "__main__":
    root = tk.Tk()
    app = AirportInterface(root)
    root.mainloop()
