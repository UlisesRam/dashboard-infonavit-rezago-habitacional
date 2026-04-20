"""Cliente para la API pública del SNIIV-SEDATU."""
import requests
import pandas as pd

BASE_URL = "https://sniiv.sedatu.gob.mx/api/CuboAPI/GetInfonavit"


def get_infonavit(anio_inicio, anio_fin, dimensiones, estado="00", municipio="000"):
    """Consulta el cubo INFONAVIT del SNIIV.

    dimensiones: lista de hasta 5 campos a desagregar,
    ej. ["estado", "genero"] o ["rango_edad", "rango_salarial"].
    """
    anios = f"{anio_inicio},{anio_fin}"
    dims = ",".join(dimensiones)
    url = f"{BASE_URL}/{anios}/{estado}/{municipio}/{dims}"

    r = requests.get(url, timeout=60)
    r.raise_for_status()
    return pd.DataFrame(r.json())


def get_infonavit_por_anio(anios, dimensiones):
    """Descarga año por año y concatena. Más robusto para rangos largos."""
    dfs = []
    for anio in anios:
        try:
            df = get_infonavit(anio, anio, dimensiones)
            df["anio"] = anio
            if "año" in df.columns:
                df = df.drop(columns=["año"])
            dfs.append(df)
            print(f"  {anio}: {len(df)} filas")
        except Exception as e:
            print(f"  {anio}: error ({e})")
    return pd.concat(dfs, ignore_index=True)
