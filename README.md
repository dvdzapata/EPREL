# EPREL
API de la BBDD EPREL

## Estructura del repositorio

### categories.json
Lista de categorías de productos con su código, URL, nombre y regulación correspondiente.

### schemas/
Carpeta con los esquemas de campos para cada categoría de producto:

| Archivo | Categoría | Regulación |
|---------|-----------|------------|
| `household_dishwasher_2019.json` | Lavavajillas domésticos | (EU) 2019/2017 |
| `household_washing_machine_2019.json` | Lavadoras domésticas | (EU) 2019/2014 |
| `household_washer_dryer_2019.json` | Lavadoras-secadoras domésticas | (EU) 2019/2014 |
| `household_tumble_drier_2023.json` | Secadoras de ropa domésticas | (EU) 2023/2534 |
| `household_refrigerating_appliance_2019.json` | Aparatos de refrigeración domésticos | (EU) 2019/2016 |
| `direct_sales_refrigeration_appliance.json` | Aparatos de refrigeración de venta directa | (EU) 2019/2018 |
| `tyres.json` | Neumáticos | (EU) 2020/740 |
| `light_source.json` | Fuentes de luz | (EU) 2019/2015 |
| `smartphones.json` | Smartphones y tablets | (EU) 2023/1669 |
| `electronic_display.json` | Pantallas electrónicas | (EU) 2019/2013 |
| `air_conditioner.json` | Aires acondicionados | (EU) 626/2011 |
| `domestic_oven.json` | Hornos domésticos | (EU) 65/2014 |
| `range_hood.json` | Campanas extractoras | (EU) 65/2014 |
| `local_space_heater.json` | Calefactores locales | (EU) 2015/1186 |
| `professional_refrigerator.json` | Refrigeradores profesionales | (EU) 2015/1094 |
| `residential_ventilation_unit.json` | Unidades de ventilación residencial | (EU) 1254/2014 |
| `space_heater.json` | Calentadores de espacio | (EU) 811/2013 |
| `space_heater_package.json` | Paquetes de calentadores de espacio | (EU) 811/2013 |
| `space_heater_temperature_control.json` | Control de temperatura para calentadores | (EU) 811/2013 |
| `space_heater_solar_device.json` | Dispositivos solares para calentadores | (EU) 811/2013 |
| `water_heaters.json` | Calentadores de agua | (EU) 812/2013 |
| `water_heater_package.json` | Paquetes de calentadores de agua | (EU) 812/2013 |
| `hot_water_storage_tank.json` | Tanques de almacenamiento de agua caliente | (EU) 812/2013 |
| `water_heater_solar_device.json` | Dispositivos solares para calentadores de agua | (EU) 812/2013 |
| `solid_fuel_boiler.json` | Calderas de combustible sólido | (EU) 2015/1187 |
| `solid_fuel_boiler_package.json` | Paquetes de calderas de combustible sólido | (EU) 2015/1187 |
| `household_dishwasher.json` | Lavavajillas domésticos (antiguo) | (EU) 1059/2010 |
| `household_washing_machine.json` | Lavadoras domésticas (antiguo) | (EU) 1061/2010 |
| `household_combined_washer_drier.json` | Lavadoras-secadoras combinadas | 96/60/EC |
| `household_tumble_drier.json` | Secadoras de ropa domésticas (antiguo) | (EU) 392/2012 |
| `household_refrigerating_appliance.json` | Aparatos de refrigeración domésticos (antiguo) | (EU) 1060/2010 |
| `lamp.json` | Lámparas | (EU) 874/2012 |
| `television.json` | Televisores | (EU) 1062/2010 |

### all_schemas.json
Archivo consolidado con todos los esquemas de categorías.

## Estructura de los esquemas

Cada archivo de esquema contiene:
- `category_code`: Código único de la categoría
- `sheet_name`: Nombre de la hoja de origen en el Excel
- `category_info`: Información de la categoría (código, URL, nombre, regulación)
- `fields`: Lista de campos con:
  - `key`: Clave del campo (nombre técnico)
  - `field_name`: Nombre descriptivo del campo
  - `type`: Tipo de dato (Number, Text, Boolean, List, URL, etc.)
  - `length_range`: Rango de valores permitidos
  - `format`: Formato esperado
- `field_count`: Número total de campos
