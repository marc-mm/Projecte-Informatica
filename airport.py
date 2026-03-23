
class Airport:
    def __init__(self):
        self.code = ""
        self.latitude = 0.0
        self.longitude = 0.0
        self.Schengen = False

airport = Airport()

def IsSchengenAirport(code):
    Schengen = ('LO', 'EB', 'LK', 'LC', 'EK', 'EE', 'EF', 'LF', 'ED', 'LG', 'EH', 'LH', 'BI', 'LI', 'EV', 'EY', 'EL', 'LM', 'EN', 'EP', 'LP', 'LR', 'LZ', 'LJ', 'LE', 'LS', 'ES')
    # AFEGIM [:2] perquè agafi només les dues primeres lletres del codi
    if code[:2] in Schengen:
        return True
    return False


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

def SetSchengen(airport):
    if IsSchengenAirport(airport.code) == True:
        airport.Schengen = True
def PrintAirport(airport):
    print(airport)

def PlotAirports(airports):
    import matplotlib.pyplot as plt

    # 1. Comptem quants aeroports n'hi ha de cada tipus
    schengen_count = 0
    non_schengen_count = 0

    for apt in airports:
        if apt.Schengen == True:
            schengen_count += 1
        else:
            non_schengen_count += 1

    # 2. Creem el llenç del gràfic (AQUESTA ÉS LA LÍNIA QUE FALTAVA!)
    fig, ax = plt.subplots()

    # Dibuixem la base: la barra dels Schengen (blau per defecte)
    ax.bar(['Airports'], [schengen_count], label='Schengen')

    # Dibuixem la part de dalt: la barra dels No Schengen
    ax.bar(['Airports'], [non_schengen_count], bottom=[schengen_count], color='salmon', label='No Schengen')

    # 3. Posem títols i llegenda
    ax.set_title('Schengen airports')
    ax.set_ylabel('Count')
    ax.legend()

    # 4. Mostrem la finestra amb el gràfic
    plt.show()

def SaveSchengenAirports(filename, airports):
    file = open(filename, 'w')
    for item in airports:
        if IsSchengenAirport(item.code) == True:
            file.write(item.code + " is Schengen\n")