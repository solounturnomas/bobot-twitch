"""
Módulo que contiene las operaciones DML (Data Manipulation Language) para la base de datos.
Incluye funciones para insertar, actualizar, eliminar y consultar datos.

Este módulo puede ejecutarse directamente para poblar la base de datos con datos iniciales:
    python database_dml.py
"""
import sqlite3
import logging
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Union

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

def inicializar_habilidades(cursor=None, usuario_crear: str = 'sistema') -> bool:
    """
    Inicializa las habilidades en la base de datos si no existen.
    
    Args:
        cursor: Cursor de la base de datos. Si es None, se crea una nueva conexión.
        usuario_crear: Usuario que realiza la creación (opcional, por defecto 'sistema')
        
    Returns:
        bool: True si se inicializaron las habilidades correctamente, False en caso contrario
    """
    # Si no se proporciona un cursor, manejar la conexión internamente
    if cursor is None:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                result = _inicializar_habilidades_impl(cursor, usuario_crear)
                conn.commit()
                return result
            except Exception as e:
                conn.rollback()
                logger_db.error(f"Error al inicializar habilidades: {e}")
                return False
    
    return _inicializar_habilidades_impl(cursor, usuario_crear)

def _inicializar_habilidades_impl(cursor, usuario_crear: str) -> bool:
    """
    Inicializa las habilidades en la base de datos si no existen.
    
    Args:
        cursor: Cursor de la base de datos
        usuario_crear: Usuario que realiza la creación (opcional, por defecto 'sistema')
        
    Returns:
        bool: True si se inicializaron las habilidades correctamente, False en caso contrario
    """
    try:
        # Verificar si ya hay habilidades en la base de datos
        cursor.execute('SELECT COUNT(*) FROM habilidades')
        if cursor.fetchone()[0] > 0:
            logger_db.info("Las habilidades ya están inicializadas")
            return True
        
        # Habilidades por defecto
        habilidades_por_defecto = [
            ('lenador', 'Leñador', 'Leñador', 'hacha.png', 'fa-tree'),
            ('recolector', 'Recolector', 'Recolector', 'cesta.png', 'fa-leaf'),
            ('pescador', 'Pescador', 'Pescador', 'caña.png', 'fa-fish'),
            ('cazador', 'Cazador', 'Cazador', 'arco.png', 'fa-bullseye'),
            ('agricultor', 'Agricultor', 'Agricultor', 'azada.png', 'fa-seedling'),
            ('guardia', 'Guardia', 'Guardia', 'escudo.png', 'fa-shield-alt'),
            ('minero', 'Minero', 'Minero', 'pico.png', 'fa-gem')
        ]
        
        # Obtener la fecha actual para los campos de auditoría
        fecha_actual = datetime.now().isoformat()
        
        # Asegurar que usuario_crear no sea nulo
        if not usuario_crear:
            usuario_crear = 'sistema'
        
        # Insertar las habilidades
        for codigo, nombre, titulo, imagen, icono in habilidades_por_defecto:
            cursor.execute('''
                INSERT OR IGNORE INTO habilidades 
                (codigo, nombre, titulo, imagen, icono, fecha_crear, usuario_crear, activo)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            ''', (codigo, nombre, titulo, imagen, icono, fecha_actual, usuario_crear))
        
        logger_db.info(f"Se insertaron {len(habilidades_por_defecto)} habilidades por defecto")
        return True
        
    except sqlite3.Error as e:
        logger_db.error(f"Error al inicializar habilidades: {e}")
        return False

