SENSOR_CATALOG = [
    {'type': 'temperature', 'label': 'Temperature', 'unit': 'c'},
    {'type': 'humidity_air', 'label': 'Humidite air', 'unit': '%'},
    {'type': 'humidity_soil', 'label': 'Humidite sol', 'unit': '%'},
]

SENSOR_TYPES = [(sensor['type'], sensor['label']) for sensor in SENSOR_CATALOG]
SENSOR_UNITS = {sensor['type']: sensor['unit'] for sensor in SENSOR_CATALOG}
SENSOR_LABELS = {sensor['type']: sensor['label'] for sensor in SENSOR_CATALOG}
