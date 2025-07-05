"""
Módulo que maneja la base de datos SQLite para el bot de Twitch.
Esta base de datos almacena información sobre los ciudadanos y sus recursos.
"""

import sqlite3
from datetime import datetime
from typing import Optional, Dict, Any
import logging
import configuracion_logging
from niveles import obtener_nivel
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

def init_db(usuario_crear: str = 'sistema'):
    """
    Inicializa la base de datos y crea las tablas necesarias si no existen.
    
    Args:
        usuario_crear: Usuario que realiza la creación de las tablas (opcional, por defecto 'sistema')
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
                    activo BOOLEAN DEFAULT TRUE
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
            # Insertar habilidades por defecto si no existen
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
            
            # Actualizar la lista de habilidades para incluir campos de auditoría
            habilidades_por_defecto_con_auditoria = [
                (*hab, fecha_actual, usuario_crear, None, None, None, None, True)
                for hab in habilidades_por_defecto
            ]
            
            cursor.executemany('''
                INSERT OR IGNORE INTO habilidades 
                (codigo, nombre, titulo, imagen, icono, fecha_crear, usuario_crear, fecha_modif, usuario_modif, fecha_borrar, usuario_borrar, activo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', habilidades_por_defecto_con_auditoria)
            
            logger_db.info("Tabla habilidades insertada")  

            # Obtener todos los códigos de habilidades
            cursor.execute("SELECT codigo FROM habilidades")
            codigos_habilidades = [row[0] for row in cursor.fetchall()]
            
            # Obtener todos los IDs de ciudadanos activos
            cursor.execute("SELECT id FROM ciudadanos WHERE borrado_logico  = 0")
            ids_ciudadanos = [row[0] for row in cursor.fetchall()]
            # Insertar registros de habilidades para cada ciudadano si no existen
            for ciudadano_id in ids_ciudadanos:
                for codigo_habilidad in codigos_habilidades:
                    # Insertar con campos de auditoría
                    cursor.execute('''
                        INSERT OR IGNORE INTO habilidades_ciudadano 
                        (ciudadano_id, habilidad_id, puntos_experiencia, nivel,
                         fecha_crear, usuario_crear, activo)
                        VALUES (?, ?, 0, 1, ?, ?, TRUE)
                    ''', (ciudadano_id, codigo_habilidad, fecha_actual, usuario_crear))
            logger_db.info("Tabla habilidades_ciudadano insertada")
            
            # Crear tabla de recursos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS recursos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    codigo TEXT UNIQUE NOT NULL,
                    nombre TEXT NOT NULL,
                    titulo TEXT,
                    imagen TEXT,
                    es_producto BOOLEAN DEFAULT FALSE,
                    -- Campos de auditoría
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
            
            # Insertar recursos por defecto si no existen
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
            for codigo, nombre, titulo, imagen, es_producto in recursos_por_defecto:
                cursor.execute('''
                    INSERT OR IGNORE INTO recursos 
                    (codigo, nombre, titulo, imagen, es_producto, usuario_crear)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (codigo, nombre, titulo, imagen, es_producto, usuario_crear))
            
            logger_db.info("Recursos por defecto insertados")
            
            # Crear tabla recursos_ciudadano
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS recursos_ciudadano (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ciudadano_id INTEGER NOT NULL,
                    recurso_id INTEGER NOT NULL,
                    cantidad INTEGER NOT NULL DEFAULT 0,
                    
                    -- Campos de auditoría
                    fecha_crear TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fecha_modif TIMESTAMP,
                    fecha_borrar TIMESTAMP,
                    usuario_crear TEXT NOT NULL,
                    usuario_modif TEXT,
                    usuario_borrar TEXT,
                    activo BOOLEAN DEFAULT TRUE,
                    version INTEGER DEFAULT 1,
                    
                    -- Restricciones
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
                    -- Campos de auditoría
                    fecha_crear TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fecha_modif TIMESTAMP,
                    fecha_borrar TIMESTAMP,
                    usuario_crear TEXT NOT NULL,
                    usuario_modif TEXT,
                    usuario_borrar TEXT,
                    activo BOOLEAN DEFAULT TRUE,
                    version INTEGER DEFAULT 1,
                    
                    -- Restricciones
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
                    
                    -- Campos de auditoría
                    fecha_crear TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fecha_modif TIMESTAMP,
                    fecha_borrar TIMESTAMP,
                    usuario_crear TEXT NOT NULL,
                    usuario_modif TEXT,
                    usuario_borrar TEXT,
                    activo BOOLEAN DEFAULT TRUE,
                    version INTEGER DEFAULT 1,
                    
                    -- Restricciones
                    FOREIGN KEY (recurso_id) REFERENCES recursos(id),
                    FOREIGN KEY (fabricacion_id) REFERENCES fabricacion_productos(id),
                    UNIQUE(recurso_id, fabricacion_id)
                )
            ''')
            logger_db.info("Tabla recursos_fabricacion creada")
            #crear vista fabricacion_lista
            cursor.execute('''
                CREATE VIEW IF NOT EXISTS fabricacion_lista AS
                select rb.id,rb.nombre as nombre_producto, fp.cantidad as cantidad_producto, rr.nombre as nombre_recurso, rf.cantidad as cantidad_recurso
                from fabricacion_productos fp, recursos_fabricacion rf, recursos rb, recursos rr 
                where fp.id = rf.fabricacion_id
                and fp.recurso_id=rb.id
                and rf.recurso_id=rr.id
            ''')
            logger_db.info("Vista fabricacion_lista creada")
            
            # Obtener todos los códigos de recursos
            cursor.execute("SELECT codigo,id FROM recursos")
            codigos_recursos = [row[1] for row in cursor.fetchall()]
            
            # Obtener todos los IDs de ciudadanos activos
            cursor.execute("SELECT id FROM ciudadanos WHERE borrado_logico  = 0")
            ids_ciudadanos = [row[0] for row in cursor.fetchall()]
            # Insertar registros de recursos para cada ciudadano si no existen
            for ciudadano_id in ids_ciudadanos:
                for codigo_recurso in codigos_recursos:
                    # Insertar con campos de auditoría
                    cursor.execute('''
                        INSERT OR IGNORE INTO recursos_ciudadano 
                        (ciudadano_id, recurso_id, usuario_crear)
                        VALUES (?, ?, ?)
                    ''', (ciudadano_id, codigo_recurso, usuario_crear))
            logger_db.info("Tabla recursos_ciudadano insertada") 


            # Verificar columnas existentes en ciudadanos
            cursor.execute("PRAGMA table_info(ciudadanos)")
            columnas = [col[1] for col in cursor.fetchall()]
            
            # Agregar columna nivel_constructor si no existe
            if 'nivel_constructor' not in columnas:
                logger_db.info("Agregando columna nivel_constructor a la tabla ciudadanos")
                cursor.execute('''
                    ALTER TABLE ciudadanos 
                    ADD COLUMN nivel_constructor INTEGER DEFAULT 0
                ''')       
            
            # Agregar columna energia si no existe
            if 'energia' not in columnas:
                logger_db.info("Agregando columna energia a la tabla ciudadanos")
                cursor.execute('''
                    ALTER TABLE ciudadanos 
                    ADD COLUMN energia INTEGER DEFAULT 20
                ''')
                logger_db.info("Columna energia agregada exitosamente")
            
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
            
            # Inicializar herramientas si no existen
            inicializar_herramientas(usuario_crear)
            
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
                    -- Restricciones
                    FOREIGN KEY (ciudadano_id) REFERENCES ciudadanos(id),
                    FOREIGN KEY (herramienta_id) REFERENCES herramientas(id),
                    UNIQUE(ciudadano_id, herramienta_id)
                )
            ''')
            logger_db.info("Tabla herramientas_ciudadano creada")
            
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
            # Insertar herramientas
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
            for codigo, nombre, titulo, imagen in herramientas:
                cursor.execute('''
                    INSERT OR IGNORE INTO herramientas 
                    (codigo, nombre, titulo, imagen, fecha_crear, usuario_crear, activo)
                    VALUES (?, ?, ?, ?, datetime('now'), ?, 1)
                ''', (codigo, nombre, titulo, imagen, usuario_crear))
            
            logger_db.info(f"{len(herramientas)} herramientas inicializadas")

            # Inicializar relaciones entre ciudadanos y herramientas
            # Obtener todos los ciudadanos activos
            cursor.execute('SELECT id FROM ciudadanos WHERE borrado_logico = 0')
            ciudadanos_cur = [row[0] for row in cursor.fetchall()]
            
            # Obtener todas las herramientas activas
            cursor.execute('SELECT id FROM herramientas WHERE activo = 1')
            herramientas_cur = [row[0] for row in cursor.fetchall()]
            
            if not ciudadanos_cur or not herramientas_cur:
                logger_db.warning("No hay ciudadanos o herramientas para crear relaciones")
                return False
            
            # Insertar una relación para cada combinación de ciudadano y herramienta
            registros_insertados = 0
            for ciudadano_id in ciudadanos_cur:
                for herramienta_id in herramientas_cur:
                    cursor.execute('''
                        INSERT OR IGNORE INTO herramientas_ciudadano 
                        (ciudadano_id, herramienta_id, tiene, fecha_crear, usuario_crear, activo)
                        VALUES (?, ?, 0, datetime('now'), ?, 1)
                    ''', (ciudadano_id, herramienta_id, usuario_crear))
                    registros_insertados += 1
            
            logger_db.info(f"Se crearon {registros_insertados} relaciones ciudadano-herramienta")
            
            conn.commit()
            logger_db.info("Tablas creadas exitosamente")
            
    except sqlite3.Error as e:
        logger_db.error(f"Error al crear tablas: {e}")
        raise

def inicializar_herramientas(usuario_crear: str = 'sistema') -> bool:
    """
    Inicializa las herramientas en la base de datos si no existen.
    
    Args:
        usuario_crear: Usuario que realiza la creación (opcional, por defecto 'sistema')
        
    Returns:
        bool: True si se inicializaron las herramientas correctamente, False en caso contrario
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Verificar si ya hay herramientas en la base de datos
            cursor.execute('SELECT COUNT(*) FROM herramientas')
            if cursor.fetchone()[0] > 0:
                logger_db.info("Las herramientas ya están inicializadas")
                return True
            
          
            return True
            
    except sqlite3.Error as e:
        logger_db.error(f"Error al inicializar herramientas: {e}")
        return False

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
            
            # Verificar si el ciudadano ya existe
            cursor.execute('SELECT id FROM ciudadanos WHERE nombre = ?', (nombre,))
            if cursor.fetchone():
                logger_db.error(f"Error al crear ciudadano {nombre}: ya existe")
                return False
                
            # Obtener la fecha actual para la creación
            fecha_crear = datetime.now().isoformat()
            
            # Asegurar que usuario_crear no sea nulo
            if not usuario_crear:
                usuario_crear = 'sistema'
            
            # Construir la consulta de inserción
            campos = ["nombre", "fecha_crear", "usuario_crear"]
            placeholders = [":nombre", ":fecha_crear", ":usuario_crear"]
            valores = {
                "nombre": nombre,
                "fecha_crear": fecha_crear,
                "usuario_crear": usuario_crear
            }
            
            # Insertar el nuevo ciudadano
            cursor.execute(f"""
                INSERT INTO ciudadanos ({', '.join(campos)}) 
                VALUES ({', '.join(placeholders)})
            """, valores)
            
            # Obtener el ID del nuevo ciudadano
            ciudadano_id = cursor.lastrowid
            
            # Insertar habilidades para el nuevo ciudadano
            cursor.execute("SELECT codigo FROM habilidades WHERE activo = 1")
            habilidades = [row[0] for row in cursor.fetchall()]
            
            fecha_actual = datetime.now().isoformat()
            for habilidad_id in habilidades:
                cursor.execute('''
                    INSERT INTO habilidades_ciudadano 
                    (ciudadano_id, habilidad_id, puntos_experiencia, nivel,
                     fecha_crear, usuario_crear, activo)
                    VALUES (?, ?, 0, 1, ?, ?, TRUE)
                ''', (ciudadano_id, habilidad_id, fecha_actual, usuario_crear))
            
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
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Verificar si el ciudadano existe
            cursor.execute('SELECT id FROM ciudadanos WHERE nombre = ?', (nombre,))
            ciudadano = cursor.fetchone()
            if not ciudadano:
                logger_db.error(f"Error al actualizar ciudadano {nombre}: ciudadano no encontrado")
                return False
                
            # Construir la consulta SQL dinámicamente
            campos_actualizar = []
            valores = []
            for campo, valor in datos.items():
                campos_actualizar.append(f"{campo} = ?")
                valores.append(valor)
            
            # Agregar campos de auditoría
            campos_actualizar.extend([
                "fecha_modif = CURRENT_TIMESTAMP",
                "usuario_modif = ?"
            ])
            valores.append(usuario_modificar if usuario_modificar else "sistema")
            # Construir la consulta final
            consulta = f"UPDATE ciudadanos SET {', '.join(campos_actualizar)} WHERE nombre = ?"
            valores.append(nombre)
            cursor.execute(consulta, tuple(valores))
            conn.commit()
            logger_db.info(f"Ciudadano actualizado: {nombre}")
            return True
            
    except sqlite3.Error as e:
        logger_db.error(f"Error al actualizar ciudadano {nombre}: {e}")
        return False

