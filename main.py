from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError
import asyncio, os
from flask import Flask
import threading

# --- TUS DATOS, CAMBIA ESTO ---
API_ID = 32695956
API_HASH = '8d939c8130ea03c01cd9abe6a6e83d7a'
SESSION = os.environ.get("SESSION_STRING")
CANAL_ORIGEN = 'https://t.me/Horny_J' # de donde copias
GRUPO_DESTINO = -1003764262854 # a donde copias
TOPIC_ID = 736414 # tu tema, si no tienes tema pon None
# ------------------------------

app = Flask(__name__)
@app.route('/')
def home(): return "Bot vivo"
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=8080), daemon=True).start()

async def cargar(client):
    try:
        async for m in client.iter_messages('me', limit=20):
            if (m.text or "").startswith("PROGRESO_BOT:"):
                return int(m.text.split(":")[1].strip())
    except: pass
    return 0

async def guardar(client, last_id):
    try:
        async for m in client.iter_messages('me', limit=20):
            if (m.text or "").startswith("PROGRESO_BOT:"):
                await m.delete()
        await client.send_message('me', f"PROGRESO_BOT:{last_id}")
    except: pass

async def copiar_uno(client, d, m):
    while True:
        try:
            if m.media:
                await client.send_file(d, m.media, caption=m.text, reply_to=TOPIC_ID)
            else:
                await client.send_message(d, m.text, reply_to=TOPIC_ID)
            return True
        except FloodWaitError as e:
            print(f"FRENO {e.seconds}s")
            await asyncio.sleep(e.seconds + 5)
        except Exception as e:
            print(f"Error {m.id}: {e}")
            await asyncio.sleep(5)
            return False

async def copiar_album(client, d, grupo):
    files = [x.media for x in grupo if x.media]
    if not files:
        return
    # Telegram solo deja 10 por álbum máximo
    for i in range(0, len(files), 10):
        chunk = files[i:i+10]
        cap = grupo[0].text if i == 0 else ""
        while True:
            try:
                await client.send_file(d, chunk, caption=cap, reply_to=TOPIC_ID)
                break
            except FloodWaitError as e:
                print(f"FRENO {e.seconds}s")
                await asyncio.sleep(e.seconds + 5)
            except Exception as e:
                print(f"Error álbum: {e}")
                await asyncio.sleep(5)
                break

async def main():
    client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)
    await client.start()
    last_id = await cargar(client)
    print(f"ARRANCO DESDE: {last_id}")

    o = await client.get_entity(CANAL_ORIGEN)
    d = await client.get_entity(GRUPO_DESTINO)

    # Traemos todos en orden, de viejo a nuevo
    mensajes = []
    async for m in client.iter_messages(o, min_id=last_id, reverse=True):
        mensajes.append(m)

    ya_procesados = set()
    for m in mensajes:
        if m.id in ya_procesados:
            continue
        if m.id <= last_id:
            continue

        # Si no tiene grouped_id, es 1 solo
        if not m.grouped_id:
            if not (m.media or m.text):
                last_id = m.id
                continue
            await copiar_uno(client, d, m)
            last_id = m.id
            await guardar(client, last_id)
            await asyncio.sleep(2)
        else:
            # Es un álbum, busca todos los del mismo grouped_id
            grupo = [x for x in mensajes if x.grouped_id == m.grouped_id]
            for x in grupo:
                ya_procesados.add(x.id)
            await copiar_album(client, d, grupo)
            last_id = max(x.id for x in grupo)
            await guardar(client, last_id)
            await asyncio.sleep(3)

    print("LISTO, COPIA TERMINADA")

asyncio.run(main())