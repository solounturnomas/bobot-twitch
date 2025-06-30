import sys
import os
from datetime import datetime
from database import mostrar_ciudadanos, mostrar_historial

def main():
    print("\n=== VISUALIZADOR DE DATOS DE SOLUVILLE ===")
    print("=" * 50)
    
    while True:
        print("\n¿Qué deseas ver?")
        print("1. Ciudadanos")
        print("2. Historial de acciones")
        print("3. Salir")
        
        opcion = input("\nElige una opción (1-3): ")
        
        if opcion == "1":
            print("\n=== CIUDADANOS ===")
            mostrar_ciudadanos()
            
        elif opcion == "2":
            print("\n=== HISTORIAL DE ACCIONES ===")
            print("\nFiltros disponibles:")
            print("1. Ver todo")
            print("2. Filtrar por fecha")
            print("3. Filtrar por ciudadano")
            
            filtro = input("\nElige un filtro (1-3): ")
            
            if filtro == "1":
                mostrar_historial()
            elif filtro == "2":
                fecha_inicio = input("Fecha inicio (YYYY-MM-DD HH:MM:SS): ")
                fecha_fin = input("Fecha fin (YYYY-MM-DD HH:MM:SS): ")
                mostrar_historial(fecha_inicio, fecha_fin)
            elif filtro == "3":
                ciudadano_id = input("ID del ciudadano: ")
                try:
                    ciudadano_id = int(ciudadano_id)
                    mostrar_historial(ciudadano_id=ciudadano_id)
                except ValueError:
                    print("Error: El ID debe ser un número")
            else:
                print("Opción no válida")
                
        elif opcion == "3":
            print("\n¡Hasta luego!")
            break
            
        else:
            print("Opción no válida")

if __name__ == "__main__":
    main()
