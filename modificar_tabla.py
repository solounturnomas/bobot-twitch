import sqlite3
import logging
import configuracion_logging

# Configurar logging
logger = configuracion_logging.logger
logger_modificacion = logger.getChild('modificar_tabla')

# Ruta de la base de datos
DB_PATH = 'soloville.db'

def modificar_tabla():
    """
    Modifica la tabla ciudadanos añadiendo los nuevos campos:
    - Campos booleanos para herramientas
    - Campo de fecha/hora para el pozo
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        logger_modificacion.info("Iniciando modificación de la tabla ciudadanos")
        
        # Lista de campos a añadir
        campos = [
            ('tiene_hacha', 'BOOLEAN DEFAULT FALSE'),
            ('tiene_pico', 'BOOLEAN DEFAULT FALSE'),
            ('tiene_espada', 'BOOLEAN DEFAULT FALSE'),
            ('tiene_hazada', 'BOOLEAN DEFAULT FALSE'),
            ('tiene_arco', 'BOOLEAN DEFAULT FALSE'),
            ('tiene_caña_pescar', 'BOOLEAN DEFAULT FALSE'),
            ('fecha_pozo', 'TIMESTAMP DEFAULT "2025-01-01 00:00:00"')
        ]
        
        # Añadir cada campo usando ALTER TABLE
        for nombre, tipo in campos:
            try:
                cursor.execute(f"ALTER TABLE ciudadanos ADD COLUMN {nombre} {tipo}")
                conn.commit()
                logger_modificacion.info(f"Campo añadido: {nombre}")
            except sqlite3.OperationalError:
                logger_modificacion.warning(f"El campo {nombre} ya existe en la tabla")
        
        logger_modificacion.info("Modificación de tabla completada exitosamente")
        
    except sqlite3.Error as e:
        logger_modificacion.error(f"Error al modificar la tabla: {e}")
        raise
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    try:
        modificar_tabla()
        print("\n=== MODIFICACIÓN DE TABLA COMPLETADA ===")
        print("Los nuevos campos han sido añadidos a la tabla ciudadanos")
        print("Campos añadidos:")
        print("- Herramientas (booleanos): hacha, pico, espada, hazada, arco, caña de pescar")
        print("- Fecha/hora: fecha_pozo")
    except Exception as e:
        print(f"\nError: {str(e)}")
