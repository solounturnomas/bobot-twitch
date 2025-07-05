import sys
import os
import logging
import datetime
import random
import sqlite3
import os
from typing import Optional, Dict, Any
import configuracion_logging
from dotenv import load_dotenv

# Obtener la ruta a la base de datos
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'soloville.db')

# Agregar el directorio raíz al path de Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database
from database import sumar_recurso_ciudadano

# Definir mensajes por defecto
MENSAJES_POR_DEFECTO = {
    'talar': '¡{autor} se ha ido a talar al bosque!',
    'trabajar en el campo': '¡{autor} ha comenzado a trabajar en el campo!',
    'trabajar de guardia': '¡{autor} ha empezado su turno de guardia!',
    'picar piedra': '¡{autor} ha empezado a picar piedra!',
    'cazar en el bosque': '¡{autor} ha entrado al bosque para cazar!',
    'pescar': '¡{autor} ha empezado a pescar!',
    'cavar arcilla': '¡{autor} ha empezado a cavar arcilla!',   
}
# Definir mensajes según el resultado
MENSAJES_RESULTADO = {
    'exito': '¡Qué bien!',
    'normal': 'No está mal!',
    'fracaso': 'Podría ser mejor.'
}

def realiza_accion(accion: str, nombre_ciudadano: str) -> str:
    """
    Realiza una acción específica, actualiza recursos y devuelve el mensaje final con los detalles.
    
    Args:
        accion: Código de la acción a realizar
        nombre_ciudadano: Nombre del ciudadano que realiza la acción
        
    Returns:
        Mensaje final con el resultado de la acción y recursos obtenidos
    """
    try:
        # Obtener el ciudadano
        ciudadano = database.get_ciudadano(nombre_ciudadano)
        if not ciudadano:
            return f"@{nombre_ciudadano} No estás registrado en Soloville. ¡Usa !registro para unirte!"
        
        # Convertir la acción a minúsculas para comparar con el diccionario RECOMPENSAS
        accion = accion.lower()
        
        # Determinar el resultado de la acción (exito, normal, fracaso)
        resultado = random.choices(
            ['exito', 'normal', 'fracaso'],
            weights=[25, 50, 25],
            k=1
        )[0]

        # Verificar si ha visitado el pozo en las últimas 24h
        tiempo_pozo = datetime.datetime.now() - datetime.datetime.fromisoformat(ciudadano['fecha_pozo'])
        uso_pozo = tiempo_pozo.total_seconds() <= 24 * 3600

        # Inicializar recursos obtenidos
        recursos_obtenidos = {
            'moneda': 0,
            'madera': 0,
            'rama': 0,
            'trigo': 0,
            'hierro': 0,
            'carne': 0,
            'piel': 0,
            'pescado': 0,
            'verdura': 0,
            'hierba': 0,
            'piedra': 0,
            'arcilla': 0,
            'energia': 0,
            'agua': 0
        }

        # Actualizar fecha de última modificación
        datos_actualizar = {
            'fecha_modif': datetime.datetime.now(),
            'usuario_modif': 'bot'
        }

        # Obtener herramientas del ciudadano en una sola consulta
        with sqlite3.connect(DB_PATH) as conn:
            # Desactivar mensajes de depuración
            conn.set_trace_callback(None)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Obtener todas las herramientas del ciudadano en una sola consulta
            cursor.execute('''
                SELECT h.codigo
                FROM herramientas_ciudadano hc
                JOIN herramientas h ON hc.herramienta_id = h.id
                WHERE hc.ciudadano_id = ? 
                  AND hc.tiene = 1 
                  AND hc.activo = 1 
                  AND h.activo = 1
            ''', (ciudadano['id'],))
            
            # Convertir resultados a un conjunto de códigos de herramientas
            herramientas_activas = {row['codigo'] for row in cursor.fetchall()}
            
            # Verificar qué herramientas tiene el ciudadano
            tiene_hacha = 'hacha' in herramientas_activas
            tiene_pico = 'pico' in herramientas_activas
            tiene_pala = 'pala' in herramientas_activas
            tiene_arco = 'arco' in herramientas_activas
            tiene_cana = 'caña' in herramientas_activas
            tiene_espada = 'espada' in herramientas_activas
            tiene_hazada = 'hazada' in herramientas_activas

        # Calcular recursos según la acción
        if accion == 'talar':
            recursos_obtenidos['madera'] += 1
            recursos_obtenidos['rama'] += 5
            recursos_obtenidos['energia'] -= 1
            if tiene_hacha:
                recursos_obtenidos['madera'] += 1
                recursos_obtenidos['energia'] += 0.2
            if uso_pozo:
                recursos_obtenidos['rama'] += 2
                recursos_obtenidos['hierba'] += 2
                recursos_obtenidos['energia'] += 0.1

        elif accion == 'trabajar en el campo':
            recursos_obtenidos['trigo'] += 5 
            recursos_obtenidos['energia'] -= 1
            if random.random() <= 0.2:
                recursos_obtenidos['verdura'] += 1
            if tiene_hazada:
                recursos_obtenidos['trigo'] += 2
                recursos_obtenidos['verdura'] += 1
                recursos_obtenidos['hierba'] += 2
                recursos_obtenidos['energia'] += 0.2
            if uso_pozo:
                recursos_obtenidos['hierba'] += 2
                recursos_obtenidos['energia'] += 0.1
                if random.random() <= 0.3:
                    recursos_obtenidos['verdura'] += 1

        elif accion == 'trabajar de guardia':
            recursos_obtenidos['moneda'] += 10
            recursos_obtenidos['energia'] -= 1
            if tiene_espada:
                recursos_obtenidos['moneda'] += 5
                recursos_obtenidos['energia'] += 0.2
            if uso_pozo:
                recursos_obtenidos['moneda'] += 5
                recursos_obtenidos['hierba'] += 2
                recursos_obtenidos['energia'] += 0.1

        elif accion == 'picar piedra':
            recursos_obtenidos['piedra'] += 5
            recursos_obtenidos['energia'] -= 1
            if tiene_pico:
                recursos_obtenidos['piedra'] += 1 
                recursos_obtenidos['energia'] += 0.2 
            if random.random() <= 0.2:
                recursos_obtenidos['hierro'] += 1
            if uso_pozo:
                if random.random() <= 0.2:
                    recursos_obtenidos['hierro'] += 1
                recursos_obtenidos['hierba'] += 2
                recursos_obtenidos['energia'] += 0.1

        elif accion == 'cazar en el bosque':
            recursos_obtenidos['carne'] += 1
            recursos_obtenidos['piel'] += 3
            recursos_obtenidos['energia'] -= 1
            if tiene_arco:
                recursos_obtenidos['carne'] += 1
                recursos_obtenidos['piel'] += 1
                recursos_obtenidos['energia'] += 0.2
            if uso_pozo:
                recursos_obtenidos['piel'] += 1
                recursos_obtenidos['hierba'] += 2
                recursos_obtenidos['energia'] += 0.1

        elif accion == 'pescar':
            recursos_obtenidos['pescado'] += 5
            recursos_obtenidos['agua'] += 3
            recursos_obtenidos['energia'] -= 1
            if tiene_cana:
                recursos_obtenidos['pescado'] += 5
                recursos_obtenidos['agua'] += 1
                recursos_obtenidos['energia'] += 0.2
            if uso_pozo:
                recursos_obtenidos['pescado'] += 1
                recursos_obtenidos['hierba'] += 2
                recursos_obtenidos['agua'] += 1
                recursos_obtenidos['energia'] += 0.1
        elif accion == 'cavar arcilla':
            recursos_obtenidos['arcilla'] += 5
            recursos_obtenidos['energia'] -= 1
            if tiene_pala:
                recursos_obtenidos['arcilla'] += 5
                recursos_obtenidos['energia'] += 0.2    
            if uso_pozo:
                recursos_obtenidos['arcilla'] += 1
                recursos_obtenidos['hierba'] += 2
                recursos_obtenidos['energia'] += 0.1

        # Ajustar recursos según el resultado de la acción
        for recurso, cantidad in recursos_obtenidos.items():
            if cantidad > 0:
                if resultado == 'exito':
                    cantidad = cantidad * 1.3  # +30%
                elif resultado == 'fracaso':
                    cantidad = max(1, cantidad * 0.7)  # -30% pero al menos 1
                recursos_obtenidos[recurso] = cantidad

        # Actualizar recursos del ciudadano
        for recurso, cantidad in recursos_obtenidos.items():
            # Verificar si el recurso necesita ser actualizado (cantidad distinta de 0)
            if cantidad != 0:
                # Mapeo de recursos a sus nombres de campo en la base de datos
                nombre_campo = {
                    'madera': 'madera',
                    'rama': 'rama',
                    'trigo': 'trigo',
                    'hierro': 'hierro',
                    'carne': 'carne',
                    'piel': 'piel',
                    'pescado': 'pescado',
                    'verdura': 'verdura',
                    'hierba': 'hierba',
                    'piedra': 'piedra',
                    'moneda': 'moneda',
                    'arcilla': 'arcilla',
                    'agua': 'agua',
                    'energia': 'energia'  # Añadido para manejar la energía
                }.get(recurso)
                
                if nombre_campo is not None:  # Solo actualizar si el recurso es válido
                    sumar_recurso_ciudadano(ciudadano['id'], nombre_campo, cantidad)
        # Registrar la acción con detalles de recursos 
        mensaje_base = MENSAJES_POR_DEFECTO.get(accion, f"@{nombre_ciudadano} ha realizado la acción {accion} y obtiene:")
        mensaje_final = mensaje_base.format(autor=nombre_ciudadano) + "\n"
        recursos_obtenidos_str = []
        for recurso, cantidad in recursos_obtenidos.items():
            if cantidad != 0:
                recursos_obtenidos_str.append(f"{round(cantidad, 2)} {recurso}")
        if recursos_obtenidos_str:
            mensaje_final += ", ".join(recursos_obtenidos_str) + ".\n"
        mensaje_final += f"{MENSAJES_RESULTADO[resultado]}"
        database.registrar_accion(accion, mensaje_final, ciudadano.get('id', 0))
        return mensaje_final 

    except Exception as e:
        logging.error(f"Error en realiza_accion: {str(e)}")
        return f"@{nombre_ciudadano} Ha ocurrido un error al realizar la acción {str(e)}"
