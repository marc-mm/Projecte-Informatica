# Script de prova de les funcions del mòdul airport (carregar, afegir, esborrar,
# desar Schengen, graficar i generar el mapa KML).
from airport import *
import matplotlib.pyplot as plt

airport = Airport("L EBL", 41.297445, 2.0832941)  # Aeroport individual de prova
SetSchengen(airport)  # Calcula el seu flag Schengen
PrintAirport(airport)  # El mostra per pantalla


airports = LoadAirports("Test_ports")  # Carrega una llista d'aeroports d'un fitxer



AddAirport(airports, airport)  # Afegeix l'aeroport de prova a la llista
SaveSchengenAirports("Test_Write",airports)  # Desa només els Schengen a un fitxer

# Mostrem codi i coordenades de cada aeroport
for i in airports:
    print(i.code)
    print(i.latitude)
    print(i.longitude)
    print()

airports = RemoveAirport(airports,"LEBL")  # Eliminem l'aeroport amb codi "LEBL"

# Tornem a mostrar la llista (ara també amb el flag Schengen)
for i in airports:
    print(i.code)
    print(i.latitude)
    print(i.longitude)
    print(i.Schengen)
    print()

PlotAirports(airports)  # Gràfic Schengen vs total
MapAirports(airports,"Geospatial_airports.kml")  # Genera i obre el mapa KML