def inicializar_herramientas(cursor=None, usuario_crear: str = 'sistema') -> bool:
    """
    Inicializa las herramientas en la base de datos si no existen.
    
    Args:
        cursor: Cursor de la base de datos. Si es None, se crea una nueva conexión.
        usuario_crear: Usuario que realiza la creación (opcional, por defecto 'sistema')
        
    Returns:
        bool: True si se inicializaron las herramientas correctamente, False en caso contrario
    """
    # Si no se proporciona un cursor, manejar la conexión internamente
    if cursor is None:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                result = _inicializar_herramientas_impl(cursor, usuario_crear)
                conn.commit()
                return result
            except Exception as e:
                conn.rollback()
                logger_db.error(f"Error al inicializar herramientas: {e}")
                return False
    
    return _inicializar_herramientas_impl(cursor, usuario_crear)

def _inicializar_herramientas_impl(cursor, usuario_crear: str) -> bool:
    """
    Inicializa las herramientas en la base de datos si no existen.
    
    Args:
        usuario_crear: Usuario que realiza la creación (opcional, por defecto 'sistema')
        
    Returns:
        bool: True si se inicializaron las herramientas correctamente, False en caso contrario
    """
    try:
        with sqlite3.connect('soloville.db') as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Verificar si ya hay herramientas en la base de datos
            cursor.execute('SELECT COUNT(*) FROM herramientas')
            if cursor.fetchone()[0] > 0:
                logger_db.info("Las herramientas ya están inicializadas")
                return True
            
            # Lista de herramientas predeterminadas
            herramientas = [    
                ('hacha', 'Hacha', 'Hacha de leñador', 'tools/hacha.png'),
                ('pico', 'Pico', 'Pico de minero', 'tools/pico.png'),
                ('espada', 'Espada', 'Espada de combate', 'tools/espada.png'),
                ('hazada', 'Hazada', 'Hazada de agricultor', 'tools/hazada.png'),
                ('arco', 'Arco', 'Arco de cazador', 'tools/arco.png'),
                ('cana', 'Caña de pescar', 'Caña de pescar', 'tools/cana.png'),
                ('pala', 'Pala', 'Pala de excavación', 'tools/pala.png')
            ]
            
            # Insertar herramientas que no existen
            fecha_actual = datetime.now().isoformat()
            for codigo, nombre, titulo, imagen in herramientas:
                cursor.execute('''
                    INSERT OR IGNORE INTO herramientas 
                    (codigo, nombre, titulo, imagen, fecha_crear, usuario_crear, activo)
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                ''', (codigo, nombre, titulo, imagen, fecha_actual, usuario_crear))
            
            logger_db.info(f"Se insertaron {len(herramientas)} herramientas iniciales")
            conn.commit()
            return True
            
    except sqlite3.Error as e:
        logger_db.error(f"Error al inicializar herramientas: {e}")
        return False

def inicializar_acciones(cursor=None, usuario_crear: str = 'sistema') -> bool:
    """
    Inicializa las acciones en la base de datos si no existen.
    
    Args:
        cursor: Cursor de la base de datos. Si es None, se crea una nueva conexión.
        usuario_crear: Usuario que realiza la creación (opcional, por defecto 'sistema')
        
    Returns:
        bool: True si se inicializaron las acciones correctamente, False en caso contrario
    """
    # Si no se proporciona un cursor, manejar la conexión internamente
    if cursor is None:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                result = _inicializar_acciones_impl(cursor, usuario_crear)
                conn.commit()
                return result
            except Exception as e:
                conn.rollback()
                logger_db.error(f"Error al inicializar acciones: {e}")
                return False
    
    return _inicializar_acciones_impl(cursor, usuario_crear)

