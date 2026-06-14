from fastapi import FastAPI, Request
from message_buffer import buffer_message


app = FastAPI()


# Subindo o endpoint para o webhook
# Foi criada uma rota para o webhook
@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json() # Pega o json do request
    print(data)

    # Pega o número do telefone
    chat_id = data.get("data").get("key").get("remoteJid")

    # Pega a mensagem enviada
    message = data.get("data").get("message").get("conversation")

    # Verifica se o chat_id e a mensagem não estão vazios e se não é um grupo
    if chat_id and message and "@g.us" not in chat_id:
        print(f"Mensagem recebida de {chat_id}: {message}")

        await buffer_message(
            chat_id=chat_id,
            message=message,
        )

        print(f"Mensagem enviada para {chat_id}: {message}")
    
    return {"status": "ok"}