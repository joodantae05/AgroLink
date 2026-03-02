SENSOR_CATALOG = [
    {'type': 'luminosity', 'label': 'Luminosity', 'unit': 'lux'},
    {'type': 'air_humidity', 'label': 'Air humidity', 'unit': '%'},
    {'type': 'soil_humidity', 'label': 'Soil humidity', 'unit': '%'},
    {'type': 'co2', 'label': 'CO2', 'unit': 'ppm'},
    {'type': 'nutrient_index', 'label': 'Nutrient index', 'unit': '%'},
    {'type': 'pressure', 'label': 'Pressure', 'unit': 'hpa'},
    {'type': 'heat', 'label': 'Heat', 'unit': 'c'},
]

SENSOR_TYPES = [(sensor['type'], sensor['label']) for sensor in SENSOR_CATALOG]
SENSOR_UNITS = {sensor['type']: sensor['unit'] for sensor in SENSOR_CATALOG}
SENSOR_LABELS = {sensor['type']: sensor['label'] for sensor in SENSOR_CATALOG}
