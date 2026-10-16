from telethon import TelegramClient, events
import asyncio, threading, os, glob
from flask import Flask
from telethon.sessions import StringSession

API_ID = int(os.environ.get("API_ID", "32695956"))
API_HASH = os.environ.get("API_HASH", "8d939c8130ea03c01cd9abe6a6e83d7a")
SESSION = os.environ.get("SESSION_STRING", "")
GRUPO = int(os.environ.get("GRUPO_DESTINO", "-1003764262854"))
TOPIC = int(os.environ.get("TOPIC_ID", "752770"))
CANAL = os.environ.get("CANAL_ORIGEN", "https://t.me/Horny_J")

app = Flask(__name__)
@app.route('/')
def home(): return "Bot vivo"

threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000), daemon=True).start()

if SESSION:
    client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)
else:
    s = glob.glob("*.session")
    client = TelegramClient(s[0].replace('.session','') if s else 'sesion_nube', API_ID, API_HASH)

async def cargar_progreso():
    try:
        async for m in client.iter_messages('me', limit=20):
            if m.text and m.text.startswith("PROGRESO_BOT:"):
                return int(m.text.split(":")[1].strip())
    except Exception as e:
        print(f"No se pudo cargar progreso: {e}")
    return 0

async def guardar_progreso(last_id):
    try:
        async for m in client.iter_messages('me', limit=20):
            if m.text and m.text.startswith("PROGRESO_BOT:"):
                await m.delete()
        await client.send_message('me', f"PROGRESO_BOT:{last_id}")
    except Exception as e:
        print(f"Error guardando progreso: {e}")

async def main():
    await client.start()
    print("CLIENTE CONECTADO OK")
    o = await client.get_entity(CANAL)
    d = await client.get_entity(GRUPO)
    last_id = await cargar_progreso()
    print(f"ARRANCO DESDE: {last_id}")
    async for m in client.iter_messages(o, min_id=last_id, reverse=True):
        if not (m.media or m.text):
            last_id = m.id
            continue
        try:
            if m.media:
                await client.send_file(d, m.media, caption=m.text, reply_to=TOPIC)
            else:
                await client.send_message(d, m.text, reply_to=TOPIC)
            print(f"Copiado {m.id}")
            last_id = m.id
            await guardar_progreso(last_id)
            await asyncio.sleep(1)
        except Exception as e:
            print(e)
            await asyncio.sleep(3)
    print("HISTORIAL LISTO - EN VIVO")
    @client.on(events.NewMessage(chats=CANAL))
    async def h(e):
        if not (e.message.media or e.message.text):
            return
        if e.message.media:
            await client.send_file(d, e.message.media, caption=e.message.text, reply_to=TOPIC)
        else:
            await client.send_message(d, e.message.text, reply_to=TOPIC)
        await guardar_progreso(e.message.id)
    await client.run_until_disconnected()

asyncio.run(main())
