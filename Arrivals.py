import os  # Per obrir el fitxer KML generat amb l'aplicació per defecte (Google Earth)
import math  # Funcions matemàtiques (radians, sin, cos...) per la distància
import matplotlib.pyplot as plt  # Per dibuixar gràfics de barres
import airport  # Importem el fitxer de la Versió 1 per usar IsSchengenAirport i les coordenades


class Aircraft:
    # Representa un vol/avió. A partir de la V4 guarda també les dades de sortida
    # (destinació i hora de sortida), que queden buides per defecte.
    def __init__(self, id_flight, airline, origin, arrival_time,
                 destination="", departure_time=""):
        self.id = id_flight
        self.airline = airline
        self.origin = origin  # Codi ICAO de l'aeroport d'origen
        self.arrival_time = arrival_time  # Format "HH:MM"
        self.destination = destination  # Codi ICAO de destinació (V4 - sortides)
        self.departure_time = departure_time  # Format "HH:MM" (V4 - sortides)
        self.lat = 0.0  # Es posarà més tard buscant a la llista d'aeroports
        self.lon = 0.0
        self.schengen = False


def LoadArrivals(filename):
    """Llegeix el fitxer arrivals.txt i retorna una llista d'objectes Aircraft.
    Retorna -1 si el fitxer no es pot obrir."""
    # Format del fitxer: AIRCRAFT ORIGIN ARRIVAL AIRLINE
    arrivals = []
    # ERROR 1: el fitxer no existeix o no es pot llegir
    try:
        with open(filename, 'r') as file:
            lines = file.readlines()
    except Exception as e:
        print(f"Error llegint arribades: {e}")  # Si el fitxer no existeix, etc.
        return -1
    # ERROR 2: el fitxer es buit o nomes conte la linia de capçalera
    if len(lines) <= 1:
        print("Error: el fitxer d'arribades es buit o no conte dades.")
        return arrivals
    skipped = 0  # Comptador de linies amb format incorrecte
    for line in lines[1:]:  # Saltem l'encapçalament
        parts = line.split()  # Separem la línia per espais
        if len(parts) == 0:
            continue  # Linia en blanc: la saltem sense comptar-la com a error
        # ERROR 3: linia mal formada (falten camps o hora en format incorrecte)
        if len(parts) >= 4 and ":" in parts[2] and len(parts[2]) == 5:
            # id=parts[0], airline=parts[3], origin=parts[1], hora=parts[2]
            a = Aircraft(parts[0], parts[3], parts[1], parts[2])
            # Assignem si és Schengen usant la funció de airport.py
            a.schengen = airport.IsSchengenAirport(a.origin)
            arrivals.append(a)
        else:
            skipped += 1  # Linia que no segueix el format esperat
    if skipped > 0:
        print(f"Avis: {skipped} linies d'arribades amb format incorrecte s'han ignorat.")
    return arrivals


def Haversine(lat1, lon1, lat2, lon2):
    """Calcula la distància en km entre dos punts geogràfics."""
    # Fórmula de Haversine: distància sobre l'esfera terrestre a partir de
    # latituds/longituds. Es treballa amb els angles en radians.
    radius = 6371  # Radi de la Terra en km
    dlat = math.radians(lat2 - lat1)  # Diferència de latitud en radians
    dlon = math.radians(lon2 - lon1)  # Diferència de longitud en radians
    # 'a' combina les diferències angulars segons la fórmula de Haversine
    a = (math.sin(dlat / 2) * math.sin(dlat / 2) +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) * math.sin(dlon / 2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))  # Angle central entre punts
    return radius * c  # Distància = radi * angle


def PlotArrivals(aircrafts):
    """Gràfic de barres: Arribades per hora."""
    hours = [0] * 24  # Un comptador per cada hora del dia (0..23)
    for a in aircrafts:
        h = int(a.arrival_time.split(":")[0])  # Hora d'arribada (part abans del ':')
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


