def escribir_mensaje_funcion(accion: str, autor: str) -> str:
    """
    Genera un mensaje específico según la acción de recompensa.
    
    Args:
        accion: La acción de la recompensa (ej: 'talar', 'trabajar en el campo', etc.)
        autor: Nombre del usuario que usó la recompensa
        
    Returns:
        Un mensaje formateado para mostrar en el chat
    """
    match accion:
        case 'talar':
            return f"¡{autor} se ha ido a talar al bosque!"
        case 'trabajar en el campo':
            return f"¡{autor} ha comenzado a trabajar en el campo!"
        case 'trabajar de guardia':
            return f"¡{autor} ha empezado su turno de guardia!"
        case 'picar piedra':
            return f"¡{autor} ha empezado a picar piedra!"
        case 'cazar en el bosque':
            return f"¡{autor} ha entrado al bosque para cazar!"
        case 'pescar':
            return f"¡{autor} ha empezado a pescar!"
        case _:
            return f"¡{autor} ha usado una acción desconocida!"

# Mensajes por defecto para cada acción
MENSAJES_POR_DEFECTO = {
    'talar': '¡{autor} se ha ido a talar al bosque!',
    'trabajar en el campo': '¡{autor} ha comenzado a trabajar en el campo!',
    'trabajar de guardia': '¡{autor} ha empezado su turno de guardia!',
    'picar piedra': '¡{autor} ha empezado a picar piedra!',
    'cazar en el bosque': '¡{autor} ha entrado al bosque para cazar!',
    'pescar': '¡{autor} ha empezado a pescar!'
}
