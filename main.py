from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import httpx
from dotenv import load_dotenv
from pathlib import Path

# Garante que vai carregar o .env que está na MESMA PASTA do main.py
BASE_DIR = Path(__file__).resolve().parent
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)

print("Lendo .env em:", env_path)  # só pra debug

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")

print("TOKEN:", "OK" if WHATSAPP_TOKEN else "VAZIO")
print("PHONE_NUMBER_ID:", PHONE_NUMBER_ID)

if not PHONE_NUMBER_ID:
    raise RuntimeError("Variável WHATSAPP_PHONE_NUMBER_ID não configurada")
if not WHATSAPP_TOKEN:
    raise RuntimeError("Variável WHATSAPP_TOKEN não configurada")

WHATSAPP_API_URL = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"

app = FastAPI(title="WhatsTime Backend")

class SendRequest(BaseModel):
    to: str      # número no formato internacional, ex: 5531999999999
    message: str

@app.get("/")
async def root():
    return {"status": "ok", "app": "WhatsTime backend"}

@app.post("/api/send")
async def send_message(req: SendRequest):
    """
    Endpoint chamado pelo app Android.
    Ele repassa a mensagem para a WhatsApp Cloud API usando o TOKEN do backend.
    """
    payload = {
        "messaging_product": "whatsapp",
        "to": req.to,
        "type": "text",
        "text": {"body": req.message}
    }

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(WHATSAPP_API_URL, json=payload, headers=headers)

        if 200 <= response.status_code < 300:
            data = response.json()
            return {"success": True, "whatsapp_response": data}
        else:
            # Loga a resposta de erro para você depurar no backend
            print("Erro WhatsApp API:", response.status_code, response.text)
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Erro ao enviar mensagem via WhatsApp API"
            )
    except httpx.RequestError as e:
        print("Erro de rede ao chamar WhatsApp API:", str(e))
        raise HTTPException(status_code=500, detail="Falha de comunicação com WhatsApp API")