def _inicializar_acciones_impl(cursor, usuario_crear: str) -> bool:
    """
    Inicializa las acciones en la base de datos si no existen.
    
    Args:
        usuario_crear: Usuario que realiza la creación (opcional, por defecto 'sistema')
        
    Returns:
        bool: True si se inicializaron las acciones correctamente, False en caso contrario
    """
    try:
        with sqlite3.connect('soloville.db') as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Verificar si ya hay acciones en la base de datos
            cursor.execute('SELECT COUNT(*) FROM acciones')
            if cursor.fetchone()[0] > 0:
                logger_db.info("Las acciones ya están inicializadas")
                return True
            
            # Obtener el ID de las herramientas relacionadas
            cursor.execute("SELECT id, codigo FROM herramientas WHERE codigo IN ('hacha', 'pico', 'caña', 'pala', 'hazada', 'arco')")
            herramientas = {row['codigo']: row['id'] for row in cursor.fetchall()}
            
            # Verificar que todas las herramientas necesarias existen
            herramientas_requeridas = ['hacha', 'pico', 'caña', 'pala', 'hazada', 'arco']
            for herramienta in herramientas_requeridas:
                if herramienta not in herramientas:
                    logger_db.error(f"No se encontró la herramienta requerida: {herramienta}")
                    return False
            
            # Definir las acciones a insertar
            acciones = [
                {
                    'codigo': 'talar',
                    'nombre': 'Talar árboles',
                    'titulo': 'Talar',
                    'imagen': 'talar.png',
                    'herramienta_id': herramientas.get('hacha')
                },
                {
                    'codigo': 'minar',
                    'nombre': 'Minar piedra',
                    'titulo': 'Minar',
                    'imagen': 'minar.png',
                    'herramienta_id': herramientas.get('pico')
                },
                {
                    'codigo': 'pescar',
                    'nombre': 'Pescar en el río',
                    'titulo': 'Pescar',
                    'imagen': 'pescar.png',
                    'herramienta_id': herramientas.get('caña')
                },
                {
                    'codigo': 'cavar',
                    'nombre': 'Cavar en busca de arcilla',
                    'titulo': 'Cavar',
                    'imagen': 'cavar.png',
                    'herramienta_id': herramientas.get('pala')
                },
                {
                    'codigo': 'guardia',
                    'nombre': 'Trabajar de guardia',
                    'titulo': 'Guardia',
                    'imagen': 'guardia.png',
                    'herramienta_id': None
                },
                {
                    'codigo': 'cultivar',
                    'nombre': 'Cultivar la tierra',
                    'titulo': 'Cultivar',
                    'imagen': 'cultivar.png',
                    'herramienta_id': herramientas.get('hazada')
                },
                {
                    'codigo': 'cazar',
                    'nombre': 'Cazar en el bosque',
                    'titulo': 'Cazar',
                    'imagen': 'cazar.png',
                    'herramienta_id': herramientas.get('arco')
                }
            ]
            
            try:
                # Insertar las acciones en una sola transacción
                fecha_actual = datetime.now().isoformat()
                for accion in acciones:
                    cursor.execute('''
                        INSERT INTO acciones 
                        (codigo, nombre, titulo, imagen, herramienta_id, fecha_crear, usuario_crear, activo)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                    ''', (
                        accion['codigo'],
                        accion['nombre'],
                        accion['titulo'],
                        accion['imagen'],
                        accion['herramienta_id'],
                        fecha_actual,
                        usuario_crear
                    ))
                
                logger_db.info(f"Se insertaron {len(acciones)} acciones iniciales")
                conn.commit()
                return True
                
            except sqlite3.IntegrityError as e:
                logger_db.error(f"Error de integridad al insertar acciones: {e}")
                conn.rollback()
                return False
            except Exception as e:
                logger_db.error(f"Error inesperado al insertar acciones: {e}")
                conn.rollback()
                return False
                
    except sqlite3.Error as e:
        logger_db.error(f"Error al inicializar acciones: {e}")
        return False

def inicializar_recursos(cursor=None, usuario_crear: str = 'sistema') -> bool:
    """
    Inicializa los recursos en la base de datos si no existen.
    
    Args:
        cursor: Cursor de la base de datos. Si es None, se crea una nueva conexión.
        usuario_crear: Usuario que realiza la creación (opcional, por defecto 'sistema')
        
    Returns:
        bool: True si se inicializaron los recursos correctamente, False en caso contrario
    """
    # Si no se proporciona un cursor, manejar la conexión internamente
    if cursor is None:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                result = _inicializar_recursos_impl(cursor, usuario_crear)
                conn.commit()
                return result
            except Exception as e:
                conn.rollback()
                logger_db.error(f"Error al inicializar recursos: {e}")
                return False
    
    return _inicializar_recursos_impl(cursor, usuario_crear)

