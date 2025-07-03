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
                    energia INTEGER DEFAULT 20,
                    cantidad_moneda INTEGER DEFAULT 0,
                    cantidad_madera INTEGER DEFAULT 0,
                    cantidad_rama INTEGER DEFAULT 0,
                    cantidad_piedra INTEGER DEFAULT 0,
                    cant_arcilla INTEGER DEFAULT 0,
                    cantidad_hierro INTEGER DEFAULT 0,
                    cantidad_pescado INTEGER DEFAULT 0,
                    cantidad_trigo INTEGER DEFAULT 0,
                    cantidad_verdura INTEGER DEFAULT 0,
                    cantidad_carne INTEGER DEFAULT 0,
                    cantidad_piel INTEGER DEFAULT 0,
                    cantidad_hierba INTEGER DEFAULT 0,
                    cant_tablas INTEGER DEFAULT 0,
                    cant_bloque INTEGER DEFAULT 0,
                    cant_ladrillo INTEGER DEFAULT 0,
                    cant_comida INTEGER DEFAULT 0,
                    cant_hierro_forjado INTEGER DEFAULT 0,
                    cant_cuerda INTEGER DEFAULT 0,
                    nivel_leñador INTEGER DEFAULT 0,
                    nivel_recolector INTEGER DEFAULT 0,
                    nivel_pescador INTEGER DEFAULT 0,
                    nivel_cazador INTEGER DEFAULT 0,
                    nivel_agricultor INTEGER DEFAULT 0,
                    nivel_guardia INTEGER DEFAULT 0,
                    nivel_minero INTEGER DEFAULT 0,
                    nivel_casa INTEGER DEFAULT 0,
                    tiene_hacha BOOLEAN DEFAULT FALSE,
                    tiene_pico BOOLEAN DEFAULT FALSE,
                    tiene_espada BOOLEAN DEFAULT FALSE,
                    tiene_hazada BOOLEAN DEFAULT FALSE,
                    tiene_arco BOOLEAN DEFAULT FALSE,
                    tiene_caña BOOLEAN DEFAULT FALSE,
                    tiene_pala BOOLEAN DEFAULT FALSE,
                    fecha_pozo TEXT,
                    fecha_crear TEXT,
                    fecha_modif TEXT,
                    fecha_borrar TEXT,
                    usuario_crear TEXT,
                    usuario_modif TEXT,
                    usuario_borrar TEXT,
                    activo BOOLEAN DEFAULT TRUE
                )
            ''')
            logger_db.info("Tabla ciudadanos creada")
            
            # Verificar columnas existentes
            cursor.execute("PRAGMA table_info(ciudadanos)")
            columnas = [col[1] for col in cursor.fetchall()]
            
            # Agregar columna nivel_constructor si no existe
            if 'nivel_constructor' not in columnas:
                logger_db.info("Agregando columna nivel_constructor a la tabla ciudadanos")
                cursor.execute('''
                    ALTER TABLE ciudadanos 
                    ADD COLUMN nivel_constructor INTEGER DEFAULT 0
                ''')
            
            # Agregar columna tiene_pala si no existe
            if 'tiene_pala' not in columnas:
                logger_db.info("Agregando columna tiene_pala a la tabla ciudadanos")
                cursor.execute('''
                    ALTER TABLE ciudadanos 
                    ADD COLUMN tiene_pala BOOLEAN DEFAULT FALSE
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
            
            conn.commit()
            logger_db.info("Tablas creadas exitosamente")
            
    except sqlite3.Error as e:
        logger_db.error(f"Error al crear tablas: {e}")
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
            
            # Verificar si el ciudadano ya existe
            cursor.execute('SELECT id FROM ciudadanos WHERE nombre = ?', (nombre,))
            if cursor.fetchone():
                logger_db.error(f"Error al crear ciudadano {nombre}: ya existe")
                return False
                
            # Insertar el nuevo ciudadano con sus recursos iniciales
            cursor.execute('''
                INSERT INTO ciudadanos (
                    nombre,
                    fecha_crear,
                    usuario_crear,
                    fecha_modif,
                    usuario_modif
                ) VALUES (?, CURRENT_TIMESTAMP, ?, CURRENT_TIMESTAMP, ?)
            ''', (nombre, usuario_crear if usuario_crear else "sistema", usuario_crear if usuario_crear else "sistema"))
            
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
#  NUEVO: SISTEMA DE FABRICACIÓN
# =============================================
RECETAS_FABRICACION = {
    'Tablas':   {'genera': 5, 'coste': {'cantidad_madera': 1, 'energia': 1}},
    'Bloque':   {'genera': 3, 'coste': {'cantidad_piedra': 1, 'energia': 1}},
    'Ladrillo': {'genera': 4, 'coste': {'cant_arcilla': 1, 'energia': 1}},
    'Cuerda':   {'genera': 2, 'coste': {'cantidad_hierba': 3, 'energia': 1}},
    'Comida':   {'genera': 1, 'coste': {'cantidad_carne': 1, 'cantidad_trigo': 2, 'cantidad_verdura': 1, 'energia': 1}},
    'Hierro forjado': {'genera': 1, 'coste': {'cantidad_hierro': 2, 'energia': 1}},
}

