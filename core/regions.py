# regions.py
# Regiones y comunas de Chile con sus códigos según Chilexpress

REGIONS = [
    {
        "code": "13",
        "name": "Región Metropolitana",
        "comunas": [
            {"code": "13123", "name": "Providencia"},
            {"code": "13124", "name": "Pudahuel"},
            {"code": "13401", "name": "San Bernardo"},
            # Agrega aquí las demás comunas de la Región Metropolitana según necesites
        ]
    },
    {
        "code": "05",
        "name": "Región de Valparaíso",
        "comunas": [
            {"code": "05101", "name": "Valparaíso"},
            {"code": "05109", "name": "Viña del Mar"},
            {"code": "05103", "name": "Concón"},
            # Agrega aquí las demás comunas de la Región de Valparaíso según necesites
        ]
    },
    # Agrega aquí más regiones y sus comunas si lo deseas
]

def get_regions():
    """
    Devuelve la lista de regiones (sin las comunas).
    Cada elemento es un dict con 'code' y 'name'.
    """
    return [{"code": r["code"], "name": r["name"]} for r in REGIONS]

def get_comunas(region_code):
    """
    Devuelve la lista de comunas (cada una como {'code', 'name'})
    para la región cuyo código es `region_code`.
    Si no existe la región, retorna lista vacía.
    """
    for region in REGIONS:
        if region["code"] == region_code:
            return region["comunas"]
    return []
