from django import template
from django.template.defaultfilters import floatformat

register = template.Library()

@register.filter(name='clp')
def clp(value):
    """
    Formatea un número como moneda CLP
    Ejemplo: 2333 -> 2.333
    """
    try:
        # Convertir a string y eliminar decimales si existen
        value = str(int(float(value)))
        # Insertar puntos como separadores de miles
        if len(value) <= 3:
            return value
        else:
            s = value[-3:]
            value = value[:-3]
            while value:
                s = value[-3:] + '.' + s if value[-3:] else value + '.' + s
                value = value[:-3]
            return s
    except (ValueError, TypeError):
        return value 