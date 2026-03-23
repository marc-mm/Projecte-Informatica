
class Airport:
    def __init__(self):
        self.code = ""
        self.latitude = 0.0
        self.longitude = 0.0
        self.Schengen = False

airport = Airport()

def IsSchengenAirport(code):
    Schengen = ('LO', 'EB', 'LK', 'LC', 'EK', 'EE', 'EF', 'LF', 'ED', 'LG', 'EH', 'LH', 'BI','LI', 'EV', 'EY', 'EL', 'LM', 'EN', 'EP', 'LP', 'LZ', 'LJ', 'LE', 'ES', 'LS')
    if code in Schengen:
        return True

def SetSchengen(airport):
    if IsSchengenAirport(airport.code) == True:
        airport.Schengen = True
def PrintAirport(airport):
    print(airport)


def parse_coordinate(coord_str):
    # Aquesta funció tradueix coses com 'N635906' o 'W0223620' a decimals
    direction = coord_str[0]


    degrees = float(coord_str[1:-4])
    minutes = float(coord_str[-4:-2])
    seconds = float(coord_str[-2:])

    # Passem tot a format decimal
    decimal_val = degrees + (minutes / 60) + (seconds / 3600)

    # Si és Sud o Oest, la coordenada ha de ser negativa
    if direction == 'S' or direction == 'W':
        decimal_val = -decimal_val

    return decimal_val


def LoadAirports(filename):
    airports = []
    file = open(filename, 'r')
    lines = file.readlines()

    for line in lines[1:]:  # Saltem la línia 0 (l'encapçalament)
        w = line.split()
        if len(w) == 3:
            airport = Airport()
            airport.code = w[0]
            # Utilitzem el "traductor" per llegir les coordenades
            airport.latitude = parse_coordinate(w[1])
            airport.longitude = parse_coordinate(w[2])
            airports.append(airport)

    file.close()
    return airports
def SaveSchengenAirports(filename, airports):
    file = open(filename, 'w')
    for item in airports:
        if IsSchengenAirport(item.code) == True:
            file.write(item.code + " is Schengen\n")