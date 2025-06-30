# Bot de Twitch para SolunTurnoMas

Este bot de Twitch está diseñado para manejar recompensas y comandos en el canal de SolunTurnoMas.

## Estructura del Proyecto

```
bobot/
├── funciones/                 # Funciones auxiliares
│   └── escribir_mensaje_funcion.py  # Gestión de mensajes de recompensas
├── logs/                     # Archivos de log rotativos
├── .env                      # Variables de entorno
├── LEEME.md                  # Documentación del proyecto
├── requisitos                # Dependencias del proyecto
├── bobot.py                  # Código principal del bot
├── configuracion_logging.py  # Configuración de logging
└── database.py               # Gestión de la base de datos
```

## Configuración

1. Crea un archivo `.env` con las siguientes variables:
   - `TOKEN_BOT`: Token de OAuth del bot
   - `NOMBRE_BOT`: Nombre del bot
   - `CANAL_BOT`: Nombre del canal donde se conectará el bot

2. Instala las dependencias necesarias:
```bash
pip install -r requisitos
```

## Funcionalidades

- Manejo de recompensas con mensajes personalizados:
  - Talar: "¡{autor} se ha ido a talar al bosque!"
  - Trabajar en el campo: "¡{autor} ha comenzado a trabajar en el campo!"
  - Trabajar de guardia: "¡{autor} ha empezado su turno de guardia!"
  - Picar piedra: "¡{autor} ha empezado a picar piedra!"
  - Cazar en el bosque: "¡{autor} ha entrado al bosque para cazar!"
  - Pescar: "¡{autor} ha empezado a pescar!"

- Sistema de logging con:
  - Logs rotativos diarios
  - Nivel de logging DEBUG
  - Logs tanto en archivo como en consola

- Manejo de comandos personalizados
- Respuestas automáticas a mensajes específicos

## IDs de Recompensas

```
Talar: f7b19ecc-5085-43b2-a07e-dee6f8c064dd
Trabajar en el campo: 45650b54-6ec3-4908-ac23-c71521d224e8
Trabajar de guardia: f6a93674-c59c-43a3-8112-97b31f9b9571
Picar piedra: 5e35690c-d9a7-4383-9365-ac3ddd2a28f0
Cazar en el bosque: 720eab8f-404a-4166-a035-b2db303cc4d5
Pescar: 065567f5-e68f-43cd-816f-f4ef0e64572d
``` 