def _inicializar_recursos_impl(cursor, usuario_crear: str) -> bool:
    """
    Inicializa los recursos en la base de datos si no existen.
    
    Args:
        usuario_crear: Usuario que realiza la creación (opcional, por defecto 'sistema')
        
    Returns:
        bool: True si se inicializaron los recursos correctamente, False en caso contrario
    """
    try:
        with sqlite3.connect('soloville.db') as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Verificar si ya hay recursos en la base de datos
            cursor.execute('SELECT COUNT(*) FROM recursos')
            if cursor.fetchone()[0] > 0:
                logger_db.info("Los recursos ya están inicializados")
                return True
            
            # Recursos por defecto
            recursos_por_defecto = [
                # Recursos básicos (es_producto = FALSE)
                ('moneda', 'Moneda', 'Monedas', 'moneda.png', False),
                ('madera', 'Madera', 'Madera', 'madera.png', False),
                ('rama', 'Rama', 'Ramas', 'rama.png', False),
                ('piedra', 'Piedra', 'Piedras', 'piedra.png', False),
                ('arcilla', 'Arcilla', 'Arcilla', 'arcilla.png', False),
                ('hierro', 'Hierro', 'Hierro', 'hierro.png', False),
                ('pescado', 'Pescado', 'Pescado', 'pescado.png', False),
                ('trigo', 'Trigo', 'Trigo', 'trigo.png', False),
                ('verdura', 'Verdura', 'Verduras', 'verdura.png', False),
                ('carne', 'Carne', 'Carne', 'carne.png', False),
                ('piel', 'Piel', 'Pieles', 'piel.png', False),
                ('hierba', 'Hierba', 'Hierbas', 'hierba.png', False),
                ('energia', 'Energia', 'Energia', 'energia.png', False),
                ('agua', 'Agua', 'Agua', 'agua.png', False),
                
                # Productos fabricables (es_producto = TRUE)
                ('tabla', 'Tabla', 'Tablas de madera', 'tabla.png', True),
                ('bloque', 'Bloque', 'Bloques de piedra', 'bloque.png', True),
                ('ladrillo', 'Ladrillo', 'Ladrillos de arcilla', 'ladrillo.png', True),
                ('cuerda', 'Cuerda', 'Cuerdas', 'cuerda.png', True),
                ('comida', 'Comida', 'Comida', 'comida.png', True),
                ('carbon', 'Carbon', 'Carbon', 'carbon.png', True),
                ('hierro_forjado', 'Hierro forjado', 'Hierro forjado', 'hierro_forjado.png', True)
            ]
            
            # Insertar cada recurso si no existe
            fecha_actual = datetime.now().isoformat()
            for codigo, nombre, titulo, imagen, es_producto in recursos_por_defecto:
                cursor.execute('''
                    INSERT OR IGNORE INTO recursos 
                    (codigo, nombre, titulo, imagen, es_producto, usuario_crear, fecha_crear, activo)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                ''', (codigo, nombre, titulo, imagen, es_producto, usuario_crear, fecha_actual))
            
            logger_db.info(f"Se insertaron {len(recursos_por_defecto)} recursos por defecto")
            conn.commit()
            return True
            
    except sqlite3.Error as e:
        logger_db.error(f"Error al inicializar recursos: {e}")
        return False

