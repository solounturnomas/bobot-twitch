"""
Módulo que maneja la base de datos SQLite para el sistema de mapa.
Esta base de datos almacena información sobre la cuadrícula del mapa.
"""

import sqlite3
from typing import Optional, Dict, Any
import logging
import configuracion_logging
from contextlib import contextmanager

# Configurar logging específico para el mapa
logger = configuracion_logging.logger
logger_mapa = logger.getChild('db_mapa')

# Configuración de la base de datos
DB_PATH = 'soloville.db'

@contextmanager
def get_db_connection():
    """
    Context manager para obtener una conexión a la base de datos.
    Asegura que la conexión se cierre correctamente.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db_mapa():
    """
    Inicializa la base de datos y crea la tabla mapa si no existe.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            logger_mapa.info("Iniciando creación de tabla mapa")
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS mapa (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    x INTEGER NOT NULL,
                    z INTEGER NOT NULL,
                    tipo INTEGER NOT NULL,
                    ciudadano_id INTEGER NULL,
                    UNIQUE(x, z)
                )
            ''')
            
            logger_mapa.info("Tabla mapa creada")
            conn.commit()
            
    except sqlite3.Error as e:
        logger_mapa.error(f"Error al crear tabla mapa: {e}")
        raise

# Tipos de casillas (IDs numéricos)
TIPOS_CASILLAS = {
    'CESPED': 1,
    'CAMPO': 2,
    'AGUA': 3,
    'MONTAÑA': 4,
    'CIUDADANO': 5,
    'CAMINO': 6,
    'CAMINO_GIRADO_1': 7,
    'CAMINO_GIRADO_2': 8,
    'CAMINO_GIRADO_3': 9,
    'CAMINO_GIRADO_4': 10,
    'POZO': 11,
    'PUEBLO': 12,
    'SOLAR': 13,
    'CAMINO_2': 14,
    'CRUCE': 15
}

def crear_casilla(x: int, z: int, tipo: str) -> bool:
    """
    Crea una nueva casilla en el mapa.
    
    Args:
        x, z: Coordenadas de la casilla
        tipo: Tipo de casilla (debe ser una clave válida de TIPOS_CASILLAS)
        
    Returns:
        True si se creó exitosamente, False si ya existe
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO mapa (x, z, tipo)
                VALUES (?, ?, ?)
            ''', (x, z, TIPOS_CASILLAS[tipo]))
            conn.commit()
            logger_mapa.info(f"Casilla creada en ({x}, {z})")
            return True
    except sqlite3.IntegrityError:
        logger_mapa.warning(f"Casilla en ({x}, {z}) ya existe")
        return False
    except KeyError:
        logger_mapa.error(f"Tipo de casilla no válido: {tipo}")
        return False

def obtener_tipo_casilla_por_id(id_tipo: int) -> str:
    """
    Obtiene el nombre del tipo de casilla dado su ID.
    
    Args:
        id_tipo: ID del tipo de casilla
        
    Returns:
        Nombre del tipo de casilla como string
    """
    for tipo, id in TIPOS_CASILLAS.items():
        if id == id_tipo:
            return tipo
    return "CESPED"  # Por defecto si no se encuentra el tipo

