import sys
import os
from typing import Optional, Dict, Any

# Agregar el directorio raíz al path de Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database

MENSAJES_POR_DEFECTO = {
    'talar': '¡{autor} se ha ido a talar al bosque!',
    'trabajar en el campo': '¡{autor} ha comenzado a trabajar en el campo!',
    'trabajar de guardia': '¡{autor} ha empezado su turno de guardia!',
    'picar piedra': '¡{autor} ha empezado a picar piedra!',
    'cazar en el bosque': '¡{autor} ha entrado al bosque para cazar!',
    'pescar': '¡{autor} ha empezado a pescar!'
}

def realiza_accion(accion: str, autor: str, codigo_accion: str) -> str:
    """
    Realiza una acción y devuelve el mensaje correspondiente.
    
    Args:
        accion: La acción a realizar (ej: 'talar', 'trabajar en el campo', etc.)
        autor: Nombre del usuario que realiza la acción
        codigo_accion: Código único de la acción (ID de la recompensa)
        
    Returns:
        Mensaje formateado para mostrar en el chat
    """
    # Buscar el ciudadano en la base de datos
    ciudadano = database.get_ciudadano(autor)
    ciudadano_id = None
    
    # Si el ciudadano no existe, crearlo
    if not ciudadano:
        if not database.crear_ciudadano(autor, autor):
            return f"Error: No se pudo crear el ciudadano de {autor}"
        ciudadano = database.get_ciudadano(autor)
    
    # Obtener el mensaje correspondiente
    mensaje = MENSAJES_POR_DEFECTO.get(accion, f"¡{autor} ha usado una acción desconocida!")
    mensaje = mensaje.format(autor=autor)
    
    # Registrar la acción en el historial
    database.registrar_accion(codigo_accion, mensaje, ciudadano['id'])
    
    return mensaje
