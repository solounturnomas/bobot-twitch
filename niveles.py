"""
Módulo que contiene las definiciones de niveles y experiencia necesaria para cada habilidad.
"""

# Diccionario que define los puntos de experiencia necesarios para cada nivel
# La clave es el nivel y el valor son los puntos necesarios para alcanzarlo
NIVELES_EXPERIENCIA = {
    1: 0,    # Nivel 1: 0 puntos
    2: 75,   # Nivel 2: 75 puntos (75 adicionales)
    3: 200,   # Nivel 3: 200 puntos (100 adicionales)
    4: 500,   # Nivel 4: 500 puntos (300 adicionales) 
    5: 750    # Nivel 5: 750 puntos (250 adicionales)
}

def obtener_nivel(puntos_experiencia: int) -> int:
    """
    Determina el nivel actual basado en los puntos de experiencia.
    
    Args:
        puntos_experiencia: Puntos de experiencia actuales del jugador
        
    Returns:
        int: Nivel actual del jugador (1-5)
    """
    for nivel, exp_necesaria in sorted(NIVELES_EXPERIENCIA.items(), reverse=True):
        if puntos_experiencia >= exp_necesaria:
            return nivel
    return 1  # Nivel mínimo

def experiencia_para_siguiente_nivel(puntos_experiencia: int) -> tuple[int, int]:
    """
    Calcula la experiencia necesaria para el siguiente nivel y el nivel objetivo.
    
    Args:
        puntos_experiencia: Puntos de experiencia actuales del jugador
        
    Returns:
        tuple: (experiencia_faltante, siguiente_nivel)
        - experiencia_faltante: Puntos que faltan para el siguiente nivel (0 si es el nivel máximo)
        - siguiente_nivel: Próximo nivel a alcanzar (o el nivel máximo si ya está en él)
    """
    nivel_actual = obtener_nivel(puntos_experiencia)
    
    # Si ya está en el nivel máximo
    if nivel_actual >= max(NIVELES_EXPERIENCIA.keys()):
        return 0, nivel_actual
    
    siguiente_nivel = nivel_actual + 1
    experiencia_requerida = NIVELES_EXPERIENCIA[siguiente_nivel]
    experiencia_faltante = max(0, experiencia_requerida - puntos_experiencia)
    
    return experiencia_faltante, siguiente_nivel