# =============================================
#  SISTEMA DE FABRICACIÓN
# =============================================
RECETAS_FABRICACION = {
    'Tabla':   {'genera': 5, 'coste': {'madera': 1, 'energia': 1}},
    'Bloque':   {'genera': 3, 'coste': {'piedra': 1, 'energia': 1}},
    'Ladrillo': {'genera': 4, 'coste': {'arcilla': 1, 'energia': 1}},
    'Cuerda':   {'genera': 2, 'coste': {'hierba': 3, 'energia': 1}},
    'Carbon':   {'genera': 3, 'coste': {'madera': 3, 'energia': 1}},
    'Comida':   {'genera': 1, 'coste': {'carne': 1, 'trigo': 2, 'verdura': 1, 'energia': 1}},
    'Hierro forjado': {'genera': 1, 'coste': {'hierro': 2, 'energia': 1}},
}

def poblar_recetas_fabricacion(usuario_crear: str = 'sistema') -> bool:
    """
    Puebla las tablas fabricacion_productos y recursos_fabricacion con las recetas
    definidas en RECETAS_FABRICACION.
    
    Para cada receta en RECETAS_FABRICACION:
    1. Inserta/actualiza en fabricacion_productos el producto resultante
    2. Inserta/actualiza en recursos_fabricacion los recursos necesarios
    
    Args:
        usuario_crear: Usuario que realiza la inserción (opcional, por defecto 'sistema')
        
    Returns:
        bool: True si se insertaron los registros correctamente, False en caso de error
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            logger_db.info("Iniciando población de recetas de fabricación")
            
            # Asegurarse de que las tablas tengan las restricciones correctas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS fabricacion_productos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recurso_id INTEGER NOT NULL UNIQUE,
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
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS recursos_fabricacion (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fabricacion_id INTEGER NOT NULL,
                    recurso_id INTEGER,
                    cantidad INTEGER NOT NULL,
                    fecha_crear TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fecha_modif TIMESTAMP,
                    fecha_borrar TIMESTAMP,
                    usuario_crear TEXT NOT NULL,
                    usuario_modif TEXT,
                    usuario_borrar TEXT,
                    activo BOOLEAN DEFAULT TRUE,
                    version INTEGER DEFAULT 1,
                    FOREIGN KEY (fabricacion_id) REFERENCES fabricacion_productos(id),
                    FOREIGN KEY (recurso_id) REFERENCES recursos(id),
                    UNIQUE(fabricacion_id, COALESCE(recurso_id, 0))
                )
            ''')
            
            # Contadores de registros insertados
            fabricaciones_insertadas = 0
            recursos_insertados = 0
            
            # Recorrer cada receta en RECETAS_FABRICACION
            for producto_nombre, datos in RECETAS_FABRICACION.items():
                # Obtener el ID del recurso producto
                cursor.execute('SELECT id FROM recursos WHERE nombre = ?', (producto_nombre,))
                recurso_row = cursor.fetchone()
                
                if not recurso_row:
                    logger_db.warning(f"No se encontró el recurso: {producto_nombre}")
                    continue
                    
                recurso_id = recurso_row[0]
                cantidad_generada = datos['genera']
                
                # Insertar/actualizar en fabricacion_productos
                cursor.execute('''
                    INSERT OR REPLACE INTO fabricacion_productos 
                    (recurso_id, cantidad, fecha_crear, fecha_modif, 
                     usuario_crear, usuario_modif, activo, version)
                    VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 
                            ?, ?, TRUE, 1)
                ''', (recurso_id, cantidad_generada, usuario_crear, usuario_crear))
                
                # Obtener el ID de la fabricación
                cursor.execute('SELECT id FROM fabricacion_productos WHERE recurso_id = ?', (recurso_id,))
                fabricacion_id = cursor.fetchone()[0]
                fabricaciones_insertadas += 1
                
                # Insertar los recursos necesarios en recursos_fabricacion
                for recurso_codigo, cantidad in datos['coste'].items():
                    # Eliminar prefijos 'cantidad_' o 'cant_' del código del recurso
                    nombre_recurso = recurso_codigo.replace('cantidad_', '').replace('cant_', '')
                   
                    
                    # Obtener el ID del recurso requerido (excepto para energía)
                    recurso_req_id = None
                    
                    cursor.execute('SELECT id FROM recursos WHERE codigo = ?', (nombre_recurso,))
                    recurso_req_row = cursor.fetchone()
                    if not recurso_req_row:
                        logger_db.warning(f"No se encontró el recurso requerido: {nombre_recurso}")
                        continue
                    recurso_req_id = recurso_req_row[0]
                    
                    # Insertar recurso requerido
                    cursor.execute('''
                        INSERT OR REPLACE INTO recursos_fabricacion 
                        (fabricacion_id, recurso_id, cantidad,
                         fecha_crear, fecha_modif, usuario_crear, usuario_modif, 
                         activo, version)
                        VALUES (?, ?, ?, 
                               CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ?, ?,
                               TRUE, 1)
                    ''', (fabricacion_id, recurso_req_id, cantidad,
                         usuario_crear, usuario_crear))
                    recursos_insertados += 1
            
            conn.commit()
            #logger_db.info(f"Se insertaron/actualizaron {fabricaciones_insertadas} fabricaciones y {recursos_insertados} recursos en las tablas")
            return True
            
    except Exception as e:
        logger_db.error(f"Error al poblar recetas de fabricación: {str(e)}", exc_info=True)
        if 'conn' in locals():
            conn.rollback()
        return False

def info_fabricacion(recurso_id: int) -> str:
    """
    Obtiene información sobre cómo fabricar un recurso específico.
    
    Args:
        recurso_id: ID del recurso a consultar
        
    Returns:
        str: Cadena con la información de fabricación o mensaje indicando que no es fabricable
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Obtener el nombre del recurso a partir de su ID
            cursor.execute('SELECT nombre FROM recursos WHERE id = ?', (recurso_id,))
            resultado = cursor.fetchone()
            
            if not resultado:
                return f"No se encontró el recurso con ID {recurso_id}"
                
            nombre_producto = resultado[0]
            
            # Verificar si el recurso es fabricable consultando el campo es_producto
            cursor.execute('SELECT es_producto FROM recursos WHERE id = ?', (recurso_id,))
            es_producto = cursor.fetchone()[0]
            
            if not es_producto:
                return f"La/El {nombre_producto} no se puede fabricar"
                
            # Obtener la información de la receta desde la base de datos
            cursor.execute('''
                SELECT fp.cantidad, r.nombre, rf.cantidad 
                FROM fabricacion_productos fp
                JOIN recursos rp ON fp.recurso_id = rp.id
                JOIN recursos_fabricacion rf ON fp.id = rf.fabricacion_id
                JOIN recursos r ON rf.recurso_id = r.id
                WHERE fp.recurso_id = ?
            ''', (recurso_id,))
            
            resultados = cursor.fetchall()
            
            if not resultados:
                return f"No se encontró receta para fabricar {nombre_producto}"
                
            # La primera fila contiene la cantidad generada
            cantidad_generada = resultados[0][0]
            
            # Construir el diccionario de coste
            coste = {}
            for _, nombre_recurso, cantidad in resultados:
                coste[nombre_recurso.lower()] = cantidad
            
            # Construir el mensaje de retorno
            mensaje = f"Fabricar {cantidad_generada} {nombre_producto}(s) cuesta: \n"
            
            # Agregar cada componente del costo
            for recurso, cantidad in coste.items():
                mensaje += f"{cantidad} x {recurso.capitalize()}\n"
                
            return mensaje.strip()
            
    except Exception as e:
        logger_db.error(f"Error en info_fabricacion: {e}")
        return f"Error al obtener información de fabricación: {e}"

