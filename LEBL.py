import Arrivals
import airport  # V4 - per calcular el flag Schengen de les sortides
import matplotlib.pyplot as plt  # V4 - per dibuixar l'ocupació diària

class BarcelonaAP:
    # Aeroport sencer: un nom i la llista de terminals que conté.
    def __init__(self):
        self.name = ""
        self.terminals = []
class Terminal:
    # Un terminal: nom, llista d'àrees d'embarcament (BA) i aerolínies (air_code).
    def __init__(self):
        self.t_name = ""
        self.BA = []  # Boarding Areas (àrees d'embarcament)
        self.air_code = []  # Codis/noms d'aerolínies assignades al terminal
class Boarding_Area:
    # Una àrea d'embarcament: nom, portes que conté i si és Schengen.
    def __init__(self):
        self.area = ""
        self.Gates = []
        self.Schengen = False
class Gate:
    # Una porta d'embarcament: nom, si està ocupada i quin avió l'ocupa.
    def __init__(self):
        self.name = ""
        self.occupied = False
        self.craftID = ""  # id de l'avió que ocupa la porta ("" si està lliure)



def SetGates(area, init_gate, end_gate, prefix):
    # Crea les portes d'una àrea, numerades de init_gate fins a end_gate
    # amb el prefix de l'àrea (p. ex. A1, A2...). Si l'àrea ja en té, no fa res.
    i = 0
    if len(area.Gates) > 0:
        pass  # L'àrea ja té portes: no les tornem a crear
    else:
        if (int(end_gate)-int(init_gate)) < 0:
            print("error code -1")  # Rang de portes invàlid
        while i < (int(end_gate)-int(init_gate)):
            gate = Gate()
            gate.name = prefix+str(int(init_gate)+i)  # Nom: prefix + número
            area.Gates.append(gate)
            i += 1



def LoadAirlines(terminal, t_name):
    # Carrega les aerolínies del terminal des del fitxer "{t_name}_Airlines.txt".
    file = open(f"{t_name}_Airlines.txt","r")
    readline = file.readline()
    while readline != "":  # Llegim fins al final del fitxer
        terminal.air_code.append(readline)
        readline = file.readline().strip("\n")
    file.close()


def LoadAirportStructure (filename):
    # Llegeix el fitxer de terminals i construeix tota l'estructura de
    # l'aeroport (BarcelonaAP -> terminals -> àrees -> portes).
    file = open(filename,"r")
    lines = file.readlines()
    file.close()
    terminals = []
    i = 1  # Saltem la línia 0 (capçalera amb el nom de l'aeroport)
    while i < len(lines):
        linia = lines[i].split(" ")
        linia = [x for x in linia if x]  # Eliminem els camps buits (espais dobles)
        if linia[0] == "Terminal":
            # Nova línia de terminal -> creem un Terminal
            terminals.append(Terminal())
            terminals[-1].t_name = linia[1]
        if linia[0] == "Area":
            # Nova àrea dins de l'últim terminal creat
            terminals[-1].BA.append(Boarding_Area())
            terminals[-1].BA[-1].area = linia[1]
            # Creem les portes amb el rang indicat (camps 4 i 6 de la línia)
            SetGates(terminals[-1].BA[-1], linia[4], linia[6], linia[1])
            if linia[2] == "Schengen":
                terminals[-1].BA[-1].Schengen = True
        i += 1
    AirportStructure = BarcelonaAP()
    linia_0 = lines[0].split(" ")  # Primera línia (info de l'aeroport)
    for i in terminals:
        LoadAirlines(i,i.t_name)  # Carreguem les aerolínies de cada terminal
    AirportStructure.name = filename
    AirportStructure.terminals = terminals
    return AirportStructure

def GateOccupancy (bcn):
    # Retorna una llista amb l'estat (dict) de totes les portes de l'aeroport.
    Gates = []
    for i in bcn:  # Per cada terminal
        for j in i.BA:  # Per cada àrea
            for k in j.Gates:  # Per cada porta
                Gates.append(k.__dict__)  # __dict__ = {name, occupied, craftID}
    return Gates

def IsAirlineInTerminal (terminal, name):
    # Retorna True si l'aerolínia 'name' apareix entre les del terminal.
    for i in terminal.air_code:
        if name in i:
            return True

def SearchTerminal (bcn, name):
    # Retorna el nom del primer terminal on opera l'aerolínia (o None).
    for i in bcn:
        return i.name if IsAirlineInTerminal(i, name) else None