def obtener_casilla(x: int, z: int) -> dict:
    """
    Obtiene los datos de una casilla por sus coordenadas.
    
    Args:
        x, z: Coordenadas de la casilla
        
    Returns:
        Diccionario con los datos de la casilla si existe, None si no existe
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM mapa WHERE x = ? AND z = ?', (x, z))
            casilla = cursor.fetchone()
            if casilla:
                # Convertir el ID del tipo a nombre
                casilla = dict(casilla)
                casilla['tipo'] = obtener_tipo_casilla_por_id(casilla['tipo'])
            return casilla
    except Exception as e:
        logger_mapa.error(f"Error al obtener casilla: {e}")
        logger_mapa.error(f"Error al obtener casilla: {str(e)}")
        return None

def actualizar_casilla(x: int, z: int, tipo: str) -> bool:
    """
    Actualiza el tipo de una casilla existente.
    
    Args:
        x, z: Coordenadas de la casilla
        tipo: Nuevo tipo de casilla
        
    Returns:
        True si se actualizó exitosamente, False si no existe.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE mapa 
                SET tipo = ?
                WHERE x = ? AND z = ?
            ''', (TIPOS_CASILLAS[tipo], x, z))
            
            if cursor.rowcount == 0:
                logger_mapa.warning(f"No se encontró casilla en ({x}, {z})")
                return False
                
            conn.commit()
            logger_mapa.info(f"Casilla actualizada en ({x}, {z})")
            return True
            
    except KeyError:
        logger_mapa.error(f"Tipo de casilla no válido: {tipo}")
        return False
    except sqlite3.Error as e:
        logger_mapa.error(f"Error al actualizar casilla: {e}")
        return False

# Inicializar la tabla mapa al importar el módulo
init_db_mapa()


def obtener_tipo_casilla(x: int, z: int) -> Optional[str]:
    """
    Obtiene el tipo actual de una casilla.
    
    Args:
        x, z: Coordenadas de la casilla
        
    Returns:
        Tipo de casilla como string si existe, None si no existe
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT tipo FROM mapa WHERE x = ? AND z = ?', (x, z))
            result = cursor.fetchone()
            if result:
                return obtener_tipo_casilla_por_id(result[0])
            return None
    except sqlite3.Error as e:
        logger_mapa.error(f"Error al obtener tipo de casilla: {e}")
        return None


def tiene_casilla_caminera_adyacente(x: int, z: int) -> bool:
    """
    Verifica si una casilla tiene al menos una casilla adyacente que es de tipo camino.
    
    Args:
        x, z: Coordenadas de la casilla a verificar
        
    Returns:
        True si tiene al menos una casilla adyacente de tipo camino, False en caso contrario
    """
    try:
        tipos_camino = ["CAMINO", "CAMINO_2", "CRUCE"]
        
        # Verificar todas las casillas adyacentes (8 posibles)
        for dx in [-1, 0, 1]:
            for dz in [-1, 0, 1]:
                if dx == 0 and dz == 0:  # No verificar la casilla actual
                    continue
                    
                tipo_adyacente = obtener_tipo_casilla(x + dx, z + dz)
                if tipo_adyacente in tipos_camino:
                    return True
        
        return False
        
    except sqlite3.Error as e:
        logger_mapa.error(f"Error al verificar casillas adyacentes: {e}")


def tiene_CRUCE_adyacente(x: int, z: int) -> bool:
    """
    Verifica si una casilla tiene al menos una casilla adyacente que es de tipo CRUCE.
    
    Args:
        x, z: Coordenadas de la casilla a verificar
        
    Returns:
        True si tiene al menos una casilla adyacente de tipo CRUCE, False en caso contrario
    """
    try:
        # Verificar todas las casillas adyacentes (8 posibles)
        for dx in [-1, 0, 1]:
            for dz in [-1, 0, 1]:
                if dx == 0 and dz == 0:  # No verificar la casilla actual
                    continue
                    
                tipo_adyacente = obtener_tipo_casilla(x + dx, z + dz)
                if tipo_adyacente == "CRUCE":
                    return True
        
        return False
        
    except sqlite3.Error as e:
        logger_mapa.error(f"Error al verificar casillas CRUCE adyacentes: {e}")
        return False
        return False


def tiene_solar_asignado(ciudadano_id: int) -> bool:
    """
    Verifica si un ciudadano ya tiene un solar asignado.
    
    Args:
        ciudadano_id: ID del ciudadano a verificar
        
    Returns:
        True si tiene solar asignado, False en caso contrario
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM mapa WHERE ciudadano_id = ?', (ciudadano_id,))
            count = cursor.fetchone()[0]
            return count > 0
    except sqlite3.Error as e:
        logger_mapa.error(f"Error al verificar solar asignado: {e}")
        return False


def encontrar_solar_mas_cercano() -> Optional[tuple[int, int]]:
    """
    Encuentra el solar más cercano a (0,0) que no tenga ciudadano asignado.
    La cercanía se determina sumando los valores absolutos de las coordenadas (|x| + |z|).
    Si hay varios solares a la misma distancia, devuelve cualquiera de ellos.
    
    Returns:
        Una tupla (x, z) con las coordenadas del solar más cercano, o None si no hay solares disponibles.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Obtener todos los solares sin ciudadano
            cursor.execute('''
                SELECT x, z 
                FROM mapa 
                WHERE tipo = ? AND ciudadano_id IS NULL
            ''', (TIPOS_CASILLAS['SOLAR'],))
            
            solares = cursor.fetchall()
            
            if not solares:
                logger_mapa.info("No se encontraron solares disponibles")
                return None
                
            # Encontrar el solar más cercano
            solar_mas_cercano = None
            distancia_minima = float('inf')
            
            for solar in solares:
                x, z = solar['x'], solar['z']
                distancia = abs(x) + abs(z)
                
                if distancia < distancia_minima:
                    distancia_minima = distancia
                    solar_mas_cercano = (x, z)
            
            if solar_mas_cercano:
                logger_mapa.info(f"Solar más cercano encontrado en {solar_mas_cercano}")
            else:
                logger_mapa.warning("No se pudo encontrar un solar más cercano")
            
            return solar_mas_cercano
            
    except sqlite3.Error as e:
        logger_mapa.error(f"Error al encontrar solar más cercano: {e}")
        return None


def asignar_ciudadano_a_solar(ciudadano_id: int) -> bool:
    """
    Asigna un ciudadano al solar más cercano disponible.
    
    Args:
        ciudadano_id: ID del ciudadano a asignar
        
    Returns:
        True si se asignó exitosamente, False en caso de error
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Encontrar el solar más cercano
            solar = encontrar_solar_mas_cercano()
            if not solar:
                logger_mapa.warning(f"No se encontró solar disponible para el ciudadano {ciudadano_id}")
                return False
                
            x, z = solar
            
            # Actualizar la casilla asignando el ciudadano
            cursor.execute('''
                UPDATE mapa 
                SET ciudadano_id = ?
                WHERE x = ? AND z = ? AND tipo = ? AND ciudadano_id IS NULL
            ''', (ciudadano_id, x, z, TIPOS_CASILLAS['SOLAR']))
            
            if cursor.rowcount == 0:
                logger_mapa.error(f"No se pudo asignar ciudadano {ciudadano_id} al solar ({x}, {z})")
                return False
                
            conn.commit()
            logger_mapa.info(f"Ciudadano {ciudadano_id} asignado al solar ({x}, {z})")
            return True
            
    except sqlite3.Error as e:
        logger_mapa.error(f"Error al asignar ciudadano {ciudadano_id} a solar: {e}")
        return False


def crear_caminos_verticales():
    """
    Actualiza las casillas existentes con diferentes tipos de camino:
    - CAMINO: Vertical en x=0 desde 0,-ABS hasta 0,-3 y desde 0,3 hasta 0,ABS
    - CAMINO_2: Todas las casillas en columnas múltiplos de 5
    - CRUCE: Todas las casillas en columnas múltiplos de 5 y en la fila 0
    
    Solo se actualizarán las casillas que sean de tipo CESPED, CAMINO o CAMINO_2.
    
    Returns:
        True si se completaron los caminos exitosamente, False en caso de error.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Obtener el valor máximo absoluto de coordenadas existentes
            cursor.execute('SELECT MAX(ABS(x)), MAX(ABS(z)) FROM mapa')
            result = cursor.fetchone()
            max_abs = max(result[0] or 0, result[1] or 0)
            
            # Actualizar caminos verticales en x=0
            for z in range(-max_abs, -2):
                tipo_actual = obtener_tipo_casilla(0, z)
                if tipo_actual in ["CESPED", "CAMINO", "CAMINO_2"]:
                    if not actualizar_casilla(0, z, "CAMINO"):
                        logger_mapa.warning(f"No se pudo actualizar camino en (0, {z})")
            
            for z in range(3, max_abs+1):
                tipo_actual = obtener_tipo_casilla(0, z)
                if tipo_actual in ["CESPED", "CAMINO", "CAMINO_2"]:
                    if not actualizar_casilla(0, z, "CAMINO"):
                        logger_mapa.warning(f"No se pudo actualizar camino en (0, {z})")
            
            # Actualizar caminos en columnas múltiplos de 5
            for z in range(-max_abs, max_abs + 1):
                if z % 5 == 0:  # Si es múltiplo de 5
                    # Actualizar todas las casillas de la columna como CAMINO_2
                    for x in range(-max_abs, max_abs + 1):
                        tipo_actual = obtener_tipo_casilla(x, z)
                        if tipo_actual in ["CESPED", "CAMINO", "CAMINO_2"]:
                            if not actualizar_casilla(x, z, "CAMINO_2"):
                                logger_mapa.warning(f"No se pudo actualizar CAMINO_2 en ({x}, {z})")
            # Actualizar caminos en columnas múltiplos de 5
            for z in range(-max_abs, max_abs + 1):
                if z % 5 == 0:  # Si es múltiplo de 5
                    # Actualizar todas las casillas de la columna como CAMINO_2
                    tipo_actual = obtener_tipo_casilla(0, z)
                    if tipo_actual in ["CESPED", "CAMINO", "CAMINO_2"]:
                        if not actualizar_casilla(0, z, "CRUCE"):
                            logger_mapa.warning(f"No se pudo actualizar CRUCE en (0, {z})")
            
            # Convertir casillas adyacentes a caminos en SOLAR si son CESPED
            for x in range(-max_abs, max_abs + 1):
                for z in range(-max_abs, max_abs + 1):
                    tipo_actual = obtener_tipo_casilla(x, z)
                    if tipo_actual == "CESPED" and tiene_casilla_caminera_adyacente(x, z):
                        if not actualizar_casilla(x, z, "SOLAR"):
                            logger_mapa.warning(f"No se pudo actualizar casilla a SOLAR en ({x}, {z})")
            
            # Convertir casillas SOLAR adyacentes a CRUCE en CESPED
            for x in range(-max_abs, max_abs + 1):
                for z in range(-max_abs, max_abs + 1):
                    tipo_actual = obtener_tipo_casilla(x, z)
                    if tipo_actual == "SOLAR" and tiene_CRUCE_adyacente(x, z):
                        if not actualizar_casilla(x, z, "CESPED"):
                            logger_mapa.warning(f"No se pudo actualizar casilla SOLAR a CESPED en ({x}, {z})")
            
            conn.commit()
            logger_mapa.info("Caminos, solares y conversiones a césped actualizados exitosamente")
            return True
            
    except sqlite3.Error as e:
        logger_mapa.error(f"Error al actualizar caminos y solares: {e}")
        return False

def plaza_central() -> bool:
    """
    Marca todas las casillas desde -2,-2 hasta 2,2 como tipo PUEBLO,
    excepto la casilla (0,0) que se marca como POZO.
    
    Returns:
        True si se completó exitosamente, False en caso de error.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Primero actualizar todas las casillas a PUEBLO
            cursor.execute('''
                UPDATE mapa 
                SET tipo = ?
                WHERE x BETWEEN ? AND ? AND z BETWEEN ? AND ?
            ''', (TIPOS_CASILLAS['PUEBLO'], -2, 2, -2, 2))
            
            # Luego actualizar la casilla (0,0) a POZO
            cursor.execute('''
                UPDATE mapa 
                SET tipo = ?
                WHERE x = ? AND z = ?
            ''', (TIPOS_CASILLAS['POZO'], 0, 0))
            
            conn.commit()
            
            if cursor.rowcount > 0:
                logger_mapa.info(f"Casillas actualizadas a PUEBLO en el rango -2,-2 a 2,2")
                logger_mapa.info(f"Casilla (0,0) actualizada a POZO")
                return True
            else:
                logger_mapa.warning("No se encontraron casillas para actualizar en el rango -2,-2 a 2,2")
                return False
                
    except Exception as e:
        logger_mapa.error(f"Error al actualizar casillas a PUEBLO/POZO: {e}")
        return False

def completar_cuadrado(tipo_casilla: str = "CESPED") -> bool:
    """
    Completa el cuadrado del mapa creando todas las casillas necesarias.
    Busca el mayor valor absoluto de x o z existente (N) y crea todas las casillas
    desde -N,-N hasta N,N con el tipo especificado.
    
    Args:
        tipo_casilla: Tipo de casilla a usar para las nuevas casillas (default: CESPED)
        
    Returns:
        True si se completó el cuadrado exitosamente, False en caso de error.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Obtener el mayor valor absoluto de x o z existente
            cursor.execute('''
                SELECT MAX(ABS(x)) as max_x, MAX(ABS(z)) as max_z 
                FROM mapa
            ''')
            result = cursor.fetchone()
            
            if not result:
                # Si no hay casillas, usar el mínimo valor de 3
                max_valor = 3
            else:
                # Usar el máximo valor encontrado o 3 si es menor
                max_valor = max(3, max(result['max_x'], result['max_z']))
            
            logger_mapa.info(f"Completando cuadrado hasta ±{max_valor}")
            
            # Crear todas las casillas necesarias
            for x in range(-max_valor, max_valor + 1):
                for z in range(-max_valor, max_valor + 1):
                    # Solo crear si no existe
                    cursor.execute('''
                        SELECT 1 FROM mapa 
                        WHERE x = ? AND z = ?
                    ''', (x, z))
                    if not cursor.fetchone():
                        cursor.execute('''
                            INSERT INTO mapa (x, z, tipo)
                            VALUES (?, ?, ?)
                        ''', (x, z, TIPOS_CASILLAS[tipo_casilla]))
                        logger_mapa.info(f"Casilla creada en ({x}, {z})")
            
            conn.commit()
            return True
            
    except Exception as e:
        logger_mapa.error(f"Error al completar cuadrado: {e}")
        return False
