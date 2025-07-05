"""
Bot de Twitch para el canal de SolunTurnoMas.
Este bot maneja recompensas y comandos para el canal de Twitch.

Configuración:
- Las variables de configuración se cargan desde un archivo .env
- El logging se maneja a través de configuracion_logging.py
- Las funciones de mensajes están en la carpeta funciones/

Recompensas disponibles:
- Talar
- Trabajar en el campo
- Trabajar de guardia
- Picar piedra
- Cazar en el bosque
- Pescar
"""

from twitchio.ext import commands
from datetime import datetime
import logging
import configuracion_logging
from dotenv import load_dotenv
import os
from funciones.realiza_accion import realiza_accion
from database import añadir_energia

# Cargar variables de entorno
load_dotenv()

# Usar el logger configurado en configuracion_logging
logger = configuracion_logging.logger

# Cargar configuración desde .env
TOKEN_BOT = os.getenv('TOKEN_BOT')
NOMBRE_BOT = os.getenv('NOMBRE_BOT')
CANAL_BOT = os.getenv('CANAL_BOT')

# Usar el nombre del bot como BOT_USERNAME
BOT_USERNAME = NOMBRE_BOT

# Diccionario de acciones para recompensas
RECOMPENSAS = {
    '3a923fe1-90f4-4f0b-bb09-fc53d5f1e0fb': 'energia1',
    'e5b9f616-826d-4188-97f1-d99729748fae': 'energia10',
}

class Bot(commands.Bot):

    def __init__(self):
        try:
            super().__init__(token=TOKEN_BOT, prefix='!', initial_channels=[CANAL_BOT])
            logger.info("Bot inicializado correctamente.")
        except Exception as e:
            logger.error(f"Error al inicializar el bot: {e}")
            raise

    async def event_ready(self):
        try:
            logger.info(f'Bot "{NOMBRE_BOT}" conectado exitosamente.')
            
            # Obtener la hora actual
            hora_actual = datetime.now().strftime('%H:%M')
            mensaje = f"¡Buenos días! Bueno, en realidad son las {hora_actual}"
            logger.info(f"Enviando mensaje de bienvenida: {mensaje}")
            
            # Enviar mensaje al canal
            channel = self.get_channel(CANAL_BOT)
            if channel:
                await channel.send(mensaje)
        except Exception as e:
            logger.error(f"Error en event_ready: {e}")

    async def event_message(self, message):
        try:
            # Obtener el ID de recompensa de los tags
            reward_id = message.tags.get("custom-reward-id")
            
            # Manejar mensajes del sistema (sin autor)
            if not message.author:
                logger.info(f"[Sistema] {message.content}")
                return

            # Mostrar el mensaje
            if reward_id:
                # Obtener la acción asociada a la recompensa
                accion = RECOMPENSAS.get(reward_id)
                if accion: 
                    logger.info(f"[Recompensa] {message.author.name}: {message.content} (ID: {reward_id}) - Acción: {accion}")
                    # Realizar acción y escribir mensaje en el chat
                    if RECOMPENSAS.get(reward_id) == 'energia1':
                        await message.channel.send(añadir_energia(message.author.name, 1, "añadir_energia"))
                    elif RECOMPENSAS.get(reward_id) == 'energia10':
                        await message.channel.send(añadir_energia(message.author.name, 10, "añadir_energia"))
                    else:
                        await message.channel.send(realiza_accion(accion, message.author.name, message.content))
                else:
                    logger.info(f"[Recompensa] {message.author.name}: {message.content} (ID: {reward_id}) - Acción no encontrada")
            else:
                logger.info(f"[Mensaje] {message.author.name}: {message.content}")

            # Lógica de respuesta al jefe
            if 'hola' in message.content.lower() and message.author.name.lower() == 'solounturnomas':
                await message.channel.send('¡Hola, jefe!')

            # Procesar comandos si existen
            await self.handle_commands(message)

        except Exception as e:
            logger.error(f"Error al procesar mensaje: {str(e)}")

            # Manejar mensajes del sistema (sin autor)
            if not message.author:
                logger.info(f"[Sistema] {message.content}")
                return

            # Ignorar mensajes del propio bot
            if message.author.name.lower() == BOT_USERNAME.lower():
                return

            # Mostrar información del mensaje
            logger.info(f"[Mensaje] {message.author.name}: {message.content}")

            # Lógica de respuesta al jefe
            if 'hola' in message.content.lower() and message.author.name.lower() == 'solounturnomas':
                await message.channel.send('¡Hola, jefe!')

            # Procesar comandos si existen
            await self.handle_commands(message)

        except Exception as e:
            logger.error(f"Error al procesar mensaje: {str(e)}")

            # Lógica de respuesta básica
            if 'hola' in message.content.lower() and message.author.name.lower() == 'solounturnomas':
                await message.channel.send('¡Hola, jefe!')

            # Procesar comandos si existen
            await self.handle_commands(message)

        except Exception as e:
            logger.error(f"Error al procesar mensaje: {str(e)}")

    async def event_command_error(self, ctx, error):
        try:
            logger.error(f"Error en comando '{ctx.command}': {error}")
            await ctx.send("⚠️ Ocurrió un error con el comando. Revisa la sintaxis.")
        except Exception as e:
            logger.error(f"Error al manejar event_command_error: {e}")


# Ejecutar el bot
try:
    bot = Bot()
    bot.run()
except Exception as e:
    logger.error(f"Fallo al iniciar el bot: {e}")