"""
Módulo que maneja la base de datos SQLite para el bot de Twitch.
Esta base de datos almacena información sobre los ciudadanos y sus recursos.
"""

import sqlite3
from datetime import datetime
from typing import Optional, Dict, Any
import logging
import configuracion_logging
from contextlib import contextmanager

# Configurar logging específico para la base de datos
logger = configuracion_logging.logger
logger_db = logger.getChild('database')

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

def init_db():
    """
    Inicializa la base de datos y crea las tablas necesarias si no existen.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            logger_db.info("Iniciando creación de tablas")
            
            # Crear tabla ciudadanos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ciudadanos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT UNIQUE NOT NULL,
                    cantidad_madera INTEGER DEFAULT 1,
                    cantidad_ramas INTEGER DEFAULT 1,
                    cantidad_piedra INTEGER DEFAULT 1,
                    cantidad_hierro INTEGER DEFAULT 1,
                    cantidad_pescado INTEGER DEFAULT 1,
                    cantidad_trigo INTEGER DEFAULT 1,
                    cantidad_verdura INTEGER DEFAULT 1,
                    cantidad_carne INTEGER DEFAULT 1,
                    cantidad_piel INTEGER DEFAULT 1,
                    hierbas INTEGER DEFAULT 1,
                    nivel_leñador INTEGER DEFAULT 1,
                    nivel_recolector INTEGER DEFAULT 1,
                    nivel_pescador INTEGER DEFAULT 1,
                    nivel_cazador INTEGER DEFAULT 1,
                    nivel_agricultor INTEGER DEFAULT 1,
                    nivel_guardia INTEGER DEFAULT 1,
                    nivel_minero INTEGER DEFAULT 1,
                    rango TEXT DEFAULT 'Ciudadano',
                    fecha_crea TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fecha_modificar TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    usuario_crear TEXT,
                    usuario_modificar TEXT,
                    fecha_borrar TIMESTAMP,
                    usuario_borrar TEXT,
                    borrado_logico BOOLEAN DEFAULT FALSE,
                    version INTEGER DEFAULT 1
                )
            ''')
            logger_db.info("Tabla ciudadanos creada")
            
            # Crear tabla de historial de acciones
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS historial_acciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    codigo_accion TEXT NOT NULL,
                    mensaje_final TEXT NOT NULL,
                    ciudadano_id INTEGER,
                    FOREIGN KEY (ciudadano_id) REFERENCES ciudadanos(id)
                )
            ''')
            logger_db.info("Tabla historial_acciones creada")
            
            conn.commit()
            logger_db.info("Tablas creadas exitosamente")
            
    except sqlite3.Error as e:
        logger_db.error(f"Error al crear las tablas: {e}")
        raise

def get_ciudadano(nombre: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene un ciudadano por su nombre.
    
    Args:
        nombre: Nombre del ciudadano a buscar.
        
    Returns:
        Diccionario con la información del ciudadano si existe, None si no existe.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM ciudadanos WHERE nombre = ?', (nombre,))
            ciudadano = cursor.fetchone()
            if ciudadano:
                logger_db.info(f"Ciudadano encontrado: {nombre}")
                return dict(ciudadano)
            else:
                logger_db.info(f"Ciudadano no encontrado: {nombre}")
                return None
    except sqlite3.Error as e:
        logger_db.error(f"Error al obtener ciudadano {nombre}: {e}")
        return None

def crear_ciudadano(nombre: str, usuario_crear: str = None) -> bool:
    """
    Crea un nuevo ciudadano en la base de datos con información de auditoría.
    
    Args:
        nombre: Nombre del nuevo ciudadano.
        usuario_crear: Usuario que crea el registro (opcional)
        
    Returns:
        True si se creó exitosamente, False si ya existe.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            logger_db.info(f"Intentando crear ciudadano: {nombre}")
            cursor.execute('''
                INSERT INTO ciudadanos 
                (nombre, usuario_crear, usuario_modificar)
                VALUES (?, ?, ?)
            ''', (nombre, usuario_crear, usuario_crear))
            conn.commit()
            logger_db.info(f"Ciudadano creado exitosamente: {nombre}")
            return True
    except sqlite3.IntegrityError:
        logger_db.warning(f"Ciudadano ya existe: {nombre}")
        return False
    except sqlite3.Error as e:
        logger_db.error(f"Error al crear ciudadano {nombre}: {e}")
        return False

