from Arrivals import *

if __name__ == "__main__":
    # 1. Necessitem carregar primer els aeroports per tenir les coordenades
    # Suposant que tens el fitxer "airports.txt"
    llista_aeroports = airport.LoadAirports("airports.txt")
    for a in llista_aeroports:
        airport.SetSchengen(a)

    # 2. Carreguem els vols
    vols = LoadArrivals("arrivals.txt")
    print(f"S'han carregat {len(vols)} vols.")

    # 3. Provem els gràfics
    if vols:
        PlotArrivals(vols)
        PlotAirlines(vols)