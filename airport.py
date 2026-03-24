import matplotlib.pyplot as plt

class Airport:
    def __init__(self, code, latitude, longitude):
        self.code = code
        self.latitude = latitude
        self.longitude = longitude
        self.Schengen = False


def IsSchengenAirport(code):
    Schengen = ('LO', 'EB', 'LK', 'LC', 'EK', 'EE', 'EF', 'LF', 'ED', 'LG', 'EH', 'LH', 'BI','LI', 'EV', 'EY', 'EL', 'LM', 'EN', 'EP', 'LP', 'LZ', 'LJ', 'LE', 'ES', 'LS')
    # AFEGIM [:2] perquè agafi només les dues primeres lletres del codi
    if code[:2] in Schengen:
        return True
    else:
        return False


def SetSchengen(airport):
    airport.Schengen = IsSchengenAirport(airport.code)

def PrintAirport(airport):
    print(str(airport.code) + " " + str(airport.latitude) + " " + str(airport.longitude) + " " + str(airport.Schengen))

def LoadAirports (filename):
    airports = []
    file = open(filename, 'r')
    lines = file.readlines()
    file.close()
    i = 1 # Saltem la línia 0 (l'encapçalament)
    while i < len(lines):
        w = lines[i].split(" ")
        code = w[0]
        latitude = 0
        latitude = float(w[1][1:3])
        latitude += float(w[1][3:5])/60
        latitude += float(w[1][5:7])/3600
        if w[1][0] == "S":
            latitude = -latitude
        longitude = 0
        longitude = float(w[2][1:4])
        longitude += float(w[2][4:6])/60
        longitude += float(w[2][6:8])/3600
        if w[2][0] == "W":
            longitude = -longitude
        airport = Airport(code, latitude, longitude)
        airports.append(airport)
        i = i + 1
    return airports

def SaveSchengenAirports(filename, airports):
    if airports == None:
        print("Error: No airports found")
    else:
        file = open(filename, 'w')
        file.write("CODE LAT LON\n")
        for item in airports:
            if IsSchengenAirport(item.code) == True:
                file.write(item.code + " " + str(item.latitude) + " " + str(item.longitude) + "\n")

def AddAirport (airports, airport):
    if airport not in airports:
        airports.append(airport)

def RemoveAirport (airports, code):
    i = 0
    while i < len(airports):
        if airports[i].code == code:
            airports = airports[:i] + airports[i+1:]
            return airports
        i += 1
    print("Error: No airport found")

def PlotAirports (airports):
    schengen = 0
    for item in airports:
        if IsSchengenAirport(item.code) == True:
            schengen += 1
    print(schengen)
    y1 = len(airports)
    plt.bar("Airports", schengen, color="blue")
    plt.bar("Airports", y1, bottom=schengen, color="pink")
    plt.title("Schengen Airports")
    plt.legend(["Schengen","No Schengen"], loc="upper right")
    plt.show()

def MapAirports(airports):
    import os
    filename = "airports.kml"
    file = open(filename, 'w')

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

    for apt in airports:
        file.write('  <Placemark>\n')
        file.write('    <name>' + apt.code + '</name>\n')

        if apt.Schengen == True:
            file.write('    <styleUrl>#schengen</styleUrl>\n')
        else:
            file.write('    <styleUrl>#non_schengen</styleUrl>\n')

        file.write('    <Point>\n')
        file.write('      <coordinates>' + str(apt.longitude) + ',' + str(apt.latitude) + ',0</coordinates>\n')
        file.write('    </Point>\n')
        file.write('  </Placemark>\n')

    file.write('</Document>\n')
    file.write('</kml>\n')
    file.close()
    os.startfile(filename)
