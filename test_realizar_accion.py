#!/usr/bin/env python3
"""
Script de prueba para la función realizar_accion del módulo DB_DML_Funciones.

Este script prueba la función realizar_accion con un ciudadano y acción específicos.
"""

import sys
import os
import logging
from datetime import datetime

# Configurar el path para poder importar DB_DML_Funciones
# Agregar el directorio padre al path para importar DB_DML_Funciones
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)  # Agregar el directorio actual al path

# También podemos intentar con la ruta completa si es necesario
db_dml_path = os.path.join(script_dir, 'DB_DML_FUNCIONES.py')
if not os.path.exists(db_dml_path):
    print(f"Error: No se encuentra el archivo {db_dml_path}")
    sys.exit(1)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_realizar_accion.log')
    ]
)
logger = logging.getLogger(__name__)

def test_realizar_accion():
    """
    Función de prueba para realizar_accion.
    """
    try:
        # Intentar importar de diferentes maneras para mayor compatibilidad
        try:
            from DB_DML_FUNCIONES import realizar_accion
        except ImportError as e:
            print(f"Error al importar: {e}")
            print("Intentando importación alternativa...")
            import DB_DML_FUNCIONES
            realizar_accion = DB_DML_FUNCIONES.realizar_accion
        
        # Datos de prueba
        nombre_ciudadano = 'solounturnomas'
        codigo_accion = '1'  # Asegúrate de que este sea un código de acción válido
        
        print(f"\n{'='*50}")
        print(f"Iniciando prueba de realizar_accion")
        print(f"Ciudadano: {nombre_ciudadano}")
        print(f"Acción: {codigo_accion}")
        print(f"Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*50}\n")
        
        # Ejecutar la función
        resultado = realizar_accion(
            nombre_ciudadano=nombre_ciudadano,
            codigo_accion=codigo_accion,
            usuario_modificar='script_prueba'
        )
        
        # Mostrar resultados
        print("\nResultado de la ejecución:")
        print(f"Éxito: {resultado.get('exito', False)}")
        print(f"Mensaje: {resultado.get('mensaje', 'Sin mensaje')}")
        
        if 'recursos_obtenidos' in resultado and resultado['recursos_obtenidos']:
            print("\nRecursos obtenidos:")
            for recurso, cantidad in resultado['recursos_obtenidos'].items():
                print(f"- {recurso}: {cantidad}")
        
        if 'energia_restante' in resultado:
            print(f"\nEnergía restante: {resultado['energia_restante']}")
        
        return resultado
        
    except Exception as e:
        logger.error(f"Error durante la prueba: {str(e)}", exc_info=True)
        print(f"\nError durante la prueba: {str(e)}")
        return {'exito': False, 'error': str(e)}

if __name__ == "__main__":
    print("Iniciando prueba de realizar_accion...")
    test_realizar_accion()
    print("\nPrueba completada. Revisa el archivo 'test_realizar_accion.log' para más detalles.")
