from pathlib import Path
import airport

# --- Data model: represents the full airport hierarchy ---
# BarcelonaAP -> Terminal -> Boarding_Area -> Gate

class BarcelonaAP:
    def __init__(self):
        self.name = ""          # Airport name read from the first line of the structure file
        self.terminals = []     # List of Terminal objects

class Terminal:
    def __init__(self):
        self.t_name = ""    # Terminal identifier (e.g. "T1", "T2")
        self.BA = []        # List of Boarding_Area objects belonging to this terminal
        self.air_code = []  # Lines from the terminal's airlines file (airline name + IATA code)

class Boarding_Area:
    def __init__(self):
        self.area = ""          # Area identifier used as the gate prefix (e.g. "A", "B")
        self.Gates = []         # List of Gate objects in this area
        self.Schengen = False   # True if this area handles Schengen flights only

class Gate:
    def __init__(self):
        self.name = ""          # Full gate name, e.g. "A12"
        self.occupied = False   # Whether an aircraft is currently assigned here
        self.craftID = ""       # Aircraft ID occupying the gate, empty when free



def SetGates(area, init_gate, end_gate, prefix):
    # Skip if gates were already created (prevents duplicate initialization)
    if len(area.Gates) > 0:
        return
    if int(end_gate) < int(init_gate):
        print("error code -1")
        return
    # Create one Gate per number in the range [init_gate, end_gate] inclusive
    for gate_number in range(int(init_gate), int(end_gate) + 1):
        gate = Gate()
        gate.name = prefix + str(gate_number)   # e.g. prefix="A", number=12 -> "A12"
        area.Gates.append(gate)



def LoadAirlines(terminal, t_name, base_dir=None):
    # Resolve the directory: use base_dir if provided, otherwise the script's own directory
    directory = Path(base_dir) if base_dir else Path(__file__).resolve().parent
    # Read all non-empty lines from "<T_NAME>_Airlines.txt" into terminal.air_code
    with open(directory / f"{t_name}_Airlines.txt", "r", encoding="utf-8") as file:
        terminal.air_code = [line.strip() for line in file if line.strip()]


def LoadAirportStructure(filename):
    # Resolve to absolute path relative to the script if not already absolute
    path = Path(filename)
    if not path.is_absolute():
        path = Path(__file__).resolve().parent / path

    with open(path, "r", encoding="utf-8") as file:
        lines = file.readlines()

    terminals = []
    i = 1   # Skip line 0 (airport name), parsed separately below
    while i < len(lines):
        # Tokenize the line, discarding extra whitespace
        linia = lines[i].split(" ")
        linia = [x for x in linia if x]

        if linia[0] == "Terminal":
            # "Terminal <name>" -> create a new Terminal and record its name
            terminals.append(Terminal())
            terminals[-1].t_name = linia[1]

        if linia[0] == "Area":
            # "Area <prefix> <Schengen|NonSchengen> ... from <init> to <end>"
            # Tokens: [0]=Area [1]=prefix [2]=Schengen? [3]=... [4]=init [5]=to [6]=end
            terminals[-1].BA.append(Boarding_Area())
            terminals[-1].BA[-1].area = linia[1]
            SetGates(terminals[-1].BA[-1], linia[4], linia[6], linia[1])
            if linia[2] == "Schengen":
                terminals[-1].BA[-1].Schengen = True
        i += 1

    AirportStructure = BarcelonaAP()
    linia_0 = lines[0].split(" ")

    # Load each terminal's airline list from its corresponding text file
    for i in terminals:
        LoadAirlines(i, i.t_name, path.parent)

    AirportStructure.name = linia_0[0]
    AirportStructure.terminals = terminals
    return AirportStructure


def GateOccupancy(bcn):
    # Flatten all gates across every terminal and area into a list of dicts
    # Each dict has the Gate's fields: name, occupied, craftID
    Gates = []
    for i in bcn:           # iterate terminals
        for j in i.BA:      # iterate boarding areas
            for k in j.Gates:
                Gates.append(k.__dict__)
    return Gates


def FindTerminal(bcn, terminal_name):
    # Case-insensitive lookup of a terminal by name; returns None if not found
    terminal_name = terminal_name.strip().upper()
    for terminal in bcn.terminals:
        if terminal.t_name.upper() == terminal_name:
            return terminal
    return None


def FindArea(terminal, area_name):
    # Case-insensitive lookup of a boarding area within a terminal; returns None if not found
    area_name = area_name.strip().upper()
    for area in terminal.BA:
        if area.area.upper() == area_name:
            return area
    return None


def AirlineMatches(airline_line, airline_query):
    # Returns True if the query matches the last token (IATA code) or appears anywhere in the line
    airline_query = airline_query.strip().upper()
    parts = airline_line.upper().split()
    return bool(parts) and (airline_query == parts[-1] or airline_query in airline_line.upper())


def IsAirlineInTerminal(terminal, airline_query):
    # Returns True if any line in the terminal's airline list matches the query
    return any(AirlineMatches(line, airline_query) for line in terminal.air_code)


def SearchTerminal(bcn, airline_query):
    # Returns a list of terminals that serve the given airline (by name or IATA code)
    return [terminal for terminal in bcn.terminals if IsAirlineInTerminal(terminal, airline_query)]


def AssignGate(bcn, aircraft_id, airline_query, origin_code):
    # Find which terminal(s) handle this airline
    terminals = SearchTerminal(bcn, airline_query)
    if not terminals:
        return None

    # Determine whether the flight needs a Schengen or non-Schengen area
    needs_schengen = airport.IsSchengenAirport(origin_code.strip().upper())

    # Search the first matching terminal for a free gate in the correct area type
    for area in terminals[0].BA:
        if area.Schengen == needs_schengen:
            for gate in area.Gates:
                if not gate.occupied:
                    gate.occupied = True
                    gate.craftID = aircraft_id.strip().upper()
                    return terminals[0], area, gate

    return None  # No free gate found


if __name__ == "__main__":
    print(GateOccupancy(LoadAirportStructure("Terminals.txt").terminals))
