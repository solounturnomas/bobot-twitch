"""
Módulo que contiene las definiciones DDL (Data Definition Language) para la base de datos.
Incluye la creación de tablas, índices y otras estructuras de la base de datos.

Este módulo puede ejecutarse directamente para crear o actualizar el esquema de la base de datos:
    python database_ddl.py
"""
import sqlite3
import logging
import sys
from datetime import datetime

# Configuración de la base de datos
DB_PATH = 'soloville.db'

# Configuración del logger
logger_db = logging.getLogger('database')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger_db.addHandler(handler)
logger_db.setLevel(logging.INFO)

def get_db_connection():
    """Crea una conexión a la base de datos con soporte para filas tipo diccionario."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def crear_tablas(cursor, usuario_crear: str = 'sistema') -> bool:
    """
    Crea todas las tablas necesarias en la base de datos si no existen.
    
    Args:
        cursor: Cursor de la base de datos
        usuario_crear: Usuario que realiza la creación (opcional, por defecto 'sistema')
        
    Returns:
        bool: True si se crearon todas las tablas correctamente, False en caso contrario
    """
    try:
        # Crear tabla ciudadanos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ciudadanos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL,
                energia INTEGER DEFAULT 20,
                nivel_casa INTEGER DEFAULT 0,
                rango INTEGER DEFAULT 0,
                fecha_pozo TEXT,
                fecha_crear TEXT NOT NULL,
                fecha_modif TEXT,
                fecha_borrar TEXT,
                usuario_crear TEXT NOT NULL,
                usuario_modif TEXT,
                usuario_borrar TEXT,
                activo BOOLEAN DEFAULT TRUE,
                borrado_logico BOOLEAN DEFAULT FALSE
            )
        ''')
        logger_db.info("Tabla ciudadanos creada")

        # Crear tabla de habilidades
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS habilidades (
                codigo TEXT PRIMARY KEY,
                nombre TEXT NOT NULL,
                titulo TEXT NOT NULL,
                imagen TEXT,
                icono TEXT,
                fecha_crear TEXT NOT NULL,
                fecha_modif TEXT,
                fecha_borrar TEXT,
                usuario_crear TEXT NOT NULL,
                usuario_modif TEXT,
                usuario_borrar TEXT,
                activo BOOLEAN DEFAULT TRUE
            )
        ''')
        logger_db.info("Tabla habilidades creada")

        # Crear tabla de relación entre ciudadanos y habilidades
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS habilidades_ciudadano (
                ciudadano_id INTEGER,
                habilidad_id TEXT,
                puntos_experiencia INTEGER DEFAULT 0,
                nivel INTEGER DEFAULT 1,
                fecha_crear TEXT NOT NULL,
                fecha_modif TEXT,
                fecha_borrar TEXT,
                usuario_crear TEXT NOT NULL,
                usuario_modif TEXT,
                usuario_borrar TEXT,
                activo BOOLEAN DEFAULT TRUE,
                PRIMARY KEY (ciudadano_id, habilidad_id),
                FOREIGN KEY (ciudadano_id) REFERENCES ciudadanos(id),
                FOREIGN KEY (habilidad_id) REFERENCES habilidades(codigo)
            )
        ''')
        logger_db.info("Tabla habilidades_ciudadano creada")

        # Crear tabla de recursos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recursos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT UNIQUE NOT NULL,
                nombre TEXT NOT NULL,
                titulo TEXT,
                imagen TEXT,
                es_producto BOOLEAN DEFAULT FALSE,
                fecha_crear TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_modif TIMESTAMP,
                fecha_borrar TIMESTAMP,
                usuario_crear TEXT NOT NULL,
                usuario_modif TEXT,
                usuario_borrar TEXT,
                activo BOOLEAN DEFAULT TRUE,
                version INTEGER DEFAULT 1
            )
        ''')
        logger_db.info("Tabla recursos creada")

        # Crear tabla recursos_ciudadano
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recursos_ciudadano (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ciudadano_id INTEGER NOT NULL,
                recurso_id INTEGER NOT NULL,
                cantidad INTEGER NOT NULL DEFAULT 0,
                fecha_crear TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_modif TIMESTAMP,
                fecha_borrar TIMESTAMP,
                usuario_crear TEXT NOT NULL,
                usuario_modif TEXT,
                usuario_borrar TEXT,
                activo BOOLEAN DEFAULT TRUE,
                version INTEGER DEFAULT 1,
                UNIQUE(ciudadano_id, recurso_id),
                FOREIGN KEY (ciudadano_id) REFERENCES ciudadanos(id) ON DELETE CASCADE,
                FOREIGN KEY (recurso_id) REFERENCES recursos(id) ON DELETE CASCADE
            )
        ''')
        logger_db.info("Tabla recursos_ciudadano creada")

        # Crear tabla fabricacion_productos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fabricacion_productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recurso_id INTEGER NOT NULL,
                cantidad INTEGER NOT NULL DEFAULT 1,
                fecha_crear TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_modif TIMESTAMP,
                fecha_borrar TIMESTAMP,
                usuario_crear TEXT NOT NULL,
                usuario_modif TEXT,
                usuario_borrar TEXT,
                activo BOOLEAN DEFAULT TRUE,
                version INTEGER DEFAULT 1,
                FOREIGN KEY (recurso_id) REFERENCES recursos(id)
            )
        ''')
        logger_db.info("Tabla fabricacion_productos creada")

        # Crear tabla recursos_fabricacion
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recursos_fabricacion (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recurso_id INTEGER NOT NULL,
                fabricacion_id INTEGER NOT NULL,
                cantidad INTEGER NOT NULL DEFAULT 1,
                fecha_crear TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_modif TIMESTAMP,
                fecha_borrar TIMESTAMP,
                usuario_crear TEXT NOT NULL,
                usuario_modif TEXT,
                usuario_borrar TEXT,
                activo BOOLEAN DEFAULT TRUE,
                version INTEGER DEFAULT 1,
                FOREIGN KEY (recurso_id) REFERENCES recursos(id),
                FOREIGN KEY (fabricacion_id) REFERENCES fabricacion_productos(id),
                UNIQUE(recurso_id, fabricacion_id)
            )
        ''')
        logger_db.info("Tabla recursos_fabricacion creada")

        # Crear vista fabricacion_lista
        cursor.execute('''
            CREATE VIEW IF NOT EXISTS fabricacion_lista AS
            SELECT 
                rb.id,
                rb.nombre AS nombre_producto, 
                fp.cantidad AS cantidad_producto, 
                rr.nombre AS nombre_recurso, 
                rf.cantidad AS cantidad_recurso
            FROM 
                fabricacion_productos fp, 
                recursos_fabricacion rf, 
                recursos rb, 
                recursos rr 
            WHERE 
                fp.id = rf.fabricacion_id
                AND fp.recurso_id = rb.id
                AND rf.recurso_id = rr.id
        ''')
        logger_db.info("Vista fabricacion_lista creada")

        # Crear tabla historial_acciones
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historial_acciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_accion TEXT NOT NULL,
                mensaje_final TEXT NOT NULL,
                fecha_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
                ciudadano_id INTEGER,
                FOREIGN KEY(ciudadano_id) REFERENCES ciudadanos(id)
            )
        ''')
        logger_db.info("Tabla historial_acciones creada")

        # Crear tabla de herramientas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS herramientas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT UNIQUE NOT NULL,
                nombre TEXT NOT NULL,
                titulo TEXT,
                imagen TEXT,
                fecha_crear TEXT NOT NULL,
                fecha_modif TEXT,
                fecha_borrar TEXT,
                usuario_crear TEXT NOT NULL,
                usuario_modif TEXT,
                usuario_borrar TEXT,
                activo BOOLEAN DEFAULT TRUE
            )
        ''')
        logger_db.info("Tabla herramientas creada")

        # Crear tabla de acciones
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS acciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT UNIQUE NOT NULL,
                nombre TEXT NOT NULL,
                titulo TEXT,
                imagen TEXT,
                herramienta_id INTEGER,
                fecha_crear TEXT NOT NULL,
                fecha_modif TEXT,
                fecha_borrar TEXT,
                usuario_crear TEXT NOT NULL,
                usuario_modif TEXT,
                usuario_borrar TEXT,
                activo BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (herramienta_id) REFERENCES herramientas(id)
            )
        ''')
        logger_db.info("Tabla acciones creada")

        # Crear tabla de relación entre acciones y recursos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recursos_acciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                accion_id INTEGER NOT NULL,
                recurso_id INTEGER NOT NULL,
                cantidad INTEGER NOT NULL DEFAULT 0,
                cantidad_pozo INTEGER NOT NULL DEFAULT 0,
                cantidad_herramienta INTEGER NOT NULL DEFAULT 0,
                probabilidad INTEGER NOT NULL DEFAULT 0,
                probabilidad_pozo INTEGER NOT NULL DEFAULT 0,
                probabilidad_herramienta INTEGER NOT NULL DEFAULT 0,
                fecha_crear TEXT NOT NULL,
                fecha_modif TEXT,
                fecha_borrar TEXT,
                usuario_crear TEXT NOT NULL,
                usuario_modif TEXT,
                usuario_borrar TEXT,
                activo BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (accion_id) REFERENCES acciones(id),
                FOREIGN KEY (recurso_id) REFERENCES recursos(id),
                UNIQUE(accion_id, recurso_id)
            )
        ''')
        logger_db.info("Tabla recursos_acciones creada")

        # Crear tabla de relación entre ciudadanos y herramientas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS herramientas_ciudadano (
                ciudadano_id INTEGER NOT NULL,
                herramienta_id INTEGER NOT NULL,
                tiene BOOLEAN DEFAULT FALSE,
                fecha_crear TEXT NOT NULL,
                fecha_modif TEXT,
                fecha_borrar TEXT,
                usuario_crear TEXT NOT NULL,
                usuario_modif TEXT,
                usuario_borrar TEXT,
                activo BOOLEAN DEFAULT TRUE,
                PRIMARY KEY (ciudadano_id, herramienta_id),
                FOREIGN KEY (ciudadano_id) REFERENCES ciudadanos(id),
                FOREIGN KEY (herramienta_id) REFERENCES herramientas(id),
                UNIQUE(ciudadano_id, herramienta_id)
            )
        ''')
        logger_db.info("Tabla herramientas_ciudadano creada")

        # Crear tabla de edificios
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS edificios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT UNIQUE NOT NULL,
                nombre TEXT NOT NULL,
                titulo TEXT,
                imagen TEXT,
                orden_construccion INTEGER DEFAULT 0,
                esta_construido BOOLEAN DEFAULT FALSE,
                fecha_crear TEXT NOT NULL,
                fecha_modif TEXT,
                fecha_borrar TEXT,
                usuario_crear TEXT NOT NULL,
                usuario_modif TEXT,
                usuario_borrar TEXT,
                activo BOOLEAN DEFAULT TRUE
            )
        ''')
        logger_db.info("Tabla edificios creada")
        
        return True

    except sqlite3.Error as e:
        logger_db.error(f"Error al crear tablas: {e}")
        return False

def crear_indices(cursor):
    """
    Crea índices adicionales para mejorar el rendimiento de las consultas.
    
    Args:
        cursor: Cursor de la base de datos
    """
    try:
        # Crear índices para mejorar el rendimiento
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_herramientas_ciudadano_ciudadano 
            ON herramientas_ciudadano(ciudadano_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_herramientas_ciudadano_herramienta 
            ON herramientas_ciudadano(herramienta_id)
        ''')
        logger_db.info("Índices de herramientas_ciudadano creados")

        # Índices para la tabla recursos_ciudadano
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_recursos_ciudadano_ciudadano 
            ON recursos_ciudadano(ciudadano_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_recursos_ciudadano_recurso 
            ON recursos_ciudadano(recurso_id)
        ''')
        
        # Índices para la tabla habilidades_ciudadano
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_habilidades_ciudadano_ciudadano 
            ON habilidades_ciudadano(ciudadano_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_habilidades_ciudadano_habilidad 
            ON habilidades_ciudadano(habilidad_id)
        ''')
        
        # Índices para la tabla recursos_acciones
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_recursos_acciones_accion 
            ON recursos_acciones(accion_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_recursos_acciones_recurso 
            ON recursos_acciones(recurso_id)
        ''')
        
        logger_db.info("Índices adicionales creados")
        return True
        
    except Exception as e:
        logger_db.error(f"Error al crear índices: {e}")
        raise

def main():
    """
    Punto de entrada principal cuando se ejecuta el script directamente.
    Crea todas las tablas e índices necesarios en la base de datos.
    """
    try:
        logger_db.info(f"Iniciando creación de esquema de base de datos en {DB_PATH}")
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Crear tablas
            if crear_tablas(cursor):
                logger_db.info("Todas las tablas se crearon correctamente")
            else:
                logger_db.error("Ocurrieron errores al crear las tablas")
                return False
            
            # Crear índices
            try:
                crear_indices(cursor)
                logger_db.info("Índices creados correctamente")
            except Exception as e:
                logger_db.error(f"Error al crear índices: {e}")
                return False
            
            conn.commit()
            logger_db.info("Esquema de base de datos creado exitosamente")
            return True
            
    except Exception as e:
        logger_db.error(f"Error inesperado al crear el esquema: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    # Configurar logging para la ejecución directa
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    
    # Ejecutar la función principal
    if main():
        sys.exit(0)
    else:
        sys.exit(1)