def es_producto_fabricable(nombre_ciudadano: str, nombre_producto: str, ) -> bool:
    """Verifica si un producto puede ser fabricado por un ciudadano.
    
    Args:
        nombre_ciudadano: Nombre del ciudadano que intenta fabricar
        nombre_producto: Nombre del producto a verificar
        
    Returns:
        bool: True si el producto puede ser fabricado (todos los recursos necesarios están disponibles),
              False en caso contrario o si hay algún error
    """
  
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Obtener ID del ciudadano
            cursor.execute('SELECT id FROM ciudadanos WHERE nombre = ?', (nombre_ciudadano,))
            ciudadano = cursor.fetchone()
            
            if not ciudadano:
                logger_db.warning(f'Ciudadano no encontrado: {nombre_ciudadano}')
                return False
                
            ciudadano_id = ciudadano['id']
            
            # Verificar si el producto es fabricable según la consulta SQL existente
            cursor.execute('''
                SELECT 
                        CASE WHEN MIN(CASE WHEN rf.cantidad <= COALESCE(rc.cantidad, 0) THEN 1 ELSE 0 END) = 1 
                    THEN 1 ELSE 0 END as fabricable
                    FROM recursos r
                    JOIN fabricacion_productos fp ON r.id = fp.recurso_id
                    JOIN recursos_fabricacion rf ON fp.id = rf.fabricacion_id
                    JOIN recursos sr ON rf.recurso_id = sr.id
                    LEFT JOIN recursos_ciudadano rc ON sr.id = rc.recurso_id AND rc.ciudadano_id = ?
                    WHERE r.es_producto = 1
                    AND r.nombre = ?
                    GROUP BY r.id
            ''', (ciudadano_id, nombre_producto))
            
            resultado = cursor.fetchone()
            
            # Si no hay resultados, el producto no existe o no es fabricable
            if not resultado:
                logger_db.warning(f'Producto no encontrado o no fabricable: {nombre_producto}')
                return False
                
            return bool(resultado['fabricable'])
        
    except Exception as e:
        logger_db.error(f"Error al verificar si el producto es fabricable: {e}")
        return False

