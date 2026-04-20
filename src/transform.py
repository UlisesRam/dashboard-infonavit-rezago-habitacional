"""Transformaciones y métricas derivadas."""
import pandas as pd

# Claves INEGI + región (para análisis regional en Power BI)
ESTADOS = {
    "01": ("Aguascalientes", "Centro-Norte"),
    "02": ("Baja California", "Noroeste"),
    "03": ("Baja California Sur", "Noroeste"),
    "04": ("Campeche", "Sureste"),
    "05": ("Coahuila de Zaragoza", "Noreste"),
    "06": ("Colima", "Occidente"),
    "07": ("Chiapas", "Sureste"),
    "08": ("Chihuahua", "Noroeste"),
    "09": ("Ciudad de México", "Centro"),
    "10": ("Durango", "Noroeste"),
    "11": ("Guanajuato", "Centro-Norte"),
    "12": ("Guerrero", "Sur"),
    "13": ("Hidalgo", "Centro"),
    "14": ("Jalisco", "Occidente"),
    "15": ("México", "Centro"),
    "16": ("Michoacán de Ocampo", "Occidente"),
    "17": ("Morelos", "Centro"),
    "18": ("Nayarit", "Occidente"),
    "19": ("Nuevo León", "Noreste"),
    "20": ("Oaxaca", "Sur"),
    "21": ("Puebla", "Centro"),
    "22": ("Querétaro", "Centro-Norte"),
    "23": ("Quintana Roo", "Sureste"),
    "24": ("San Luis Potosí", "Centro-Norte"),
    "25": ("Sinaloa", "Noroeste"),
    "26": ("Sonora", "Noroeste"),
    "27": ("Tabasco", "Sureste"),
    "28": ("Tamaulipas", "Noreste"),
    "29": ("Tlaxcala", "Centro"),
    "30": ("Veracruz de Ignacio de la Llave", "Sureste"),
    "31": ("Yucatán", "Sureste"),
    "32": ("Zacatecas", "Centro-Norte"),
}

NOMBRE_A_CLAVE = {nombre: clave for clave, (nombre, _) in ESTADOS.items()}


def dim_estados():
    return pd.DataFrame(
        [{"clave_estado": k, "estado": n, "region": r}
         for k, (n, r) in ESTADOS.items()]
    )


def dim_tiempo(anio_inicio, anio_fin):
    df = pd.DataFrame({"anio": range(anio_inicio, anio_fin + 1)})
    df["sexenio"] = df["anio"].apply(_sexenio)
    return df


def _sexenio(anio):
    if 2013 <= anio <= 2018:
        return "Peña Nieto (2012-2018)"
    if 2019 <= anio <= 2024:
        return "AMLO (2018-2024)"
    if anio >= 2025:
        return "Sheinbaum (2024-2030)"
    return "Anterior"


def fct_anual(df_raw):
    """Tabla de hechos: año x estado x sexo."""
    df = df_raw.rename(columns={"año": "anio"})
    df = df.groupby(["anio", "estado", "sexo"], as_index=False).agg(
        acciones=("acciones", "sum"),
        monto=("monto", "sum"),
    )
    df["clave_estado"] = df["estado"].map(NOMBRE_A_CLAVE)
    df["monto_promedio"] = (df["monto"] / df["acciones"]).round(2)
    return df[["anio", "clave_estado", "estado", "sexo",
               "acciones", "monto", "monto_promedio"]]


def fct_perfil(df_raw):
    """Tabla de hechos: año x edad x salario x sexo (nacional)."""
    df = df_raw.rename(columns={"año": "anio", "grupo_edad": "rango_edad"})
    return df.groupby(
        ["anio", "rango_edad", "rango_salarial", "sexo"], as_index=False
    ).agg(acciones=("acciones", "sum"), monto=("monto", "sum"))


def dim_rezago(df_raw):
    """Pivota el CSV de rezago ENIGH a formato ancho con métricas."""
    df = df_raw[["ent", "rezago", "viviendas", "personas"]].copy()
    df["clave_estado"] = df["ent"].astype(str).str.zfill(2)

    ancho = df.pivot_table(
        index="clave_estado",
        columns="rezago",
        values=["viviendas", "personas"],
        aggfunc="sum",
    )
    ancho.columns = [f"{m}_{e.lower().replace(' ', '_')}" for m, e in ancho.columns]
    ancho = ancho.reset_index()

    ancho["viviendas_total"] = ancho["viviendas_en_rezago"] + ancho["viviendas_sin_rezago"]
    ancho["pct_rezago_viviendas"] = (
        ancho["viviendas_en_rezago"] / ancho["viviendas_total"] * 100
    ).round(2)
    return ancho


def resumen_ejecutivo(fct, estados, rezago):
    """Tabla con una fila por estado y métricas clave."""
    historico = fct.groupby("clave_estado", as_index=False).agg(
        creditos_totales=("acciones", "sum"),
        monto_total=("monto", "sum"),
    )

    ultimo_anio = fct["anio"].max()
    actual = fct[fct["anio"] == ultimo_anio].groupby(
        "clave_estado", as_index=False
    ).agg(creditos_ultimo_anio=("acciones", "sum"))

    # CAGR: tasa de crecimiento anual compuesto
    primer_anio = fct["anio"].min()
    n = ultimo_anio - primer_anio
    pivote = fct.groupby(["clave_estado", "anio"])["acciones"].sum().unstack(fill_value=0)
    cagr = (((pivote[ultimo_anio] / pivote[primer_anio]) ** (1 / n) - 1) * 100).round(2)
    cagr = cagr.reset_index().rename(columns={0: "cagr"})
    cagr.columns = ["clave_estado", "cagr"]

    df = (
        estados
        .merge(historico, on="clave_estado", how="left")
        .merge(actual, on="clave_estado", how="left")
        .merge(cagr, on="clave_estado", how="left")
        .merge(rezago[["clave_estado", "pct_rezago_viviendas", "viviendas_en_rezago"]],
               on="clave_estado", how="left")
    )

    df["ratio_cobertura_vs_rezago"] = (
        df["creditos_totales"] / df["viviendas_en_rezago"] * 100
    ).round(2)

    return df.sort_values("creditos_totales", ascending=False)