def inicializar_recursos_acciones(cursor=None, usuario_crear: str = 'sistema') -> bool:
    """
    Inicializa la relación entre acciones y recursos en la base de datos.
    
    Args:
        cursor: Cursor de la base de datos. Si es None, se crea una nueva conexión.
        usuario_crear: Usuario que realiza la creación (opcional, por defecto 'sistema')
        
    Returns:
        bool: True si se inicializó correctamente, False en caso contrario
    """
    # Si no se proporciona un cursor, manejar la conexión internamente
    if cursor is None:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                result = _inicializar_recursos_acciones_impl(cursor, usuario_crear)
                conn.commit()
                return result
            except Exception as e:
                conn.rollback()
                logger_db.error(f"Error al inicializar recursos_acciones: {e}")
                return False
    
    return _inicializar_recursos_acciones_impl(cursor, usuario_crear)

def _inicializar_recursos_acciones_impl(cursor, usuario_crear: str) -> bool:
    """
    Inicializa la relación entre acciones y recursos en la base de datos.
    
    Args:
        usuario_crear: Usuario que realiza la creación (opcional, por defecto 'sistema')
        
    Returns:
        bool: True si se inicializó correctamente, False en caso contrario
    """
    try:
        with sqlite3.connect('soloville.db') as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Verificar si ya hay datos en la tabla
            cursor.execute('SELECT COUNT(*) FROM recursos_acciones')
            if cursor.fetchone()[0] > 0:
                logger_db.info("La relación recursos-acciones ya está inicializada")
                return True
            
            # Obtener las acciones
            cursor.execute('SELECT id, codigo FROM acciones')
            acciones = {row['codigo']: row['id'] for row in cursor.fetchall()}
            
            # Obtener los recursos
            cursor.execute('SELECT id, codigo FROM recursos')
            recursos = {row['codigo']: row['id'] for row in cursor.fetchall()}
            
            # Definir las relaciones entre acciones y recursos
            # Formato: (codigo_accion, codigo_recurso, cantidad, cantidad_pozo, cantidad_herramienta, probabilidad, probabilidad_pozo, probabilidad_herramienta)
            relaciones = [
            # Cavar
            ('cavar', 'arcilla', 5, 1, 3, 100, 100, 100),
            ('cavar', 'piedra', 1, 0, 1, 100, 100, 100),
            ('cavar', 'hierba', 0, 2, 0, 100, 100, 100),
            ('cavar', 'energia', 1, -0.1, -0.2, 100, 100, 100),
            ('cavar', 'moneda', 2, 1, 2, 100, 100, 100),
                                                                        
            # Cazar                                                      
            ('cazar', 'carne', 1, 0, 1, 100, 100, 100),
            ('cazar', 'piel', 3, 1, 1, 100, 100, 100),
            ('cazar', 'hierba', 0, 2, 0, 100, 100, 100),
            ('cazar', 'energia', 1, -0.1, -0.2, 100, 100, 100),
            ('cazar', 'moneda', 2, 1, 2, 100, 100, 100),
                                                                        
            # Cultivar                                                   
            ('cultivar', 'trigo', 5, 0, 2, 100, 100, 100),
            ('cultivar', 'verdura', 1, 1, 1, 30, 20, 100),
            ('cultivar', 'hierba', 0, 2, 2, 100, 100, 100),
            ('cultivar', 'energia', 1, -0.1, -0.2, 100, 100, 100),
            ('cultivar', 'moneda', 2, 1, 2, 100, 100, 100),
                                                                        
            # Minar                                                      
            ('minar', 'piedra', 4, 1, 1, 100, 100, 100),
            ('minar', 'carbon', 0, 1, 1, 100, 100, 100),
            ('minar', 'hierro', 1, 1, 1, 20 , 30 , 100),
            ('minar', 'hierba', 0, 1, 0, 100, 100, 100),
            ('minar', 'energia', 1, -0.1, -0.2, 100, 100, 100),
            ('minar', 'moneda', 2, 1, 2, 100, 100, 100),
                                                                        
            # Pescar                                                     
            ('pescar', 'pescado', 2, 1, 2, 100, 100, 100),
            ('pescar', 'agua', 1, 0, 0, 100, 100, 100),
            ('pescar', 'hierba', 0, 3, 0, 100, 100, 100),
            ('pescar', 'energia', 1, -0.1, -0.2, 100, 100, 100),
            ('pescar', 'moneda', 2, 1, 2, 100, 100, 100),
                                                                        
            # Talar árboles                                              
            ('talar', 'madera', 1, 0, 0.5, 100, 100, 100),
            ('talar', 'rama', 4, 5, 2, 100, 100, 100),
            ('talar', 'hierba', 0, 3, 0, 100, 100, 100),
            ('talar', 'energia', 1, -0.1, -0.2, 100, 100, 100),
            ('talar', 'moneda', 2, 1, 2, 100, 100, 100),
                                                                        
            # Guardia                                                    
            ('guardia', 'moneda', 10, 5, 5, 100, 100, 100),
            ('guardia', 'hierba', 0, 3, 0, 100, 100, 100),
            ('guardia', 'energia', 1, -0.1, -0.2, 100, 100, 100)
            ]
            
            # Insertar las relaciones
            fecha_actual = datetime.now().isoformat()
            insertados = 0
            
            for (codigo_accion, codigo_recurso, cantidad, cant_pozo, cant_herramienta, 
                 prob, prob_pozo, prob_herramienta) in relaciones:
                
                accion_id = acciones.get(codigo_accion)
                recurso_id = recursos.get(codigo_recurso)
                
                if not accion_id or not recurso_id:
                    logger_db.warning(f"No se pudo encontrar acción o recurso: {codigo_accion}, {codigo_recurso}")
                    continue
                
                cursor.execute('''
                    INSERT INTO recursos_acciones 
                    (accion_id, recurso_id, cantidad, cantidad_pozo, cantidad_herramienta,
                     probabilidad, probabilidad_pozo, probabilidad_herramienta,
                     fecha_crear, usuario_crear, activo)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                ''', (
                    accion_id, recurso_id, cantidad, cant_pozo, cant_herramienta,
                    prob, prob_pozo, prob_herramienta,
                    fecha_actual, usuario_crear
                ))
                insertados += 1
            
            logger_db.info(f"Se insertaron {insertados} relaciones entre acciones y recursos")
            conn.commit()
            return True
            
    except sqlite3.Error as e:
        logger_db.error(f"Error al inicializar recursos_acciones: {e}")
        return False

