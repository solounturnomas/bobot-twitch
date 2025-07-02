from db_mapa import crear_casilla, obtener_casilla, actualizar_casilla, completar_cuadrado, plaza_central, TIPOS_CASILLAS, crear_caminos_verticales, tiene_solar_asignado, asignar_ciudadano_a_solar
from database import get_db_connection
import sqlite3

def tiene_solar_asignado(ciudadano_id: int) -> bool:
    """
    Verifica si un ciudadano ya tiene un solar asignado.
    
    Args:
        ciudadano_id: ID del ciudadano a verificar
        
    Returns:
        True si tiene solar asignado, False en caso contrario
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM mapa WHERE ciudadano_id = ?', (ciudadano_id,))
            count = cursor.fetchone()[0]
            return count > 0
    except sqlite3.Error as e:
        print(f"Error al verificar solar asignado: {e}")
        return False

def main():
    # Crear algunas casillas de prueba
    print("Creando casillas de prueba...")
    
    # Crear un cesped
    if crear_casilla(0, 0, "CESPED"):
        print("Cesped creado en (0,0)")
    
    # Crear un camino
    if crear_casilla(1, 0, "CAMINO"):
        print("Camino creado en (1,0)")
    
    # Crear un camino girado
    if crear_casilla(1, 1, "CAMINO_GIRADO"):
        print("Camino girado creado en (1,1)")
    
    # Intentar crear una casilla en una posición que ya existe
    if not crear_casilla(0, 0, "CESPED"):
        print("No se pudo crear cesped en (0,0) - ya existe")
    
    # Obtener casillas
    print("\nObteniendo casillas...")
    casilla = obtener_casilla(0, 0)
    if casilla:
        print(f"Casilla en (0,0): {casilla}")
    
    # Actualizar una casilla
    print("\nActualizando casilla...")
    if actualizar_casilla(0, 0, "CAMINO"):
        print("Casilla actualizada a CAMINO")
    else:
        print("No se pudo actualizar la casilla")
    
    # Verificar la actualización
    casilla = obtener_casilla(0, 0)
    if casilla:
        print(f"Casilla en (0,0) después de actualizar: {casilla}")

    # Probar completar cuadrado
    print("\nCompletando cuadrado...")
    if completar_cuadrado():
        print("Cuadrado completado exitosamente")
    else:
        print("Error al completar el cuadrado")

    # Probar plaza central
    print("\nCreando plaza central...")
    if plaza_central():
        print("Plaza central creada exitosamente")
        if crear_caminos_verticales():
            print("Caminos verticales creados exitosamente")
        else:
            print("Error al crear caminos verticales")
    else:
        print("Error al crear la plaza central")

    # Verificar y asignar solar al ciudadano solounturnomas
    ciudadano_id = 1  # ID del ciudadano solounturnomas
    if not tiene_solar_asignado(ciudadano_id):
        if asignar_ciudadano_a_solar(ciudadano_id):
            print(f"Se asignó un solar al ciudadano {ciudadano_id}")
        else:
            print(f"No se pudo asignar un solar al ciudadano {ciudadano_id}")

if __name__ == "__main__":
    main()