def MapFlights(aircrafts, airport_list, filename="flights_map.kml"):
    """Shows in Google Earth the trajectories of all flights in the list, from
    origin airport to LEBL. Show in different colors the trajectories with origin
    in a Schengen country. Remember that Annex A explains how to draw lines in
    Google Earth.
    """
    # Coordenades de Barcelona (LEBL) aproximades o buscades
    lebl_lat, lebl_lon = 41.297, 2.083

    with open(filename, 'w') as f:
        # Capçalera del document KML
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<kml xmlns="http://www.opengis.net/kml/2.2">\n')
        f.write('<Document>\n')

        # Definim dos estils de línia. El color KML va en ordre aabbggrr
        # (alfa, blau, verd, vermell).
        # Verd = origen en un país Schengen; Vermell = origen fora de Schengen.
        f.write('<Style id="schengen">\n')
        f.write('  <LineStyle><color>ff00ff00</color><width>3</width></LineStyle>\n')
        f.write('</Style>\n')
        f.write('<Style id="noschengen">\n')
        f.write('  <LineStyle><color>ff0000ff</color><width>3</width></LineStyle>\n')
        f.write('</Style>\n')

        # Funció auxiliar: busca les coordenades d'un aeroport pel seu codi ICAO
        def find_coords(code):
            for apt in airport_list:
                if apt.code == code:  # Coincidència de codi ICAO
                    return (apt.latitude, apt.longitude)
            return None

        for a in aircrafts:
            # --- Tram d'ARRIBADA: de l'aeroport d'origen fins a LEBL ---
            if a.origin != "":
                origin_coords = find_coords(a.origin)
                # Només dibuixem la línia si hem trobat les coordenades d'origen
                if origin_coords:
                    # Triem el color segons si l'origen és Schengen o no
                    if airport.IsSchengenAirport(a.origin):
                        style = "schengen"
                    else:
                        style = "noschengen"
                    f.write('<Placemark>\n')
                    f.write(f'  <name>{a.id} ({a.origin} -> LEBL)</name>\n')
                    f.write(f'  <styleUrl>#{style}</styleUrl>\n')
                    f.write('  <LineString>\n')
                    f.write('      <tessellate>1</tessellate>\n')  # La línia segueix el terreny
                    # Coordenades en ordre lon,lat,alt: origen i LEBL
                    f.write(f'    <coordinates>{origin_coords[1]},{origin_coords[0]},0 {lebl_lon},{lebl_lat},0</coordinates>\n')
                    f.write('  </LineString>\n')
                    f.write('</Placemark>\n')

            # --- Tram de SORTIDA: de LEBL fins a l'aeroport de destinació ---
            if a.destination != "":
                dest_coords = find_coords(a.destination)
                # Només dibuixem la línia si hem trobat les coordenades de destinació
                if dest_coords:
                    # Triem el color segons si la destinació és Schengen o no
                    if airport.IsSchengenAirport(a.destination):
                        style = "schengen"
                    else:
                        style = "noschengen"
                    f.write('<Placemark>\n')
                    f.write(f'  <name>{a.id} (LEBL -> {a.destination})</name>\n')
                    f.write(f'  <styleUrl>#{style}</styleUrl>\n')
                    f.write('  <LineString>\n')
                    f.write('      <tessellate>1</tessellate>\n')  # La línia segueix el terreny
                    # Coordenades en ordre lon,lat,alt: LEBL i destinació
                    f.write(f'    <coordinates>{lebl_lon},{lebl_lat},0 {dest_coords[1]},{dest_coords[0]},0</coordinates>\n')
                    f.write('  </LineString>\n')
                    f.write('</Placemark>\n')

        f.write('</Document>\n')
        f.write('</kml>\n')
    print(f"Mapa KML generat: {filename}")
    os.startfile(filename)  # Obre el fitxer amb Google Earth (o l'app per defecte)



# VERSIÓ 4 — Sortides, fusió de moviments i avions nocturns

def _time_to_minutes(t):
    """Converteix una hora 'H:MM' o 'HH:MM' a minuts des de mitjanit.
    Retorna -1 si la cadena no és una hora vàlida."""
    try:
        h, m = t.split(":")
        return int(h) * 60 + int(m)
    except Exception:
        return -1


def LoadDepartures(filename):
    """Opens the departures file and returns a list of Aircraft initialised
    with the data found. Update only the departure-related fields. If the file
    does not exist, return an empty list and an error code. File format:
        AIRCRAFT DESTINATION DEPARTURE AIRLINE
        ECMKV LYBE 0:04 VLG
        ECJGM EGCC 0:05 VLG
    """
    departures = []
    try:
        with open(filename, 'r') as file:
            lines = file.readlines()
    except Exception as e:
        print(f"Error llegint sortides: {e}")
        return -1  # ERROR 1: el fitxer no existeix o no es pot llegir
    # ERROR 2: el fitxer es buit o nomes conte la linia de capçalera
    if len(lines) <= 1:
        print("Error: el fitxer de sortides es buit o no conte dades.")
        return departures
    skipped = 0  # Comptador de linies amb format incorrecte
    for line in lines[1:]:  # Saltem l'encapçalament
        parts = line.split()
        if len(parts) == 0:
            continue  # Linia en blanc: la saltem sense comptar-la com a error
        # ERROR 3: linia mal formada (falten camps o hora en format incorrecte)
        if len(parts) >= 4 and ":" in parts[2] and _time_to_minutes(parts[2]) >= 0:
            # Només omplim les dades de sortida (origen/arribada buits)
            a = Aircraft(parts[0], parts[3], "", "", parts[1], parts[2])
            # Schengen segons la destinació de la sortida
            a.schengen = airport.IsSchengenAirport(a.destination)
            departures.append(a)
        else:
            skipped += 1  # Linia que no segueix el format esperat
    if skipped > 0:
        print(f"Avis: {skipped} linies de sortides amb format incorrecte s'han ignorat.")
    return departures