def main():
    """
    Punto de entrada principal cuando se ejecuta el script directamente.
    Inicializa todos los datos en la base de datos.
    """
    try:
        logger_db.info(f"Iniciando inicialización de datos en {DB_PATH}")
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Verificar si las tablas existen antes de intentar inicializarlas
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name IN ('habilidades', 'herramientas', 'acciones', 'recursos')
            """)
            tablas_existentes = {row[0] for row in cursor.fetchall()}
            
            if len(tablas_existentes) < 4:
                logger_db.error("No se encontraron todas las tablas necesarias. Ejecute primero database_ddl.py")
                return False
            
            # Inicializar datos en orden de dependencias
            inicializaciones = [
                (inicializar_habilidades, "Habilidades"),
                (inicializar_herramientas, "Herramientas"),
                (inicializar_acciones, "Acciones"),
                (inicializar_recursos, "Recursos"),
                (inicializar_recursos_acciones, "Recursos por Acción")
            ]
            
            for funcion, nombre in inicializaciones:
                logger_db.info(f"Inicializando {nombre}...")
                if not funcion(cursor):
                    logger_db.error(f"Error al inicializar {nombre}")
                    conn.rollback()
                    return False
            
            conn.commit()
            logger_db.info("Datos inicializados exitosamente")
            return True
            
    except Exception as e:
        logger_db.error(f"Error inesperado al inicializar datos: {e}")
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
