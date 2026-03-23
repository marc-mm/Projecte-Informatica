import matplotlib.pyplot as plt

class Airport:
    def __init__(self, code, latitude, longitude):
        self.code = code
        self.latitude = latitude
        self.longitude = longitude
        self.Schengen = False

def IsSchengenAirport(code):
    Schengen = ('LO', 'EB', 'LK', 'LC', 'EK', 'EE', 'EF', 'LF', 'ED', 'LG', 'EH', 'LH', 'BI','LI', 'EV', 'EY', 'EL', 'LM', 'EN', 'EP', 'LP', 'LZ', 'LJ', 'LE', 'ES', 'LS')
    if code[:2] in Schengen:
        return True
    else:
        return False


def SetSchengen(airport):
    if IsSchengenAirport(airport.code) == True:
        setattr(airport, 'Schengen', True)

def PrintAirport(airport):
    print(str(airport.code) + " " + str(airport.latitude) + " " + str(airport.longitude) + " " + str(airport.Schengen))

def LoadAirports (filename):
    airports = []
    file = open(filename, 'r')
    lines = file.readlines()
    i = 1
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
        return "Error: No airports found"
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
        if item.Schengen == True:
            schengen += 1
    y1 = len(airports)-schengen
    plt.bar("Airports", y1, color="pink")
    plt.bar("Airports", schengen, bottom=y1, color="blue")
    plt.show()
