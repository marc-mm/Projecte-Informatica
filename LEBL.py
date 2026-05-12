

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
    i = 0
    if len(area.Gates) > 0:
        pass
    else:
        if (int(end_gate)-int(init_gate)) < 0:
            print("error code -1")
        while i < (int(end_gate)-int(init_gate)):
            area.Gates.append(prefix+str(int(init_gate)+i))
            i += 1



def LoadAirlines(terminal, t_name):
    file = open(f"{t_name}_Airlines.txt","r")
    readline = file.readline()
    while readline != "":
        terminal.air_code.append(readline)
        readline = file.readline().strip("\n")
    file.close()


def LoadAirportStructure (filename):
    file = open(filename,"r")
    lines = file.readlines()
    file.close()
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
        LoadAirlines(i,i.t_name)
    AirportStructure.name = filename
    AirportStructure.terminals = terminals
    return AirportStructure


print(LoadAirportStructure("Terminals.txt").terminals[0].BA[4].__dict__)
