from flask import Flask, render_template, redirect, url_for, request, jsonify
from datetime import datetime
import sqlite3
import os
import sys

# Asegurar que la raíz del proyecto esté en sys.path para poder importar database.py
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from database import mejorar_casa, fabricar_producto, RECETAS_FABRICACION
from db_mapa import TIPOS_CASILLAS

app = Flask(__name__)

# Configuración de la ruta de la base de datos
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'soloville.db')

def singularizar_nombre(nombre):
    """
    Convierte un nombre plural a singular y aplica reglas específicas
    """
    nombre = nombre.lower()
    # Reglas específicas
    if nombre == 'hierbas':
        return 'hierba'
    if nombre == 'pescados':
        return 'pescado'
    # Regla específica para nombres compuestos
    if nombre == 'hierro forjado':
        return 'hierro_forjado'
    # Regla general para plurales
    if nombre.endswith('s'):
        return nombre[:-1]
    return nombre

def get_ciudadano(nombre):
    """Obtiene los datos del ciudadano de la base de datos"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM ciudadanos 
            WHERE nombre = ?
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
            SELECT x, z, tipo FROM mapa
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
                'tipo': tipo_nombre
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
        return redirect(url_for('perfil'))


@app.route('/fabricar/<producto>', methods=['POST'])
def route_fabricar(producto):
    """Llama a la lógica de fabricación y vuelve al perfil."""
    nombre = 'solounturnomas'
    try:
        fabricar_producto(nombre, producto, usuario_modificar=nombre)
    except Exception:
        pass
    return redirect(url_for('perfil'))


@app.route('/')
def perfil():
    ciudadano = get_ciudadano('solounturnomas')
    if not ciudadano:
        return "Ciudadano no encontrado"
        
    # Organizar los datos para la plantilla
    # Crear diccionario de recursos con nombres singularizados
    recursos = {
        'Moneda': ciudadano.get('cantidad_moneda', 0),
        'Madera': ciudadano.get('cantidad_madera', 0),
        'Rama': ciudadano.get('cantidad_rama', 0),
        'Piedra': ciudadano.get('cantidad_piedra', 0),
        'Arcilla': ciudadano.get('cant_arcilla', 0),
        'Hierro': ciudadano.get('cantidad_hierro', 0),
        'Pescado': ciudadano.get('cantidad_pescado', 0),
        'Trigo': ciudadano.get('cantidad_trigo', 0),
        'Verdura': ciudadano.get('cantidad_verdura', 0),
        'Carne': ciudadano.get('cantidad_carne', 0),
        'Piel': ciudadano.get('cantidad_piel', 0),
        'Hierbas': ciudadano.get('cantidad_hierba', 0)
    }
    
    # Crear diccionario de nombres singularizados para las imágenes
    recursos_singulares = {}
    for nombre, cantidad in recursos.items():
        singular = singularizar_nombre(nombre)
        # Guardar tanto la versión singular como la plural
        recursos_singulares[singular] = singular
        if nombre.lower() != singular:
            recursos_singulares[nombre.lower()] = singular
    
    niveles = {
        'Leñador': ciudadano.get('nivel_leñador', 0),
        'Recolector': ciudadano.get('nivel_recolector', 0),
        'Pescador': ciudadano.get('nivel_pescador', 0),
        'Cazador': ciudadano.get('nivel_cazador', 0),
        'Agricultor': ciudadano.get('nivel_agricultor', 0),
        'Guardia': ciudadano.get('nivel_guardia', 0),
        'Minero': ciudadano.get('nivel_minero', 0)
    }
    
    herramientas = {
        'Hacha': ciudadano.get('tiene_hacha', False),
        'Pico': ciudadano.get('tiene_pico', False),
        'Espada': ciudadano.get('tiene_espada', False),
        'Hazada': ciudadano.get('tiene_hazada', False),
        'Arco': ciudadano.get('tiene_arco', False),
        'Caña de pescar': ciudadano.get('tiene_caña', False)
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
        2: 'Pionero',
        3: 'Vecino Distinguido',
        4: 'Alta Sociedad',
    }.get(ciudadano.get('rango', 0), 'Desconocido')

    # Formatos de fecha de creación y modificación
    # ----- Productos (recursos manufacturados) -----
    productos = {
        'Tablas': ciudadano.get('cant_tablas', 0),
        'Bloque': ciudadano.get('cant_bloque', 0),
        'Ladrillo': ciudadano.get('cant_ladrillo', 0),
        'Comida': ciudadano.get('cant_comida', 0),
        'Hierro forjado': ciudadano.get('cant_hierro_forjado', 0),
        'Cuerda': ciudadano.get('cant_cuerda', 0),
    }
    productos_singulares = {}
    # ---- Calcular si se puede fabricar cada producto y tooltip ----
    fabricacion_info = {}
    for prod, receta in RECETAS_FABRICACION.items():
        # determinar si tiene materiales
        tiene = all(ciudadano.get(campo,0) >= cant for campo, cant in receta['coste'].items())
        # construir partes de tooltip
        partes = []
        for campo, cant in receta['coste'].items():
            nombre_mat = campo.replace('cantidad_', '').replace('cant_', '')
            partes.append(f"{cant} {nombre_mat}")
        tooltip = f"Fabricar {receta['genera']} {prod}(s) cuesta: " + ', '.join(partes)
        fabricacion_info[prod] = {'puede': tiene, 'tooltip': tooltip}
    for nombre, cantidad in productos.items():
        singular = singularizar_nombre(nombre)
        productos_singulares[singular] = singular
        if nombre.lower() != singular:
            productos_singulares[nombre.lower()] = singular

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
                'cantidad_piel': 10,
                'cantidad_rama': 20,
                'cant_cuerda': 2,
                'cantidad_moneda': 20,
            },
            2: {
                'cantidad_madera': 20,
                'cantidad_hierro': 1,
                'cant_cuerda': 10,
                'cantidad_moneda': 200,
            },
            3: {
                'cantidad_piedra': 40,
                'cantidad_madera': 10,
                'cantidad_hierro': 4,
                'cantidad_moneda': 1000,
            },
            4: {
                'cant_ladrillo': 60,
                'cantidad_piedra': 10,
                'cantidad_madera': 10,
                'cantidad_hierro': 10,
                'cantidad_moneda': 5000,
            },
        }
        reqs = requisitos_por_nivel[siguiente_nivel]
        puede_mejorar = all(ciudadano.get(campo, 0) >= cantidad for campo, cantidad in reqs.items())
        desc_edificio_siguiente = {
                1: 'Tienda de campaña',
                2: 'Cabaña de madera',
                3: 'Casa de piedra',
                4: 'Casa de ladrillos',
        }.get(siguiente_nivel, 'Vivienda')
        partes = []
        for campo, cant in reqs.items():
            nombre = campo.replace('cantidad_', '').replace('cant_', '')
            partes.append(f"{cant} {nombre}")
        if puede_mejorar:
            tooltip_mejora = f"Construir {desc_edificio_siguiente} requiere: " + ', '.join(partes)
        else:
            tooltip_mejora = f"Para mejorar a {desc_edificio_siguiente} necesitas: " + ', '.join(partes)

    # Mostrar tooltip aunque no pueda mejorar, salvo si ya es nivel máximo
    show_mejora_info = nivel_casa_actual < 4

    desc_casa = {
        0: 'Sin hogar',
        1: 'Tienda de campaña',
        2: 'Cabaña de madera',
        3: 'Casa de piedra',
        4: 'Casa de ladrillos',
    }.get(ciudadano.get('nivel_casa', 0), 'Desconocido')
    
    return render_template('perfil.html',
                          ciudadano=ciudadano,
                          fecha_pozo_fmt=fecha_pozo_fmt,
                          desc_casa=desc_casa,
                          desc_rango=desc_rango,
                          ciudad_desde_fmt=ciudad_desde_fmt,
                          ultima_ciudad_fmt=ultima_ciudad_fmt,
                          show_mejora_info=show_mejora_info,
                          puede_mejorar=puede_mejorar,
                          tooltip_mejora=tooltip_mejora,
                          productos=productos,
                          productos_singulares=productos_singulares,
                          fabricacion_info=fabricacion_info,
                          recursos=recursos,
                          recursos_singulares=recursos_singulares,
                          niveles=niveles,
                          herramientas=herramientas)

@app.route('/mapa')
def mapa():
    ciudadano = get_ciudadano('solounturnomas')
    if not ciudadano:
        return "Ciudadano no encontrado"
        
    # Organizar los datos para la plantilla
    # Crear diccionario de recursos con nombres singularizados
    recursos = {
        'Monedas': ciudadano.get('cantidad_moneda', 0),
        'Madera': ciudadano.get('cantidad_madera', 0),
        'Ramas': ciudadano.get('cantidad_rama', 0),
        'Piedra': ciudadano.get('cantidad_piedra', 0),
        'Arcilla': ciudadano.get('cant_arcilla', 0),
        'Hierro': ciudadano.get('cantidad_hierro', 0),
        'Pescado': ciudadano.get('cantidad_pescado', 0),
        'Trigo': ciudadano.get('cantidad_trigo', 0),
        'Verdura': ciudadano.get('cantidad_verdura', 0),
        'Carne': ciudadano.get('cantidad_carne', 0),
        'Piel': ciudadano.get('cantidad_piel', 0),
        'Hierbas': ciudadano.get('cantidad_hierba', 0)
    }
    
    # Crear diccionario de nombres singularizados para las imágenes
    recursos_singulares = {}
    for nombre, cantidad in recursos.items():
        singular = singularizar_nombre(nombre)
        # Guardar tanto la versión singular como la plural
        recursos_singulares[singular] = singular
        if nombre.lower() != singular:
            recursos_singulares[nombre.lower()] = singular
    
    niveles = {
        'Leñador': ciudadano.get('nivel_leñador', 0),
        'Recolector': ciudadano.get('nivel_recolector', 0),
        'Pescador': ciudadano.get('nivel_pescador', 0),
        'Cazador': ciudadano.get('nivel_cazador', 0),
        'Agricultor': ciudadano.get('nivel_agricultor', 0),
        'Guardia': ciudadano.get('nivel_guardia', 0),
        'Minero': ciudadano.get('nivel_minero', 0)
    }
    
    herramientas = {
        'Hacha': ciudadano.get('tiene_hacha', False),
        'Pico': ciudadano.get('tiene_pico', False),
        'Espada': ciudadano.get('tiene_espada', False),
        'Hazada': ciudadano.get('tiene_hazada', False),
        'Arco': ciudadano.get('tiene_arco', False),
        'Caña de pescar': ciudadano.get('tiene_caña', False)
    }
    
    return render_template('mapa.html', 
                         ciudadano=ciudadano,
                         recursos=recursos,
                         recursos_singulares=recursos_singulares,
                         niveles=niveles,
                         herramientas=herramientas)

if __name__ == '__main__':
    #☺app.run(debug=True)
    app.run(debug=True)
