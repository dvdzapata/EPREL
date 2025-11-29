# EPREL Database Sync

Sistema para sincronizar y almacenar datos del European Product Registry for Energy Labelling (EPREL) en una base de datos PostgreSQL 16.

## Inicio Rápido - Paso 1: Verificar Conexión API

Antes de sincronizar todos los datos, verifica la conexión a la API obteniendo 1 muestra de cada categoría:

```bash
# Configurar API key
export EPREL_API_KEY="tu_api_key_aqui"

# Instalar dependencias
pip install requests

# Ejecutar script de muestras
python fetch_samples.py
```

Este script conecta con las **22 categorías de productos** de EPREL y descarga 1 producto de ejemplo de cada una.

## Categorías de Productos EPREL (22 totales)

| Código URL | Nombre | Regulación |
|------------|--------|------------|
| airconditioners | Air conditioners | EU 626/2011 |
| ovens | Domestic Ovens | EU 65/2014 |
| rangehoods | Range hoods | EU 65/2014 |
| washerdriers | Household combined washer-driers | 96/60/EC |
| dishwashers | Household dishwashers | EU 1059/2010 |
| refrigeratingappliances | Household refrigerating appliances | EU 1060/2010 |
| tumbledriers | Household tumble driers | EU 392/2012 |
| washingmachines | Household washing machines | EU 1061/2010 |
| localspaceheaters | Local space heaters | EU 2015/1186 |
| residentialventilationunits | Residential Ventilation Units | EU 1254/2014 |
| televisions | Televisions | EU 1062/2010 |
| spaceheaters | Space heaters/Combination heaters | EU 811/2013 |
| spaceheatertemperaturecontrol | Temperature controls for space heaters | EU 811/2013 |
| waterheaters | Water heaters | EU 812/2013 |
| hotwaterstoragetanks | Hot water storage tanks | EU 812/2013 |
| electronicdisplays | Electronic displays | EU 2019/2013 |
| washerdriers2019 | Household washer-dryers | EU 2019/2014 |
| washingmachines2019 | Household washing machines | EU 2019/2014 |
| refrigeratingappliances2019 | Refrigerating appliances | EU 2019/2016 |
| dishwashers2019 | Household dishwashers | EU 2019/2017 |
| tumbledryers20232534 | Household tumble dryers | EU 2023/2534 |
| smartphonestablets20231669 | Smartphones and slate tablets | EU 2023/1669 |

## Requisitos

- Python 3.10+
- API Key de EPREL (solicitar en https://eprel.ec.europa.eu/screen/requestpublicapikey)

## Estructura del Proyecto

```
EPREL/
├── fetch_samples.py        # Script para obtener 1 muestra de cada categoría
├── requirements.txt        # Dependencias Python
├── .env.example           # Plantilla de configuración
├── docker-compose.yml     # PostgreSQL 16 (para fase posterior)
├── sql/                   # Esquemas de base de datos
└── src/                   # Servicio de sincronización completo
```

## API de EPREL

Base URL: `https://eprel.ec.europa.eu/api/products`

Headers requeridos:
- `x-api-key`: Tu API key de EPREL
- `Accept`: application/json

Parámetros:
- `limit`: Número de productos a obtener (máximo 100)

## Licencia

Este proyecto está bajo la Licencia MIT.