def AssignGate (bcn,aircraft):
    # Assigna a l'avió la primera porta lliure que compleixi: l'aerolínia
    # opera en el terminal I l'àrea coincideix en condició Schengen.
    # 'bcn' és la llista de terminals (BarcelonaAP.terminals).
    i = 0
    while i < len(bcn):  # Recorrem terminals

        if IsAirlineInTerminal(bcn[i],aircraft.airline):
            j = 0
            while j < len(bcn[i].BA):  # Recorrem àrees del terminal

                # L'àrea ha de ser del mateix tipus (Schengen / no Schengen) que l'avió
                if aircraft.schengen == bcn[i].BA[j].Schengen:
                    k = 0
                    while k < len(bcn[i].BA[j].Gates):  # Recorrem portes de l'àrea
                        if bcn[i].BA[j].Gates[k].occupied == False:
                            # Primera porta lliure trobada: l'ocupem i sortim
                            bcn[i].BA[j].Gates[k].occupied = True
                            bcn[i].BA[j].Gates[k].craftID = aircraft.id
                            return


                        k += 1
                j += 1
        i += 1



# --- Prova ràpida a nivell de mòdul (s'executa també en importar el fitxer) ---
arrivals = Arrivals.LoadArrivals("Arrivals.txt")  # Carreguem les arribades

bcn = LoadAirportStructure("Terminals.txt").terminals  # Estructura de portes
AssignGate(bcn,arrivals[0])  # Assignem porta al primer avió com a prova
print(GateOccupancy(bcn))  # Mostrem l'estat de totes les portes


# =====================================================================
# VERSIÓ 4 — Sortides, alliberament i assignació dinàmica de portes
# =====================================================================

def _terminals(bcn):
    """Accepta un BarcelonaAP o directament la llista de terminals (com fa
    AssignGate) i retorna sempre la llista de terminals. Així les noves
    funcions funcionen amb tots dos formats sense trencar els callers de la V3."""
    return bcn.terminals if hasattr(bcn, "terminals") else bcn


def _minutes(t):
    """Minuts des de mitjanit d'una hora 'HH:MM'; -1 si és buida/invàlida."""
    return Arrivals._time_to_minutes(t) if t else -1


def _departure_minutes(aircrafts, craft_id):
    """Hora de sortida (en minuts) de l'avió amb aquest id; -1 si no en té."""
    for a in aircrafts:
        if a.id == craft_id and a.departure_time:
            return Arrivals._time_to_minutes(a.departure_time)
    return -1


def _craft_in_gate(bcn, id):
    """Retorna True si l'avió amb aquest id ocupa alguna porta."""
    for terminal in _terminals(bcn):
        for area in terminal.BA:
            for gate in area.Gates:
                if gate.occupied and gate.craftID == id:
                    return True
    return False


def AssignNightGates(bcn, aircrafts):
    """bcn: BarcelonaAP; aircrafts: list. Assign a gate to each aircraft using
    the (new) AssignGate. Only process departure-only aircraft (empty arrival
    data); skip any that don't meet this. If the list is empty, return an error
    code."""
    if not aircrafts:
        return -1  # codi d'error: llista buida
    for aircraft in aircrafts:
        # Només avions amb dades de sortida i SENSE dades d'arribada
        if (aircraft.destination != "" and aircraft.departure_time != ""
                and aircraft.origin == "" and aircraft.arrival_time == ""):
            # Per a una sortida el Schengen es decideix per la destinació
            aircraft.schengen = airport.IsSchengenAirport(aircraft.destination)
            AssignGate(_terminals(bcn), aircraft)


def FreeGate(bcn, id):
    """bcn: BarcelonaAP; id: aircraft id. Set the gate currently occupied by
    that aircraft to free. If the aircraft is not found in any gate, return an
    error code."""
    for terminal in _terminals(bcn):
        for area in terminal.BA:
            for gate in area.Gates:
                if gate.occupied and gate.craftID == id:
                    gate.occupied = False
                    gate.craftID = ""
                    return
    return -1  # codi d'error: cap porta ocupada per aquest avió