def fabricar_producto(nombre_ciudadano: str, nombre_producto: str, usuario_modificar: str = 'sistema') -> bool:
    """Fábrica un producto para un ciudadano, restando los recursos necesarios y sumando el producto.
    
    Args:
        nombre_ciudadano: Nombre del ciudadano que fabrica el producto
        nombre_producto: Nombre del producto a fabricar
        usuario_modificar: Usuario que realiza la modificación (opcional)
        
    Returns:
        bool: True si la fabricación fue exitosa, False en caso contrario
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Iniciar transacción
        cursor.execute('BEGIN TRANSACTION')
            
        # 1. Obtener ID del ciudadano
        cursor.execute('SELECT id FROM ciudadanos WHERE nombre = ?', (nombre_ciudadano,))
        ciudadano = cursor.fetchone()
        
        if not ciudadano:
            logger_db.warning(f'Ciudadano no encontrado: {nombre_ciudadano}')
            conn.rollback()
            conn.close()
            return False
            
        ciudadano_id = ciudadano['id']
        
        # 2. Verificar si el producto es fabricable
        cursor.execute('''
            SELECT 
                CASE WHEN MIN(CASE WHEN rf.cantidad <= COALESCE(rc.cantidad, 0) THEN 1 ELSE 0 END) = 1 
                THEN 1 ELSE 0 END as fabricable
            FROM recursos r
            JOIN fabricacion_productos fp ON r.id = fp.recurso_id
            JOIN recursos_fabricacion rf ON fp.id = rf.fabricacion_id
            JOIN recursos sr ON rf.recurso_id = sr.id
            LEFT JOIN recursos_ciudadano rc ON sr.id = rc.recurso_id AND rc.ciudadano_id = ?
            WHERE r.es_producto = 1
            AND r.nombre = ?
            GROUP BY r.id
        ''', (ciudadano_id, nombre_producto))
        
        resultado = cursor.fetchone()
        es_producto_fabricable = bool(resultado and resultado['fabricable'])

        if not es_producto_fabricable:
            logger_db.warning(f'No se puede fabricar {nombre_producto} para {nombre_ciudadano}: recursos insuficientes o producto no encontrado')
            conn.rollback()
            conn.close()
            return False
        
        # 3. Obtener información del producto a fabricar
        cursor.execute('''
            SELECT r.id as producto_id, r.nombre, r.codigo, fp.cantidad as cantidad_producida
            FROM recursos r
            JOIN fabricacion_productos fp ON r.id = fp.recurso_id
            WHERE r.nombre = ? AND r.es_producto = 1
        ''', (nombre_producto,))
        
        producto_info = cursor.fetchone()
        
        if not producto_info:
            logger_db.warning(f'Producto no encontrado o no es fabricable: {nombre_producto}')
            conn.rollback()
            conn.close()
            return False
        
        # 4. Obtener los materiales requeridos para la fabricación
        cursor.execute('''
            SELECT r.id as recurso_id, r.nombre, r.codigo, rf.cantidad as cantidad_requerida
            FROM recursos r
            JOIN recursos_fabricacion rf ON r.id = rf.recurso_id
            JOIN fabricacion_productos fp ON rf.fabricacion_id = fp.id
            WHERE fp.recurso_id = ?
        ''', (producto_info['producto_id'],))
        
        materiales = cursor.fetchall()
        
        if not materiales:
            logger_db.warning(f'No se encontraron materiales para fabricar {nombre_producto}')
            conn.rollback()
            conn.close()
            return False
        
        # 5. Restar los recursos necesarios
        for material in materiales:
            cursor.execute('''
                UPDATE recursos_ciudadano
                SET cantidad = cantidad - ?,
                    fecha_modif = CURRENT_TIMESTAMP,
                    usuario_modif = ?
                WHERE recurso_id = ? AND ciudadano_id = ?
            ''', (material['cantidad_requerida'], usuario_modificar, material['recurso_id'], ciudadano_id))
            
            # Verificar si la actualización fue exitosa
            if cursor.rowcount == 0:
                logger_db.warning(f'No se pudo actualizar el recurso {material["nombre"]} para {nombre_ciudadano}')
                conn.rollback()
                conn.close()
                return False
        
        # 6. Sumar el producto fabricado al inventario del ciudadano
        cursor.execute('''
            INSERT INTO recursos_ciudadano (ciudadano_id, recurso_id, cantidad, fecha_crear, usuario_crear)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?)
            ON CONFLICT(ciudadano_id, recurso_id) 
            DO UPDATE SET 
                cantidad = cantidad + excluded.cantidad,
                fecha_modif = CURRENT_TIMESTAMP,
                usuario_modif = excluded.usuario_crear
        ''', (ciudadano_id, producto_info['producto_id'], producto_info['cantidad_producida'], usuario_modificar))
        
        # 7. Registrar la acción
        cursor.execute('''
            INSERT INTO historial_acciones (ciudadano_id, codigo_accion, mensaje_final, fecha_hora)
            VALUES (?, 'FABRICAR', ?, CURRENT_TIMESTAMP)
        ''', (ciudadano_id, f'{nombre_ciudadano} fabricó {producto_info["cantidad_producida"]} {producto_info["nombre"]}(s)'))
        
        # Confirmar la transacción
        conn.commit()
        logger_db.info(f'{nombre_ciudadano} fabricó exitosamente {producto_info["cantidad_producida"]} {nombre_producto}')
        return True
            
    except Exception as e:
        logger_db.error(f'Error al fabricar {nombre_producto} para {nombre_ciudadano}: {str(e)}')
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def obtener_receta_fabricacion(nombre_producto: str) -> Optional[Dict[str, Any]]:
    """Obtiene la información de fabricación de un producto desde la base de datos.
    
    Args:
        nombre_producto: Nombre del producto a fabricar
        
    Returns:
        Un diccionario con la información de la receta o None si no se encuentra
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Buscar el producto en la tabla de recursos
            cursor.execute('''
                SELECT r.id, r.codigo, r.nombre, fp.cantidad as cantidad_generada
                FROM recursos r
                JOIN fabricacion_productos fp ON r.id = fp.recurso_id
                WHERE r.nombre = ? AND r.es_producto = 1
            ''', (nombre_producto,))
            producto_info = cursor.fetchone()
            
            if not producto_info:
                logger_db.warning(f'Producto no encontrado o no fabricable: {nombre_producto}')
                return None
                
            # Obtener los recursos necesarios para la fabricación
            cursor.execute('''
                SELECT r.id, r.codigo, r.nombre, rf.cantidad
                FROM recursos_fabricacion rf
                JOIN recursos r ON rf.recurso_id = r.id
                WHERE rf.fabricacion_id = (
                    SELECT id FROM fabricacion_productos WHERE recurso_id = ?
                )
            ''', (producto_info['id'],))
            recursos_necesarios = cursor.fetchall()
            
            # Construir el diccionario de coste
            coste = {}
            for recurso in recursos_necesarios:
                coste[recurso['codigo']] = recurso['cantidad']
            
            return {
                'producto_id': producto_info['id'],
                'producto_codigo': producto_info['codigo'],
                'producto_nombre': producto_info['nombre'],
                'cantidad_generada': producto_info['cantidad_generada'],
                'coste': coste
            }
            
    except Exception as e:
        logger_db.error(f'Error al obtener receta de fabricación: {str(e)}', exc_info=True)
        return None

