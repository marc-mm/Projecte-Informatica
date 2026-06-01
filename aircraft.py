# NOTA: aquest fitxer és una versió antiga/duplicada del mòdul de vols. El que
# realment fa servir el projecte (LEBL.py i Interface.py) és Arrivals.py. Es
# manté aquí com a còpia històrica; comentat per completesa.

import math  # Funcions matemàtiques per a la distància (Haversine)
import matplotlib.pyplot as plt  # Per dibuixar gràfics
import airport  # Importem el fitxer de la Versió 1 per usar IsSchengenAirport i les coordenades


class Aircraft:
    # Representa un vol/avió amb el seu identificador, aerolínia, origen i hora.
    def __init__(self, id_flight, airline, origin, arrival_time):
        self.id = id_flight
        self.airline = airline
        self.origin = origin  # Codi ICAO de l'aeroport d'origen
        self.arrival_time = arrival_time  # Format "HH:MM"
        self.lat = 0.0  # Es posarà més tard buscant a la llista d'aeroports
        self.lon = 0.0
        self.schengen = False


def LoadArrivals(filename):
    """Llegeix el fitxer arrivals.txt i retorna una llista d'objectes Aircraft."""
    arrivals = []
    try:
        with open(filename, 'r') as file:
            lines = file.readlines()
            for line in lines[1:]:  # Saltem l'encapçalament
                parts = line.split()  # Separem la línia per espais
                if len(parts) >= 4:
                    # Validació bàsica de l'hora (format HH:MM)
                    hora = parts[3]
                    if ":" in hora and len(hora) == 5:
                        a = Aircraft(parts[0], parts[1], parts[2], hora)
                        # Assignem si és Schengen usant la funció de airport.py
                        a.schengen = airport.IsSchengenAirport(a.origin)
                        arrivals.append(a)
    except Exception as e:
        print(f"Error llegint arribades: {e}")  # Si el fitxer no existeix, etc.
    return arrivals


def Haversine(lat1, lon1, lat2, lon2):
    """Calcula la distància en km entre dos punts geogràfics."""
    # Fórmula de Haversine (distància sobre l'esfera terrestre), angles en radians.
    radius = 6371  # Radi de la Terra en km
    dlat = math.radians(lat2 - lat1)  # Diferència de latitud en radians
    dlon = math.radians(lon2 - lon1)  # Diferència de longitud en radians
    a = (math.sin(dlat / 2) * math.sin(dlat / 2) +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) * math.sin(dlon / 2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))  # Angle central
    return radius * c  # Distància = radi * angle


def PlotArrivals(aircrafts):
    """Gràfic de barres: Arribades per hora."""
    hours = [0] * 24  # Un comptador per cada hora del dia (0..23)
    for a in aircrafts:
        h = int(a.arrival_time.split(":")[0])  # Hora d'arribada
        hours[h] += 1  # Sumem una arribada en aquesta hora

    plt.figure(figsize=(10, 5))
    plt.bar(range(24), hours, color='skyblue')
    plt.title("Frequència d'arribades per hora")
    plt.xlabel("Hora del dia")
    plt.ylabel("Número de vols")
    plt.xticks(range(24))
    plt.show()


def PlotAirlines(aircrafts):
    """Gràfic de barres: Vols per aerolínia."""
    stats = {}  # Diccionari aerolínia -> nombre de vols
    for a in aircrafts:
        stats[a.airline] = stats.get(a.airline, 0) + 1  # Comptem cada aerolínia

    plt.figure(figsize=(10, 5))
    plt.bar(stats.keys(), stats.values(), color='lightgreen')
    plt.title("Vols per Aerolínia")
    plt.ylabel("Número de vols")
    plt.show()


def MapFlights(aircrafts, airport_list):
    """Genera un KML amb les trajectòries des de l'origen fins a Barcelona (LEBL)."""
    # Coordenades de Barcelona (LEBL) aproximades o buscades
    lebl_lat, lebl_lon = 41.297, 2.083

    filename = "flights_map.kml"
    with open(filename, 'w') as f:
        # Capçalera del document KML
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<kml xmlns="http://www.opengis.net/kml/2.2">\n')
        f.write('<Document>\n')

        for a in aircrafts:
            # Busquem les coordenades de l'aeroport d'origen a la llista de la Versió 1
            origin_coords = None
            for apt in airport_list:
                if apt.code == a.origin:  # Coincidència de codi ICAO
                    origin_coords = (apt.latitude, apt.longitude)
                    break

            # Només dibuixem la línia si tenim les coordenades d'origen
            if origin_coords:
                f.write('<Placemark>\n')
                f.write(f'  <name>{a.id} ({a.origin} -> LEBL)</name>\n')
                f.write('  <LineString>\n')
                # Coordenades en ordre lon,lat,alt: origen i LEBL
                f.write(
                    f'    <coordinates>{origin_coords[1]},{origin_coords[0]},0 {lebl_lon},{lebl_lat},0</coordinates>\n')
                f.write('  </LineString>\n')
                f.write('</Placemark>\n')

        f.write('</Document>\n')
        f.write('</kml>\n')
    print("Mapa KML generat: flights_map.kml")


# --- SECCIÓ DE TEST ---
if __name__ == "__main__":
    # 1. Necessitem carregar primer els aeroports per tenir les coordenades
    # Suposant que tens el fitxer "airports.txt"
    llista_aeroports = airport.LoadAirports("airports.txt")
    for a in llista_aeroports:
        airport.SetSchengen(a)  # Calculem el flag Schengen de cada aeroport

    # 2. Carreguem els vols
    vols = LoadArrivals("arrivals.txt")
    print(f"S'han carregat {len(vols)} vols.")

    # 3. Provem els gràfics (només si s'han carregat vols)
    if vols:
        PlotArrivals(vols)
        PlotAirlines(vols)