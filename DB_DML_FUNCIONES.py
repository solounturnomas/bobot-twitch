"""
Módulo que contiene funciones de manipulación de datos (DML) para la base de datos.
Incluye operaciones como inserción, actualización, eliminación y consulta de datos.
"""
import sqlite3
import logging
import random
from typing import Dict, Any, Optional, List, Tuple, Union
from datetime import datetime

# Configuración del logger
logger_db = logging.getLogger('database')

# Configuración de la base de datos
DB_PATH = 'soloville.db'

def get_db_connection():
    """Crea una conexión a la base de datos con soporte para filas tipo diccionario."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def obtener_receta_fabricacion(nombre_producto: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene la información de fabricación de un producto desde la base de datos.
    
    Args:
        nombre_producto: Nombre del producto del que se quiere obtener la receta
        
    Returns:
        Dict con la información de la receta o None si no se encuentra
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

def realizar_accion(nombre_ciudadano: str, codigo_accion: str, usuario_modificar: str = 'sistema') -> Dict[str, Any]:
    """
    Realiza una acción para un ciudadano, consumiendo energía y generando recursos.
    
    Args:
        nombre_ciudadano: Nombre del ciudadano que realiza la acción
        codigo_accion: Código de la acción a realizar
        usuario_modificar: Usuario que realiza la modificación (opcional)
        
    Returns:
        Dict con el resultado de la operación y detalles de los recursos obtenidos
    """
    try:
        with get_db_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Iniciar transacción
            cursor.execute('BEGIN TRANSACTION')
            
            # 1. Obtener ID del ciudadano y verificar energía
            cursor.execute('''
                SELECT c.id, cr.cantidad as energia ,c.fecha_pozo, hc.tiene, a.id as accion_id
                FROM ciudadanos c
                join recursos_ciudadano cr on c.id = cr.ciudadano_id
                join recursos r on cr.recurso_id = r.id
                join acciones a on a.codigo = ?
                join herramientas_ciudadano hc on c.id = hc.ciudadano_id 
                AND a.herramienta_id = hc.herramienta_id
                WHERE c.nombre = ? 
                AND c.borrado_logico = 0
                AND r.codigo = 'energia'
                
            ''', (codigo_accion, nombre_ciudadano))
            
            ciudadano = cursor.fetchone()
            if not ciudadano:
                return {'exito': False, 'mensaje': 'Ciudadano ' + nombre_ciudadano + ' no encontrado o inactivo'}
                
            if ciudadano['energia'] < 1:
                return {'exito': False, 'mensaje': 'No tienes suficiente energía para realizar esta acción'}
            
            ciudadano_id = ciudadano['id']
            fecha_pozo = ciudadano['fecha_pozo']    
            tiene_herramienta = ciudadano['tiene']
            accion_id = ciudadano['accion_id']
            # Determinar el exito de la accion
            suerte = random.random() 
            if suerte < 0.3:
                resultado_suerte = 'exito'
                mensaje_suerte = '¡Qué bien!'
            elif suerte < 0.7:
                resultado_suerte = 'normal'
                mensaje_suerte = '¡No está mal!'
            else:
                resultado_suerte = 'fracaso'
                mensaje_suerte = '¡Podría ser mejor!'

            # 3. Obtener los recursos asociados a la acción
            cursor.execute('''
                SELECT r.codigo, ra.cantidad, ra.cantidad_pozo, ra.cantidad_herramienta,
                       ra.probabilidad, ra.probabilidad_pozo, ra.probabilidad_herramienta
                FROM recursos_acciones ra
                JOIN recursos r ON ra.recurso_id = r.id
                WHERE ra.accion_id = ? AND ra.activo = 1
            ''', (accion_id,))
            
            recursos_accion = cursor.fetchall()
            if not recursos_accion:
                return {'exito': False, 'mensaje': 'No hay recursos asociados a esta acción'}
                        
            # 5. Calcular recursos obtenidos
            recursos_obtenidos = {}
            mensaje = []
            
            for recurso in recursos_accion:
                codigo = recurso['codigo']
                cantidad = 0
                
                # Calcular cantidad base
                if random.random() * 100 <= recurso['probabilidad']:
                    cantidad += recurso['cantidad']
                
                # Aplicar bono de pozo si corresponde (solo si es de hace menos de 24h)
                if fecha_pozo:
                    from datetime import datetime, timedelta
                    fecha_pozo_dt = datetime.strptime(fecha_pozo, '%Y-%m-%d %H:%M:%S')
                    ahora = datetime.now()
                    diferencia = ahora - fecha_pozo_dt
                    
                    if diferencia < timedelta(hours=24) and random.random() * 100 <= recurso['probabilidad_pozo']:
                        cantidad += recurso['cantidad_pozo']
                
                # Aplicar bono de herramienta si corresponde (implementar lógica de herramienta si es necesario)
                if tiene_herramienta == 1 and random.random() * 100 <= recurso['probabilidad_herramienta']:
                    cantidad += recurso['cantidad_herramienta']
                #aplicar modificador suerte si el recurso no es energia
                if resultado_suerte == 'exito' and codigo != 'energia':
                    cantidad = cantidad * 1.3
                elif resultado_suerte == 'fracaso' and codigo != 'energia':
                    cantidad = cantidad * 0.7


                if cantidad > 0:
                    # Redondear a 2 decimales
                    cantidad_redondeada = round(cantidad, 2)
                    # Convertir a entero si no tiene decimales
                    if cantidad_redondeada == int(cantidad_redondeada):
                        cantidad_redondeada = int(cantidad_redondeada)
                    
                    recursos_obtenidos[codigo] = recursos_obtenidos.get(codigo, 0) + cantidad_redondeada
                    mensaje.append(f"{cantidad_redondeada} {codigo}")
            
            # 6. Actualizar recursos del ciudadano
            for codigo, cantidad in recursos_obtenidos.items():
                cursor.execute('''
                    UPDATE recursos_ciudadano 
                    SET cantidad = cantidad + ?,
                        fecha_modif = CURRENT_TIMESTAMP,
                        usuario_modif = ?
                    WHERE ciudadano_id = ? 
                    AND recurso_id = (SELECT id FROM recursos WHERE codigo = ?)
                ''', (cantidad, usuario_modificar, ciudadano_id, codigo))
                
                if cursor.rowcount == 0:
                    # Si no existe el recurso, crearlo
                    cursor.execute('''
                        INSERT INTO recursos_ciudadano 
                        (ciudadano_id, recurso_id, cantidad, fecha_crear, usuario_crear)
                        SELECT ?, r.id, ?, CURRENT_TIMESTAMP, ?
                        FROM recursos r
                        WHERE r.codigo = ?
                    ''', (ciudadano_id, cantidad, usuario_modificar, codigo))
            
            # 8. Registrar la acción en el historial
            mensaje_final = f"{nombre_ciudadano} realizó {codigo_accion} y obtuvo: {', '.join(mensaje) if mensaje else 'nada'}"
            mensaje_final += f"\n{mensaje_suerte}"
            cursor.execute('''
                INSERT INTO historial_acciones 
                (ciudadano_id, codigo_accion, mensaje_final, fecha_hora)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (ciudadano_id, codigo_accion, mensaje_final))
            
            # Confirmar transacción
            conn.commit()
            
            return {
                'exito': True,
                'mensaje': mensaje_final,
                'recursos_obtenidos': recursos_obtenidos,
                'energia_restante': ciudadano['energia'] - 1
            }
            
    except Exception as e:
        logger_db.error(f"Error al realizar acción {codigo_accion} para {nombre_ciudadano}: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
        return {
            'exito': False,
            'mensaje': f'Error al realizar la acción: {str(e)}'
        }

# Si se ejecuta este archivo directamente, poblar las recetas de fabricación
if __name__ == "__main__":
    import sys
    import os
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger_db.info("Proceso completado")