def actualizar_ciudadano(nombre: str, datos: Dict[str, Any], usuario_modificar: str = None) -> bool:
    """
    Actualiza los datos de un ciudadano existente con información de auditoría.
    
    Args:
        nombre: Nombre del ciudadano a actualizar.
        datos: Diccionario con los datos a actualizar.
        usuario_modificar: Usuario que actualiza el registro (opcional)
        
    Returns:
        True si se actualizó exitosamente, False si no existe.
    """
    try:
        if not datos:
            logger_db.warning(f"No se proporcionaron datos para actualizar ciudadano: {nombre}")
            return False
        
        # Añadir campos de auditoría a los datos
        datos['fecha_modificar'] = datetime.now()
        datos['usuario_modificar'] = usuario_modificar
        datos['version'] = datos.get('version', 1) + 1
        
        set_clause = ', '.join(f'{campo} = ?' for campo in datos.keys())
        valores = list(datos.values()) + [nombre]
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            logger_db.info(f"Intentando actualizar ciudadano: {nombre}")
            cursor.execute(f'UPDATE ciudadanos SET {set_clause} WHERE nombre = ?', valores)
            conn.commit()
            if cursor.rowcount > 0:
                logger_db.info(f"Ciudadano actualizado exitosamente: {nombre}")
                return True
            else:
                logger_db.warning(f"No se encontró ciudadano para actualizar: {nombre}")
                return False
    except sqlite3.Error as e:
        logger_db.error(f"Error al actualizar ciudadano {nombre}: {e}")
        return False

def eliminar_ciudadano(nombre: str, usuario_borrar: str = None) -> bool:
    """
    Desactiva un ciudadano (soft delete) en lugar de eliminarlo.
    
    Args:
        nombre: Nombre del ciudadano a desactivar.
        usuario_borrar: Usuario que realiza la desactivación (opcional)
        
    Returns:
        True si se desactivó exitosamente, False si no existía.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            logger_db.info(f"Intentando desactivar ciudadano: {nombre}")
            cursor.execute('''
                UPDATE ciudadanos 
                SET borrado_logico = 1,
                    fecha_borrar = ?,
                    usuario_borrar = ?,
                    fecha_modificar = ?,
                    usuario_modificar = ?
                WHERE nombre = ?
            ''', (datetime.now(), usuario_borrar, datetime.now(), usuario_borrar, nombre))
            conn.commit()
            if cursor.rowcount > 0:
                logger_db.info(f"Ciudadano desactivado exitosamente: {nombre}")
                return True
            else:
                logger_db.warning(f"No se encontró ciudadano para desactivar: {nombre}")
                return False
    except sqlite3.Error as e:
        logger_db.error(f"Error al desactivar ciudadano {nombre}: {e}")
        return False

def listar_ciudadanos() -> list:
    """
    Lista todos los ciudadanos activos en la base de datos.
    
    Returns:
        Lista de diccionarios con la información de los ciudadanos activos.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM ciudadanos WHERE borrado_logico = 0 ORDER BY fecha_crea DESC')
            ciudadanos = [dict(row) for row in cursor.fetchall()]
            logger_db.info(f"Listado {len(ciudadanos)} ciudadanos activos")
            return ciudadanos
    except sqlite3.Error as e:
        logger_db.error(f"Error al listar ciudadanos: {e}")
        return []

def mostrar_ciudadanos():
    """
    Muestra en formato amigable la lista de ciudadanos.
    """
    ciudadanos = listar_ciudadanos()
    if not ciudadanos:
        print("No hay ciudadanos registrados")
        return
    
    print("\n=== LISTA DE CIUDADANOS ===")
    print("-" * 50)
    for ciudadano in ciudadanos:
        print(f"\nID: {ciudadano['id']}")
        print(f"Nombre: {ciudadano['nombre']}")
        print(f"Rango: {ciudadano['rango']}")
        print("\nRecursos:")
        print(f"  Madera: {ciudadano['cantidad_madera']}")
        print(f"  Ramas: {ciudadano['cantidad_ramas']}")
        print(f"  Piedra: {ciudadano['cantidad_piedra']}")
        print(f"  Hierro: {ciudadano['cantidad_hierro']}")
        print(f"  Pescado: {ciudadano['cantidad_pescado']}")
        print(f"  Trigo: {ciudadano['cantidad_trigo']}")
        print(f"  Verdura: {ciudadano['cantidad_verdura']}")
        print(f"  Carne: {ciudadano['cantidad_carne']}")
        print(f"  Piel: {ciudadano['cantidad_piel']}")
        print(f"  Hierbas: {ciudadano['hierbas']}")
        
        print("\nNiveles:")
        print(f"  Leñador: {ciudadano['nivel_leñador']}")
        print(f"  Recolector: {ciudadano['nivel_recolector']}")
        print(f"  Pescador: {ciudadano['nivel_pescador']}")
        print(f"  Cazador: {ciudadano['nivel_cazador']}")
        print(f"  Agricultor: {ciudadano['nivel_agricultor']}")
        print(f"  Guardia: {ciudadano['nivel_guardia']}")
        print(f"  Minero: {ciudadano['nivel_minero']}")
        
        print("\nAuditoría:")
        print(f"  Fecha creación: {ciudadano['fecha_crea']}")
        print(f"  Fecha última modificación: {ciudadano['fecha_modificar']}")
        print(f"  Creado por: {ciudadano['usuario_crear']}")
        print(f"  Modificado por: {ciudadano['usuario_modificar']}")
        print("-" * 50)

