# Dashboard INFONAVIT — Créditos vs Rezago habitacional

Análisis del otorgamiento de crédito hipotecario del INFONAVIT (2015-2025) cruzado con el rezago habitacional estatal, para evaluar la cobertura territorial del Instituto.

La pregunta que busca responder: **¿INFONAVIT está llegando a los estados que más lo necesitan?**

## Hallazgos principales

- Durante 2015-2025 se otorgaron **~5.7 millones de créditos** por un monto de **$1.9 billones MXN**.
- El ratio de cobertura vs rezago varía **más de 100 veces** entre estados: Nuevo León con 481% (los créditos acumulados equivalen a 4.8x el rezago actual) frente a Oaxaca con 4.5%.
- **Chiapas** es el caso paradigmático: tiene el mayor crecimiento anual del país (CAGR +5.5%) pero su rezago es tan alto que la cobertura acumulada apenas llega al 7.8%.
- Estados como Guerrero, Baja California Sur y Morelos muestran contracciones anuales superiores al -7%.

## Arquitectura

```
├── src/
│   ├── sniiv.py         # cliente de la API del SNIIV-SEDATU
│   ├── transform.py     # transformaciones y métricas derivadas
│   └── pipeline.py      # orquestador ETL end-to-end
├── notebooks/
│   └── exploracion.ipynb
├── data/
│   └── processed/       # CSVs listos para Power BI
├── dashboard.pbix
└── requirements.txt
```

Los datos se consumen directamente de la API pública del SNIIV (sin token ni autenticación) y del repositorio de SEDATU para el CSV de rezago. Todo el pipeline es reproducible con un solo comando.

## Fuentes

- **Créditos INFONAVIT**: API del [Sistema Nacional de Información e Indicadores de Vivienda (SNIIV-SEDATU)](https://sniiv.sedatu.gob.mx/Reporte/Datos_abiertos), endpoint `GetInfonavit`. Cobertura consistente desde 2015.
- **Rezago habitacional**: CSV estatal de ENIGH 2022, publicado por CONAVI en el repositorio de SEDATU.

## Cómo correrlo

```bash
git clone <este-repo>
cd dashboard-infonavit
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

python -m src.pipeline
```

Los CSVs se generan en `data/processed/`. El archivo `dashboard.pbix` apunta a esa carpeta como origen; abre el PBIX y actualiza para ver los datos.

## Modelo dimensional

El pipeline produce 6 tablas diseñadas como modelo en estrella para Power BI:

| Tabla | Tipo | Granularidad |
|---|---|---|
| `fct_creditos_anual` | Hechos | año × estado × sexo |
| `fct_creditos_perfil` | Hechos | año × rango_edad × rango_salarial × sexo |
| `dim_estados` | Dimensión | 32 entidades federativas + región |
| `dim_tiempo` | Dimensión | años + sexenio |
| `dim_rezago` | Dimensión | rezago ENIGH 2022 por entidad |
| `resumen_ejecutivo` | Tabla analítica | métricas pre-calculadas por estado |

## Métricas calculadas

- **Monto promedio por crédito**: monto / acciones
- **CAGR (Compound Annual Growth Rate)**: `(V_final/V_inicial)^(1/n) - 1`, usado para comparar crecimientos en períodos largos de forma anualizada.
- **Ratio de cobertura vs rezago**: créditos acumulados / viviendas en rezago × 100. Es un proxy, no una medida directa — un crédito no elimina automáticamente una vivienda del rezago (puede ser para segunda vivienda, remodelación, etc.).
- **Años para cubrir el rezago**: rezago / ritmo anual actual.

## Consideraciones metodológicas

- El rango 2010-2014 no está disponible en la API del SNIIV con cobertura consistente. Se acotó el análisis a 2015-2025.
- El rezago habitacional proviene de ENIGH 2022 (última versión pública). El archivo 2024 requiere autenticación en el repositorio de SEDATU.
- El ratio de cobertura se calcula contra el rezago actual, no contra el rezago de inicio del período, por lo que sobreestima en estados donde el rezago ya se redujo.

## Stack

Python 3.11 · pandas · requests · Power BI · DAX
