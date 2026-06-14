import re
from fastapi import FastAPI, Request
from WahaService import WahaService 
from ShipManager import ShipManager

app = FastAPI()
waha = WahaService()
manager = ShipManager() 

# Controle de estado simples
user_states = {}

# --- FUNÇÃO DE NORMALIZAÇÃO (O SEGREDO) ---
def normalizar_id(payload):
    """
    Descobre quem é o dono da mensagem, não importa de qual dispositivo veio.
    Retorna sempre o ID @c.us (Número real).
    """
    chat_id = payload.get("from", "")
    
    # Se já for um número de celular padrão, retorna ele mesmo
    if chat_id.endswith("@c.us"):
        return chat_id
    
    # Se for LID (Dispositivo vinculado), busca o dono dentro dos metadados
    if chat_id.endswith("@lid"):
        # O WAHA geralmente envia os dados brutos em '_data'
        data_interno = payload.get("_data", {})
        id_remoto = data_interno.get("id", {}).get("remote")
        
        if id_remoto and id_remoto.endswith("@c.us"):
            return id_remoto
            
    # Se falhar a normalização, retorna None para ser ignorado
    return None

# --- FUNÇÃO DE RELATÓRIO (Opção 4) ---
async def handle_status_request(chat_id, imo):
    imo = re.sub(r'\D', '', imo) 
    timeline = manager.get_ship_timeline(imo)
    
    if not timeline:
        await waha.send_message(chat_id, f"⚠️ Nenhum registro encontrado para o IMO {imo}.")
        return

    info = manager.get_ship_details(imo)
    nome_navio = info[0] if info else "Navio Desconhecido"
    bandeira = info[1] if info else "N/A"

    report = [
        f"⚓ *RELATÓRIO DE SITUAÇÃO*",
        f"🚢 *{nome_navio}* (IMO: {imo})",
        f"🏳️ Bandeira: {bandeira}",
        "-------------------------------",
        "*Últimas Movimentações:*"
    ]

    icons = {
        "Fundeado": "⚓", "Atracado": "🏗️", 
        "Navegando": "🌊", "Esperando Prático": "👨‍✈️", "Operando": "⚙️"
    }

    for row in timeline:
        situacao = row[0] 
        data = row[1]     
        manobra = row[2] if len(row) > 2 and row[2] else ""
        icon = icons.get(situacao, "📌")
        line = f"📅 {data} - {icon} *{situacao}*"
        if manobra: line += f" ({manobra})"
        report.append(line)

    report.append("-------------------------------")
    await waha.send_message(chat_id, "\n".join(report))


# --- WEBHOOK (CÉREBRO) ---
@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    
    # 1. Validações básicas
    event = data.get("event")
    if event not in ["message", "message.created"]: 
        return {"status": "ignored_event"}
    
    payload = data.get("payload", {})
    text = payload.get("body", "").strip()

    # 2. Filtros de Segurança
    if payload.get("fromMe"): return {"status": "ignored_me"}
    if not text: return {"status": "ignored_empty"}

    # 3. NORMALIZAÇÃO: Transforma LID em C.US
    chat_id = normalizar_id(payload)
    
    if not chat_id:
        # Se não conseguimos achar o número real (ex: Status, Grupo anônimo), ignoramos
        print(f"🛑 Origem não identificada ou inválida: {payload.get('from')}")
        return {"status": "ignored_unknown_origin"}

    print(f"📩 Mensagem de: {chat_id} (Origem Processada)")
    print(f"📝 Texto: '{text}'")

    state = user_states.get(chat_id)

    # --- LÓGICA DE NAVEGAÇÃO ---

    # Menu Principal
    if text in ["1", "2", "3", "4"] and state is None:
        if text == "1":
            await waha.send_message(chat_id, "🆕 *Adicionar Navio*\nDigite o IMO e o Nome (ex: `1234567 Navio X`):")
            user_states[chat_id] = "WAITING_ADD"
        elif text == "2":
            await waha.send_message(chat_id, "🗑️ *Remover Navio*\nDigite o IMO do navio:")
            user_states[chat_id] = "WAITING_DEL"
        elif text == "3":
            navios = manager.list_ships()
            lista = "\n".join([f"🚢 {n[0]} (IMO: {n[1]})" for n in navios]) if navios else "Nenhum navio monitorado."
            await waha.send_message(chat_id, f"*Navios Monitorados:*\n{lista}")
        elif text == "4":
            await waha.send_message(chat_id, "📊 *Relatório*\nDigite o IMO para ver a situação:")
            user_states[chat_id] = "WAITING_STATUS"

    # Estados
    elif state == "WAITING_STATUS":
        await handle_status_request(chat_id, text)
        user_states[chat_id] = None 

    elif state == "WAITING_ADD":
        # Regex flexível: Aceita "123456 Navio" ou "123456 - Navio"
        match = re.match(r'^(\d+)\s*[-]?\s*(.+)$', text)
        if match:
            imo, nome = match.group(1), match.group(2)
            try:
                manager.add_ship(imo, nome)
                await waha.send_message(chat_id, f"✅ Monitoramento iniciado para *{nome}*.")
                user_states[chat_id] = None
            except Exception as e:
                await waha.send_message(chat_id, "❌ Erro ao salvar. Tente novamente.")
                print(f"Erro BD: {e}")
        else:
            await waha.send_message(chat_id, "⚠️ Formato inválido.\nUse: `IMO Nome` (Ex: `999999 Navio Beta`)")

    elif state == "WAITING_DEL":
        manager.remove_ship(text)
        await waha.send_message(chat_id, f"✅ Navio IMO {text} removido.")
        user_states[chat_id] = None

    # Fallback (Menu)
    else:
        menu = (
            "⚓ *Hydra Bot - Menu*\n\n"
            "1 - Adicionar Monitoramento\n"
            "2 - Remover Monitoramento\n"
            "3 - Listar Monitorados\n"
            "4 - Relatório de Situação"
        )
        await waha.send_message(chat_id, menu)
        user_states[chat_id] = None

    return {"status": "ok"}