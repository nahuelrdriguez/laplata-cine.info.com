"""
Rating de TMDB + link a Letterboxd, para la cartelera
=======================================================

Por qué TMDB y no Letterboxd directo: la API de Letterboxd es por
aprobación manual (no hay forma de activarla hoy), y scrapear sus páginas
está bloqueado por detección de bots. TMDB es gratis, de aprobación
instantánea, y la usamos para traer la puntuación — el botón igual te
lleva a Letterboxd (a la página de búsqueda de esa película, porque no
tenemos forma confiable de adivinar la URL exacta del film en Letterboxd
sin su API).

Uso:
    pip install requests
    python tmdb_rating.py "Zootopia 2"
    python tmdb_rating.py "Zootopia 2" 2025    (con año, para desambiguar)

Te imprime el fragmento listo para pegar en la película correspondiente
dentro de FUNCIONES, en tu index.html.
"""

import sys
import urllib.parse

import requests

TMDB_API_KEY = "a39150777ec90f478b59936578e25306"  # la conseguís gratis en themoviedb.org/settings/api


def buscar_pelicula(titulo, anio="Backrooms, 2025"):
    params = {"api_key": TMDB_API_KEY, "query": titulo, "language": "es-AR"}
    if anio:
        params["year"] = anio

    resp = requests.get("https://api.themoviedb.org/3/search/movie", params=params, timeout=10)
    resp.raise_for_status()
    resultados = resp.json().get("results", [])

    if not resultados:
        return None

    peli = resultados[0]
    letterboxd_query = urllib.parse.quote(peli["title"])

    return {
        "titulo_tmdb": peli["title"],
        "rating": round(peli["vote_average"], 1),
        "votos": peli["vote_count"],
        "poster": f"https://image.tmdb.org/t/p/w300{peli['poster_path']}" if peli.get("poster_path") else None,
        "letterboxd_url": f"https://letterboxd.com/search/films/{letterboxd_query}/",
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
