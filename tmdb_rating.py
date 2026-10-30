"""
Rating de TMDB + link a Letterboxd, para la cartelera
=======================================================

Por qué TMDB y no Letterboxd directo: la API de Letterboxd es por
aprobación manual (no hay forma de activarla hoy), y scrapear sus páginas
está bloqueado por detección de bots. TMDB es gratis, de aprobación
instantánea, y la usamos para traer la puntuación y el ID de la película
— con ese ID armamos el link a Letterboxd usando su formato oficial de
redirección (letterboxd.com/tmdb/{id}), documentado por ellos mismos para
integraciones como esta. Va directo a la página de la película, no a una
búsqueda.

Uso:
    pip install requests
    python tmdb_rating.py "Zootopia 2"
    python tmdb_rating.py "Zootopia 2" 2025    (con año, para desambiguar)

Te imprime el fragmento listo para pegar en la película correspondiente
dentro de FUNCIONES, en tu index.html.
"""

import sys

import requests

TMDB_API_KEY = "TU_API_KEY_ACA"  # la conseguís gratis en themoviedb.org/settings/api


def buscar_pelicula(titulo, anio=None):
    params = {"api_key": TMDB_API_KEY, "query": titulo, "language": "es-AR"}
    if anio:
        params["year"] = anio

    resp = requests.get("https://api.themoviedb.org/3/search/movie", params=params, timeout=10)
    resp.raise_for_status()
    resultados = resp.json().get("results", [])

    if not resultados:
        return None

    peli = resultados[0]

    return {
        "titulo_tmdb": peli["title"],
        "rating": round(peli["vote_average"], 1),
        "votos": peli["vote_count"],
        "poster": f"https://image.tmdb.org/t/p/w300{peli['poster_path']}" if peli.get("poster_path") else None,
        "letterboxd_url": f"https://letterboxd.com/tmdb/{peli['id']}",
    }


def generar_snippet(titulo, anio=None):
    datos = buscar_pelicula(titulo, anio)

    if not datos:
        print(f"No encontré '{titulo}' en TMDB. Probá con el año, o revisá cómo está escrito el título.")
        return

    print("Pegá esto dentro de la película correspondiente en FUNCIONES:\n")
    print(f'  rating: {datos["rating"]},')
    print(f'  letterboxdUrl: "{datos["letterboxd_url"]}",')
    print(f'\n(TMDB encontró: "{datos["titulo_tmdb"]}" · {datos["votos"]} votos)')

    if datos["titulo_tmdb"].lower() != titulo.lower():
        print(f'\nOjo: TMDB encontró un título distinto al que pediste — confirmá que sea la peli correcta '
              f'antes de pegar el snippet (puede ser un caso de título ambiguo, probá agregando el año).')


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Uso: python tmdb_rating.py "Nombre de la película" [año]')
    else:
        titulo_arg = sys.argv[1]
        anio_arg = sys.argv[2] if len(sys.argv) > 2 else None
        generar_snippet(titulo_arg, anio_arg)