def mostrar_historial(fecha_inicio: str = None, fecha_fin: str = None, 
                     codigo_accion: str = None, ciudadano_id: int = None):
    """
    Muestra el historial de acciones de manera amigable.
    """
    historial = listar_historial_acciones(fecha_inicio, fecha_fin, codigo_accion, ciudadano_id)
    if not historial:
        print("No hay acciones registradas en el historial")
        return
    
    print("\n=== HISTORIAL DE ACCIONES ===")
    print("-" * 50)
    for accion in historial:
        print(f"\nID: {accion['id']}")
        print(f"Fecha y hora: {accion['fecha_hora']}")
        print(f"Código de acción: {accion['codigo_accion']}")
        print(f"Mensaje: {accion['mensaje_final']}")
        if accion['ciudadano_id']:
            print(f"Ciudadano ID: {accion['ciudadano_id']}")
        print("-" * 50)

def registrar_accion(codigo_accion: str, mensaje_final: str, ciudadano_id: int = None) -> bool:
    """
    Registra una nueva acción en el historial.
    
    Args:
        codigo_accion: Código de la acción realizada
        mensaje_final: Mensaje final devuelto
        ciudadano_id: ID del ciudadano asociado (opcional)
        
    Returns:
        True si se registró exitosamente, False en caso de error
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            logger_db.info(f"Registrando acción: {codigo_accion}")
            cursor.execute('''
                INSERT INTO historial_acciones 
                (codigo_accion, mensaje_final, ciudadano_id)
                VALUES (?, ?, ?)
            ''', (codigo_accion, mensaje_final, ciudadano_id))
            conn.commit()
            logger_db.info(f"Acción registrada exitosamente: {codigo_accion}")
            return True
    except sqlite3.Error as e:
        logger_db.error(f"Error al registrar acción: {e}")
        return False

def listar_historial_acciones(fecha_inicio: str = None, fecha_fin: str = None, 
                            codigo_accion: str = None, ciudadano_id: int = None) -> list:
    """
    Lista las acciones del historial según los filtros proporcionados.
    
    Args:
        fecha_inicio: Fecha inicial para filtrar (opcional)
        fecha_fin: Fecha final para filtrar (opcional)
        codigo_accion: Código de acción específico para filtrar (opcional)
        ciudadano_id: ID del ciudadano para filtrar (opcional)
        
    Returns:
        Lista de diccionarios con la información de las acciones.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            logger_db.info("Listando historial de acciones")
            
            # Construir la consulta base
            query = "SELECT * FROM historial_acciones"
            params = []
            
            # Añadir condiciones según los filtros proporcionados
            condiciones = []
            if fecha_inicio:
                condiciones.append("fecha_hora >= ?")
                params.append(fecha_inicio)
            if fecha_fin:
                condiciones.append("fecha_hora <= ?")
                params.append(fecha_fin)
            if codigo_accion:
                condiciones.append("codigo_accion = ?")
                params.append(codigo_accion)
            if ciudadano_id is not None:
                condiciones.append("ciudadano_id = ?")
                params.append(ciudadano_id)
            
            if condiciones:
                query += " WHERE " + " AND ".join(condiciones)
            
            # Ordenar por fecha_hora descendente
            query += " ORDER BY fecha_hora DESC"
            
            cursor.execute(query, params)
            acciones = [dict(row) for row in cursor.fetchall()]
            logger_db.info(f"Encontradas {len(acciones)} acciones en el historial")
            return acciones
    except sqlite3.Error as e:
        logger_db.error(f"Error al listar historial de acciones: {e}")
        return []

# Inicializar la base de datos al importar el módulo
init_db()
