"""Pipeline end-to-end: extrae, transforma y guarda todo para Power BI.

Uso:
    python -m src.pipeline
"""
from pathlib import Path
import requests
import pandas as pd

from src.sniiv import get_infonavit_por_anio
from src.transform import (
    dim_estados, dim_tiempo, dim_rezago,
    fct_anual, fct_perfil, resumen_ejecutivo,
)

ANIO_INICIO = 2015
ANIO_FIN = 2025
OUT = Path("data/processed")

# URL directa al CSV de rezago habitacional ENIGH 2022 en el repo de SEDATU
URL_REZAGO = (
    "https://sistemas.sedatu.gob.mx/repositorio/proxy/alfresco-noauth/"
    "api/internal/shared/node/LGBlxMFKTW-QoezUJn5YBw/content/"
    "rezago_habitacional_est_2022.csv?&a=true"
)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    anios = list(range(ANIO_INICIO, ANIO_FIN + 1))

    print(f"Descargando INFONAVIT {ANIO_INICIO}-{ANIO_FIN}")
    print("[1/2] por estado y sexo")
    raw_anual = get_infonavit_por_anio(anios, dimensiones=["estado", "genero"])

    print("[2/2] perfil demográfico")
    raw_perfil = get_infonavit_por_anio(
        anios, dimensiones=["rango_edad", "rango_salarial", "genero"]
    )

    print("\nDescargando rezago habitacional (ENIGH 2022)")
    from io import StringIO
    r = requests.get(URL_REZAGO, timeout=60, verify=False)
    r.raise_for_status()
    raw_rezago = pd.read_csv(StringIO(r.text), dtype={"ent": str})

    print("\nTransformando")
    tablas = {
        "fct_creditos_anual": fct_anual(raw_anual),
        "fct_creditos_perfil": fct_perfil(raw_perfil),
        "dim_estados": dim_estados(),
        "dim_tiempo": dim_tiempo(ANIO_INICIO, ANIO_FIN),
        "dim_rezago": dim_rezago(raw_rezago),
    }
    tablas["resumen_ejecutivo"] = resumen_ejecutivo(
        tablas["fct_creditos_anual"],
        tablas["dim_estados"],
        tablas["dim_rezago"],
    )

    print(f"\nGuardando CSVs en {OUT}/")
    for nombre, df in tablas.items():
        if "clave_estado" in df.columns:
            df["clave_estado"] = df["clave_estado"].astype(str).str.zfill(2)
        df.to_csv(OUT / f"{nombre}.csv", index=False, encoding="utf-8-sig")
        print(f"  {nombre}.csv ({len(df)} filas)")


if __name__ == "__main__":
    main()
