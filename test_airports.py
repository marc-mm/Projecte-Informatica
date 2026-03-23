from airport import *
import matplotlib.pyplot as plt

airport = Airport("LEBL", 41.297445, 2.0832941)
SetSchengen(airport)
PrintAirport(airport)


airports = LoadAirports("Test_ports")



AddAirport(airports, airport)
SaveSchengenAirports("Test_Write",airports)

for i in airports:
    print(i.code)
    print(i.latitude)
    print(i.longitude)
    print()

airports = RemoveAirport(airports,"LEBL")

for i in airports:
    print(i.code)
    print(i.latitude)
    print(i.longitude)
    print()

PlotAirports(airports)