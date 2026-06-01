# Petit script de prova del mòdul Arrivals (carrega aeroports i vols i dibuixa).
from Arrivals import *  # Importem tot el mòdul de vols

if __name__ == "__main__":
    # 1. Necessitem carregar primer els aeroports per tenir les coordenades
    # Suposant que tens el fitxer "airports.txt"
    llista_aeroports = airport.LoadAirports("airports.txt")
    for a in llista_aeroports:
        airport.SetSchengen(a)  # Calculem el flag Schengen de cada aeroport

    # 2. Carreguem els vols
    vols = LoadArrivals("arrivals.txt")
    print(f"S'han carregat {len(vols)} vols.")

    # 3. Provem els gràfics (només si hi ha vols)
    if vols:
        PlotArrivals(vols)
        PlotAirlines(vols)