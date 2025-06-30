import sys
import os
import logging
import datetime
import random
from typing import Optional, Dict, Any
import configuracion_logging
from dotenv import load_dotenv

# Agregar el directorio raíz al path de Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database

MENSAJES_POR_DEFECTO = {
    'talar': '¡{autor} se ha ido a talar al bosque!',
    'trabajar en el campo': '¡{autor} ha comenzado a trabajar en el campo!',
    'trabajar de guardia': '¡{autor} ha empezado su turno de guardia!',
    'picar piedra': '¡{autor} ha empezado a picar piedra!',
    'cazar en el bosque': '¡{autor} ha entrado al bosque para cazar!',
    'pescar': '¡{autor} ha empezado a pescar!'
}

def realiza_accion(accion: str, nombre_ciudadano: str, reward_id: str, mensaje: str = '') -> str:
    """
    Realiza una acción específica, actualiza recursos y devuelve el mensaje final con los detalles.
    
    Args:
        accion: Código de la acción a realizar
        nombre_ciudadano: Nombre del ciudadano que realiza la acción
        reward_id: ID de la recompensa
        mensaje: Mensaje completo del usuario para detectar palabras clave
        
    Returns:
        Mensaje final con el resultado de la acción y recursos obtenidos
    """
    try:
        # Convertir la acción a minúsculas para comparar con el diccionario RECOMPENSAS
        accion = accion.lower()
        
        ciudadano = database.get_ciudadano(nombre_ciudadano)
        if not ciudadano:
            return f"@{nombre_ciudadano} No estás registrado en Soloville. ¡Usa !registro para unirte!"

        # Definir mensajes según el resultado
        MENSAJES_RESULTADO = {
            'exito': '¡Qué bien!',
            'normal': 'No está mal!',
            'fracaso': 'Podría ser mejor'
        }

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
            'piedra': 0
        }

        # Palabras clave para cada recurso según la acción
        recursos_por_accion = {
            'talar': ['madera', 'rama', 'hierba'],
            'trabajar en el campo': ['trigo', 'verdura', 'hierba'],
            'trabajar de guardia': ['moneda', 'hierba'],
            'picar piedra': ['piedra', 'hierro', 'hierba'],
            'cazar en el bosque': ['carne', 'piel', 'hierba'],
            'pescar': ['pescado', 'hierba']
        }

        # Palabras clave para cada recurso
        palabras_clave = {
            'madera': ['madera', 'maderas', 'tronco', 'troncos'],
            'rama': ['rama', 'ramas'],
            'trigo': ['trigo', 'trigos'],
            'hierro': ['hierro', 'hierros'],
            'hierba': ['hierba', 'hierbas'],
            'carne': ['carne', 'carnes'],
            'piel': ['piel', 'pieles'],
            'pescado': ['pescado', 'pescados', 'pez'],
            'hierbas': ['hierba', 'hierbas'],
            'piedra': ['piedra', 'piedras', 'roca', 'rocas'],
            'moneda': ['moneda', 'monedas', 'coin', 'dinero'],
            'verdura': ['verdura', 'verduras']
        }

        # Actualizar fecha de última modificación
        datos_actualizar = {
            'fecha_modif': datetime.datetime.now(),
            'usuario_modif': 'bot'
        }

        # Calcular recursos según la acción
        if accion == 'talar':
            recursos_obtenidos['madera'] +=  1
            recursos_obtenidos['rama'] +=  5
            if ciudadano['tiene_hacha']:
                recursos_obtenidos['madera'] += 1
            if uso_pozo:
                recursos_obtenidos['rama'] += 2
                recursos_obtenidos['hierba'] += 2

        elif accion == 'trabajar en el campo':
            recursos_obtenidos['trigo'] += 5 
            # Probabilidad de obtener Verduras
            if random.random() <= 0.2:
                recursos_obtenidos['verdura'] += 1
            if ciudadano['tiene_hazada']:
                recursos_obtenidos['trigo'] += 2
                recursos_obtenidos['verdura'] += 1
                recursos_obtenidos['hierba'] += 2
            if uso_pozo:
                recursos_obtenidos['hierba'] += 2
                # Probabilidad de obtener Verduras
                if random.random() <= 0.3:
                    recursos_obtenidos['verdura'] += 1

        elif accion == 'trabajar de guardia':
            recursos_obtenidos['moneda'] += 10
            if ciudadano['tiene_espada']:
                recursos_obtenidos['moneda'] += 5
            if uso_pozo:
                recursos_obtenidos['moneda'] += 5
                recursos_obtenidos['hierba'] += 2

        elif accion == 'picar piedra':
            recursos_obtenidos['piedra'] += 5
            if ciudadano['tiene_pico']:
                recursos_obtenidos['madera'] += 3
                recursos_obtenidos['piedra'] += 1  
            # Probabilidad de obtener hierro
            if random.random() <= 0.2:
                recursos_obtenidos['hierro'] += 1
            if uso_pozo:
                # Probabilidad de obtener hierro
                if random.random() <= 0.2:
                    recursos_obtenidos['hierro'] += 1
                recursos_obtenidos['hierba'] += 2

        elif accion == 'cazar en el bosque':
            recursos_obtenidos['carne'] += 1
            recursos_obtenidos['piel'] += 3
            if ciudadano['tiene_arco']:
                recursos_obtenidos['carne'] += 1
                recursos_obtenidos['piel'] += 1
            if uso_pozo:
                recursos_obtenidos['piel'] += 1
                recursos_obtenidos['hierba'] += 2

        elif accion == 'pescar':
            recursos_obtenidos['pescado'] += 5
            if ciudadano['tiene_caña_pescar']:
                recursos_obtenidos['pescado'] += 5
            if uso_pozo:
                recursos_obtenidos['pescado'] += 1
                recursos_obtenidos['hierba'] += 2
        # Detectar palabras clave en el mensaje solo para los recursos permitidos en esta acción
        if accion in recursos_por_accion:
            recursos_permitidos = recursos_por_accion[accion]
            mensaje = mensaje.lower()
            for recurso in recursos_permitidos:
                if any(palabra in mensaje for palabra in palabras_clave[recurso]):
                    # Añadir bonificación del 25% de la cantidad obtenida si se menciona en el mensaje
                    nombre_campo = {
                        'madera': 'cantidad_madera',
                        'rama': 'cantidad_rama',
                        'trigo': 'cantidad_trigo',
                        'hierro': 'cantidad_hierro',
                        'carne': 'cantidad_carne',
                        'piel': 'cantidad_piel',
                        'pescado': 'cantidad_pescado',
                        'verdura': 'cantidad_verdura',
                        'hierba': 'cantidad_hierba',
                        'piedra': 'cantidad_piedra',
                        'moneda': 'cantidad_moneda'
                    }[recurso]
                    cantidad_actual = ciudadano.get(nombre_campo, 0)
                    cantidad_obtenida = recursos_obtenidos.get(recurso, 0)
                    bonificacion = cantidad_obtenida * 0.25  # 25% de la cantidad obtenida
                    if bonificacion > 0:  # Solo si la bonificación es mayor que 0
                        datos_actualizar[nombre_campo] = cantidad_actual + bonificacion
                        recursos_obtenidos[recurso] = cantidad_obtenida + bonificacion


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
            if cantidad > 0:
                # Mapeo de recursos a sus nombres de campo en la base de datos
                nombre_campo = {
                    'madera': 'cantidad_madera',
                    'rama': 'cantidad_rama',
                    'trigo': 'cantidad_trigo',
                    'hierro': 'cantidad_hierro',
                    'carne': 'cantidad_carne',
                    'piel': 'cantidad_piel',
                    'pescado': 'cantidad_pescado',
                    'verdura': 'cantidad_verdura',
                    'hierba': 'cantidad_hierba',
                    'piedra': 'cantidad_piedra',
                    'moneda': 'cantidad_moneda'
                }[recurso]
                cantidad_actual = ciudadano.get(nombre_campo, 0)
                datos_actualizar[nombre_campo] = cantidad_actual + cantidad
        database.actualizar_ciudadano(nombre_ciudadano, datos_actualizar)
        
        # Registrar la acción con detalles de recursos
        mensaje_base = MENSAJES_POR_DEFECTO.get(accion, f"@{nombre_ciudadano} ha realizado la acción {accion} y obtiene:")
        mensaje_final = mensaje_base.format(autor=nombre_ciudadano)
        recursos_obtenidos_str = []
        for recurso, cantidad in recursos_obtenidos.items():
            if cantidad > 0:
                recursos_obtenidos_str.append(f"{cantidad} {recurso}")
        mensaje_final += " " + ", ".join(recursos_obtenidos_str)
        mensaje_final += f" {MENSAJES_RESULTADO[resultado]}"
        database.registrar_accion(accion, mensaje_final, ciudadano.get('id', 0))
        return mensaje_final

    except Exception as e:
        logging.error(f"Error en realiza_accion: {str(e)}")
        return f"@{nombre_ciudadano} Ha ocurrido un error al realizar la acción"