def AssignGatesAtTime(bcn, aircrafts, time):
    """bcn: BarcelonaAP; aircrafts: list of arriving/departing aircraft; time:
    exact hour string ('01:00','02:00',...,'23:00'). Update bcn by assigning
    gates to aircraft that LAND during the one-hour period starting at 'time'.
    First FREE gates whose aircraft have already departed; then loop the list
    and assign gates to those landing in that hour. Return the number of
    aircraft landing in the period that could NOT be assigned (full occupancy).
    Gate assignment is therefore DYNAMIC across the day."""
    if not aircrafts:
        return -1  # codi d'error: llista buida
    terminals = _terminals(bcn)
    start = _minutes(time)
    if start < 0:
        return -1  # codi d'error: hora invàlida
    end = start + 60

    # 1) Alliberem les portes dels avions que ja han marxat (sortida <= inici)
    to_free = []
    for terminal in terminals:
        for area in terminal.BA:
            for gate in area.Gates:
                if gate.occupied:
                    dep = _departure_minutes(aircrafts, gate.craftID)
                    if 0 <= dep <= start:
                        to_free.append(gate.craftID)
    for craft_id in to_free:
        FreeGate(terminals, craft_id)

    # 2) Assignem porta als avions que aterren en aquesta franja [start, end)
    not_assigned = 0
    for aircraft in aircrafts:
        at = _minutes(aircraft.arrival_time)
        if start <= at < end:
            # El Schengen d'una arribada es decideix per l'origen
            if aircraft.origin != "":
                aircraft.schengen = airport.IsSchengenAirport(aircraft.origin)
            AssignGate(terminals, aircraft)
            # Comprovem si realment ha obtingut porta (sense tocar AssignGate)
            if not _craft_in_gate(terminals, aircraft.id):
                not_assigned += 1
    return not_assigned


def PlotDayOccupancy(bcn, aircrafts):
    """bcn: BarcelonaAP (state = start of day, only night aircraft assigned);
    aircrafts: full day list. Build a plot showing, per hour period of the day,
    the total number of gates assigned in every terminal, and the number of
    aircraft that were NOT assigned in that period."""
    if not aircrafts:
        return -1  # codi d'error: llista buida
    terminals = _terminals(bcn)
    names = [t.t_name for t in terminals]
    hours = list(range(24))
    per_terminal = {n: [] for n in names}
    unassigned = []

    # Recorrem el dia hora a hora (assignació dinàmica)
    for h in hours:
        nf = AssignGatesAtTime(terminals, aircrafts, f"{h:02d}:00")
        unassigned.append(nf if nf != -1 else 0)
        for t in terminals:
            occ = 0
            for area in t.BA:
                for gate in area.Gates:
                    if gate.occupied:
                        occ += 1
            per_terminal[t.t_name].append(occ)

    plt.figure(figsize=(12, 6))
    colors = ["#7cc7ed", "#7fd9ab", "#ebcf73", "#e7a3a3", "#b0a3e7", "#a3e7df"]
    bottoms = [0] * 24
    for idx, n in enumerate(names):
        plt.bar(hours, per_terminal[n], bottom=bottoms,
                label=f"{n} (portes)", color=colors[idx % len(colors)])
        bottoms = [bottoms[i] + per_terminal[n][i] for i in range(24)]
    plt.plot(hours, unassigned, color="red", marker="o", linewidth=2,
             label="Avions no assignats")
    plt.title("Ocupació de portes per franja horària")
    plt.xlabel("Hora del dia")
    plt.ylabel("Portes assignades / avions no assignats")
    plt.xticks(hours)
    plt.legend()
    plt.show()


# --- SECCIÓ DE TEST VERSIÓ 4 ---
if __name__ == "__main__":
    estructura = LoadAirportStructure("Terminals.txt")

    arribades = Arrivals.LoadArrivals("Arrivals.txt")
    sortides = Arrivals.LoadDepartures("Departures.txt")
    moviments = Arrivals.MergeMovements(arribades, sortides)
    nocturns = Arrivals.NightAircraft(moviments)
    print(f"Moviments: {len(moviments)} | Nocturns: {len(nocturns)}")

    # AssignNightGates (i el seu codi d'error amb llista buida)
    print("AssignNightGates([]) ->", AssignNightGates(estructura, []))
    AssignNightGates(estructura, nocturns)
    ocupades = [g for g in GateOccupancy(estructura.terminals) if g['occupied']]
    print(f"Portes ocupades després dels nocturns: {len(ocupades)}")

    # AssignGatesAtTime per a una franja concreta
    nf = AssignGatesAtTime(estructura, moviments, "08:00")
    print(f"Avions no assignats a la franja 08:00: {nf}")
    print("AssignGatesAtTime([]) ->", AssignGatesAtTime(estructura, [], "08:00"))

    # FreeGate (cas correcte i codi d'error)
    if ocupades:
        cid = ocupades[0]['craftID']
        print(f"FreeGate({cid}) ->", FreeGate(estructura, cid))
    print("FreeGate(inexistent) ->", FreeGate(estructura, "XXXXX"))

    # PlotDayOccupancy: reconstruïm l'estructura per començar net
    estructura2 = LoadAirportStructure("Terminals.txt")
    AssignNightGates(estructura2, nocturns)
    print("PlotDayOccupancy([]) ->", PlotDayOccupancy(estructura2, []))
    PlotDayOccupancy(estructura2, moviments)



