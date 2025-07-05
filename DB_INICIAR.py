"""
Módulo que maneja la base de datos SQLite para el bot de Twitch.
Esta base de datos almacena información sobre los ciudadanos y sus recursos.

Este módulo importa la funcionalidad de los módulos database_ddl.py y database_dml.py
para mantener una estructura modular y organizada.
"""

import sqlite3
import logging
from contextlib import contextmanager
from typing import Dict, Any, Optional
import configuracion_logging

# Configuración del logger
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

def init_db(usuario_crear: str = 'sistema') -> bool:
    """
    Inicializa la base de datos importando las funciones de los módulos DDL y DML.
    
    Args:
        usuario_crear: Nombre del usuario que realiza la inicialización
        
    Returns:
        bool: True si la inicialización fue exitosa, False en caso contrario
    """ 
    try:
        from database_ddl import main as ddl_init_db
        from database_dml import main as dml_init_db
        
        # Inicializar esquema de la base de datos
        if not ddl_init_db():
            logger_db.error("Error al inicializar el esquema de la base de datos")
            return False
            
        # Inicializar datos de la base de datos
        if not dml_init_db():
            logger_db.error("Error al inicializar los datos de la base de datos")
            return False
        
        logger_db.info("Base de datos inicializada correctamente")
        return True
        
    except ImportError as e:
        logger_db.error(f"Error al importar módulos DDL/DML: {e}")
        return False
    except Exception as e:
        logger_db.error(f"Error inesperado al inicializar la base de datos: {e}")
        return False

# Inicializar la base de datos al importar el módulo
init_db()