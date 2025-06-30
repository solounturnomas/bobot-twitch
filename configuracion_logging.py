import logging
import logging.handlers
from datetime import datetime

def setup_logging():
    """Configura el sistema de logging"""
    # Crear logger principal
    logger = logging.getLogger('twitch_bot')
    logger.setLevel(logging.DEBUG)
    
    # Formato de los logs
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para archivo de logs rotativo (nuevo archivo cada día)
    file_handler = logging.handlers.TimedRotatingFileHandler(
        'logs/twitch_bot.log',
        when='midnight',
        interval=1,
        backupCount=7  # Mantener 7 días de logs
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Handler para consola (todos los niveles)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    
    # Agregar handlers al logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Crear el directorio de logs si no existe
import os
os.makedirs('logs', exist_ok=True)

# Configurar logging al importar el módulo
logger = setup_logging()
