# Prova ràpida de la classe Airport amb un únic aeroport (LEBL).
from airport import *
airport = Airport("LEBL", 41.297445, 2.0832941)  # Creem un aeroport de prova
airport.SetSchengen()  # Calcula si és Schengen
airport.PrintAirport()  # Mostra les seves dades