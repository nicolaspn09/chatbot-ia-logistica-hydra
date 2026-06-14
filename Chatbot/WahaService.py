import os
import re
import time
import random
import requests
import asyncio
from dotenv import load_dotenv, find_dotenv

class WahaService:
    def __init__(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        load_dotenv(find_dotenv(os.path.join(script_dir, '.env')))
        self.url_base = os.getenv("WAHA_API_URL")
        self.session = os.getenv("WAHA_SESSION", "default")
        self.api_key = os.getenv("WAHA_API_KEY")
        self.headers = {"Content-Type": "application/json"}
        if self.api_key:
            self.headers["X-Api-Key"] = self.api_key

    def _formata_numero(self, numero):
        numero = str(numero).strip()
        numero_limpo = re.sub(r'[^\d@c.us]', '', numero)
        return f"{numero_limpo}@c.us" if "@c.us" not in numero_limpo else numero_limpo

    def _alternar_nono_digito(self, chat_id):
        numero_limpo = chat_id.replace('@c.us', '')
        if not numero_limpo.startswith('55'): return chat_id
        
        if len(numero_limpo) == 13: # Remove 9
            novo = numero_limpo[:4] + numero_limpo[5:]
        elif len(numero_limpo) == 12: # Adiciona 9
            novo = numero_limpo[:4] + '9' + numero_limpo[4:]
        else:
            return chat_id
        return f"{novo}@c.us"

    async def _simula_presenca(self, chat_id, texto_len):
        """Versão assíncrona para não travar sua VPS"""
        try:
            requests.post(f"{self.url_base}/api/sendSeen", 
                          json={"session": self.session, "chatId": chat_id}, headers=self.headers)
            requests.post(f"{self.url_base}/api/startTyping", 
                          json={"session": self.session, "chatId": chat_id}, headers=self.headers)
            
            tempo = max(2, min(15, (texto_len / 5) + random.uniform(0.5, 1.5)))
            await asyncio.sleep(tempo) # Não bloqueia o servidor
            
            requests.post(f"{self.url_base}/api/stopTyping", 
                          json={"session": self.session, "chatId": chat_id}, headers=self.headers)
        except Exception as e:
            print(f"Erro simulação: {e}")

    async def send_message(self, number, text):
        chat_id = self._formata_numero(number)
        await self._simula_presenca(chat_id, len(text))

        payload = {"session": self.session, "chatId": chat_id, "text": text}
        
        try:
            response = requests.post(f"{self.url_base}/api/sendText", json=payload, headers=self.headers)
            
            if response.status_code == 500:
                novo_id = self._alternar_nono_digito(chat_id)
                payload["chatId"] = novo_id
                response = requests.post(f"{self.url_base}/api/sendText", json=payload, headers=self.headers)
            
            return response.status_code == 200
        except Exception as e:
            print(f"Erro fatal envio: {e}")
            return False