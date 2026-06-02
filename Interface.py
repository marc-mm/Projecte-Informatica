import tkinter as tk
from collections import Counter
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog
import random
import string

import matplotlib.pyplot as plt  # Per generar gràfics
# Eines per incrustar gràfics de matplotlib dins de finestres tkinter
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from PIL import Image, ImageTk  # Per carregar i mostrar imatges (el logo)

# Suposem que aquests mòduls existeixen al teu entorn de treball
import Arrivals  # Vols / Aircraft (V1-V4)
import airport  # Aeroports i funcions Schengen (V1)
import LEBL  # Estructura de portes i assignació (V3-V4)


class AirportInterface:
    # Finestra principal de l'aplicació. Construeix tota la interfície gràfica
    # i connecta cada botó (tile) amb les funcions dels mòduls Arrivals/airport/LEBL.
    def __init__(self, root):
        self.root = root  # Finestra arrel de tkinter
        self.base_dir = Path(__file__).resolve().parent  # Carpeta del projecte
        self.airport_list = []
        self.arrival_list = []
        self.departure_list = []  # V4 - sortides carregades
        self.merged_list = []  # V4 - moviments del dia (arribades + sortides)
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

        # Variables de text que es mostren a les targetes d'estat (s'actualitzen soles)
        self.airports_status = tk.StringVar(value="Airports loaded: 0")
        self.arrivals_status = tk.StringVar(value="Arrivals loaded: 0")
        self.console_status = tk.StringVar(
            value="Load airports or arrivals to start exploring the data."
        )

        # Configuració bàsica de la finestra (títol, mida, color de fons)
        self.root.title("Airport Management System")
        self.root.geometry("1320x860")
        self.root.minsize(1120, 620)
        self.root.configure(bg=self.colors["background"])
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

        self._build_interface()  # Construïm tots els widgets de la finestra
        self._set_console_text(
            "Airport Management System ready.\n"
            "Use the airport and arrival tiles to load files, inspect data and open plots."
        )

    def switch_view(self, view_frame):
        # Canvia la vista visible (home / airport / arrival) amagant les altres.
        for view in (self.view_home, self.view_airport, self.view_arrival):
            view.grid_remove()
        view_frame.grid(row=0, column=0, sticky="nsew")
        self.root.after(50, self._update_scroll_region)  # Recalcula l'scroll

    def generate_boarding_pass(self):
        """
        Obre un formulari modal per demanar totes les dades alhora.
        Si es deixen camps en blanc, es generen dades automàtiques aleatòries.
        """
        # Finestra modal (Toplevel) que bloqueja la principal mentre és oberta
        form_win = tk.Toplevel(self.root)
        form_win.title("Dades del Passatger")
        form_win.geometry("420x320")
        form_win.configure(bg=self.colors["surface"])
        form_win.transient(self.root)
        form_win.grab_set()  # Captura tots els clics fins que es tanqui

        tk.Label(form_win, text="Dades del Boarding Pass", font=("Trebuchet MS", 14, "bold"),
                 bg=self.colors["surface"], fg=self.colors["text"]).pack(pady=(20, 15))

        frame = tk.Frame(form_win, bg=self.colors["surface"])
        frame.pack(padx=20, fill="x")

        def create_field(label_text, row):
            # Crea una etiqueta + caixa de text en una fila del formulari
            tk.Label(frame, text=label_text, bg=self.colors["surface"], fg=self.colors["text"],
                     font=("Trebuchet MS", 10, "bold")).grid(row=row, column=0, sticky="w", pady=8)
            entry = tk.Entry(frame, width=20, font=("Trebuchet MS", 10), bg="#ffffff")
            entry.grid(row=row, column=1, pady=8, padx=10)
            return entry

        # Camps opcionals (si estan buits, seran aleatoris)
        entry_name = create_field("Nom (en blanc = aleatori):", 0)
        entry_dest = create_field("Destinació (ex: JFK):", 1)
        entry_flight = create_field("Vol (ex: IB1234):", 2)
        entry_seat = create_field("Seient (ex: 12A):", 3)

        entry_name.focus()

        def submit():
            # Per cada camp: si l'usuari l'ha deixat buit, generem un valor aleatori
            name = entry_name.get().strip() or random.choice(
                ["JOHN DOE", "MARIA GARCIA", "ALEX SMITH", "LUCIA PEREZ", "JAMES BOND"])
            destination = entry_dest.get().strip() or random.choice(["JFK", "LHR", "HND", "CDG", "DXB", "SYD"])
            flight = entry_flight.get().strip() or f"{random.choice(string.ascii_uppercase)}{random.choice(string.ascii_uppercase)}{random.randint(100, 9999)}"
            seat = entry_seat.get().strip() or f"{random.randint(1, 40)}{random.choice(['A', 'B', 'C', 'D', 'E', 'F'])}"

            # Generem la resta de dades automàticament
            gate = f"{random.choice(['A', 'B', 'C', 'D'])}{random.randint(1, 25)}"  # Porta aleatòria
            time = f"{random.randint(0, 23):02d}:{random.choice(['00', '15', '30', '45'])}"  # Hora aleatòria

            form_win.destroy()  # Tanquem el formulari
            # Mostrem el bitllet amb l'animació d'impressió
            self._animate_boarding_pass(name, destination, flight, seat, gate, time)

        tk.Button(
            form_win, text="Generar Billete", command=submit,
            bg=self.colors["gold_fill"], fg=self.colors["text"],
            font=("Trebuchet MS", 11, "bold"), relief="groove", cursor="hand2", padx=15, pady=5
        ).pack(pady=20)

    def _animate_boarding_pass(self, name, destination, flight, seat, gate, time):
        """
        Dibuixa el bitllet amb un disseny realista i l'anima simulant una caiguda/impressió.
        """
        bp_win = tk.Toplevel(self.root)
        bp_win.title("El teu Boarding Pass")
        bp_win.geometry("850x350")
        bp_win.configure(bg="#1a252f")

        canvas = tk.Canvas(bp_win, bg="#1a252f", highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        # Tot el bitllet es dibuixa desplaçat cap amunt (y_off negatiu) i després
        # l'animació el fa "caure" fins a la posició final. Tots els elements
        # porten l'etiqueta "ticket" per poder moure'ls junts.
        y_off = -400

        # Ombra
        canvas.create_rectangle(55, 55 + y_off, 805, 255 + y_off, fill="#000000", outline="", stipple="gray50",
                                tags="ticket")
        # Base blanca
        canvas.create_rectangle(50, 50 + y_off, 800, 250 + y_off, fill="#ffffff", outline="#bdc3c7", width=2,
                                tags="ticket")
        # Capçalera vermella
        canvas.create_rectangle(50, 50 + y_off, 800, 90 + y_off, fill="#e74c3c", outline="", tags="ticket")
        canvas.create_text(70, 70 + y_off, anchor="w", text="✈ BOARDING PASS", fill="#ffffff",
                           font=("Trebuchet MS", 16, "bold"), tags="ticket")
        canvas.create_text(780, 70 + y_off, anchor="e", text="PRIORITY BOARDING", fill="#ffffff",
                           font=("Trebuchet MS", 12, "bold"), tags="ticket")

        # Línia de tall (Stub)
        canvas.create_line(600, 50 + y_off, 600, 250 + y_off, fill="#bdc3c7", dash=(5, 5), width=2, tags="ticket")

        # Informació principal
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

        # Stub (part dreta)
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

        # Codi de barres fals (barres de gruix i posició aleatòries)
        for i in range(48):
            x = 70 + (i * 10) + random.randint(-2, 2)
            w = random.randint(1, 4)
            canvas.create_rectangle(x, 215 + y_off, x + w, 240 + y_off, fill="#2c3e50", outline="", tags="ticket")

        # Segon codi de barres, més petit, a la part dreta (stub)
        for i in range(16):
            x = 620 + (i * 10) + random.randint(-2, 2)
            w = random.randint(1, 4)
            canvas.create_rectangle(x, 200 + y_off, x + w, 230 + y_off, fill="#2c3e50", outline="", tags="ticket")

        def drop_animation(current_y_offset):
            # Anima la caiguda: mou el bitllet cap avall fins arribar a y=0.
            if current_y_offset < 0:
                distance = abs(current_y_offset)
                step = max(2, int(distance * 0.15))  # Pas proporcional (frena al final)

                canvas.move("ticket", 0, step)  # Movem tots els elements del bitllet
                new_offset = current_y_offset + step

                if new_offset > 0:
                    # No ens passem de la posició final: corregim l'excés
                    canvas.move("ticket", 0, -new_offset)
                    new_offset = 0

                bp_win.after(16, lambda: drop_animation(new_offset))  # ~60 FPS
            else:
                # Quan ha arribat, escrivim un missatge a la consola
                self.write_console(f"🎟️ Boarding pass generat per a {name.upper()} (Vol: {flight.upper()}).")

        drop_animation(-400)  # Iniciem l'animació des de dalt

    def _build_interface(self):
        # Construeix tota la interfície: zona amb scroll, capçalera, targetes
        # d'estat, les tres vistes (home / airport / arrival) amb els seus botons
        # i el panell de consola inferior.
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

        # ---- INICI DE L'ÀREA DINÀMICA DE VISTES ----
        self.dynamic_area = tk.Frame(main, bg=self.colors["background"])
        self.dynamic_area.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(0, 18))
        self.dynamic_area.columnconfigure(0, weight=1)
        self.dynamic_area.rowconfigure(0, weight=1)

        self.view_home = tk.Frame(self.dynamic_area, bg=self.colors["background"])
        self.view_home.columnconfigure(0, weight=1)
        self.view_home.columnconfigure(1, weight=1)
        self.view_home.rowconfigure(0, weight=1)
        self.view_home.rowconfigure(1, weight=1)  # Donem pes a la fila del passatger
        self.view_home.rowconfigure(2, weight=1)  # Donem pes a la fila de File tools

        self.view_airport = tk.Frame(self.dynamic_area, bg=self.colors["background"])
        self.view_arrival = tk.Frame(self.dynamic_area, bg=self.colors["background"])

        for view in (self.view_home, self.view_airport, self.view_arrival):
            view.grid(row=0, column=0, sticky="nsew")

        # --- 1. VISTA PRINCIPAL (HOME) - Inici ---
        airport_home_panel = self._create_section_panel(
            self.view_home, row=0, column=0, title="Airport tools",
            subtitle="Load, edit and visualize airport information."
        )
        arrival_home_panel = self._create_section_panel(
            self.view_home, row=0, column=1, title="Flight tools",
            subtitle="Inspect incoming flights, gates and terminal structures."
        )
        # Panell del passatger ocupant 2 columnes (amplada completa)
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
            home_arr_tiles, 0, 0, "Open Flight Tools", "Access all flight arrival features.",
            lambda: self.switch_view(self.view_arrival),
            self.colors["arrival_fill"], self.colors["arrival_outline"], self.colors["arrival_hover"]
        )

        # Botó per al Boarding Pass dins del seu panell
        home_pass_tiles = tk.Frame(passenger_home_panel, bg=self.colors["surface"])
        home_pass_tiles.pack(fill="both", expand=True)
        home_pass_tiles.columnconfigure(0, weight=1)
        self._create_tile(
            home_pass_tiles, 0, 0, "Generate Boarding Pass", "Create a passenger boarding pass ticket.",
            self.generate_boarding_pass,
            self.colors["gold_fill"], self.colors["gold_outline"], self.colors["gold_hover"]
        )

        # Panell de fitxers ocupant 2 columnes (mateixa amplada que Passenger tools)
        file_home_panel = self._create_section_panel(
            self.view_home, row=2, column=0, columnspan=2, title="File tools",
            subtitle="Load the project data files in one click."
        )
        # Botó de càrrega ràpida dins del seu panell (just a sota del títol)
        home_file_tiles = tk.Frame(file_home_panel, bg=self.colors["surface"])
        home_file_tiles.pack(fill="both", expand=True)
        home_file_tiles.columnconfigure(0, weight=1)
        self._create_tile(
            home_file_tiles, 0, 0, "Load bundled files",
            "Quick load Airports, Arrivals, Departures and Terminals.",
            self.load_project_files,
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

        # ---- Botons moguts des de Flight tools cap a Airport tools ----
        self._create_tile(airport_tiles, 2, 2, "Load Airport Structure", "Load terminals and gate areas.",
                          self.load_airport_structure, self.colors["gold_fill"], self.colors["gold_outline"],
                          self.colors["gold_hover"])
        self._create_tile(airport_tiles, 3, 0, "Gate Occupancy", "Show gate usage.", self.show_gate_occupancy,
                          self.colors["gold_fill"], self.colors["gold_outline"], self.colors["gold_hover"])
        self._create_tile(airport_tiles, 3, 1, "Assign day gates",
                          "Simulate gate assignment for every one-hour period of the day.", self.assign_day_gates,
                          self.colors["gold_fill"], self.colors["gold_outline"], self.colors["gold_hover"])
        self._create_tile(airport_tiles, 3, 2, "Day occupancy plot",
                          "Gates per terminal per hour + unassigned aircraft per hour.", self.plot_day_occupancy,
                          self.colors["gold_fill"], self.colors["gold_outline"], self.colors["gold_hover"])
        self._create_tile(airport_tiles, 4, 0, "Occupancy by hour",
                          "Inspect gate occupancy at a chosen hour period.", self.show_occupancy_by_hour,
                          self.colors["gold_fill"], self.colors["gold_outline"], self.colors["gold_hover"])
        self._create_tile(airport_tiles, 4, 1, "Interactive day timeline",
                          "Animated hour-by-hour gate occupancy timeline (extra feature).", self.open_day_timeline,
                          self.colors["airport_fill"], self.colors["airport_outline"], self.colors["airport_hover"])

        # --- 3. VISTA D'ARRIVAL TOOLS ---
        arrival_header = tk.Frame(self.view_arrival, bg=self.colors["background"])
        arrival_header.pack(fill="x", pady=(0, 10))
        tk.Button(
            arrival_header, text="← Back to Menu", command=lambda: self.switch_view(self.view_home),
            bg=self.colors["surface"], fg=self.colors["text"], font=("Trebuchet MS", 11, "bold"),
            relief="groove", cursor="hand2", padx=10, pady=5
        ).pack(side="left")
        tk.Label(
            arrival_header, text="Flight Tools", font=("Trebuchet MS", 16, "bold"),
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
        self._create_tile(arrival_tiles, 0, 2, "Load Airlines", "Load terminal airline list.", self.load_airlines,
                          self.colors["gold_fill"], self.colors["gold_outline"], self.colors["gold_hover"])

        # ---- VERSIÓ 4: SORTIDES I ASSIGNACIÓ DINÀMICA DE PORTES ----
        self._create_tile(arrival_tiles, 1, 0, "Load departures",
                          "Import a departures file (id, destination, time, airline).", self.load_departures,
                          self.colors["arrival_fill"], self.colors["arrival_outline"], self.colors["arrival_hover"])
        self._create_tile(arrival_tiles, 1, 1, "Merge movements",
                          "Merge arrivals and departures into the full daily movements.", self.merge_movements,
                          self.colors["arrival_fill"], self.colors["arrival_outline"], self.colors["arrival_hover"])
        self._create_tile(arrival_tiles, 1, 2, "Night aircraft",
                          "List aircraft that only depart (no arrival).", self.show_night_aircraft,
                          self.colors["arrival_fill"], self.colors["arrival_outline"], self.colors["arrival_hover"])

        self._create_tile(arrival_tiles, 2, 0, "Plot by company", "Bar chart of arrivals grouped by airline company.",
                          self.plot_arrivals_by_company, self.colors["airport_fill"], self.colors["airport_outline"],
                          self.colors["airport_hover"])
        self._create_tile(arrival_tiles, 2, 1, "Plot by origin", "Horizontal ranking of the busiest origin airports.",
                          self.plot_arrivals_by_origin, self.colors["airport_fill"], self.colors["airport_outline"],
                          self.colors["airport_hover"])
        self._create_tile(arrival_tiles, 2, 2, "Hourly flow", "Line chart of expected arrivals by landing hour.",
                          self.plot_arrivals_by_hour, self.colors["gold_fill"], self.colors["gold_outline"],
                          self.colors["gold_hover"])

        self.switch_view(self.view_home)
        # ---- FI DE L'ÀREA DINÀMICA ----

        # ---- PANELL DE LA CONSOLA ----
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
        # Recalcula l'àrea desplaçable perquè l'scroll abasti tot el contingut.
        if self.scroll_canvas is None:
            return
        self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))

    def _resize_scrollable_content(self, event):
        # Fa que el contingut intern ocupi tota l'amplada del canvas amb scroll.
        if self.scroll_canvas is None or self.scroll_window_id is None:
            return
        self.scroll_canvas.itemconfigure(self.scroll_window_id, width=event.width)

    def _bind_main_scroll(self):
        # Connecta la roda del ratolí amb l'scroll (Windows/Mac i Linux).
        self.root.bind_all("<MouseWheel>", self._on_main_mousewheel, add="+")
        self.root.bind_all("<Button-4>", self._on_main_mousewheel_linux, add="+")
        self.root.bind_all("<Button-5>", self._on_main_mousewheel_linux, add="+")

    def _event_is_from_main_window(self, event):
        # True si l'esdeveniment ve de la finestra principal (no d'una emergent).
        try:
            return event.widget.winfo_toplevel() == self.root
        except Exception:
            return False

    def _on_main_mousewheel(self, event):
        # Gestió de la roda del ratolí a Windows/Mac (event.delta en passos de 120).
        if self.scroll_canvas is None or not self._event_is_from_main_window(event):
            return
        if isinstance(event.widget, tk.Text):
            return  # Dins d'una caixa de text deixem que faci el seu propi scroll

        delta_units = int(-event.delta / 120)  # Convertim el delta a "passos"
        if delta_units == 0 and event.delta:
            delta_units = -1 if event.delta > 0 else 1  # Garantim com a mínim 1 pas
        if delta_units:
            self.scroll_canvas.yview_scroll(delta_units, "units")

    def _on_main_mousewheel_linux(self, event):
        # Gestió de la roda del ratolí a Linux (botons 4 = amunt, 5 = avall).
        if self.scroll_canvas is None or not self._event_is_from_main_window(event):
            return
        if isinstance(event.widget, tk.Text):
            return

        if event.num == 4:
            self.scroll_canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.scroll_canvas.yview_scroll(1, "units")

    def _render_header(self, event=None):
        # Dibuixa la capçalera (rectangle arrodonit + logo + títols).
        if not self.header_canvas:
            return

        canvas = self.header_canvas
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        if width <= 1 or height <= 1:
            return

        canvas.delete("all")  # Esborrem el dibuix anterior abans de tornar-lo a fer
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
            self._load_logo()  # Carreguem el logo el primer cop

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
        # Busca i carrega el logo de l'EETAC (prova dos noms de fitxer possibles).
        for logo_name in ("eetac.png", "eetac_logo_bgless.png"):
            logo_path = self.base_dir / logo_name
            if not logo_path.exists():
                continue
            try:
                logo_image = Image.open(logo_path)
                logo_image = logo_image.resize((132, 72), Image.Resampling.LANCZOS)  # Mida fixa
                self.logo_photo = ImageTk.PhotoImage(logo_image)
                return
            except Exception:
                self.logo_photo = None
        self.logo_photo = None  # Si no s'ha trobat cap logo

    def _load_home_airport_code(self):
        # Llegeix el codi de l'aeroport base (primera paraula de Terminals.txt).
        terminals_path = self.base_dir / "Terminals.txt"
        try:
            with open(terminals_path, "r", encoding="utf-8") as file:
                first_line = file.readline().strip()
                if first_line:
                    return first_line.split()[0].upper()
        except Exception:
            pass
        return "LEBL"  # Valor per defecte si no es pot llegir el fitxer

    def _create_status_card(self, parent, column, title, variable, bg_color):
        # Crea una targeta d'estat (títol + valor que canvia sol) a la fila superior.
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
        # Crea un panell amb títol i subtítol que conté un grup de botons (tiles).
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
        # Crea un botó rectangular arrodonit (dibuixat sobre un Canvas) que
        # executa 'command' en fer-hi clic i canvia de color en passar-hi per sobre.
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
        # Cada cop que canvia de mida es torna a dibuixar
        tile.bind("<Configure>", lambda event: self._draw_tile(tile, title, subtitle, fill, outline))

        def handle_enter(_event):
            # Ratolí a sobre -> color de "hover"
            tile.configure(bg=self.colors["surface"])
            self._draw_tile(tile, title, subtitle, hover_fill, outline)

        def handle_leave(_event):
            # Ratolí fora -> color normal
            tile.configure(bg=self.colors["surface"])
            self._draw_tile(tile, title, subtitle, fill, outline)

        # Fem servir <ButtonRelease-1> per evitar rebots en tancar finestres modals
        for sequence in ("<ButtonRelease-1>", "<Return>", "<space>"):
            tile.bind(sequence, lambda _event: command())  # Clic, Enter o espai

        tile.bind("<Enter>", handle_enter)
        tile.bind("<Leave>", handle_leave)

    def _draw_tile(self, tile, title, subtitle, fill, outline):
        # Dibuixa el contingut d'un tile: fons arrodonit, títol, subtítol i fletxa ">".
        width = tile.winfo_width()
        height = tile.winfo_height()
        if width <= 1 or height <= 1:
            return  # Encara no té mida real

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
        # Dibuixa un rectangle de cantonades arrodonides. El truc és crear un
        # polígon amb els punts de les cantonades i activar smooth=True, que
        # corba les cantonades automàticament.
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
        # Substitueix tot el text de la consola inferior pel missatge donat.
        self.text_box.delete("1.0", tk.END)
        self.text_box.insert(tk.END, message)

    def write_console(self, message):
        # Drecera pública per escriure a la consola.
        self._set_console_text(message)

    def _open_text_window(self, title, subtitle, content):
        # Obre una finestra emergent amb capçalera i una caixa de text (només
        # lectura) i barres de desplaçament. S'usa per mostrar llistes/taules.
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
        text_widget.configure(state="disabled")  # Només lectura

    def _open_plot_window(self, fig, title, subtitle):
        # Obre una finestra emergent que incrusta un gràfic de matplotlib (fig)
        # amb la seva barra d'eines de navegació (zoom, desar imatge...).
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

        # Incrustem la figura de matplotlib dins de la finestra tkinter
        canvas = FigureCanvasTkAgg(fig, master=body)
        canvas.draw()
        canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

        toolbar_frame = tk.Frame(body, bg=self.colors["surface"])
        toolbar_frame.grid(row=1, column=0, sticky="ew")
        toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)  # Barra d'eines del gràfic
        toolbar.update()

        def _on_close():
            # En tancar, alliberem la figura de matplotlib per no acumular memòria
            try:
                plt.close(fig)
            except Exception:
                pass
            window.destroy()

        window.protocol("WM_DELETE_WINDOW", _on_close)

    def _update_status_labels(self):
        # Actualitza els comptadors d'aeroports i arribades de les targetes d'estat.
        self.airports_status.set(f"Airports loaded: {len(self.airport_list)}")
        self.arrivals_status.set(f"Arrivals loaded: {len(self.arrival_list)}")

    def _require_airports(self):
        # Comprova que hi hagi aeroports carregats; si no, avisa i retorna False.
        if self.airport_list:
            return True
        messagebox.showwarning("No airport data", "Please load airport data first.")
        return False

    def _require_arrivals(self):
        # Comprova que hi hagi arribades carregades; si no, avisa i retorna False.
        if self.arrival_list:
            return True
        messagebox.showwarning("No arrival data", "Please load arrival data first.")
        return False

    def _airport_lookup(self, include_project_airports=False):
        # Construeix un diccionari codi->aeroport. Opcionalment hi afegeix també
        # els aeroports del fitxer Airports.txt del projecte (sense sobreescriure).
        lookup = {item.code.upper(): item for item in self.airport_list}
        if include_project_airports:
            bundled_airports_path = self.base_dir / "Airports.txt"
            if bundled_airports_path.exists():
                try:
                    bundled = airport.LoadAirports(str(bundled_airports_path))
                    # Només iterem si el lector ha retornat una llista (no -1)
                    if bundled != -1:
                        for item in bundled:
                            lookup.setdefault(item.code.upper(), item)  # No pisa els ja existents
                except Exception:
                    pass
        return lookup

    def _format_airport_rows(self):
        # Genera el text en columnes de la llista d'aeroports (per mostrar-la).
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
        # Genera el text en columnes de la llista d'arribades (per mostrar-la).
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
        # Carrega l'estructura de portes des del fitxer indicat i la desa.
        structure = LEBL.LoadAirportStructure(str(path))
        # Si el lector retorna -1, el fitxer no s'ha pogut llegir o es buit
        if structure == -1:
            raise ValueError("The terminal structure file is missing, empty or invalid.")
        self.airport_structure = structure
        return self.airport_structure

    def _need_structure(self):
        # Garanteix que hi ha estructura carregada; si no, intenta carregar
        # Terminals.txt automàticament. Retorna False si no és possible.
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
        # Genera un resum de text de l'estructura (terminals, àrees i portes).
        lines = []
        for terminal in self.airport_structure.terminals:
            lines.append(f"{terminal.t_name}: {len(terminal.BA)} areas, {len(terminal.air_code)} airlines")
            for area in terminal.BA:
                kind = "Schengen" if area.Schengen else "non-Schengen"
                lines.append(f"  Area {area.area}: {kind}, {len(area.Gates)} gates")
        return "\n".join(lines)

    def load_airport_structure(self):
        # Demana un fitxer de terminals, carrega l'estructura i la mostra.
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
        # Demana un terminal i carrega/mostra les seves aerolínies.
        if not self._need_structure():
            return
        terminal_name = simpledialog.askstring("Load airlines", "Terminal:")
        if not terminal_name:
            return
        terminal = Arrivals.FindTerminal(self.airport_structure, terminal_name)
        if terminal is None:
            messagebox.showerror("Not found", "Terminal not found.")
            return
        # Les aerolínies ja s'han carregat en carregar l'estructura. Només les
        # tornem a llegir si encara no n'hi ha, per evitar duplicar-les.
        if len(terminal.air_code) == 0:
            LEBL.LoadAirlines(terminal, terminal.t_name)
        text = "\n".join(terminal.air_code)
        self._set_console_text(f"{terminal.t_name} airlines loaded: {len(terminal.air_code)}")
        self._open_text_window(f"{terminal.t_name} airlines", "Loaded airline list.", text)

    def show_gate_occupancy(self):
        # Mostra en una finestra l'estat de totes les portes (ocupada i quin avió).
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
        # Càrrega ràpida dels fitxers del projecte (aeroports, arribades, sortides, terminals).
        try:
            airports_path = self.base_dir / "Airports.txt"
            arrivals_path = self.base_dir / "Arrivals.txt"
            departures_path = self.base_dir / "Departures.txt"
            terminals_path = self.base_dir / "Terminals.txt"

            if airports_path.exists():
                loaded_airports = airport.LoadAirports(str(airports_path))
                # Si el lector retorna -1 (fitxer il·legible), deixem la llista buida
                self.airport_list = loaded_airports if loaded_airports != -1 else []
            if arrivals_path.exists():
                loaded_arrivals = Arrivals.LoadArrivals(str(arrivals_path))
                self.arrival_list = loaded_arrivals if loaded_arrivals != -1 else []
            if departures_path.exists():
                loaded_departures = Arrivals.LoadDepartures(str(departures_path))
                self.departure_list = loaded_departures if loaded_departures != -1 else []
                self.merged_list = []  # Si carreguem sortides noves, cal tornar a fusionar
            if terminals_path.exists():
                self._load_structure_from(terminals_path)

            self._update_status_labels()
            self.console_status.set("Bundled project files loaded.")
            self._set_console_text(
                "Bundled files loaded from the project folder.\n"
                f"Airports: {len(self.airport_list)}\n"
                f"Arrivals: {len(self.arrival_list)}\n"
                f"Departures: {len(self.departure_list)}\n"
                f"Terminals: {len(self.airport_structure.terminals) if self.airport_structure else 0}"
            )
        except Exception as exc:
            messagebox.showerror("Load error", f"Could not load bundled files.\nDetails: {exc}")

    def load_airports(self):
        # Demana un fitxer d'aeroports i el carrega a la llista de treball.
        try:
            filepath = filedialog.askopenfilename(
                title="Select airports file",
                initialdir=self.base_dir,
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            )
            if not filepath:
                return

            result = airport.LoadAirports(filepath)
            # ERROR: el fitxer no s'ha pogut obrir/llegir
            if result == -1:
                messagebox.showerror("Load error", "The airports file could not be opened or read.")
                return
            # ERROR: el fitxer s'ha llegit pero no tenia cap aeroport valid
            if not result:
                messagebox.showwarning(
                    "Empty data",
                    "No valid airports were found.\nCheck the file format: CODE DMS-LATITUDE DMS-LONGITUDE",
                )
                return

            self.airport_list = result
            self._update_status_labels()
            self.console_status.set("Airport dataset loaded successfully.")
            self._set_console_text(f"Successfully loaded {len(self.airport_list)} airports from:\n{filepath}")
            messagebox.showinfo("Success", "Airports loaded successfully.")
        except Exception as exc:
            messagebox.showerror("Load error", f"Could not load airport file.\nDetails: {exc}")

    def show_airports(self):
        # Obre una finestra amb la taula d'aeroports carregats.
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
        # Àlies de show_airports (compatibilitat).
        self.show_airports()

    def set_schengen(self):
        # Recalcula el flag Schengen de tots els aeroports carregats.
        if not self._require_airports():
            return

        try:
            for aero in self.airport_list:
                airport.SetSchengen(aero)
            schengen_count = sum(1 for aero in self.airport_list if aero.Schengen)  # Quants són Schengen
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
        # Demana codi i coordenades a l'usuari i afegeix un aeroport nou.
        code = simpledialog.askstring("New airport", "Enter ICAO code (for example, LEBL):")
        if not code:
            return  # L'usuari ha cancel·lat

        latitude = simpledialog.askfloat("Latitude", "Enter latitude in decimal degrees:")
        if latitude is None:
            return

        longitude = simpledialog.askfloat("Longitude", "Enter longitude in decimal degrees:")
        if longitude is None:
            return

        # ERROR: coordenades fora del rang valid (lat -90..90, lon -180..180)
        if latitude < -90 or latitude > 90 or longitude < -180 or longitude > 180:
            messagebox.showerror(
                "Invalid coordinates",
                "Latitude must be between -90 and 90 and longitude between -180 and 180.",
            )
            return

        normalized_code = code.strip().upper()
        if any(item.code == normalized_code for item in self.airport_list):
            messagebox.showwarning("Duplicate airport", "That airport code is already loaded.")
            return  # Evitem codis duplicats

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
        # Demana un codi ICAO i elimina aquest aeroport de la llista.
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
        # Demana on desar i exporta només els aeroports Schengen a un fitxer.
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
        # Mostra el gràfic Schengen vs no-Schengen dins de la nostra finestra.
        if not self._require_airports():
            return

        # Truc: les funcions Plot* dels mòduls criden plt.show() (que obriria una
        # finestra a part). El desactivem temporalment, agafem la figura amb
        # plt.gcf() i la incrustem nosaltres a _open_plot_window.
        original_show = plt.show
        plt.show = lambda *args, **kwargs: None
        try:
            try:
                airport.PlotAirports(self.airport_list)
                fig = plt.gcf()  # "Get current figure": la que acaba de crear PlotAirports
            finally:
                plt.show = original_show  # Restaurem sempre el plt.show original
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
        # Genera un mapa KML (Google Earth): tots els aeroports i, opcionalment,
        # la ruta d'una arribada concreta des del seu origen fins a LEBL.
        if not self._require_airports():
            return

        try:
            filename = self.base_dir / "airports.kml"
            route_note = "Airport map opened."
            # Si hi ha arribades, oferim dibuixar una ruta concreta
            if self.arrival_list and messagebox.askyesno("Arrival route", "Draw one loaded arrival route?"):
                id_flight = simpledialog.askstring("Arrival route", "Arrival flight ID:")
                # Busquem el vol amb aquest identificador (o None si no es troba)
                selected = next(
                    (item for item in self.arrival_list if item.id.upper() == id_flight.strip().upper()),
                    None,
                ) if id_flight else None
                if selected is None:
                    messagebox.showwarning("Arrival not found", "The map will open without a route.")
                    airport.MapAirports(self.airport_list, str(filename))
                else:
                    filename = self.base_dir / "flights_map.kml"
                    airports_for_map = list(self._airport_lookup(include_project_airports=True).values())
                    Arrivals.MapFlights([selected], airports_for_map, str(filename))
                    route_note = f"Route highlighted: {selected.id}"
            elif (self.arrival_list or self.departure_list) and messagebox.askyesno(
                "All routes",
                "Highlight ALL arrival + departure routes?\n(Schengen origins/destinations in a different colour)",
            ):
                # Dibuixem totes les trajectories (arribades i sortides) de cop
                filename = self.base_dir / "flights_map.kml"
                airports_for_map = list(self._airport_lookup(include_project_airports=True).values())
                all_flights = self.arrival_list + self.departure_list
                Arrivals.MapFlights(all_flights, airports_for_map, str(filename))
                route_note = (
                    f"All routes highlighted: {len(self.arrival_list)} arrivals "
                    f"+ {len(self.departure_list)} departures"
                )
            elif (self.arrival_list or self.departure_list) and messagebox.askyesno(
                "Long-distance flights",
                "Plot only long-distance flights?\n(Haversine distance greater than 2000 km)",
            ):
                # Filtrem nomes els vols amb distancia (origen/desti a LEBL) > 2000 km
                filename = self.base_dir / "flights_map.kml"
                airports_for_map = list(self._airport_lookup(include_project_airports=True).values())
                long_flights = self._long_distance_flights(airports_for_map)
                if not long_flights:
                    messagebox.showinfo("No long-distance flights", "No flights over 2000 km were found.")
                    airport.MapAirports(self.airport_list, str(filename))
                    route_note = "No long-distance flights found."
                else:
                    Arrivals.MapFlights(long_flights, airports_for_map, str(filename))
                    route_note = f"Long-distance flights (> 2000 km): {len(long_flights)}"
            else:
                airport.MapAirports(self.airport_list, str(filename))  # Només els aeroports

            self.console_status.set("Google Earth map opened.")
            self._set_console_text(
                "Map exported to Google Earth.\n"
                f"Airports shown: {len(self.airport_list)}\n"
                f"{route_note}\n"
                f"KML file: {filename}"
            )
        except Exception as exc:
            messagebox.showerror("Map error", f"Could not generate the KML map.\nDetails: {exc}")

    def _long_distance_flights(self, airports):
        # Retorna els vols amb distancia (origen->LEBL o LEBL->desti) > 2000 km.
        # Diccionari codi ICAO -> (latitud, longitud) per buscar coordenades rapid
        coords = {}
        for apt in airports:
            coords[apt.code] = (apt.latitude, apt.longitude)
        # Coordenades de Barcelona (LEBL)
        lebl_lat, lebl_lon = 41.297, 2.083
        result = []
        # Mirem totes les arribades i sortides carregades
        for a in self.arrival_list + self.departure_list:
            # Per a una arribada: distancia de l'origen fins a LEBL
            if a.origin != "" and a.origin in coords:
                olat, olon = coords[a.origin]
                if Arrivals.Haversine(olat, olon, lebl_lat, lebl_lon) > 2000:
                    result.append(a)
                    continue
            # Per a una sortida: distancia de LEBL fins a la destinacio
            if a.destination != "" and a.destination in coords:
                dlat, dlon = coords[a.destination]
                if Arrivals.Haversine(lebl_lat, lebl_lon, dlat, dlon) > 2000:
                    result.append(a)
        return result

    def load_arrivals(self):
        # Demana un fitxer d'arribades i el carrega a la llista de treball.
        try:
            filepath = filedialog.askopenfilename(
                title="Select arrivals file",
                initialdir=self.base_dir,
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            )
            if not filepath:
                return

            result = Arrivals.LoadArrivals(filepath)
            # ERROR: el fitxer no s'ha pogut obrir/llegir
            if result == -1:
                messagebox.showerror("Load error", "The arrivals file could not be opened or read.")
                return
            # ERROR: el fitxer s'ha llegit pero no tenia cap arribada valida
            if not result:
                messagebox.showwarning(
                    "Empty data",
                    "No valid arrivals were found.\nCheck the file format: AIRCRAFT ORIGIN ARRIVAL AIRLINE",
                )
                return

            self.arrival_list = result
            self._update_status_labels()
            self.console_status.set("Arrival dataset loaded successfully.")
            self._set_console_text(f"Successfully loaded {len(self.arrival_list)} arrivals from:\n{filepath}")
            messagebox.showinfo("Success", "Arrival flights loaded successfully.")
        except Exception as exc:
            messagebox.showerror("Load error", f"Could not load arrival file.\nDetails: {exc}")

    def show_arrivals(self):
        # Obre una finestra amb la taula d'arribades carregades.
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
        # Gràfic d'arribades per aerolínia (mateix truc de plt.show que plot_airports).
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
        # Gràfic de barres horitzontals amb els 10 aeroports d'origen més freqüents.
        if not self._require_arrivals():
            return

        try:
            from matplotlib.figure import Figure

            origin_counter = Counter(arrival.origin for arrival in self.arrival_list)  # Compta per origen
            labels, values = zip(*origin_counter.most_common(10))  # Els 10 amb més vols

            fig = Figure(figsize=(10, 6))
            ax = fig.add_subplot(111)
            # [::-1] inverteix l'ordre perquè el més gran quedi a dalt
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
        # Gràfic d'arribades per hora del dia (mateix truc de plt.show).
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

    # =================================================================
    # VERSIÓ 4 — Sortides, fusió i assignació dinàmica de portes
    # =================================================================
    def _require_departures(self):
        if self.departure_list:
            return True
        messagebox.showwarning("No departure data", "Please load departures first.")
        return False

    def _format_movement_rows(self, movements):
        lines = [
            f"{'ID':<10}{'ORIGIN':<8}{'ARRIVAL':<9}{'DEST':<8}{'DEPART':<9}{'AIRLINE'}",
            "-" * 56,
        ]
        for m in movements:
            lines.append(
                f"{m.id:<10}{(m.origin or '-'):<8}{(m.arrival_time or '-'):<9}"
                f"{(m.destination or '-'):<8}{(m.departure_time or '-'):<9}{m.airline}"
            )
        return "\n".join(lines)

    def _build_day_movements(self):
        """Retorna la llista de moviments del dia, construint-la des de les
        arribades i sortides si encara no s'ha fusionat. None si falten dades."""
        if self.merged_list:
            return self.merged_list
        if self.arrival_list and self.departure_list:
            result = Arrivals.MergeMovements(self.arrival_list, self.departure_list)
            if result != -1:
                self.merged_list = result
                return result
        return None

    def _reload_structure(self):
        """Recarrega una estructura d'aeroport neta (totes les portes lliures)."""
        source = self.base_dir / "Terminals.txt"
        if self.airport_structure is not None and Path(self.airport_structure.name).exists():
            source = Path(self.airport_structure.name)
        structure = LEBL.LoadAirportStructure(str(source))
        # Si el fitxer no s'ha pogut llegir o es buit, avisem amb un error clar
        if structure == -1:
            raise ValueError(f"The terminal structure file could not be read: {source}")
        return structure

    def load_departures(self):
        try:
            filepath = filedialog.askopenfilename(
                title="Select departures file",
                initialdir=self.base_dir,
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            )
            if not filepath:
                return

            result = Arrivals.LoadDepartures(filepath)
            # ERROR: el fitxer no s'ha pogut obrir/llegir
            if result == -1:
                messagebox.showerror("Load error", "The departures file could not be opened.")
                return
            # ERROR: el fitxer s'ha llegit pero no tenia cap sortida valida
            if not result:
                messagebox.showwarning(
                    "Empty data",
                    "No valid departures were found.\nCheck the file format: AIRCRAFT DESTINATION DEPARTURE AIRLINE",
                )
                return

            self.departure_list = result
            self.merged_list = []  # cal tornar a fusionar
            self.console_status.set("Departure dataset loaded successfully.")
            self._set_console_text(f"Successfully loaded {len(self.departure_list)} departures from:\n{filepath}")
            messagebox.showinfo("Success", "Departure flights loaded successfully.")
        except Exception as exc:
            messagebox.showerror("Load error", f"Could not load departure file.\nDetails: {exc}")

    def merge_movements(self):
        if not self._require_arrivals() or not self._require_departures():
            return

        result = Arrivals.MergeMovements(self.arrival_list, self.departure_list)
        if result == -1:
            messagebox.showerror("Merge error", "Both arrivals and departures are required.")
            return

        self.merged_list = result
        complete = [m for m in result if m.origin and m.destination]
        night = Arrivals.NightAircraft(result)
        night = night if night != -1 else []

        self.console_status.set("Daily movements merged.")
        self._set_console_text(
            f"Merged daily movements: {len(result)}\n"
            f"  With arrival + departure: {len(complete)}\n"
            f"  Night aircraft (departure only): {len(night)}"
        )
        self._open_text_window(
            "Daily movements",
            "Merged arrivals and departures (origin/arrival and destination/departure).",
            self._format_movement_rows(result),
        )

    def show_night_aircraft(self):
        movements = self.merged_list or self.departure_list
        if not movements:
            messagebox.showwarning("No data", "Merge movements or load departures first.")
            return

        night = Arrivals.NightAircraft(movements)
        if night == -1:
            messagebox.showerror("Error", "No movement data available.")
            return

        lines = [f"{'ID':<10}{'DEST':<8}{'DEPART':<9}{'AIRLINE'}", "-" * 36]
        for a in night:
            lines.append(f"{a.id:<10}{a.destination:<8}{a.departure_time:<9}{a.airline}")
        sel(f"Night aircraft (departure only): {len(night)}")
        self._open_text_window("Night aircraft", "Aircraft that only depart from the airport.", "\n".join(lines))

    def _simulate_day(self, structure, movements):
        """Estat inicial = nomes nocturns assignats; despres recorre les 24
        franges horaries. Retorna (assignats_per_hora, no_assignats_per_hora)."""
        night = Arrivals.NightAircraft(movements)
        LEBL.AssignNightGates(structure, night if night != -1 else [])
        assigned_per_hour = []
        unassigned_per_hour = []
        for h in range(24):
            nf = LEBL.AssignGatesAtTime(structure, movements, f"{h:02d}:00")
            unassigned_per_hour.append(nf if nf != -1 else 0)
            assigned = sum(1 for g in LEBL.GateOccupancy(structure.terminals) if g["occupied"])
            assigned_per_hour.append(assigned)
        return assigned_per_hour, unassigned_per_hour

    def assign_day_gates(self):
        movements = self._build_day_movements()
        if movements is None:
            messagebox.showwarning("No movements", "Load arrivals and departures, then merge movements first.")
            return
        try:
            structure = self._reload_structure()
            assigned, unassigned = self._simulate_day(structure, movements)
            self.airport_structure = structure  # conservem l'estat simulat

            lines = [f"{'PERIOD':<9}{'ASSIGNED':<10}{'UNASSIGNED'}", "-" * 30]
            for h in range(24):
                lines.append(f"{h:02d}:00    {assigned[h]:<10}{unassigned[h]}")
            total_unassigned = sum(unassigned)

            self.console_status.set("Daily gate assignment simulated.")
            self._set_console_text(
                f"Day simulated over 24 one-hour periods.\n"
                f"Total landings that could not be assigned: {total_unassigned}"
            )
            self._open_text_window(
                "Daily gate assignment",
                "Assigned gates and unassigned landings for each one-hour period.",
                "\n".join(lines),
            )
        except Exception as exc:
            messagebox.showerror("Assignment error", f"Could not simulate the day.\nDetails: {exc}")

    def plot_day_occupancy(self):
        movements = self._build_day_movements()
        if movements is None:
            messagebox.showwarning("No movements", "Load arrivals and departures, then merge movements first.")
            return

        try:
            structure = self._reload_structure()
            night = Arrivals.NightAircraft(movements)
            LEBL.AssignNightGates(structure, night if night != -1 else [])
        except Exception as exc:
            messagebox.showerror("Structure error", f"Could not reload terminals.\nDetails: {exc}")
            return

        original_show = plt.show
        plt.show = lambda *args, **kwargs: None
        try:
            try:
                LEBL.PlotDayOccupancy(structure, movements)
                fig = plt.gcf()
            finally:
                plt.show = original_show
            self._open_plot_window(
                fig,
                "Day occupancy",
                "Gates assigned per terminal per hour and aircraft not assigned per hour.",
            )
            self.console_status.set("Day occupancy chart opened.")
        except Exception as exc:
            plt.show = original_show
            messagebox.showerror("Plot error", f"Could not generate the occupancy chart.\nDetails: {exc}")

    def show_occupancy_by_hour(self):
        movements = self._build_day_movements()
        if movements is None:
            messagebox.showwarning("No movements", "Load arrivals and departures, then merge movements first.")
            return

        hour = simpledialog.askinteger("Occupancy by hour", "Hour period (0-23):", minvalue=0, maxvalue=23)
        if hour is None:
            return

        try:
            structure = self._reload_structure()
            night = Arrivals.NightAircraft(movements)
            LEBL.AssignNightGates(structure, night if night != -1 else [])

            unassigned = 0
            for h in range(hour + 1):
                nf = LEBL.AssignGatesAtTime(structure, movements, f"{h:02d}:00")
                unassigned = nf if nf != -1 else 0

            lines = [f"Occupancy at {hour:02d}:00 - {hour:02d}:59", "=" * 40]
            for terminal in structure.terminals:
                occ = sum(1 for area in terminal.BA for g in area.Gates if g.occupied)
                total = sum(len(area.Gates) for area in terminal.BA)
                lines.append(f"{terminal.t_name}: {occ}/{total} gates occupied")
            lines.append("")
            lines.append(f"Aircraft that could not be assigned in this period: {unassigned}")

            self._set_console_text(f"Occupancy computed for period {hour:02d}:00.")
            self._open_text_window(
                "Occupancy by hour", f"Gate occupancy at the {hour:02d}:00 period.", "\n".join(lines)
            )
        except Exception as exc:
            messagebox.showerror("Occupancy error", f"Could not compute occupancy.\nDetails: {exc}")

    def open_day_timeline(self):
        """EXTRA: línia de temps interactiva i animada de l'ocupació de portes."""
        movements = self._build_day_movements()
        if movements is None:
            messagebox.showwarning("No movements", "Load arrivals and departures, then merge movements first.")
            return

        try:
            structure = self._reload_structure()
            night = Arrivals.NightAircraft(movements)
            LEBL.AssignNightGates(structure, night if night != -1 else [])

            # Pre-calculem una instantània de l'ocupació per a cada hora del dia
            snapshots = []
            for h in range(24):
                nf = LEBL.AssignGatesAtTime(structure, movements, f"{h:02d}:00")
                terms = []
                for terminal in structure.terminals:
                    gates = []
                    for area in terminal.BA:
                        for g in area.Gates:
                            gates.append(bool(g.occupied))
                    terms.append({"name": terminal.t_name, "gates": gates})
                snapshots.append({"hour": h, "terminals": terms, "unassigned": nf if nf != -1 else 0})

            self._render_timeline_window(snapshots)
            self.console_status.set("Interactive day timeline opened.")
        except Exception as exc:
            messagebox.showerror("Timeline error", f"Could not build the timeline.\nDetails: {exc}")

    def _render_timeline_window(self, snapshots):
        win = tk.Toplevel(self.root)
        win.title("Interactive day timeline")
        win.geometry("1120x740")
        win.configure(bg=self.colors["background"])
        win.transient(self.root)

        header = tk.Frame(
            win, bg=self.colors["surface"], highlightbackground=self.colors["border"],
            highlightthickness=1, bd=0, padx=18, pady=12,
        )
        header.pack(fill="x", padx=16, pady=(16, 8))
        tk.Label(
            header, text="Interactive Day Timeline", font=("Trebuchet MS", 16, "bold"),
            bg=self.colors["surface"], fg=self.colors["text"],
        ).pack(anchor="w")
        info_var = tk.StringVar()
        tk.Label(
            header, textvariable=info_var, font=("Trebuchet MS", 11),
            bg=self.colors["surface"], fg=self.colors["muted"],
        ).pack(anchor="w", pady=(4, 0))

        canvas = tk.Canvas(
            win, bg=self.colors["console"], highlightthickness=1,
            highlightbackground=self.colors["border"],
        )
        canvas.pack(fill="both", expand=True, padx=16, pady=8)

        controls = tk.Frame(win, bg=self.colors["background"])
        controls.pack(fill="x", padx=16, pady=(0, 16))

        hour_var = tk.IntVar(value=0)
        playing = {"on": False}

        def draw(hour):
            snap = snapshots[hour]
            canvas.delete("all")
            width = canvas.winfo_width() or 1080
            n = len(snap["terminals"])
            if n == 0:
                return
            margin = 30
            col_w = (width - 2 * margin) / n
            total_occ = 0
            total_gates = 0
            for ti, term in enumerate(snap["terminals"]):
                x0 = margin + ti * col_w
                cx = x0 + col_w / 2
                gates = term["gates"]
                occ = sum(1 for g in gates if g)
                total_occ += occ
                total_gates += len(gates)
                canvas.create_text(
                    cx, 22, text=f"{term['name']}   {occ}/{len(gates)}",
                    fill=self.colors["text"], font=("Trebuchet MS", 12, "bold"),
                )
                cols = 8
                cell = 18
                pad = 4
                gx0 = x0 + 18
                gy0 = 50
                for gi, occupied in enumerate(gates):
                    r = gi // cols
                    c = gi % cols
                    gx = gx0 + c * (cell + pad)
                    gy = gy0 + r * (cell + pad)
                    color = "#e0564f" if occupied else "#7fd9ab"
                    canvas.create_rectangle(
                        gx, gy, gx + cell, gy + cell, fill=color, outline=self.colors["border"]
                    )
            info_var.set(
                f"Period {snap['hour']:02d}:00 - {snap['hour']:02d}:59     "
                f"Gates occupied: {total_occ}/{total_gates}     "
                f"Aircraft not assigned this hour: {snap['unassigned']}     "
                f"(green = free, red = occupied)"
            )

        def on_slide(value):
            hour_var.set(int(float(value)))
            draw(hour_var.get())

        slider = tk.Scale(
            controls, from_=0, to=23, orient="horizontal", variable=hour_var,
            command=on_slide, length=720, bg=self.colors["background"], fg=self.colors["text"],
            highlightthickness=0, troughcolor=self.colors["surface_alt"], label="Hour of day",
        )
        slider.pack(side="left", padx=(0, 12))

        def step():
            if not playing["on"]:
                return
            nxt = (hour_var.get() + 1) % 24
            slider.set(nxt)  # actualitza variable i dispara on_slide -> draw
            win.after(700, step)

        def toggle_play():
            playing["on"] = not playing["on"]
            play_btn.configure(text="⏸ Pause" if playing["on"] else "▶ Play")
            if playing["on"]:
                step()

        play_btn = tk.Button(
            controls, text="▶ Play", command=toggle_play,
            bg=self.colors["gold_fill"], fg=self.colors["text"], font=("Trebuchet MS", 11, "bold"),
            relief="groove", cursor="hand2", padx=14, pady=4,
        )
        play_btn.pack(side="left")

        def _on_close():
            playing["on"] = False
            win.destroy()

        win.protocol("WM_DELETE_WINDOW", _on_close)
        canvas.bind("<Configure>", lambda _e: draw(hour_var.get()))
        win.after(80, lambda: draw(0))


# Punt d'entrada: crea la finestra arrel i engega l'aplicació.
if __name__ == "__main__":
    root = tk.Tk()  # Finestra principal de tkinter
    app = AirportInterface(root)  # Construeix tota la interfície
    root.mainloop()  # Bucle d'esdeveniments (manté la finestra oberta)