# ---- FUNCIONES DE NEGOCIO EXISTENTES ----

def mejorar_casa(nombre: str, usuario_modificar: str = None) -> bool:
    """
    Mejora la vivienda de un ciudadano si dispone de los recursos necesarios.

    Niveles y requisitos:
        1: 10 piel, 20 rama, 2 cuerda, 20 moneda
        2: 20 madera, 1 hierro, 10 cuerda, 200 moneda
        3: 40 piedra, 10 madera, 4 hierro, 1000 moneda
        4: 60 ladrillo, 10 piedra, 10 madera, 10 hierro, 5000 moneda
    """
    requisitos_por_nivel = {
        1: {
            'piel': 10,
            'rama': 20,
            'cuerda': 2,
            'moneda': 20,
            'energia': 5,
        },
        2: {
            'madera': 20,
            'hierro': 1,
            'cuerda': 10,
            'moneda': 200,
            'energia': 10,
        },
        3: {
            'piedra': 40,
            'madera': 10,
            'hierro': 4,
            'moneda': 1000,
            'energia': 15,
        },
        4: {
            'ladrillo': 60,
            'piedra': 10,
            'madera': 10,
            'hierro': 10,
            'moneda': 5000,
            'energia': 20,
            },
    }

    ciudadano = get_ciudadano(nombre)
    if not ciudadano:
        logger_db.error(f"Ciudadano no encontrado: {nombre}")
        return False

    nivel_actual = ciudadano.get('nivel_casa', 0)
    if nivel_actual >= 4:
        logger_db.info(f"{nombre} ya tiene la casa al nivel máximo")
        return False

    siguiente_nivel = nivel_actual + 1
    requisitos = requisitos_por_nivel[siguiente_nivel]

    # Verificar recursos suficientes
    for campo, requerido in requisitos.items():
        if ciudadano.get(campo, 0) < requerido:
            logger_db.info(f"{nombre} no tiene suficientes {campo} para mejorar la casa")
            return False

    # Construir datos de actualización: restar recursos y aumentar nivel_casa
    datos_update = {'nivel_casa': siguiente_nivel}
    for campo, requerido in requisitos.items():
        datos_update[campo] = ciudadano[campo] - requerido

    if actualizar_ciudadano(nombre, datos_update, usuario_modificar):
        registrar_accion('MEJORAR_CASA', f"Casa mejorada a nivel {siguiente_nivel}", ciudadano_id=ciudadano['id'])
        logger_db.info(f"{nombre} ha mejorado su casa a nivel {siguiente_nivel}")
        return True
    else:
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
            
            # Verificar si el ciudadano existe
            cursor.execute('SELECT id FROM ciudadanos WHERE nombre = ?', (nombre,))
            ciudadano = cursor.fetchone()
            if not ciudadano:
                logger_db.error(f"Error al desactivar ciudadano {nombre}: ciudadano no encontrado")
                return False
                
            # Asegurar que usuario_borrar no sea nulo
            if not usuario_borrar:
                usuario_borrar = 'sistema'
                
            # Obtener la fecha actual
            fecha_actual = datetime.now().isoformat()
            
            # Actualizar el registro con soft delete
            cursor.execute('''
                UPDATE ciudadanos 
                SET activo = 0,
                    fecha_borrar = ?,
                    usuario_borrar = ?,
                    fecha_modif = ?,
                    usuario_modif = ?
                WHERE nombre = ?
            ''', (fecha_actual, usuario_borrar, fecha_actual, usuario_borrar, nombre))
            
            conn.commit()
            logger_db.info(f"Ciudadano desactivado: {nombre}")
            return True
            
    except sqlite3.Error as e:
        logger_db.error(f"Error al desactivar ciudadano {nombre}: {e}")
        return False

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
        logger_db.error(f"Detalles: codigo_accion={codigo_accion}, ciudadano_id={ciudadano_id}")
        logger_db.error(f"Mensaje: {mensaje_final}")
        return False

