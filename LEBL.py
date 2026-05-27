from pathlib import Path
import airport

class BarcelonaAP:
    def __init__(self):
        self.name = ""
        self.terminals = []
class Terminal:
    def __init__(self):
        self.t_name = ""
        self.BA = []
        self.air_code = []
class Boarding_Area:
    def __init__(self):
        self.area = ""
        self.Gates = []
        self.Schengen = False
class Gate:
    def __init__(self):
        self.name = ""
        self.occupied = False
        self.craftID = ""



def SetGates(area, init_gate, end_gate, prefix):
    if len(area.Gates) > 0:
        return
    if int(end_gate) < int(init_gate):
        print("error code -1")
        return
    for gate_number in range(int(init_gate), int(end_gate) + 1):
        gate = Gate()
        gate.name = prefix + str(gate_number)
        area.Gates.append(gate)



def LoadAirlines(terminal, t_name, base_dir=None):
    directory = Path(base_dir) if base_dir else Path(__file__).resolve().parent
    with open(directory / f"{t_name}_Airlines.txt", "r", encoding="utf-8") as file:
        terminal.air_code = [line.strip() for line in file if line.strip()]


def LoadAirportStructure (filename):
    path = Path(filename)
    if not path.is_absolute():
        path = Path(__file__).resolve().parent / path
    with open(path, "r", encoding="utf-8") as file:
        lines = file.readlines()
    terminals = []
    i = 1
    while i < len(lines):
        linia = lines[i].split(" ")
        linia = [x for x in linia if x]
        if linia[0] == "Terminal":
            terminals.append(Terminal())
            terminals[-1].t_name = linia[1]
        if linia[0] == "Area":
            terminals[-1].BA.append(Boarding_Area())
            terminals[-1].BA[-1].area = linia[1]
            SetGates(terminals[-1].BA[-1], linia[4], linia[6], linia[1])
            if linia[2] == "Schengen":
                terminals[-1].BA[-1].Schengen = True
        i += 1
    AirportStructure = BarcelonaAP()
    linia_0 = lines[0].split(" ")
    for i in terminals:
        LoadAirlines(i, i.t_name, path.parent)
    AirportStructure.name = linia_0[0]
    AirportStructure.terminals = terminals
    return AirportStructure

def GateOccupancy (bcn):
    Gates = []
    for i in bcn:
        for j in i.BA:
            for k in j.Gates:
                Gates.append(k.__dict__)
    return Gates


def FindTerminal(bcn, terminal_name):
    terminal_name = terminal_name.strip().upper()
    for terminal in bcn.terminals:
        if terminal.t_name.upper() == terminal_name:
            return terminal
    return None


def FindArea(terminal, area_name):
    area_name = area_name.strip().upper()
    for area in terminal.BA:
        if area.area.upper() == area_name:
            return area
    return None


def AirlineMatches(airline_line, airline_query):
    airline_query = airline_query.strip().upper()
    parts = airline_line.upper().split()
    return bool(parts) and (airline_query == parts[-1] or airline_query in airline_line.upper())


def IsAirlineInTerminal(terminal, airline_query):
    return any(AirlineMatches(line, airline_query) for line in terminal.air_code)


def SearchTerminal(bcn, airline_query):
    return [terminal for terminal in bcn.terminals if IsAirlineInTerminal(terminal, airline_query)]


def AssignGate(bcn, aircraft_id, airline_query, origin_code):
    terminals = SearchTerminal(bcn, airline_query)
    if not terminals:
        return None
    needs_schengen = airport.IsSchengenAirport(origin_code.strip().upper())
    for area in terminals[0].BA:
        if area.Schengen == needs_schengen:
            for gate in area.Gates:
                if not gate.occupied:
                    gate.occupied = True
                    gate.craftID = aircraft_id.strip().upper()
                    return terminals[0], area, gate
    return None


if __name__ == "__main__":
    print(GateOccupancy(LoadAirportStructure("Terminals.txt").terminals))
