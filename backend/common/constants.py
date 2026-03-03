SENSOR_CATALOG = [
    {'type': 'humidity', 'label': 'Humidity', 'unit': '%'},
    {'type': 'luminosity', 'label': 'Luminosity', 'unit': 'lux'},
    {'type': 'temperature', 'label': 'Temperature', 'unit': 'c'},
    {'type': 'pressure', 'label': 'Pressure', 'unit': 'hpa'},
]

SENSOR_TYPES = [(sensor['type'], sensor['label']) for sensor in SENSOR_CATALOG]
SENSOR_UNITS = {sensor['type']: sensor['unit'] for sensor in SENSOR_CATALOG}
SENSOR_LABELS = {sensor['type']: sensor['label'] for sensor in SENSOR_CATALOG}