def mostrar_historial_acciones(fecha_inicio: str = None, fecha_fin: str = None, 
                             codigo_accion: str = None, ciudadano_id: int = None):
    """
    Muestra en formato amigable el historial de acciones.
    """
    acciones = listar_historial_acciones(fecha_inicio, fecha_fin, codigo_accion, ciudadano_id)
    if not acciones:
        print("No hay acciones registradas")
        return
    
    print("\n=== HISTORIAL DE ACCIONES ===")
    print("-" * 50)
    for accion in acciones:
        print(f"\nID: {accion['id']}")
        print(f"Código acción: {accion['codigo_accion']}")
        print(f"Mensaje final: {accion['mensaje_final']}")
        print(f"Fecha y hora: {accion['fecha_hora']}")
        print(f"Ciudadano ID: {accion['ciudadano_id']}")
        print("-" * 50)

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
            limite = 10
            if ciudadano_id:
                cursor.execute('''
                    SELECT * FROM historial_acciones 
                    WHERE ciudadano_id = ? 
                    ORDER BY fecha_hora DESC 
                    LIMIT ?
                ''', (ciudadano_id, limite))
            else:
                cursor.execute('''
                    SELECT * FROM historial_acciones 
                    ORDER BY fecha_hora DESC 
                    LIMIT ?
                ''', (limite,))
            
            acciones = [dict(row) for row in cursor.fetchall()]
            logger_db.info("Se encontraron %d acciones en el historial", len(acciones))
            return acciones
            
    except sqlite3.Error as e:
        logger_db.error("Error al listar historial de acciones: %s", str(e))
        return []
    except Exception as e:
        # Capturar cualquier otro error, incluyendo problemas de logging
        print(f"Error en listar_historial_acciones: {str(e)}")
        return []

