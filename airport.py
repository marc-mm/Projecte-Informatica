import matplotlib.pyplot as plt  # Llibreria per dibuixar gràfics


class Airport:
    # Representa un aeroport amb el seu codi ICAO, coordenades i flag Schengen.
    def __init__(self, code, latitude, longitude):
        self.code = code  # Codi ICAO (p. ex. "LEBL")
        self.latitude = latitude  # Latitud en graus decimals
        self.longitude = longitude  # Longitud en graus decimals
        self.Schengen = False  # Es calcularà més tard amb SetSchengen


def IsSchengenAirport(code):
    # Tupla amb els prefixos ICAO (2 lletres) dels països de l'espai Schengen.
    Schengen = ('LO', 'EB', 'LK', 'LC', 'EK', 'EE', 'EF', 'LF', 'ED', 'LG', 'EH', 'LH', 'BI','LI', 'EV', 'EY', 'EL', 'LM', 'EN', 'EP', 'LP', 'LZ', 'LJ', 'LE', 'ES', 'LS')
    # AFEGIM [:2] perquè agafi només les dues primeres lletres del codi
    if code[:2] in Schengen:
        return True
    else:
        return False


def SetSchengen(airport):
    # Assigna a l'aeroport si és o no Schengen segons el seu codi.
    airport.Schengen = IsSchengenAirport(airport.code)

def PrintAirport(airport):
    # Mostra per pantalla les dades bàsiques de l'aeroport.
    print(str(airport.code) + " " + str(airport.latitude) + " " + str(airport.longitude) + " " + str(airport.Schengen))

def LoadAirports (filename):
    # Llegeix un fitxer d'aeroports i retorna una llista d'objectes Airport.
    # Les coordenades venen en format graus/minuts/segons enganxats (DDMMSS)
    # amb un prefix de hemisferi (N/S per latitud, E/W per longitud).
    airports = []
    file = open(filename, 'r')
    lines = file.readlines()
    file.close()
    i = 1 # Saltem la línia 0 (l'encapçalament)
    while i < len(lines):
        w = lines[i].split(" ")  # Separem la línia en camps
        code = w[0]  # Primer camp: codi ICAO
        # --- Conversió de la latitud (DMS -> graus decimals) ---
        latitude = 0
        latitude = float(w[1][1:3])  # Graus (posicions 1-2, la 0 és N/S)
        latitude += float(w[1][3:5])/60  # Minuts -> graus
        latitude += float(w[1][5:7])/3600  # Segons -> graus
        if w[1][0] == "S":  # Hemisferi sud -> latitud negativa
            latitude = -latitude
        # --- Conversió de la longitud (DMS -> graus decimals) ---
        longitude = 0
        longitude = float(w[2][1:4])  # Graus (la longitud en té 3 dígits)
        longitude += float(w[2][4:6])/60  # Minuts -> graus
        longitude += float(w[2][6:8])/3600  # Segons -> graus
        if w[2][0] == "W":  # Oest -> longitud negativa
            longitude = -longitude
        airport = Airport(code, latitude, longitude)
        airports.append(airport)
        i = i + 1
    return airports

def SaveSchengenAirports(filename, airports):
    # Desa en un fitxer només els aeroports que són Schengen.
    if airports == None:
        print("Error: No airports found")  # Cap aeroport a la llista
    else:
        with open(filename, 'w', encoding="utf-8") as file:
            file.write("CODE LAT LON\n")  # Capçalera del fitxer
            for item in airports:
                if IsSchengenAirport(item.code) == True:
                    file.write(item.code + " " + str(item.latitude) + " " + str(item.longitude) + "\n")

def AddAirport (airports, airport):
    # Afegeix un aeroport a la llista si encara no hi és.
    if airport not in airports:
        airports.append(airport)

def RemoveAirport (airports, code):
    # Elimina de la llista l'aeroport amb el codi indicat i retorna la nova llista.
    i = 0
    while i < len(airports):
        if airports[i].code == code:
            airports = airports[:i] + airports[i+1:]  # Llista sense l'element i
            return airports
        i += 1
    print("Error: No airport found")  # No s'ha trobat cap aeroport amb aquest codi

def PlotAirports (airports):
    # Gràfic de barres apilades: aeroports Schengen vs total.
    schengen = 0
    for item in airports:
        if IsSchengenAirport(item.code) == True:
            schengen += 1  # Comptem quants són Schengen
    print(schengen)
    y1 = len(airports)  # Total d'aeroports
    plt.bar("Airports", schengen, color="blue")  # Part Schengen (a sota)
    plt.bar("Airports", y1, bottom=schengen, color="pink")  # Resta a sobre
    plt.title("Schengen Airports")
    plt.legend(["Schengen","No Schengen"], loc="upper right")
    plt.show()

def MapAirports(airports, filename="airports.kml"):
    # Genera un fitxer KML (Google Earth) amb un marcador per cada aeroport,
    # verd si és Schengen i vermell si no ho és, i l'obre automàticament.
    import os
    file = open(filename, 'w', encoding="utf-8")

    # Capçalera estàndard d'un document KML
    file.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    file.write('<kml xmlns="http://www.opengis.net/kml/2.2">\n')
    file.write('<Document>\n')

    # 1. Estil Verd (Schengen) - ENLLAÇ CORREGIT
    file.write('  <Style id="schengen">\n')
    file.write('    <IconStyle>\n')
    file.write('      <Icon>\n')
    file.write('        <href>http://maps.google.com/mapfiles/kml/paddle/grn-circle.png</href>\n')
    file.write('      </Icon>\n')
    file.write('    </IconStyle>\n')
    file.write('  </Style>\n')

    # 2. Estil Vermell (No Schengen) - ENLLAÇ CORREGIT
    file.write('  <Style id="non_schengen">\n')
    file.write('    <IconStyle>\n')
    file.write('      <Icon>\n')
    file.write('        <href>http://maps.google.com/mapfiles/kml/paddle/red-circle.png</href>\n')
    file.write('      </Icon>\n')
    file.write('    </IconStyle>\n')
    file.write('  </Style>\n')

    # Un Placemark (marcador) per cada aeroport
    for apt in airports:
        file.write('  <Placemark>\n')
        file.write('    <name>' + apt.code + '</name>\n')

        # Triem l'estil de color segons si és Schengen o no
        if IsSchengenAirport(apt.code) == True:
            file.write('    <styleUrl>#schengen</styleUrl>\n')
        else:
            file.write('    <styleUrl>#non_schengen</styleUrl>\n')

        # El KML vol les coordenades en ordre longitud,latitud,altitud
        file.write('    <Point>\n')
        file.write('      <coordinates>' + str(apt.longitude) + ',' + str(apt.latitude) + ',0</coordinates>\n')
        file.write('    </Point>\n')
        file.write('  </Placemark>\n')

    file.write('</Document>\n')
    file.write('</kml>\n')
    file.close()
    os.startfile(filename)  # Obre el fitxer amb Google Earth (o l'app per defecte)
    return filename
