import tkinter as tk
from collections import Counter
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog
import random
import string

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from PIL import Image, ImageTk

# Asumimos que estos módulos existen en tu entorno de trabajo
import Arrivals
import airport
import LEBL


class AirportInterface:
    def __init__(self, root):
        self.root = root
        self.base_dir = Path(__file__).resolve().parent
        self.airport_list = []
        self.arrival_list = []
        self.airport_structure = None
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

    def switch_view(self, view_frame):
        for view in (self.view_home, self.view_airport, self.view_arrival):
            view.grid_remove()
        view_frame.grid(row=0, column=0, sticky="nsew")
        self.root.after(50, self._update_scroll_region)

    def generate_boarding_pass(self):
        """
        Abre un formulario modal para pedir todos los datos a la vez.
        Si se dejan campos en blanco, se generan datos automáticos aleatorios.
        """
        form_win = tk.Toplevel(self.root)
        form_win.title("Dades del Passatger")
        form_win.geometry("420x320")
        form_win.configure(bg=self.colors["surface"])
        form_win.transient(self.root)
        form_win.grab_set()

        tk.Label(form_win, text="Dades del Boarding Pass", font=("Trebuchet MS", 14, "bold"),
                 bg=self.colors["surface"], fg=self.colors["text"]).pack(pady=(20, 15))

        frame = tk.Frame(form_win, bg=self.colors["surface"])
        frame.pack(padx=20, fill="x")

        def create_field(label_text, row):
            tk.Label(frame, text=label_text, bg=self.colors["surface"], fg=self.colors["text"],
                     font=("Trebuchet MS", 10, "bold")).grid(row=row, column=0, sticky="w", pady=8)
            entry = tk.Entry(frame, width=20, font=("Trebuchet MS", 10), bg="#ffffff")
            entry.grid(row=row, column=1, pady=8, padx=10)
            return entry

        # Campos opcionales (si están vacíos, serán aleatorios)
        entry_name = create_field("Nom (en blanc = aleatori):", 0)
        entry_dest = create_field("Destinació (ex: JFK):", 1)
        entry_flight = create_field("Vol (ex: IB1234):", 2)
        entry_seat = create_field("Seient (ex: 12A):", 3)

        entry_name.focus()

        def submit():
            name = entry_name.get().strip() or random.choice(
                ["JOHN DOE", "MARIA GARCIA", "ALEX SMITH", "LUCIA PEREZ", "JAMES BOND"])
            destination = entry_dest.get().strip() or random.choice(["JFK", "LHR", "HND", "CDG", "DXB", "SYD"])
            flight = entry_flight.get().strip() or f"{random.choice(string.ascii_uppercase)}{random.choice(string.ascii_uppercase)}{random.randint(100, 9999)}"
            seat = entry_seat.get().strip() or f"{random.randint(1, 40)}{random.choice(['A', 'B', 'C', 'D', 'E', 'F'])}"

            # Generamos el resto de datos chulos automáticamente
            gate = f"{random.choice(['A', 'B', 'C', 'D'])}{random.randint(1, 25)}"
            time = f"{random.randint(0, 23):02d}:{random.choice(['00', '15', '30', '45'])}"

            form_win.destroy()
            self._animate_boarding_pass(name, destination, flight, seat, gate, time)

        tk.Button(
            form_win, text="Generar Billete", command=submit,
            bg=self.colors["gold_fill"], fg=self.colors["text"],
            font=("Trebuchet MS", 11, "bold"), relief="groove", cursor="hand2", padx=15, pady=5
        ).pack(pady=20)

    def _animate_boarding_pass(self, name, destination, flight, seat, gate, time):
        """
        Dibuja el billete con diseño realista y lo anima simulando una caída/impresión.
        """
        bp_win = tk.Toplevel(self.root)
        bp_win.title("El teu Boarding Pass")
        bp_win.geometry("850x350")
        bp_win.configure(bg="#1a252f")

        canvas = tk.Canvas(bp_win, bg="#1a252f", highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        y_off = -400

        # Sombra
        canvas.create_rectangle(55, 55 + y_off, 805, 255 + y_off, fill="#000000", outline="", stipple="gray50",
                                tags="ticket")
        # Base blanca
        canvas.create_rectangle(50, 50 + y_off, 800, 250 + y_off, fill="#ffffff", outline="#bdc3c7", width=2,
                                tags="ticket")
        # Cabecera roja
        canvas.create_rectangle(50, 50 + y_off, 800, 90 + y_off, fill="#e74c3c", outline="", tags="ticket")
        canvas.create_text(70, 70 + y_off, anchor="w", text="✈ BOARDING PASS", fill="#ffffff",
                           font=("Trebuchet MS", 16, "bold"), tags="ticket")
        canvas.create_text(780, 70 + y_off, anchor="e", text="PRIORITY BOARDING", fill="#ffffff",
                           font=("Trebuchet MS", 12, "bold"), tags="ticket")

        # Línea de corte (Stub)
        canvas.create_line(600, 50 + y_off, 600, 250 + y_off, fill="#bdc3c7", dash=(5, 5), width=2, tags="ticket")

        # Información principal
        canvas.create_text(70, 110 + y_off, anchor="w", text="PASSENGER NAME", fill="#7f8c8d",
                           font=("Helvetica", 8, "bold"), tags="ticket")
        canvas.create_text(70, 130 + y_off, anchor="w", text=name.upper(), fill="#2c3e50",
                           font=("Helvetica", 16, "bold"), tags="ticket")

        canvas.create_text(70, 170 + y_off, anchor="w", text="FLIGHT", fill="#7f8c8d", font=("Helvetica", 8, "bold"),
                           tags="ticket")
        canvas.create_text(70, 190 + y_off, anchor="w", text=flight.upper(), fill="#2c3e50",
                           font=("Helvetica", 14, "bold"), tags="ticket")

        canvas.create_text(180, 170 + y_off, anchor="w", text="GATE", fill="#7f8c8d", font=("Helvetica", 8, "bold"),
                           tags="ticket")
        canvas.create_text(180, 190 + y_off, anchor="w", text=gate, fill="#2c3e50", font=("Helvetica", 14, "bold"),
                           tags="ticket")

        canvas.create_text(270, 170 + y_off, anchor="w", text="BOARDING TIME", fill="#7f8c8d",
                           font=("Helvetica", 8, "bold"), tags="ticket")
        canvas.create_text(270, 190 + y_off, anchor="w", text=time, fill="#e74c3c", font=("Helvetica", 16, "bold"),
                           tags="ticket")

        canvas.create_text(400, 170 + y_off, anchor="w", text="SEAT", fill="#7f8c8d", font=("Helvetica", 8, "bold"),
                           tags="ticket")
        canvas.create_text(400, 190 + y_off, anchor="w", text=seat.upper(), fill="#2c3e50",
                           font=("Helvetica", 20, "bold"), tags="ticket")

        origin = self.home_airport_code if self.home_airport_code else "LEBL"
        canvas.create_text(400, 125 + y_off, anchor="center", text=f"{origin} ⟶ {destination.upper()}", fill="#bdc3c7",
                           font=("Helvetica", 22, "bold"), tags="ticket")

        # Stub (parte derecha)
        canvas.create_text(620, 110 + y_off, anchor="w", text="NAME", fill="#7f8c8d", font=("Helvetica", 7, "bold"),
                           tags="ticket")
        canvas.create_text(620, 125 + y_off, anchor="w", text=name.upper(), fill="#2c3e50",
                           font=("Helvetica", 10, "bold"), tags="ticket")
        canvas.create_text(620, 155 + y_off, anchor="w", text="FLIGHT", fill="#7f8c8d", font=("Helvetica", 7, "bold"),
                           tags="ticket")
        canvas.create_text(620, 170 + y_off, anchor="w", text=flight.upper(), fill="#2c3e50",
                           font=("Helvetica", 10, "bold"), tags="ticket")
        canvas.create_text(710, 155 + y_off, anchor="w", text="SEAT", fill="#7f8c8d", font=("Helvetica", 7, "bold"),
                           tags="ticket")
        canvas.create_text(710, 170 + y_off, anchor="w", text=seat.upper(), fill="#2c3e50",
                           font=("Helvetica", 10, "bold"), tags="ticket")

        # Código de barras falso
        for i in range(48):
            x = 70 + (i * 10) + random.randint(-2, 2)
            w = random.randint(1, 4)
            canvas.create_rectangle(x, 215 + y_off, x + w, 240 + y_off, fill="#2c3e50", outline="", tags="ticket")

        for i in range(16):
            x = 620 + (i * 10) + random.randint(-2, 2)
            w = random.randint(1, 4)
            canvas.create_rectangle(x, 200 + y_off, x + w, 230 + y_off, fill="#2c3e50", outline="", tags="ticket")

        def drop_animation(current_y_offset):
            if current_y_offset < 0:
                distance = abs(current_y_offset)
                step = max(2, int(distance * 0.15))

                canvas.move("ticket", 0, step)
                new_offset = current_y_offset + step

                if new_offset > 0:
                    canvas.move("ticket", 0, -new_offset)
                    new_offset = 0

                bp_win.after(16, lambda: drop_animation(new_offset))
            else:
                self.write_console(f"🎟️ Boarding pass generat per a {name.upper()} (Vol: {flight.upper()}).")

        drop_animation(-400)

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
            status_frame, 0, "Airport dataset", self.airports_status, self.colors["airport_fill"]
        )
        self._create_status_card(
            status_frame, 1, "Arrival dataset", self.arrivals_status, self.colors["arrival_fill"]
        )
        self._create_status_card(
            status_frame, 2, "Session", self.console_status, self.colors["gold_fill"]
        )

        # ---- INICIO DEL ÁREA DINÁMICA DE VISTAS ----
        self.dynamic_area = tk.Frame(main, bg=self.colors["background"])
        self.dynamic_area.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(0, 18))
        self.dynamic_area.columnconfigure(0, weight=1)
        self.dynamic_area.rowconfigure(0, weight=1)

        self.view_home = tk.Frame(self.dynamic_area, bg=self.colors["background"])
        self.view_home.columnconfigure(0, weight=1)
        self.view_home.columnconfigure(1, weight=1)
        self.view_home.rowconfigure(0, weight=1)
        self.view_home.rowconfigure(1, weight=1)  # Damos peso a la nueva fila

        self.view_airport = tk.Frame(self.dynamic_area, bg=self.colors["background"])
        self.view_arrival = tk.Frame(self.dynamic_area, bg=self.colors["background"])

        for view in (self.view_home, self.view_airport, self.view_arrival):
            view.grid(row=0, column=0, sticky="nsew")

        # --- 1. VISTA PRINCIPAL (HOME) ---
        airport_home_panel = self._create_section_panel(
            self.view_home, row=0, column=0, title="Airport tools",
            subtitle="Load, edit and visualize airport information."
        )
        arrival_home_panel = self._create_section_panel(
            self.view_home, row=0, column=1, title="Arrival tools",
            subtitle="Inspect incoming flights, gates and terminal structures."
        )
        # Panel del pasajero ocupando 2 columnas (ancho completo)
        passenger_home_panel = self._create_section_panel(
            self.view_home, row=1, column=0, columnspan=2, title="Passenger tools",
            subtitle="Generate boarding passes and passenger utilities."
        )

        home_air_tiles = tk.Frame(airport_home_panel, bg=self.colors["surface"])
        home_air_tiles.pack(fill="both", expand=True)
        home_air_tiles.columnconfigure(0, weight=1)
        self._create_tile(
            home_air_tiles, 0, 0, "Open Airport Tools", "Access all airport management features.",
            lambda: self.switch_view(self.view_airport),
            self.colors["airport_fill"], self.colors["airport_outline"], self.colors["airport_hover"]
        )

        home_arr_tiles = tk.Frame(arrival_home_panel, bg=self.colors["surface"])
        home_arr_tiles.pack(fill="both", expand=True)
        home_arr_tiles.columnconfigure(0, weight=1)
        self._create_tile(
            home_arr_tiles, 0, 0, "Open Arrival Tools", "Access all flight arrival features.",
            lambda: self.switch_view(self.view_arrival),
            self.colors["arrival_fill"], self.colors["arrival_outline"], self.colors["arrival_hover"]
        )

        # Botón para el Boarding Pass dentro de su panel
        home_pass_tiles = tk.Frame(passenger_home_panel, bg=self.colors["surface"])
        home_pass_tiles.pack(fill="both", expand=True)
        home_pass_tiles.columnconfigure(0, weight=1)
        self._create_tile(
            home_pass_tiles, 0, 0, "Generate Boarding Pass", "Create a passenger boarding pass ticket.",
            self.generate_boarding_pass,
            self.colors["gold_fill"], self.colors["gold_outline"], self.colors["gold_hover"]
        )

        # --- 2. VISTA D'AIRPORT TOOLS ---
        airport_header = tk.Frame(self.view_airport, bg=self.colors["background"])
        airport_header.pack(fill="x", pady=(0, 10))
        tk.Button(
            airport_header, text="← Back to Menu", command=lambda: self.switch_view(self.view_home),
            bg=self.colors["surface"], fg=self.colors["text"], font=("Trebuchet MS", 11, "bold"),
            relief="groove", cursor="hand2", padx=10, pady=5
        ).pack(side="left")
        tk.Label(
            airport_header, text="Airport Tools", font=("Trebuchet MS", 16, "bold"),
            bg=self.colors["background"], fg=self.colors["text"]
        ).pack(side="left", padx=15)

        airport_panel = tk.Frame(
            self.view_airport, bg=self.colors["surface"], highlightbackground=self.colors["border"],
            highlightthickness=1, bd=0, padx=18, pady=18
        )
        airport_panel.pack(fill="both", expand=True)
        airport_tiles = tk.Frame(airport_panel, bg=self.colors["surface"])
        airport_tiles.pack(fill="both", expand=True)

        for c in range(3):
            airport_tiles.columnconfigure(c, weight=1)

        self._create_tile(airport_tiles, 0, 0, "Load airports", "Import airport coordinates from a text file.",
                          self.load_airports, self.colors["airport_fill"], self.colors["airport_outline"],
                          self.colors["airport_hover"])
        self._create_tile(airport_tiles, 0, 1, "Show airports", "Open the loaded airport list in a separate window.",
                          self.show_airports, self.colors["airport_fill"], self.colors["airport_outline"],
                          self.colors["airport_hover"])
        self._create_tile(airport_tiles, 0, 2, "Set Schengen", "Compute the Schengen flag for every loaded airport.",
                          self.set_schengen, self.colors["airport_fill"], self.colors["airport_outline"],
                          self.colors["airport_hover"])

        self._create_tile(airport_tiles, 1, 0, "Add airport", "Insert a new airport by code and coordinates.",
                          self.add_airport, self.colors["gold_fill"], self.colors["gold_outline"],
                          self.colors["gold_hover"])
        self._create_tile(airport_tiles, 1, 1, "Delete airport",
                          "Remove an airport by ICAO code from the current list.", self.delete_airport,
                          self.colors["gold_fill"], self.colors["gold_outline"], self.colors["gold_hover"])
        self._create_tile(airport_tiles, 1, 2, "Save Schengen", "Export only the Schengen airports to a text file.",
                          self.save_schengen, self.colors["gold_fill"], self.colors["gold_outline"],
                          self.colors["gold_hover"])

        self._create_tile(airport_tiles, 2, 0, "Plot Schengen split",
                          "Open a bar chart with Schengen and non-Schengen counts.", self.plot_airports,
                          self.colors["arrival_fill"], self.colors["arrival_outline"], self.colors["arrival_hover"])
        self._create_tile(airport_tiles, 2, 1, "Show map",
                          "Open Google Earth with airports and an optional arrival route.", self.show_map,
                          self.colors["arrival_fill"], self.colors["arrival_outline"], self.colors["arrival_hover"])

        # --- 3. VISTA D'ARRIVAL TOOLS ---
        arrival_header = tk.Frame(self.view_arrival, bg=self.colors["background"])
        arrival_header.pack(fill="x", pady=(0, 10))
        tk.Button(
            arrival_header, text="← Back to Menu", command=lambda: self.switch_view(self.view_home),
            bg=self.colors["surface"], fg=self.colors["text"], font=("Trebuchet MS", 11, "bold"),
            relief="groove", cursor="hand2", padx=10, pady=5
        ).pack(side="left")
        tk.Label(
            arrival_header, text="Arrival Tools", font=("Trebuchet MS", 16, "bold"),
            bg=self.colors["background"], fg=self.colors["text"]
        ).pack(side="left", padx=15)

        arrival_panel = tk.Frame(
            self.view_arrival, bg=self.colors["surface"], highlightbackground=self.colors["border"],
            highlightthickness=1, bd=0, padx=18, pady=18
        )
        arrival_panel.pack(fill="both", expand=True)
        arrival_tiles = tk.Frame(arrival_panel, bg=self.colors["surface"])
        arrival_tiles.pack(fill="both", expand=True)

        for c in range(3):
            arrival_tiles.columnconfigure(c, weight=1)

        self._create_tile(arrival_tiles, 0, 0, "Load arrivals",
                          "Import arrival flights from a text file such as Arrivals.txt.", self.load_arrivals,
                          self.colors["arrival_fill"], self.colors["arrival_outline"], self.colors["arrival_hover"])
        self._create_tile(arrival_tiles, 0, 1, "Show arrivals", "Open the arrival list in a separate window.",
                          self.show_arrivals, self.colors["arrival_fill"], self.colors["arrival_outline"],
                          self.colors["arrival_hover"])
        self._create_tile(arrival_tiles, 0, 2, "Load bundled files", "Quick load Airports, Arrivals and Terminals.",
                          self.load_project_files, self.colors["gold_fill"], self.colors["gold_outline"],
                          self.colors["gold_hover"])

        self._create_tile(arrival_tiles, 1, 0, "Plot by company", "Bar chart of arrivals grouped by airline company.",
                          self.plot_arrivals_by_company, self.colors["airport_fill"], self.colors["airport_outline"],
                          self.colors["airport_hover"])
        self._create_tile(arrival_tiles, 1, 1, "Plot by origin", "Horizontal ranking of the busiest origin airports.",
                          self.plot_arrivals_by_origin, self.colors["airport_fill"], self.colors["airport_outline"],
                          self.colors["airport_hover"])
        self._create_tile(arrival_tiles, 1, 2, "Hourly flow", "Line chart of expected arrivals by landing hour.",
                          self.plot_arrivals_by_hour, self.colors["gold_fill"], self.colors["gold_outline"],
                          self.colors["gold_hover"])

        self._create_tile(arrival_tiles, 2, 0, "Load Airport Structure", "Load terminals and gate areas.",
                          self.load_airport_structure, self.colors["gold_fill"], self.colors["gold_outline"],
                          self.colors["gold_hover"])

        self._create_tile(arrival_tiles, 2, 2, "Load Airlines", "Load terminal airline list.", self.load_airlines,
                          self.colors["gold_fill"], self.colors["gold_outline"], self.colors["gold_hover"])

        self._create_tile(arrival_tiles, 2, 1, "Gate Occupancy", "Show gate usage.", self.show_gate_occupancy,
                          self.colors["gold_fill"], self.colors["gold_outline"], self.colors["gold_hover"])


        self.switch_view(self.view_home)
        # ---- FIN DEL ÁREA DINÁMICA ----

        # ---- PANEL DE LA CONSOLA ----
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

    def _create_section_panel(self, parent, row, column, title, subtitle, columnspan=1):
        panel = tk.Frame(
            parent,
            bg=self.colors["surface"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            bd=0,
            padx=18,
            pady=18,
        )
        panel.grid(row=row, column=column, columnspan=columnspan, sticky="nsew", padx=6, pady=(0, 18))
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

        # Usamos <ButtonRelease-1> para evitar rebotes al cerrar ventanas modales
        for sequence in ("<ButtonRelease-1>", "<Return>", "<space>"):
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

    def _open_plot_window(self, fig, title, subtitle):
        window = tk.Toplevel(self.root)
        window.title(title)
        window.geometry("960x680")
        window.minsize(720, 500)
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
            pady=14,
        )
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
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

        canvas = FigureCanvasTkAgg(fig, master=body)
        canvas.draw()
        canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

        toolbar_frame = tk.Frame(body, bg=self.colors["surface"])
        toolbar_frame.grid(row=1, column=0, sticky="ew")
        toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
        toolbar.update()

        def _on_close():
            try:
                plt.close(fig)
            except Exception:
                pass
            window.destroy()

        window.protocol("WM_DELETE_WINDOW", _on_close)

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
                f"{arrival.id:<12}{arrival.airline:<14}{arrival.origin:<12}{arrival.arrival_time:<8}"
            )
        return "\n".join(lines)

    def _load_structure_from(self, path):
        self.airport_structure = LEBL.LoadAirportStructure(str(path))
        return self.airport_structure

    def _need_structure(self):
        if self.airport_structure is not None:
            return True
        path = self.base_dir / "Terminals.txt"
        if not path.exists():
            messagebox.showwarning("No structure", "Load Terminals.txt first.")
            return False
        try:
            self._load_structure_from(path)
            return True
        except Exception as exc:
            messagebox.showerror("Structure error", f"Could not load Terminals.txt.\nDetails: {exc}")
            return False

    def _structure_text(self):
        lines = []
        for terminal in self.airport_structure.terminals:
            lines.append(f"{terminal.t_name}: {len(terminal.BA)} areas, {len(terminal.air_code)} airlines")
            for area in terminal.BA:
                kind = "Schengen" if area.Schengen else "non-Schengen"
                lines.append(f"  Area {area.area}: {kind}, {len(area.Gates)} gates")
        return "\n".join(lines)

    def load_airport_structure(self):
        try:
            path = filedialog.askopenfilename(
                title="Select terminal structure file",
                initialdir=self.base_dir,
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            )
            if not path:
                return
            self._load_structure_from(path)
            text = self._structure_text()
            self.console_status.set("Airport structure loaded.")
            self._set_console_text(text)
            self._open_text_window("Airport structure", "Loaded terminals and gates.", text)
        except Exception as exc:
            messagebox.showerror("Structure error", f"Could not load the structure.\nDetails: {exc}")


    def load_airlines(self):
        if not self._need_structure():
            return
        terminal_name = simpledialog.askstring("Load airlines", "Terminal:")
        if not terminal_name:
            return
        terminal = LEBL.FindTerminal(self.airport_structure, terminal_name)
        if terminal is None:
            messagebox.showerror("Not found", "Terminal not found.")
            return
        LEBL.LoadAirlines(terminal, terminal.t_name, self.base_dir)
        text = "\n".join(terminal.air_code)
        self._set_console_text(f"{terminal.t_name} airlines loaded: {len(terminal.air_code)}")
        self._open_text_window(f"{terminal.t_name} airlines", "Loaded airline list.", text)

    def show_gate_occupancy(self):
        if not self._need_structure():
            return
        gates = LEBL.GateOccupancy(self.airport_structure.terminals)
        lines = [f"{'GATE':<8}{'OCCUPIED':<12}{'AIRCRAFT'}"]
        for gate in gates:
            lines.append(f"{gate['name']:<8}{str(gate['occupied']):<12}{gate['craftID'] or '-'}")
        text = "\n".join(lines)
        self._set_console_text(f"Gate occupancy loaded: {len(gates)} gates")
        self._open_text_window("Gate occupancy", "Current gate status.", text)


    def load_project_files(self):
        try:
            airports_path = self.base_dir / "Airports.txt"
            arrivals_path = self.base_dir / "Arrivals.txt"
            terminals_path = self.base_dir / "Terminals.txt"

            if airports_path.exists():
                self.airport_list = airport.LoadAirports(str(airports_path))
            if arrivals_path.exists():
                self.arrival_list = Arrivals.LoadArrivals(str(arrivals_path))
            if terminals_path.exists():
                self._load_structure_from(terminals_path)

            self._update_status_labels()
            self.console_status.set("Bundled project files loaded.")
            self._set_console_text(
                "Bundled files loaded from the project folder.\n"
                f"Airports: {len(self.airport_list)}\n"
                f"Arrivals: {len(self.arrival_list)}\n"
                f"Terminals: {len(self.airport_structure.terminals) if self.airport_structure else 0}"
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

            airport.SaveSchengenAirports(filepath, self.airport_list)
            self.console_status.set("Schengen export saved.")
            self._set_console_text(f"Schengen airports saved to:\n{filepath}")
            messagebox.showinfo("Success", "Schengen airport file saved successfully.")
        except Exception as exc:
            messagebox.showerror("Save error", f"Could not save the file.\nDetails: {exc}")

    def plot_airports(self):
        if not self._require_airports():
            return

        original_show = plt.show
        plt.show = lambda *args, **kwargs: None
        try:
            try:
                airport.PlotAirports(self.airport_list)
                fig = plt.gcf()
            finally:
                plt.show = original_show
            self._open_plot_window(
                fig,
                "Schengen split",
                "Schengen vs non-Schengen airport counts from the loaded dataset.",
            )
            self.console_status.set("Airport chart opened.")
        except Exception as exc:
            plt.show = original_show
            messagebox.showerror("Plot error", f"Could not generate the airport chart.\nDetails: {exc}")

    def show_map(self):
        if not self._require_airports():
            return

        try:
            filename = self.base_dir / "airports.kml"
            route_note = "Airport map opened."
            if self.arrival_list and messagebox.askyesno("Arrival route", "Draw one loaded arrival route?"):
                flight_id = simpledialog.askstring("Arrival route", "Arrival flight ID:")
                selected = next(
                    (item for item in self.arrival_list if item.flight_id.upper() == flight_id.strip().upper()),
                    None,
                ) if flight_id else None
                if selected is None:
                    messagebox.showwarning("Arrival not found", "The map will open without a route.")
                    airport.MapAirports(self.airport_list, str(filename))
                else:
                    filename = self.base_dir / "flights_map.kml"
                    airports_for_map = list(self._airport_lookup(include_project_airports=True).values())
                    Arrivals.MapFlights([selected], airports_for_map, str(filename))
                    route_note = f"Route highlighted: {selected.flight_id}"
            else:
                airport.MapAirports(self.airport_list, str(filename))

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

            self.arrival_list = Arrivals.LoadArrivals(filepath)
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

        original_show = plt.show
        plt.show = lambda *args, **kwargs: None
        try:
            try:
                Arrivals.PlotAirlines(self.arrival_list)
                fig = plt.gcf()
            finally:
                plt.show = original_show
            self._open_plot_window(
                fig,
                "Arrivals by company",
                "Flight count grouped by airline company.",
            )
            self.console_status.set("Company arrivals chart opened.")
        except Exception as exc:
            plt.show = original_show
            messagebox.showerror("Plot error", f"Could not generate the company chart.\nDetails: {exc}")

    def plot_arrivals_by_origin(self):
        if not self._require_arrivals():
            return

        try:
            from matplotlib.figure import Figure

            origin_counter = Counter(arrival.origin for arrival in self.arrival_list)
            labels, values = zip(*origin_counter.most_common(10))

            fig = Figure(figsize=(10, 6))
            ax = fig.add_subplot(111)
            ax.barh(labels[::-1], values[::-1], color="#7fd9ab", edgecolor="#3c936c")
            ax.set_title("Top origin airports for arrivals")
            ax.set_xlabel("Flights")
            ax.set_ylabel("Origin airport")
            ax.grid(axis="x", alpha=0.25)
            fig.tight_layout()

            self._open_plot_window(
                fig,
                "Arrivals by origin",
                "Top 10 busiest origin airports for the loaded arrival flights.",
            )
            self.console_status.set("Origin arrivals chart opened.")
        except Exception as exc:
            messagebox.showerror("Plot error", f"Could not generate the origin chart.\nDetails: {exc}")

    def plot_arrivals_by_hour(self):
        if not self._require_arrivals():
            return

        original_show = plt.show
        plt.show = lambda *args, **kwargs: None
        try:
            try:
                Arrivals.PlotArrivals(self.arrival_list)
                fig = plt.gcf()
            finally:
                plt.show = original_show
            self._open_plot_window(
                fig,
                "Hourly arrival flow",
                "Expected arrivals grouped by landing hour.",
            )
            self.console_status.set("Hourly arrival flow chart opened.")
        except Exception as exc:
            plt.show = original_show
            messagebox.showerror("Plot error", f"Could not generate the hourly chart.\nDetails: {exc}")


if __name__ == "__main__":
    root = tk.Tk()
    app = AirportInterface(root)
    root.mainloop()