def actualizar_experiencia_ciudadano(ciudadano_nombre: str, habilidad_id: str, puntos_experiencia: int, 
                                  usuario_modificar: str = None) -> tuple[bool, str]:
    """
    Actualiza los puntos de experiencia de un ciudadano en una habilidad específica
    y actualiza automáticamente su nivel.
    
    Args:
        ciudadano_nombre: Nombre del ciudadano
        habilidad_id: ID de la habilidad a actualizar
        puntos_experiencia: Nueva cantidad de puntos de experiencia (no incremental)
        usuario_modificar: Usuario que realiza la modificación (opcional)
        
    Returns:
        Tupla (éxito, mensaje) donde:
        - éxito: Booleano que indica si la operación fue exitosa
        - mensaje: Mensaje descriptivo del resultado
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Obtener ID del ciudadano
            cursor.execute('SELECT id FROM ciudadanos WHERE nombre = ?', (ciudadano_nombre,))
            ciudadano = cursor.fetchone()
            
            if not ciudadano:
                return False, f"No se encontró al ciudadano {ciudadano_nombre}"
                
            ciudadano_id = ciudadano['id']
            fecha_actual = datetime.now().isoformat()
            
            # Calcular el nivel basado en los puntos de experiencia
            from niveles import obtener_nivel
            nivel = obtener_nivel(puntos_experiencia)
            
            # Actualizar o insertar el registro de habilidad
            cursor.execute('''
                INSERT INTO habilidades_ciudadano 
                (ciudadano_id, habilidad_id, puntos_experiencia, nivel,
                 fecha_crear, usuario_crear, fecha_modif, usuario_modif, activo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, TRUE)
                ON CONFLICT(ciudadano_id, habilidad_id) 
                DO UPDATE SET 
                    puntos_experiencia = excluded.puntos_experiencia,
                    nivel = ?,
                    fecha_modif = excluded.fecha_modif,
                    usuario_modif = excluded.usuario_modif
            ''', (
                ciudadano_id, habilidad_id, puntos_experiencia, nivel,
                fecha_actual, usuario_modificar or 'sistema',
                fecha_actual, usuario_modificar or 'sistema',
                nivel  # Para el UPDATE en ON CONFLICT
            ))
            
            # Registrar la acción
            registrar_accion(
                codigo_accion="actualizar_experiencia",
                mensaje_final=f"Experiencia actualizada a {puntos_experiencia} (nivel {nivel})",
                ciudadano_id=ciudadano_id,
                usuario_crear=usuario_modificar
            )
            
            conn.commit()
            return True, f"Experiencia de {ciudadano_nombre} en {habilidad_id} actualizada a {puntos_experiencia} (nivel {nivel})"
            
    except sqlite3.Error as e:
        logger_db.error(f"Error al actualizar experiencia de {ciudadano_nombre}: {e}")
        return False, f"Error al actualizar la experiencia: {e}"

def añadir_experiencia_ciudadano(ciudadano_nombre: str, habilidad_id: str, cantidad: int, 
                              usuario_modificar: str = None) -> tuple[bool, str]:
    """
    Añade puntos de experiencia a un ciudadano en una habilidad específica
    y actualiza automáticamente su nivel.
    
    Args:
        ciudadano_nombre: Nombre del ciudadano
        habilidad_id: ID de la habilidad a actualizar
        cantidad: Cantidad de puntos de experiencia a añadir (puede ser negativo)
        usuario_modificar: Usuario que realiza la modificación (opcional)
        
    Returns:
        Tupla (éxito, mensaje) donde:
        - éxito: Booleano que indica si la operación fue exitosa
        - mensaje: Mensaje descriptivo del resultado
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Obtener experiencia actual
            cursor.execute('''
                SELECT c.id, COALESCE(hc.puntos_experiencia, 0)
                FROM ciudadanos c
                LEFT JOIN habilidades_ciudadano hc ON c.id = hc.ciudadano_id 
                    AND hc.habilidad_id = ?
                WHERE c.nombre = ?
            ''', (habilidad_id, ciudadano_nombre))
            
            resultado = cursor.fetchone()
            if not resultado:
                return False, f"No se encontró al ciudadano {ciudadano_nombre}"
                
            ciudadano_id, experiencia_actual = resultado
            nueva_experiencia = max(0, experiencia_actual + cantidad)
            
            # Usar la función actualizar_experiencia_ciudadano para guardar los cambios
            return actualizar_experiencia_ciudadano(
                ciudadano_nombre=ciudadano_nombre,
                habilidad_id=habilidad_id,
                puntos_experiencia=nueva_experiencia,
                usuario_modificar=usuario_modificar
            )
            
    except sqlite3.Error as e:
        logger_db.error(f"Error al añadir experiencia a {ciudadano_nombre}: {e}")
        return False, f"Error al añadir experiencia: {e}"

def añadir_energia(nombre: str, cantidad: int, usuario_modificar: str = None) -> tuple[bool, str]:
    """
    Añade energía a un ciudadano existente.
    
    Args:
        nombre: Nombre del ciudadano al que se le añadirá energía.
        cantidad: Cantidad de energía a añadir (puede ser negativa para restar).
        usuario_modificar: Usuario que realiza la acción (opcional).
        
    Returns:
        Tupla (éxito, mensaje) donde:
        - éxito: Booleano que indica si la operación fue exitosa.
        - mensaje: Mensaje descriptivo del resultado.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Obtener la energía actual y el ID del ciudadano
            cursor.execute('SELECT id, energia FROM ciudadanos WHERE nombre = ?', (nombre,))
            resultado = cursor.fetchone()
            
            if not resultado:
                return False, f"Error: No se encontró al ciudadano {nombre}"
                
            ciudadano_id = resultado['id']
            energia_actual = resultado['energia']
            nueva_energia = max(0, energia_actual + cantidad)  # No permitir energía negativa
            
            # Actualizar la energía usando la función existente
            exito = actualizar_ciudadano(
                nombre=nombre,
                datos={'energia': nueva_energia},
                usuario_modificar=usuario_modificar
            )
            accion = 'sumar_energia' if cantidad > 0 else 'restar_energia'
            mensaje_historial = f"{nombre} ha {'aumentado' if cantidad > 0 else 'reducido'} la energía en {abs(cantidad)} puntos. Energía actual: {nueva_energia}"
            if exito:
                registrar_accion(
                    codigo_accion=accion,
                    mensaje_final=mensaje_historial,
                    ciudadano_id=ciudadano_id
                )
                logger_db.info(mensaje_historial)
                return True, mensaje_historial
            else:
                mensaje = f"Error al actualizar la energía de {nombre}"
                logger_db.error(mensaje)
                return False, mensaje
                
    except sqlite3.Error as e:
        mensaje = f"Error en añadir_energia para {nombre}: {e}"
        logger_db.error(mensaje)
        return False, mensaje

def obtener_cantidad_recurso(ciudadano_id: int, codigo_recurso: str) -> int:
    """
    Obtiene la cantidad de un recurso específico que posee un ciudadano.
    
    Args:
        ciudadano_id: ID del ciudadano
        codigo_recurso: Código del recurso a consultar
        
    Returns:
        int: Cantidad del recurso que posee el ciudadano, 0 si no tiene nada
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Primero obtener el ID del recurso
            cursor.execute('SELECT id FROM recursos WHERE codigo = ?', (codigo_recurso,))
            recurso = cursor.fetchone()
            
            if not recurso:
                return 0
                
            recurso_id = recurso['id']
            
            # Obtener la cantidad del recurso para el ciudadano
            cursor.execute('''
                SELECT cantidad 
                FROM recursos_ciudadano 
                WHERE ciudadano_id = ? AND recurso_id = ?
            ''', (ciudadano_id, recurso_id))
            
            resultado = cursor.fetchone()
            
            # Si no hay registro, devolver 0
            if not resultado:
                return 0
                
            return resultado['cantidad']
            
    except sqlite3.Error as e:
        logger_db.error(f"Error al obtener cantidad de recurso: {e}")
        return 0

