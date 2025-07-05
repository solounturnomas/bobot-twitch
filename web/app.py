from flask import Flask, render_template, redirect, url_for, request, jsonify, flash
from datetime import datetime
import sqlite3
import os
import sys
import logging

# Configuración del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Asegurar que la raíz del proyecto esté en sys.path para poder importar database.py
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from database import mejorar_casa, listar_historial_acciones, get_db_connection, info_fabricacion, es_producto_fabricable, fabricar_producto
from funciones.realiza_accion import realiza_accion 
from db_mapa import TIPOS_CASILLAS

app = Flask(__name__)

# Configuración de la clave secreta para las sesiones
app.secret_key = 'tu_clave_secreta_aqui_12345!'

# Configuración de la ruta de la base de datos
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'soloville.db')

def get_ciudadano(nombre):
    """Obtiene los datos del ciudadano de la base de datos"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.nombre as nombre,
            c.id as id, 
            c.nivel_casa as nivel_casa,
            ROUND(rc.cantidad, 2) as energia,
            c.fecha_pozo as fecha_pozo,
            c.rango as rango,
            c.fecha_crear as fecha_crear,
            c.fecha_modif as fecha_modif,
            c.usuario_crear as usuario_crear
            FROM ciudadanos c
            join recursos_ciudadano rc on c.id = rc.ciudadano_id 
            join recursos r on rc.recurso_id = r.id 
            WHERE c.nombre = ? and r.nombre ='Energia'
        ''', (nombre,))
        ciudadano = cursor.fetchone()
        
        if ciudadano:
            # Convertir los nombres de las columnas a minúsculas
            columnas = [col[0].lower() for col in cursor.description]
            return dict(zip(columnas, ciudadano))



@app.route('/api/mapa')
def api_mapa():
    """Endpoint para obtener los datos de la cuadrícula"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT m.x, m.z, m.tipo, m.ciudadano_id, c.nivel_casa, c.nombre FROM mapa m
            LEFT JOIN ciudadanos c ON m.ciudadano_id = c.id
        ''')
        casillas = cursor.fetchall()
        
        # Convertir los resultados a un formato JSON con los nombres de los tipos
        resultado = []
        for casilla in casillas:
            # Convertir el ID del tipo a su nombre
            tipo_nombre = next(key for key, value in TIPOS_CASILLAS.items() if value == casilla[2])
            resultado.append({
                'x': casilla[0],
                'z': casilla[1],
                'tipo': tipo_nombre,
                'ciudadano_id': casilla[3],
                'nivel_casa': casilla[4],
                'nombre': casilla[5]
            })
        
        return jsonify(resultado)

@app.route('/mejorar_casa', methods=['POST'])
def route_mejorar_casa():
    nombre = 'solounturnomas'
    # Llamar a la función de negocio; ignoramos resultado porque se mostrará en la vista
    try:
        mejorar_casa(nombre, usuario_modificar=nombre)
    except Exception:
        pass  # Se podría loggear
        return redirect(url_for('ciudadano'))


@app.route('/realiza_accion', methods=['POST'])
def route_realiza_accion():
    """Endpoint para realizar acciones sin mensaje desde la interfaz web."""
    try:
        data = request.get_json()
        accion = data.get('accion')
        ciudadano_id = data.get('ciudadano_id')
        
        # Obtener el nombre del ciudadano por su ID
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT nombre FROM ciudadanos WHERE id = ?', (ciudadano_id,))
            result = cursor.fetchone()
            
            if not result:
                return jsonify({
                    'success': False,
                    'mensaje': 'Ciudadano no encontrado'
                }), 404
                
            nombre_ciudadano = result[0]
            
        # Ejecutar la acción
        resultado = realiza_accion(accion, nombre_ciudadano)
        
        return jsonify({
            'success': True,
            'mensaje': str(resultado)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'mensaje': f'Error al realizar la acción: {str(e)}'
        }), 500
    return redirect(url_for('ciudadano'))


@app.route('/ciudadano')
@app.route('/')  # Mantener ruta raíz para compatibilidad
def ciudadano():
    ciudadano = get_ciudadano('solounturnomas')
    if not ciudadano:
        return "Ciudadano no encontrado"
        
    # Obtener recursos no producibles de la base de datos
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT r.codigo, r.nombre, r.titulo, r.imagen, rc.cantidad
            FROM recursos r, recursos_ciudadano rc  
            WHERE r.activo = 1 AND (r.es_producto = 0 OR r.es_producto IS NULL)
            AND r.id = rc.recurso_id
            AND rc.ciudadano_id = ?
        ''', (ciudadano['id'],))
        recursos_rows = cursor.fetchall()
        
        # Convertir a una lista de diccionarios con la información completa de cada recurso
        recursos = []
        for row in recursos_rows:
            recurso = {
                'nombre': row['nombre'],
                'imagen': row['imagen'],
                'titulo': row['titulo'] or row['nombre'],  # Usar título si existe, si no, usar nombre
                'cantidad': row['cantidad']
            }
            recursos.append(recurso)
 
    # Obtener herramientas del ciudadano desde la base de datos
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT h.nombre, h.imagen , hc.tiene 
            FROM herramientas_ciudadano hc
            JOIN herramientas h ON hc.herramienta_id = h.id
            WHERE hc.ciudadano_id = ? AND hc.activo = 1 AND h.activo = 1
        ''', (ciudadano['id'],))
        
        # Crear diccionario de herramientas
        herramientas = {}
        for herramienta in cursor.fetchall():
            nombre = herramienta['nombre']
            imagen = herramienta['imagen']
            tiene = bool(herramienta['tiene'])
            # Crear una entrada para cada herramienta con su información
            herramientas[nombre] = {
                'nombre': nombre,
                'tiene': tiene,
                'imagen': imagen
            }
    
    # Formatear fecha del pozo a dd/mm/yy HH:MM
    fecha_pozo_raw = ciudadano.get('fecha_pozo')
    try:
        fecha_dt = datetime.strptime(fecha_pozo_raw, '%Y-%m-%d %H:%M:%S') if isinstance(fecha_pozo_raw, str) else datetime.fromisoformat(str(fecha_pozo_raw))
        fecha_pozo_fmt = fecha_dt.strftime('%d/%m/%y %H:%M')
    except Exception:
        fecha_pozo_fmt = str(fecha_pozo_raw)
    # Descripción textual de rango
    desc_rango = {
        0: 'Forastero',
        1: 'Colono',
        2: 'Ciudadano',
        3: 'Consejero',
        4: 'Alta Sociedad',
    }.get(ciudadano.get('rango', 0), 'Desconocido')

    # ----- Productos fabricables (obtenidos de la base de datos) -----
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Obtener todos los recursos fabricables
            cursor.execute('''
                SELECT r.id, r.nombre, r.codigo, r.titulo, r.imagen, 
                       fp.cantidad as cantidad_generada,
                       rc.cantidad as cantidad_actual
                FROM recursos r
                JOIN fabricacion_productos fp ON r.id = fp.recurso_id
                LEFT JOIN recursos_ciudadano rc ON r.id = rc.recurso_id AND rc.ciudadano_id = ?
                WHERE r.activo = 1 AND r.es_producto = 1
            ''', (ciudadano['id'],))
            
            productos_db = cursor.fetchall()
            
            # Debug: Ver qué datos estamos obteniendo
            logger.info(f"Productos obtenidos de la base de datos: {productos_db}")
            
            # Inicializar diccionario de productos
            productos = {}
            
            for producto in productos_db:
                nombre = producto['nombre']
                cantidad = producto['cantidad_actual'] or 0
                # Obtener información de fabricación
                info = info_fabricacion(producto['id'])
                puede_fabricar = True
                # Inicializar el diccionario del producto con la información básica
                producto_info = {
                    'cantidad': cantidad,
                    'imagen': producto['imagen'],
                    'titulo': producto['titulo'],
                    'puede': True,  # Por defecto asumimos que se puede fabricar
                    'tooltip': info
                }
                
                # Determinar si se puede fabricar (tiene los recursos necesarios)
                if 'no se puede fabricar' not in info:
                    # Obtener recursos necesarios para la fabricación
                    cursor.execute('''
                        SELECT r.nombre, rf.cantidad
                        FROM recursos_fabricacion rf
                        JOIN recursos r ON rf.recurso_id = r.id
                        WHERE rf.fabricacion_id = (
                            SELECT id FROM fabricacion_productos WHERE recurso_id = ?
                        )
                    ''', (producto['id'],))
                    
                    recursos_necesarios = cursor.fetchall()
                    
                    # Verificar si tiene los recursos necesarios
                    for recurso in recursos_necesarios:
                        # Buscar si el ciudadano tiene el recurso necesario
                        cursor.execute('''
                            SELECT cantidad 
                            FROM recursos_ciudadano 
                            WHERE ciudadano_id = ? AND recurso_id = (
                                SELECT id FROM recursos WHERE nombre = ?
                            )
                        ''', (ciudadano['id'], recurso['nombre']))
                        
                        recurso_ciudadano = cursor.fetchone()
                        cantidad_tiene = recurso_ciudadano['cantidad'] if recurso_ciudadano else 0
                        
                        if cantidad_tiene < recurso['cantidad']:
                            producto_info['puede'] = False
                            break
                
                # Actualizar el tooltip con información de fabricación
                if 'no se puede fabricar' in info:
                    producto_info['tooltip'] = f"{nombre} no se puede fabricar"
                
                # Agregar el producto al diccionario
                productos[nombre] = producto_info
    
    except Exception as e:
        logger.error(f"Error al obtener productos fabricables: {e}")
        # En caso de error, inicializar diccionarios vacíos
        productos = {}

    fecha_crear_raw = ciudadano.get('fecha_crear')
    fecha_modif_raw = ciudadano.get('fecha_modif')
    try:
        fecha_crear_dt = datetime.strptime(fecha_crear_raw, '%Y-%m-%d %H:%M:%S') if isinstance(fecha_crear_raw, str) else datetime.fromisoformat(str(fecha_crear_raw))
        ciudad_desde_fmt = fecha_crear_dt.strftime('%m/%y')
    except Exception:
        ciudad_desde_fmt = str(fecha_crear_raw)
    try:
        fecha_modif_dt = datetime.strptime(fecha_modif_raw, '%Y-%m-%d %H:%M:%S') if isinstance(fecha_modif_raw, str) else datetime.fromisoformat(str(fecha_modif_raw))
        ultima_ciudad_fmt = fecha_modif_dt.strftime('%d/%m/%y')
    except Exception:
        ultima_ciudad_fmt = str(fecha_modif_raw)

    # Determinar si puede mejorar casa
    nivel_casa_actual = ciudadano.get('nivel_casa', 0)
    puede_mejorar = False
    tooltip_mejora = ''
    if nivel_casa_actual < 4:
        siguiente_nivel = ciudadano.get('nivel_casa', 0) + 1
        requisitos_por_nivel = {
            1: {
                'piel': 10,
                'rama': 20,
                'cuerda': 2,
                'moneda': 20,
            },
            2: {
                'madera': 20,
                'hierro': 1,
                'cuerda': 10,
                'moneda': 200,
            },
            3: {
                'piedra': 40,
                'madera': 10,
                'hierro': 4,
                'moneda': 1000,
            },
            4: {
                'ladrillo': 60,
                'piedra': 10,
                'madera': 10,
                'hierro': 10,
                'moneda': 5000,
            },
        }
        reqs = requisitos_por_nivel[siguiente_nivel]
        #puede_mejorar = all(ciudadano.get(campo, 0) >= cantidad for campo, cantidad in reqs.items())
        puede_mejorar = all(ciudadano.get(campo, 0) >= cantidad for campo, cantidad in reqs.items())
        desc_edificio_siguiente = {
                1: 'Tienda de campaña',
                2: 'Cabaña de madera',
                3: 'Casa de piedra',
                4: 'Casa de ladrillos',
        }.get(siguiente_nivel, 'Vivienda')
        partes = []
        for campo, cant in reqs.items():
            partes.append(f"{cant} {campo}")
        if puede_mejorar:
            tooltip_mejora = f"Construir {desc_edificio_siguiente} requiere: " + ', '.join(partes)
        else:
            tooltip_mejora = f"Para mejorar a {desc_edificio_siguiente} necesitas: " + ', '.join(partes)

    # Mostrar tooltip aunque no pueda mejorar, salvo si ya es nivel máximo
    show_mejora_info = nivel_casa_actual < 4
    
    # Obtener la última acción del ciudadano
    ultima_accion = None
    try:
        acciones = listar_historial_acciones(ciudadano_id=ciudadano.get('id'))
        if acciones:
            ultima_accion = acciones[0]  # La más reciente es la primera
            # Formatear la fecha
            try:
                fecha_dt = datetime.strptime(ultima_accion['fecha_hora'], '%Y-%m-%d %H:%M:%S')
                ultima_accion['fecha_formateada'] = fecha_dt.strftime('%d/%m - %H:%M')
            except Exception as e:
                ultima_accion['fecha_formateada'] = ultima_accion['fecha_hora']
    except Exception as e:
        print(f"Error al obtener última acción: {e}")

    desc_casa = {
        0: 'Sin hogar',
        1: 'Tienda de campaña',
        2: 'Cabaña de madera',
        3: 'Casa de piedra',
        4: 'Casa de ladrillos',
    }.get(ciudadano.get('nivel_casa', 0), 'Desconocido')
    
    # Obtener las habilidades del ciudadano
    habilidades_ciudadano = []
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT h.codigo, h.nombre, h.icono, hc.nivel 
                FROM habilidades_ciudadano hc
                JOIN habilidades h ON hc.habilidad_id = h.codigo
                WHERE hc.ciudadano_id = ? AND hc.activo = 1
            ''', (ciudadano['id'],))
            
            for row in cursor.fetchall():
                habilidades_ciudadano.append({
                    'codigo': row[0],
                    'nombre': row[1],
                    'icono': row[2],
                    'nivel': row[3]
                })
    except Exception as e:
        logger.error(f"Error al obtener habilidades del ciudadano: {e}")
    
    return render_template('ciudadano.html',
                         ciudadano=ciudadano,
                         fecha_pozo=fecha_pozo_fmt,
                         desc_rango=desc_rango,
                         ciudad_desde_fmt=ciudad_desde_fmt,
                         ultima_ciudad_fmt=ultima_ciudad_fmt,
                         show_mejora_info=show_mejora_info,
                         puede_mejorar=puede_mejorar,
                         tooltip_mejora=tooltip_mejora,
                         productos=productos,
                         recursos=recursos,
                         ultima_accion=ultima_accion,
                         habilidades_ciudadano=habilidades_ciudadano,
                         herramientas=herramientas,
                         es_producto_fabricable=es_producto_fabricable)

@app.route('/fabricar', methods=['POST'])
def fabricar():
    """Endpoint para fabricar un producto."""
    try:
        data = request.get_json()
        producto = data.get('producto')
        
        if not producto:
            return jsonify({'success': False, 'message': 'Producto no especificado'}), 400
            
        # Intentar fabricar el producto
        if fabricar_producto('solounturnomas', producto, 'usuario_web'):
            return jsonify({
                'success': True,
                'message': f'Se fabricó exitosamente {producto}'
            })
        else:
            return jsonify({
                'success': False,
                'message': f'No se pudo fabricar {producto}. Verifica que tengas los recursos necesarios.'
            }), 400
            
    except Exception as e:
        logger.error(f'Error al fabricar producto: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Error al procesar la solicitud: {str(e)}'
        }), 500

@app.route('/mapa')
def mapa():
    return render_template('mapa.html')

if __name__ == '__main__':
    #☺app.run(debug=True)
    app.run(debug=True)
