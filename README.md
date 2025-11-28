# EPREL Database Sync

Sistema para sincronizar y almacenar datos completos del European Product Registry for Energy Labelling (EPREL) en una base de datos PostgreSQL 16.

## Características

- **Base de datos PostgreSQL 16** con esquema completo para todas las categorías de productos EPREL
- **Cliente API EPREL** con soporte para paginación (máximo 100 artículos por petición)
- **Sincronización eficiente** para categorías con más de 200,000 productos
- **Descargas resumibles** - guarda el progreso para continuar después de interrupciones
- **Rate limiting** y reintentos automáticos
- **Datos específicos por categoría** - tablas especializadas para cada tipo de producto

## Categorías de Productos Soportadas

| Categoría | Descripción |
|-----------|-------------|
| airconditioners | Aires Acondicionados |
| dishwashers | Lavavajillas |
| washingmachines | Lavadoras |
| washerdryers | Lavadoras-Secadoras |
| tumbledryers | Secadoras |
| refrigeratingappliances | Refrigeradores y Congeladores |
| electronicdisplays | Televisores y Monitores |
| lightsources | Fuentes de Luz |
| ovens | Hornos |
| rangehoods | Campanas Extractoras |
| tyres | Neumáticos |
| waterheaters | Calentadores de Agua |
| spaceheaters | Calentadores de Espacio |
| ventilationunits | Unidades de Ventilación |
| professionalrefrigeratedstoragecabinets | Armarios Refrigerados Profesionales |

## Requisitos

- Docker y Docker Compose
- Python 3.10+
- API Key de EPREL (solicitar en https://eprel.ec.europa.eu/screen/requestpublicapikey)

## Instalación

### 1. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env con tus credenciales
```

Variables requeridas:
- `EPREL_API_KEY`: Tu API key de EPREL
- `POSTGRES_PASSWORD`: Contraseña segura para PostgreSQL

### 2. Iniciar PostgreSQL

```bash
docker-compose up -d postgres
```

### 3. Instalar dependencias Python

```bash
pip install -r requirements.txt
```

## Uso

### Probar conectividad API

```bash
cd src
python sync_service.py --test-api
```

### Sincronizar todas las categorías

```bash
python sync_service.py --sync all
```

### Sincronizar una categoría específica

```bash
python sync_service.py --sync category --category dishwashers
```

### Sincronizar múltiples categorías

```bash
python sync_service.py --sync all --categories dishwashers washingmachines refrigeratingappliances
```

### Ver estadísticas

```bash
python sync_service.py --stats
```

### Opciones adicionales

- `--no-resume`: No continuar desde el último punto de progreso
- `--max-products N`: Limitar el número de productos por categoría

## Estructura de la Base de Datos

### Tablas Principales

- `product_groups`: Categorías de productos
- `suppliers`: Fabricantes/proveedores
- `products`: Tabla principal de productos con datos comunes
- `sync_jobs`: Historial de trabajos de sincronización
- `sync_progress`: Progreso de sincronización para descargas resumibles

### Tablas Específicas por Categoría

Cada categoría tiene su propia tabla con campos específicos:

- `product_airconditioners`
- `product_dishwashers`
- `product_washingmachines`
- `product_washerdryers`
- `product_tumbledryers`
- `product_refrigerators`
- `product_displays`
- `product_lightsources`
- `product_ovens`
- `product_rangehoods`
- `product_tyres`
- `product_waterheaters`
- `product_spaceheaters`
- `product_ventilationunits`
- `product_profrefrigeratedcabinets`

### Campo raw_data

Todos los datos originales de la API se almacenan en el campo `raw_data` (JSONB) de la tabla `products`, permitiendo acceder a cualquier campo no mapeado explícitamente.

## Arquitectura

```
EPREL/
├── docker-compose.yml      # Configuración de PostgreSQL
├── requirements.txt        # Dependencias Python
├── .env.example           # Plantilla de configuración
├── sql/
│   └── init/
│       └── 001_schema.sql # Esquema de la base de datos
└── src/
    ├── __init__.py
    ├── eprel_client.py    # Cliente API EPREL
    ├── database.py        # Operaciones de base de datos
    └── sync_service.py    # Servicio de sincronización
```

## Manejo de Grandes Volúmenes

El sistema está diseñado para manejar categorías con más de 200,000 productos:

1. **Paginación**: Solicita máximo 100 productos por petición
2. **Guardado de progreso**: Guarda el estado cada página para poder reanudar
3. **Rate limiting**: Respeta los límites de la API con delays configurables
4. **Reintentos**: Reintenta automáticamente las peticiones fallidas con backoff exponencial
5. **Interrupciones graceful**: Captura señales SIGINT/SIGTERM para guardar progreso antes de salir

## API de EPREL

Base URL: `https://eprel.ec.europa.eu/api/public`

La API requiere:
- Header `x-api-key` con tu API key
- Paginación con parámetros `page` y `limit` (máximo 100)

## Licencia

Este proyecto está bajo la Licencia MIT.
