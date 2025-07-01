from flask import Flask, render_template
import sqlite3
import os

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
        return None

@app.route('/')
def perfil():
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
    
    return render_template('perfil.html', 
                         ciudadano=ciudadano,
                         recursos=recursos,
                         recursos_singulares=recursos_singulares,
                         niveles=niveles,
                         herramientas=herramientas)

@app.route('/cuadricula')
def cuadricula():
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
    
    return render_template('cuadricula.html', 
                         ciudadano=ciudadano,
                         recursos=recursos,
                         recursos_singulares=recursos_singulares,
                         niveles=niveles,
                         herramientas=herramientas)

if __name__ == '__main__':
    #☺app.run(debug=True)
    app.run(debug=True)