def fabricar_producto(nombre: str, producto: str, usuario_modificar: str = None) -> bool:
    """Intenta fabricar un producto para el ciudadano.
    Retorna True si se fabricó, False si faltan recursos o error."""
    producto = producto.capitalize()
    if producto not in RECETAS_FABRICACION:
        return False
    receta = RECETAS_FABRICACION[producto]

    ciudadano = get_ciudadano(nombre)
    if not ciudadano:
        return False

    # Verificar recursos suficientes
    for campo, cant_necesaria in receta['coste'].items():
        if ciudadano.get(campo, 0) < cant_necesaria:
            return False

    # Preparar update
    datos_update = {}
    # Descontar recursos
    for campo, cant_necesaria in receta['coste'].items():
        datos_update[campo] = ciudadano[campo] - cant_necesaria
    # Sumar producto manufacturado
    campo_producto = {
        'Tabla': 'cant_tabla',
        'Bloque': 'cant_bloque',
        'Ladrillo': 'cant_ladrillo',
        'Cuerda': 'cant_cuerda',
        'Comida': 'cant_comida',
        'Hierro forjado': 'cant_hierro_forjado',
    }[producto]
    datos_update[campo_producto] = ciudadano.get(campo_producto, 0) + receta['genera']

    if actualizar_ciudadano(nombre, datos_update, usuario_modificar):
        registrar_accion('FABRICAR', f"Fabricó {receta['genera']} {producto}(s)", ciudadano_id=ciudadano['id'])
        return True
    return False

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
            'cantidad_piel': 10,
            'cantidad_rama': 20,
            'cant_cuerda': 2,
            'cantidad_moneda': 20,
            'energia': 5,
        },
        2: {
            'cantidad_madera': 20,
            'cantidad_hierro': 1,
            'cant_cuerda': 10,
            'cantidad_moneda': 200,
            'energia': 10,
        },
        3: {
            'cantidad_piedra': 40,
            'cantidad_madera': 10,
            'cantidad_hierro': 4,
            'cantidad_moneda': 1000,
            'energia': 15,
        },
        4: {
            'cant_ladrillo': 60,
            'cantidad_piedra': 10,
            'cantidad_madera': 10,
            'cantidad_hierro': 10,
            'cantidad_moneda': 5000,
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
                
            # Actualizar el registro con soft delete
            cursor.execute('''
                UPDATE ciudadanos 
                SET borrado_logico = 1,
                    fecha_borrar = CURRENT_TIMESTAMP,
                    usuario_borrar = ?,
                    fecha_modif = CURRENT_TIMESTAMP,
                    usuario_modif = ?
                WHERE nombre = ?
            ''', (usuario_borrar if usuario_borrar else "sistema",
                  usuario_borrar if usuario_borrar else "sistema",
                  nombre))
            
            conn.commit()
            logger_db.info(f"Ciudadano desactivado: {nombre}")
            return True
            
    except sqlite3.Error as e:
        logger_db.error(f"Error al desactivar ciudadano {nombre}: {e}")
        return False

def listar_ciudadanos():
    """
    Lista todos los ciudadanos activos en la base de datos.
    
    Returns:
        Lista de diccionarios con la información de los ciudadanos activos.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM ciudadanos 
                WHERE borrado_logico = 0
                ORDER BY nombre
            ''')
            ciudadanos = cursor.fetchall()
            logger_db.info(f"Listado de ciudadanos: {len(ciudadanos)} encontrados")
            return [dict(c) for c in ciudadanos]
            
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
        print(f"  Moneda: {ciudadano['cantidad_moneda']}")
        print(f"  Madera: {ciudadano['cantidad_madera']}")
        print(f"  Ramas: {ciudadano['cantidad_rama']}")
        print(f"  Piedra: {ciudadano['cantidad_piedra']}")
        print(f"  Hierro: {ciudadano['cantidad_hierro']}")
        print(f"  Pescado: {ciudadano['cantidad_pescado']}")
        print(f"  Trigo: {ciudadano['cantidad_trigo']}")
        print(f"  Verdura: {ciudadano['cantidad_verdura']}")
        print(f"  Carne: {ciudadano['cantidad_carne']}")
        print(f"  Piel: {ciudadano['cantidad_piel']}")
        print(f"  Hierbas: {ciudadano['cantidad_hierba']}")
        print(f"  Tablas: {ciudadano['cant_tabla']}")
        print(f"  Bloques: {ciudadano['cant_bloque']}")
        print(f"  Arcilla: {ciudadano['cant_arcilla']}")
        print(f"  Ladrillo: {ciudadano['cant_ladrillo']}")
        print(f"  Comida: {ciudadano['cant_comida']}")
        print(f"  Cuerda: {ciudadano['cant_cuerda']}")
        
        print("\nNiveles:")
        print(f"  Rango: {ciudadano['rango']}")
        print(f"  Leñador: {ciudadano['nivel_leñador']}")
        print(f"  Recolector: {ciudadano['nivel_recolector']}")
        print(f"  Pescador: {ciudadano['nivel_pescador']}")
        print(f"  Cazador: {ciudadano['nivel_cazador']}")
        print(f"  Agricultor: {ciudadano['nivel_agricultor']}")
        print(f"  Guardia: {ciudadano['nivel_guardia']}")
        print(f"  Minero: {ciudadano['nivel_minero']}")
        print(f"  Nivel casa: {ciudadano['nivel_casa']}")
        print(f"  Nivel constructor: {ciudadano['nivel_constructor']}")
        
        # Mostrar solo las herramientas que tiene
        print("\nHerramientas que posee:")
        herramientas = {
            'hacha': ciudadano['tiene_hacha'],
            'pico': ciudadano['tiene_pico'],
            'espada': ciudadano['tiene_espada'],
            'hazada': ciudadano['tiene_hazada'],
            'arco': ciudadano['tiene_arco'],
            'caña de pescar': ciudadano['tiene_caña'],
            'pala': ciudadano['tiene_pala']
        }
        
        herramientas_tiene = [herramienta for herramienta, tiene in herramientas.items() if tiene]
        if herramientas_tiene:
            print("- " + "\n- ".join(herramientas_tiene))
        else:
            print("- No tiene ninguna herramienta")
        
        print("\nAuditoría:")
        print(f"  Fecha del pozo: {ciudadano['fecha_pozo']}")
        print(f"  Fecha creación: {ciudadano['fecha_crear']}")
        print(f"  Fecha última modificación: {ciudadano['fecha_modif']}")
        print(f"  Creado por: {ciudadano['usuario_crear']}")
        print(f"  Modificado por: {ciudadano['usuario_modif']}")
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