def MergeMovements(arrivals, departures):
    """Receives two lists of Aircraft (arrivals, departures) and returns a new
    list where aircraft with the same id AND compatible times are merged into
    one Aircraft (compatible = arrival time earlier than departure time). Some
    aircraft have only an arrival, some only a departure (night aircraft). If
    either input list is empty, return an error code. IMPORTANT: the same
    aircraft can land and take off MORE THAN ONCE during the same day, so an id
    may produce multiple merged Aircraft entries."""
    if not arrivals or not departures:
        return -1  # codi d'error: alguna llista és buida

    merged = []
    ids = set()
    for a in arrivals:
        ids.add(a.id)
    for d in departures:
        ids.add(d.id)

    for fid in ids:
        # Arribades i sortides d'aquest id, ordenades per hora
        arr = sorted([a for a in arrivals if a.id == fid],
                     key=lambda x: _time_to_minutes(x.arrival_time))
        dep = sorted([d for d in departures if d.id == fid],
                     key=lambda x: _time_to_minutes(x.departure_time))
        used = [False] * len(dep)

        for a in arr:
            at = _time_to_minutes(a.arrival_time)
            match = -1
            # Busquem la primera sortida lliure amb hora posterior a l'arribada
            for k in range(len(dep)):
                if not used[k] and _time_to_minutes(dep[k].departure_time) > at:
                    match = k
                    break
            if match >= 0:
                d = dep[match]
                used[match] = True
                m = Aircraft(a.id, a.airline, a.origin, a.arrival_time,
                             d.destination, d.departure_time)
                m.schengen = a.schengen
                merged.append(m)
            else:
                # Arribada sense sortida compatible (es queda a l'aeroport)
                m = Aircraft(a.id, a.airline, a.origin, a.arrival_time, "", "")
                m.schengen = a.schengen
                merged.append(m)

        # Sortides no aparellades amb cap arribada -> avions nocturns
        for k in range(len(dep)):
            if not used[k]:
                d = dep[k]
                m = Aircraft(d.id, d.airline, "", "", d.destination, d.departure_time)
                m.schengen = d.schengen
                merged.append(m)

    # Ordenem per hora efectiva (arribada si en té, si no la sortida)
    merged.sort(key=lambda x: _time_to_minutes(x.arrival_time)
                if x.arrival_time else _time_to_minutes(x.departure_time))
    return merged


def NightAircraft(aircrafts):
    """Returns a new list with the aircraft that have departure info set but no
    arrival info. If the input list is empty, return an error code."""
    if not aircrafts:
        return -1  # codi d'error: llista buida
    night = []
    for a in aircrafts:
        has_departure = a.destination != "" and a.departure_time != ""
        has_arrival = a.origin != "" and a.arrival_time != ""
        if has_departure and not has_arrival:
            night.append(a)
    return night


def FindTerminal(bcn, name):
    """Busca un terminal pel seu nom i el retorna. 'bcn' pot ser un BarcelonaAP
    o directament la llista de terminals. Retorna None si no el troba."""
    # Acceptem tant un BarcelonaAP (amb .terminals) com una llista de terminals
    if hasattr(bcn, "terminals"):
        terminals = bcn.terminals
    else:
        terminals = bcn

    # Preparem el nom buscat sense espais ni majúscules per comparar bé
    name_to_find = name.strip().upper()

    # Recorrem tots els terminals i comparem el seu nom
    for terminal in terminals:
        if terminal.t_name.upper() == name_to_find:
            return terminal

    # Si arribem aquí, no hi ha cap terminal amb aquest nom
    return None


# --- SECCIÓ DE TEST ---
if __name__ == "__main__":
    # --- TEST VERSIÓ 4 (sortides, fusió i avions nocturns) ---
    arribades = LoadArrivals("Arrivals.txt")
    print(f"Arribades carregades: {len(arribades)}")

    sortides = LoadDepartures("Departures.txt")
    if sortides == -1:
        print("Error: no s'ha pogut obrir el fitxer de sortides.")
    else:
        print(f"Sortides carregades: {len(sortides)}")

    # Comprovem el codi d'error amb un fitxer inexistent
    print("LoadDepartures fitxer inexistent ->", LoadDepartures("no_existeix.txt"))

    moviments = MergeMovements(arribades, sortides)
    if moviments == -1:
        print("Error: una de les llistes està buida.")
    else:
        print(f"Moviments fusionats: {len(moviments)}")
        complets = [m for m in moviments if m.origin and m.destination]
        print(f"  - amb arribada i sortida: {len(complets)}")
        if complets:
            m = complets[0]
            print(f"    Exemple: {m.id} {m.origin} {m.arrival_time}"
                  f" -> {m.destination} {m.departure_time}")
        # Codi d'error amb una llista buida
        print("MergeMovements(arribades, []) ->", MergeMovements(arribades, []))

    base = moviments if moviments != -1 else []
    nocturns = NightAircraft(base)
    if nocturns == -1:
        print("Error: llista buida per a NightAircraft.")
    else:
        print(f"Avions nocturns (només sortida): {len(nocturns)}")
    print("NightAircraft([]) ->", NightAircraft([]))

    # Gràfics de les versions anteriors (només si hi ha dades)
    if arribades:
        PlotArrivals(arribades)
        PlotAirlines(arribades)