def sumar_recurso_ciudadano(ciudadano_id: int, codigo_recurso: str, cantidad: int, usuario_modificar: str = None) -> bool:
    """
    Suma una cantidad específica de un recurso a un ciudadano.
    
    Args:
        ciudadano_id: ID del ciudadano
        codigo_recurso: Código del recurso a actualizar
        cantidad: Cantidad a sumar (puede ser negativa para restar)
        usuario_modificar: Usuario que realiza la modificación (opcional)
        
    Returns:
        bool: True si la operación fue exitosa, False en caso contrario
    """
    logger_db.info(f'sumar_recurso_ciudadano - Iniciando: ciudadano_id={ciudadano_id}, recurso={codigo_recurso}, cantidad={cantidad}')
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Obtener el ID del recurso
            cursor.execute('SELECT id, nombre FROM recursos WHERE codigo = ?', (codigo_recurso,))
            recurso = cursor.fetchone()
            
            if not recurso:
                error_msg = f'Recurso no encontrado: {codigo_recurso}'
                logger_db.error(error_msg)
                return False
                
            recurso_id = recurso['id']
            logger_db.info(f'Recuperado recurso: ID={recurso_id}, Nombre={recurso["nombre"]}')
            
            # Obtener la cantidad actual del recurso
            cursor.execute('''
                SELECT cantidad, id 
                FROM recursos_ciudadano 
                WHERE ciudadano_id = ? AND recurso_id = ?
            ''', (ciudadano_id, recurso_id))
            
            recurso_actual = cursor.fetchone()
            
            if recurso_actual:
                cantidad_actual = recurso_actual['cantidad']
                nueva_cantidad = cantidad_actual + cantidad
                logger_db.info(f'Recurso existente - ID: {recurso_actual["id"]}, Actual: {cantidad_actual}, Nueva cantidad: {nueva_cantidad}')
                
                # Si la cantidad resultante es 0 o negativa, lo deja en 0
                if nueva_cantidad <= 0:
                    logger_db.info(f'Estableciendo cantidad a 0 para recurso {codigo_recurso}')
                    cursor.execute('''
                        UPDATE recursos_ciudadano 
                        SET cantidad = 0, 
                            fecha_modif = CURRENT_TIMESTAMP,
                            usuario_modif = ?
                        WHERE id = ?
                    ''', (usuario_modificar or 'sistema', recurso_actual['id']))
                else:
                    # Actualizar cantidad existente
                    logger_db.info(f'Actualizando cantidad a {nueva_cantidad} para recurso {codigo_recurso}')
                    cursor.execute('''
                        UPDATE recursos_ciudadano 
                        SET cantidad = ?, 
                            fecha_modif = CURRENT_TIMESTAMP,
                            usuario_modif = ?
                        WHERE id = ?
                    ''', (nueva_cantidad, usuario_modificar or 'sistema', recurso_actual['id']))
            else:
                # Solo crear nuevo registro si la cantidad es positiva
                if cantidad > 0:
                    logger_db.info(f'Creando nuevo registro para recurso {codigo_recurso} con cantidad {cantidad}')
                    cursor.execute('''
                        INSERT INTO recursos_ciudadano 
                        (ciudadano_id, recurso_id, cantidad, usuario_crear, usuario_modif)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (ciudadano_id, recurso_id, cantidad, 
                          usuario_modificar or 'sistema', usuario_modificar or 'sistema'))
                else:
                    # No crear registros con cantidad 0 o negativa
                    logger_db.info(f'No se crea registro para cantidad no positiva: {cantidad}')
                    return True
            
            # Verificar si se realizó la actualización
            if recurso_actual and cursor.rowcount == 0:
                # Verificar manualmente si la actualización fue exitosa
                cursor.execute('''
                    SELECT cantidad FROM recursos_ciudadano 
                    WHERE id = ?
                ''', (recurso_actual['id'],))
                
                resultado = cursor.fetchone()
                if not resultado or resultado['cantidad'] == recurso_actual['cantidad']:
                    logger_db.warning(f'No se actualizó ningún registro para el recurso {codigo_recurso}')
                    conn.rollback()
                    return False
            
            # Confirmar la transacción
            try:
                conn.commit()
                logger_db.info(f'Recurso {codigo_recurso} actualizado exitosamente')
                return True
            except sqlite3.Error as e:
                logger_db.error(f'Error al confirmar la transacción: {str(e)}')
                conn.rollback()
                return False
            
    except sqlite3.Error as e:
        error_msg = f'Error al sumar recurso a ciudadano: {str(e)}'
        logger_db.error(error_msg, exc_info=True)
        if 'conn' in locals():
            conn.rollback()
        return False

# Inicializar la base de datos al importar el módulo
init_db()

# Poblar las recetas de fabricación
poblar_recetas_fabricacion()
