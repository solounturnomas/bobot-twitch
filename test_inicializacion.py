"""
Script para probar la inicialización de la base de datos.

Este script fuerza la reinicialización de las tablas y verifica que todos los datos
se hayan insertado correctamente.
"""
import sqlite3
import logging
from database import get_db_connection, init_db, inicializar_herramientas, inicializar_acciones, inicializar_recursos_acciones

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_inicializacion')

def verificar_herramientas():
    """Verifica que las herramientas se hayan insertado correctamente."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM herramientas')
        count = cursor.fetchone()[0]
        logger.info(f"Se encontraron {count} herramientas en la base de datos")
        
        cursor.execute('SELECT codigo, nombre FROM herramientas')
        for row in cursor.fetchall():
            logger.info(f"Herramienta: {row['codigo']} - {row['nombre']}")
        
        return count > 0

def verificar_acciones():
    """Verifica que las acciones se hayan insertado correctamente."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT a.codigo, a.nombre, h.codigo as herramienta_codigo 
            FROM acciones a 
            LEFT JOIN herramientas h ON a.herramienta_id = h.id
        ''')
        acciones = cursor.fetchall()
        logger.info(f"Se encontraron {len(acciones)} acciones en la base de datos")
        
        for accion in acciones:
            logger.info(f"Acción: {accion['codigo']} - {accion['nombre']} (Herramienta: {accion['herramienta_codigo'] or 'Ninguna'})")
        
        return len(acciones) > 0

def verificar_recursos_acciones():
    """Verifica que las relaciones entre acciones y recursos se hayan insertado correctamente."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM recursos_acciones')
        count = cursor.fetchone()[0]
        logger.info(f"Se encontraron {count} relaciones entre acciones y recursos")
        
        cursor.execute('''
            SELECT a.codigo as accion, r.codigo as recurso, 
                   ra.cantidad, ra.cantidad_herramienta, ra.cantidad_pozo,
                   ra.probabilidad, ra.probabilidad_herramienta, ra.probabilidad_pozo
            FROM recursos_acciones ra
            JOIN acciones a ON ra.accion_id = a.id
            JOIN recursos r ON ra.recurso_id = r.id
            ORDER BY a.codigo, r.codigo
        ''')
        
        for rel in cursor.fetchall():
            logger.info(
                f"Relación: {rel['accion']} -> {rel['recurso']} | "
                f"Cantidades: {rel['cantidad']}/{rel['cantidad_herramienta']}/{rel['cantidad_pozo']} | "
                f"Probabilidades: {rel['probabilidad']}%/{rel['probabilidad_herramienta']}%/{rel['probabilidad_pozo']}%"
            )
        
        return count > 0

def main():
    """Función principal para probar la inicialización de la base de datos."""
    logger.info("Iniciando prueba de inicialización de la base de datos...")
    
    try:
        # Forzar la reinicialización de la base de datos
        logger.info("Reinicializando la base de datos...")
        init_db()
        
        # Inicializar herramientas forzando la inserción
        logger.info("Inicializando herramientas...")
        if not inicializar_herramientas(forzar=True):
            logger.error("Error al inicializar herramientas")
            return False
        
        # Inicializar acciones
        logger.info("Inicializando acciones...")
        if not inicializar_acciones():
            logger.error("Error al inicializar acciones")
            return False
        
        # Inicializar relaciones entre acciones y recursos
        logger.info("Inicializando relaciones entre acciones y recursos...")
        if not inicializar_recursos_acciones():
            logger.error("Error al inicializar relaciones entre acciones y recursos")
            return False
        
        # Verificar que todo se haya insertado correctamente
        logger.info("Verificando datos insertados...")
        herramientas_ok = verificar_herramientas()
        acciones_ok = verificar_acciones()
        recursos_acciones_ok = verificar_recursos_acciones()
        
        if herramientas_ok and acciones_ok and recursos_acciones_ok:
            logger.info("¡Todas las verificaciones fueron exitosas!")
            return True
        else:
            logger.error("Algunas verificaciones fallaron")
            return False
            
    except Exception as e:
        logger.exception("Error durante la prueba de inicialización")
        return False

if __name__ == "__main__":
    if main():
        print("\n¡Prueba completada exitosamente!")
    else:
        print("\n¡La prueba falló! Revisa los logs para más detalles.")
