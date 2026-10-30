"""
Actualiza rating + link de Letterboxd en TODAS las películas de index.html
===========================================================================

Recorre cada película del bloque FUNCIONES, busca su ID en TMDB, y escribe
(o reemplaza) los campos `rating` y `letterboxdUrl` directamente en el
archivo. El link queda en el formato oficial de Letterboxd,
letterboxd.com/tmdb/{id}, que lleva directo a la película.

Antes de escribir, guarda una copia: index.html.bak

Uso (con index.html en la misma carpeta que este script):
    python actualizar_ratings.py --probar    # no escribe nada, solo muestra qué haría
    python actualizar_ratings.py             # actualiza index.html

Desambiguar por año: si TMDB elige la película equivocada, agregá el campo
`anio` en esa película dentro de FUNCIONES y volvé a correr el script:
    titulo: "Backrooms",
    anio: 2026,

Películas sin votos en TMDB (estrenos muy nuevos o ciclos poco conocidos) se
saltean y quedan como están.
"""

import re
import shutil
import sys
import time

import requests

try:
    # Reusa la API key que ya pegaste en tmdb_rating.py, si está en la misma carpeta.
    from tmdb_rating import TMDB_API_KEY
except Exception:
    TMDB_API_KEY = "TU_API_KEY_ACA"

ARCHIVO = "index.html"


def buscar_tmdb(titulo, anio=None):
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
        "id": peli["id"],
        "titulo": peli["title"],
        "anio": (peli.get("release_date") or "")[:4],
        "rating": round(peli["vote_average"], 1),
        "votos": peli["vote_count"],
    }


def encontrar_objetos(texto):
    """Devuelve (inicio, fin) de cada película { ... } del array FUNCIONES."""
    m = re.search(r"const\s+FUNCIONES\s*=\s*\[", texto)
    if not m:
        raise SystemExit("No encontré 'const FUNCIONES = [' en el archivo.")

    objetos = []
    profundidad = 0
    en_string = None
    obj_inicio = None
    i = m.end()

    while i < len(texto):
        c = texto[i]
        if en_string:
            if c == "\\":
                i += 1
            elif c == en_string:
                en_string = None
        elif c == "/" and texto[i + 1:i + 2] == "/":
            salto = texto.find("\n", i)
            i = len(texto) if salto == -1 else salto
        elif c in "\"'`":
            en_string = c
        elif c == "{":
            if profundidad == 0:
                obj_inicio = i
            profundidad += 1
        elif c == "}":
            profundidad -= 1
            if profundidad == 0:
                objetos.append((obj_inicio, i + 1))
        elif c == "]" and profundidad == 0:
            break
        i += 1

    return objetos


def aplicar_campos(bloque, rating, url):
    """Reemplaza rating/letterboxdUrl si ya existen; si no, los agrega bajo `titulo`."""
    nuevo = bloque

    if re.search(r"\brating:\s*[\d.]+", nuevo):
        nuevo = re.sub(r"(\brating:\s*)[\d.]+", lambda m: f"{m.group(1)}{rating}", nuevo, count=1)
        agregar_rating = False
    else:
        agregar_rating = True

    if re.search(r'letterboxdUrl:\s*"[^"]*"', nuevo):
        nuevo = re.sub(r'(letterboxdUrl:\s*)"[^"]*"', lambda m: f'{m.group(1)}"{url}"', nuevo, count=1)
        agregar_url = False
    else:
        agregar_url = True

    if agregar_rating or agregar_url:
        m = re.search(r'\n([ \t]*)titulo:\s*"[^"]*",?', nuevo)
        if not m:
            return nuevo
        indent = m.group(1)
        extra = ""
        if agregar_rating:
            extra += f"\n{indent}rating: {rating},"
        if agregar_url:
            extra += f'\n{indent}letterboxdUrl: "{url}",'
        nuevo = nuevo[:m.end()] + extra + nuevo[m.end():]

    return nuevo


def main():
    probar = "--probar" in sys.argv

    if TMDB_API_KEY == "TU_API_KEY_ACA":
        raise SystemExit("Falta la API key de TMDB: pegala en tmdb_rating.py (o en este archivo).")

    with open(ARCHIVO, encoding="utf-8") as f:
        texto = f.read()

    objetos = encontrar_objetos(texto)
    print(f"Encontré {len(objetos)} películas en FUNCIONES.\n")

    cache = {}
    ediciones = []  # (inicio, fin, bloque_nuevo)

    for inicio, fin in objetos:
        bloque = texto[inicio:fin]
        m_titulo = re.search(r'titulo:\s*"([^"]+)"', bloque)
        if not m_titulo:
            continue
        titulo = m_titulo.group(1)
        m_anio = re.search(r"\banio:\s*(\d{4})", bloque)
        anio = m_anio.group(1) if m_anio else None

        clave = (titulo, anio)
        if clave not in cache:
            try:
                cache[clave] = buscar_tmdb(titulo, anio)
            except requests.RequestException as e:
                print(f"  ✗ {titulo}: error consultando TMDB ({e})")
                cache[clave] = None
            time.sleep(0.3)

        datos = cache[clave]
        if not datos:
            print(f"  ✗ {titulo}: no lo encontré en TMDB (probá agregando `anio:`).")
            continue
        if datos["votos"] == 0:
            print(f"  – {titulo}: TMDB lo tiene pero sin votos todavía, lo salteo.")
            continue

        url = f"https://letterboxd.com/tmdb/{datos['id']}"
        print(f"  ✓ {titulo}  →  TMDB: \"{datos['titulo']}\" ({datos['anio']})  ★ {datos['rating']}  ({datos['votos']} votos)")
        ediciones.append((inicio, fin, aplicar_campos(bloque, datos["rating"], url)))

    if probar:
        print("\nModo prueba: no se escribió nada.")
        return

    if not ediciones:
        print("\nNo hubo nada para actualizar.")
        return

    shutil.copyfile(ARCHIVO, ARCHIVO + ".bak")
    for inicio, fin, nuevo in sorted(ediciones, reverse=True):
        texto = texto[:inicio] + nuevo + texto[fin:]
    with open(ARCHIVO, "w", encoding="utf-8") as f:
        f.write(texto)

    print(f"\nListo: {len(ediciones)} películas actualizadas. Copia de seguridad en {ARCHIVO}.bak")
    print("Revisá arriba que cada título coincida con la película correcta (mirá el año).")


if __name__ == "__main__":
    main()
