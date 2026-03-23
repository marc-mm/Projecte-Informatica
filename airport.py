
class Airport:
    def __init__(self):
        self.code = ""
        self.latitude = 0.0
        self.longitude = 0.0
        self.Schengen = False

airport = Airport()

def IsSchengenAirport(code):
    Schengen = ('LO', 'EB', 'LK', 'LC', 'EK', 'EE', 'EF', 'LF', 'ED', 'LG', 'EH', 'LH', 'BI','LI', 'EV', 'EY', 'EL', 'LM', 'EN', 'EP', 'LP', 'LZ', 'LJ', 'LE', 'ES', 'LS')
    if code[0:1] in Schengen:
        return True

def SetSchengen(airport):
    if IsSchengenAirport(airport.code) == True:
        airport.Schengen = True
def PrintAirport(airport):
    print(airport)

def LoadAirports (filename):
    airports = []
    file = open(filename, 'r')
    lines = file.readlines()
    for line in lines:
        w = line.split(" ")
        airport = Airport()
        airport.code = w[0]
        airport.latitude = float(w[1])
        airport.longitude = float(w[2])
        airports.append(airport)
    return airports

def SaveSchengenAirports(filename, airports):
    if airports == None:
        return "Error: No airports found"
    else:
        file = open(filename, 'w')
        file.write("CODE LAT LON")
        for item in airports:
            if IsSchengenAirport(item.code) == True:
                file.write(item.code + " " + item.latitude + " " + item.longitude)

def AddAirport (airports, airport):
    if airport not in airports:
        airports.append(airport)
def RemoveAirport (airports, code):
    i = 0
    while i < len(airports):
        if airports[i].code == code:
            airports = airports[:i] + airports[i+1:]
        i += 1
