from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from pathlib import Path
import unicodedata
import random


def strip_accents(text: str) -> str:
    return "".join(
        ch for ch in unicodedata.normalize("NFD", text)
        if unicodedata.category(ch) != "Mn"
    )


def normalize(text: str) -> str:
    text = strip_accents(text or "")
    return " ".join(text.strip().lower().split())


def money(value: float) -> str:
    s = f"{value:,.2f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


def parse_date_ddmmyyyy(text: str) -> date | None:
    text = normalize(text).replace("-", "/")
    try:
        d, m, y = text.split("/")
        return date(int(y), int(m), int(d))
    except Exception:
        return None


TRANSACTIONS = [
    {
        "date": date(2026, 3, 2),
        "type": "debito",
        "description": "IFOOD *PEDIDO",
        "amount": 58.90,
        "category": "Alimentacao",
        "explanation": "Compra em aplicativo de delivery.",
    },
    {
        "date": date(2026, 3, 3),
        "type": "debito",
        "description": "UBER TRIP",
        "amount": 22.40,
        "category": "Transporte",
        "explanation": "Corrida de transporte por aplicativo.",
    },
    {
        "date": date(2026, 3, 4),
        "type": "credito",
        "description": "PIX RECEBIDO ANA",
        "amount": 250.00,
        "category": "Entradas",
        "explanation": "Transferencia recebida via PIX.",
    },
    {
        "date": date(2026, 3, 5),
        "type": "debito",
        "description": "NETFLIX.COM",
        "amount": 39.90,
        "category": "Assinaturas",
        "explanation": "Assinatura recorrente de streaming.",
    },
    {
        "date": date(2026, 3, 6),
        "type": "debito",
        "description": "PGTO ELETR 3421",
        "amount": 49.90,
        "category": "Pagamentos",
        "explanation": "Pagamento eletronico identificado no extrato.",
    },
    {
        "date": date(2026, 2, 18),
        "type": "debito",
        "description": "POSTO SHELL",
        "amount": 210.00,
        "category": "Transporte",
        "explanation": "Abastecimento realizado em posto de combustivel.",
    },
    {
        "date": date(2026, 2, 20),
        "type": "credito",
        "description": "SALARIO EMPRESA X",
        "amount": 6300.00,
        "category": "Entradas",
        "explanation": "Credito referente ao pagamento de salario.",
    },
    {
        "date": date(2026, 2, 21),
        "type": "debito",
        "description": "DDA ENERGIA",
        "amount": 184.55,
        "category": "Contas",
        "explanation": "Debito referente ao pagamento de conta de energia.",
    },
    {
        "date": date(2026, 2, 23),
        "type": "debito",
        "description": "SPOTIFY",
        "amount": 21.90,
        "category": "Assinaturas",
        "explanation": "Assinatura mensal de musica.",
    },
]

TODAY = date(2026, 3, 8)


class ChatLogger:
    def __init__(self, base_dir: str = "logs") -> None:
        Path(base_dir).mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.path = Path(base_dir) / f"chatbot_parte01_{stamp}.txt"
        self.path.write_text(
            "TP1 - Chatbot Parte 01 (Log)\n"
            f"Inicio: {datetime.now().isoformat(sep=' ', timespec='seconds')}\n"
            "--------------------------------------------------\n",
            encoding="utf-8",
        )

    def log_turn(self, flow: str, user_msg: str, bot_msg: str) -> None:
        ts = datetime.now().isoformat(sep=" ", timespec="seconds")
        line = f"[{ts}] (flow={flow}) USER: {user_msg} | BOT: {bot_msg.replace(chr(10), ' \\n ')}\n"
        with self.path.open("a", encoding="utf-8") as f:
            f.write(line)


@dataclass
class BotState:
    running: bool = True
    current_flow: str = "menu"
    step: str = ""
    fallback_count: int = 0
    context: dict = field(default_factory=dict)


def show_menu() -> str:
    return (
        "\n=== MENU PRINCIPAL ===\n"
        "1) Entender um lancamento\n"
        "2) Ver resumo de gastos\n"
        "3) Contestar uma cobranca\n"
        "4) Ajuda\n"
        "Digite o numero da opcao ou escreva o que deseja.\n"
        "Comandos globais: menu, voltar, reiniciar, ajuda, atendente, sair."
    )


def help_message() -> str:
    return (
        "Exemplos do que eu posso fazer:\n"
        "- 'O que e essa cobranca PGTO ELETR 3421?'\n"
        "- 'Quanto eu gastei esse mes?'\n"
        "- 'Nao reconheco essa compra'\n"
        "- 'Quanto gastei com alimentacao?'\n"
        "Digite 'menu' para ver as opcoes principais."
    )


def end_message() -> str:
    return "\nPosso ajudar em mais algo? Digite 'menu' para voltar ao menu ou 'sair' para encerrar."


def human_message() -> str:
    return (
        "Vou simular o redirecionamento para um atendente humano.\n"
        "Protocolo de atendimento: ATD-2026-0001.\n"
        "Enquanto isso, voce pode digitar 'menu' para continuar no autoatendimento."
    )


def fallback(state: BotState) -> str:
    state.fallback_count += 1
    if state.fallback_count == 1:
        return (
            "Desculpe, nao consegui entender sua solicitacao.\n"
            "Voce pode reformular ou escolher uma das opcoes abaixo:\n"
            "1) Entender um lancamento\n"
            "2) Ver resumo de gastos\n"
            "3) Contestar uma cobranca"
        )
    return (
        "Ainda estou com dificuldade para entender. Deseja falar com um atendente?\n"
        "Digite 'sim' ou 'nao'."
    )


def reset_to_menu(state: BotState) -> str:
    state.current_flow = "menu"
    state.step = ""
    state.context.clear()
    state.fallback_count = 0
    return show_menu()


def find_transaction_by_text(text: str):
    t = normalize(text)
    for tx in TRANSACTIONS:
        desc = normalize(tx["description"])
        if desc in t or any(word in t for word in desc.split() if len(word) > 3):
            return tx
    return None


def current_month_range() -> tuple[date, date]:
    start = date(TODAY.year, TODAY.month, 1)
    return start, TODAY


def previous_month_range() -> tuple[date, date]:
    first_this_month = date(TODAY.year, TODAY.month, 1)
    last_prev = first_this_month - timedelta(days=1)
    start_prev = date(last_prev.year, last_prev.month, 1)
    return start_prev, last_prev


def summarize_period(start: date, end: date) -> dict:
    debits = [tx for tx in TRANSACTIONS if start <= tx["date"] <= end and tx["type"] == "debito"]
    credits = [tx for tx in TRANSACTIONS if start <= tx["date"] <= end and tx["type"] == "credito"]
    total_debits = sum(tx["amount"] for tx in debits)
    total_credits = sum(tx["amount"] for tx in credits)

    by_cat: dict[str, float] = {}
    for tx in debits:
        by_cat[tx["category"]] = by_cat.get(tx["category"], 0.0) + tx["amount"]

    top_category = None
    if by_cat:
        top_category = max(by_cat.items(), key=lambda x: x[1])

    return {
        "debits": total_debits,
        "credits": total_credits,
        "balance": total_credits - total_debits,
        "top_category": top_category,
    }


def classify_intent(msg: str) -> str | None:
    msg = normalize(msg)

    explain_keywords = ["cobranca", "debito", "que compra e essa", "lancamento", "pgto", "tarifa", "valor saiu de onde"]
    summary_keywords = ["quanto gastei", "resumo", "saldo do mes", "saldo final", "ultimos 7 dias", "esse mes", "mes passado", "entrou na conta"]
    contest_keywords = ["nao reconheco", "contestar", "fraude", "erro", "compra indevida", "cobranca indevida"]

    if any(k in msg for k in contest_keywords):
        return "contestacao"
    if any(k in msg for k in summary_keywords):
        return "resumo"
    if any(k in msg for k in explain_keywords):
        return "explicar"
    if msg in ("1", "2", "3", "4"):
        return msg
    return None


def flow_explicar(state: BotState, msg: str) -> str:
    msg = normalize(msg)

    if state.step == "":
        state.step = "aguardando_lancamento"
        return (
            "[ENTENDER LANCAMENTO]\n"
            "Informe a descricao do lancamento que deseja entender.\n"
            "Exemplo: PGTO ELETR 3421, NETFLIX, UBER TRIP."
        )

    if state.step == "aguardando_lancamento":
        tx = find_transaction_by_text(msg)
        if not tx:
            return (
                "Nao encontrei esse lancamento na base simulada.\n"
                "Tente informar a descricao principal, por exemplo: NETFLIX ou PGTO ELETR 3421."
            )

        state.context["selected_tx"] = tx
        state.step = "perguntar_contestacao"
        return (
            f"Encontrei o lancamento: {tx['description']} em {tx['date'].strftime('%d/%m/%Y')} no valor de {money(tx['amount'])}.\n"
            f"Explicacao: {tx['explanation']}\n"
            f"Categoria sugerida: {tx['category']}.\n"
            "Deseja contestar essa cobranca? Digite 'sim' ou 'nao'."
        )

    if state.step == "perguntar_contestacao":
        if msg in ("sim", "s"):
            tx = state.context.get("selected_tx")
            state.current_flow = "contestacao"
            state.step = "confirmar_contestacao"
            state.context["selected_tx"] = tx
            return (
                "Certo. Vamos iniciar a contestacao.\n"
                "Voce confirma que nao reconhece essa transacao? Digite 'sim' ou 'nao'."
            )
        if msg in ("nao", "n"):
            return "Tudo bem. Esse foi apenas um detalhamento do lancamento." + end_message()
        return "Por favor, responda com 'sim' ou 'nao'."

    return reset_to_menu(state)


def flow_resumo(state: BotState, msg: str) -> str:
    msg = normalize(msg)

    if state.step == "":
        state.step = "periodo"
        return (
            "[RESUMO DE GASTOS]\n"
            "Qual periodo deseja consultar?\n"
            "1) Este mes\n"
            "2) Mes passado\n"
            "3) Ultimos 7 dias\n"
            "4) Personalizar periodo"
        )

    if state.step == "periodo":
        if msg in ("1", "este mes", "esse mes"):
            state.context["range"] = current_month_range()
        elif msg in ("2", "mes passado"):
            state.context["range"] = previous_month_range()
        elif msg in ("3", "ultimos 7 dias", "ultimos sete dias"):
            state.context["range"] = (TODAY - timedelta(days=6), TODAY)
        elif msg in ("4", "personalizar", "periodo personalizado"):
            state.step = "data_inicial"
            return "Digite a data inicial no formato DD/MM/AAAA."
        else:
            return "Escolha 1, 2, 3 ou 4."

        state.step = "visualizacao"
        return (
            "Deseja visualizar:\n"
            "1) Total de gastos\n"
            "2) Total de entradas\n"
            "3) Ambos"
        )

    if state.step == "data_inicial":
        dt = parse_date_ddmmyyyy(msg)
        if not dt:
            return "Data invalida. Digite a data inicial no formato DD/MM/AAAA."
        state.context["data_inicial"] = dt
        state.step = "data_final"
        return "Agora digite a data final no formato DD/MM/AAAA."

    if state.step == "data_final":
        dt_final = parse_date_ddmmyyyy(msg)
        dt_ini = state.context.get("data_inicial")
        if not dt_final:
            return "Data invalida. Digite a data final no formato DD/MM/AAAA."
        if dt_final < dt_ini:
            return "A data final nao pode ser menor que a data inicial. Digite novamente."
        state.context["range"] = (dt_ini, dt_final)
        state.step = "visualizacao"
        return (
            "Deseja visualizar:\n"
            "1) Total de gastos\n"
            "2) Total de entradas\n"
            "3) Ambos"
        )

    if state.step == "visualizacao":
        if msg not in ("1", "2", "3", "gastos", "entradas", "ambos"):
            return "Escolha 1, 2 ou 3."

        start, end = state.context["range"]
        summary = summarize_period(start, end)
        state.step = "detalhar_categoria"

        lines = [f"Resumo de {start.strftime('%d/%m/%Y')} ate {end.strftime('%d/%m/%Y')}: "]
        if msg in ("1", "gastos"):
            lines.append(f"- Total gasto: {money(summary['debits'])}")
        elif msg in ("2", "entradas"):
            lines.append(f"- Total recebido: {money(summary['credits'])}")
        else:
            lines.append(f"- Total gasto: {money(summary['debits'])}")
            lines.append(f"- Total recebido: {money(summary['credits'])}")
            lines.append(f"- Saldo final: {money(summary['balance'])}")

        if summary["top_category"]:
            cat, value = summary["top_category"]
            lines.append(f"- Maior categoria de gasto: {cat} ({money(value)})")

        lines.append("Deseja ver os detalhes por categoria? Digite 'sim' ou 'nao'.")
        return "\n".join(lines)

    if state.step == "detalhar_categoria":
        if msg in ("sim", "s"):
            start, end = state.context["range"]
            debits = [tx for tx in TRANSACTIONS if start <= tx["date"] <= end and tx["type"] == "debito"]
            if not debits:
                return "Nao houve gastos no periodo selecionado." + end_message()

            by_cat: dict[str, float] = {}
            for tx in debits:
                by_cat[tx["category"]] = by_cat.get(tx["category"], 0.0) + tx["amount"]

            details = ["Detalhes por categoria:"]
            for cat, value in sorted(by_cat.items(), key=lambda x: x[1], reverse=True):
                details.append(f"- {cat}: {money(value)}")
            return "\n".join(details) + end_message()

        if msg in ("nao", "n"):
            return "Tudo bem. Resumo finalizado." + end_message()

        return "Por favor, responda com 'sim' ou 'nao'."

    return reset_to_menu(state)


def generate_protocol() -> str:
    return f"{random.randint(10000, 99999)}"


def flow_contestacao(state: BotState, msg: str) -> str:
    msg = normalize(msg)

    if state.step == "":
        state.step = "confirmar_contestacao"
        return (
            "[CONTESTACAO DE COBRANCA]\n"
            "Voce confirma que nao reconhece essa transacao?\n"
            "Digite 'sim' ou 'nao'."
        )

    if state.step == "confirmar_contestacao":
        if msg in ("nao", "n"):
            return "Tudo bem. Contestacao cancelada." + end_message()
        if msg not in ("sim", "s"):
            return "Por favor, responda com 'sim' ou 'nao'."

        state.step = "tipo_transacao"
        return (
            "A transacao foi realizada com:\n"
            "1) Cartao fisico\n"
            "2) Cartao virtual\n"
            "3) Debito automatico\n"
            "4) Nao sei"
        )

    if state.step == "tipo_transacao":
        protocol = generate_protocol()
        state.context["protocol"] = protocol
        state.step = "bloqueio_temporario"

        if msg in ("1", "cartao fisico"):
            return (
                "Registramos sua contestacao.\n"
                "Orientacao: recomendamos bloqueio preventivo do cartao fisico.\n"
                f"Prazo estimado de analise: ate 7 dias uteis. Protocolo: {protocol}.\n"
                "Deseja bloquear temporariamente seu cartao? Digite 'sim' ou 'nao'."
            )
        if msg in ("2", "cartao virtual"):
            return (
                "Registramos sua contestacao.\n"
                "Orientacao: cancele ou substitua o cartao virtual no app.\n"
                f"Prazo estimado de analise: ate 7 dias uteis. Protocolo: {protocol}.\n"
                "Deseja bloquear temporariamente seu cartao? Digite 'sim' ou 'nao'."
            )
        if msg in ("3", "debito automatico"):
            return (
                "Registramos sua contestacao.\n"
                "Orientacao: recomendamos contato com o estabelecimento e revisao do debito automatico.\n"
                f"Prazo estimado de analise: ate 7 dias uteis. Protocolo: {protocol}.\n"
                "Deseja bloquear temporariamente seu cartao? Digite 'sim' ou 'nao'."
            )
        if msg in ("4", "nao sei"):
            return (
                "Registramos sua contestacao.\n"
                "Como voce nao soube informar o tipo, seguimos com analise padrao.\n"
                f"Prazo estimado de analise: ate 7 dias uteis. Protocolo: {protocol}.\n"
                "Deseja bloquear temporariamente seu cartao? Digite 'sim' ou 'nao'."
            )
        return "Escolha 1, 2, 3 ou 4."

    if state.step == "bloqueio_temporario":
        if msg in ("sim", "s"):
            return (
                "Certo. O bloqueio preventivo deve ser feito em: App > Cartoes > Seguranca > Bloquear cartao.\n"
                f"Seu protocolo continua sendo {state.context.get('protocol', 'N/A')}."
                + end_message()
            )
        if msg in ("nao", "n"):
            return (
                f"Tudo bem. Sua contestacao foi registrada sob o protocolo {state.context.get('protocol', 'N/A')}."
            ) + end_message()
        return "Por favor, responda com 'sim' ou 'nao'."

    return reset_to_menu(state)


def handle_global_commands(state: BotState, msg: str) -> str | None:
    msg = normalize(msg)

    if msg == "sair":
        state.running = False
        return "Encerrando. Obrigado!"
    if msg == "menu":
        return reset_to_menu(state)
    if msg == "reiniciar":
        return reset_to_menu(state)
    if msg == "ajuda":
        return help_message()
    if msg == "atendente":
        return human_message()

    if state.fallback_count >= 2 and msg in ("sim", "s"):
        state.fallback_count = 0
        return human_message()
    if state.fallback_count >= 2 and msg in ("nao", "n"):
        state.fallback_count = 0
        return show_menu()

    return None


def route_to_flow(state: BotState, msg: str) -> str:
    msg_norm = normalize(msg)

    global_reply = handle_global_commands(state, msg_norm)
    if global_reply is not None:
        return global_reply

    if msg_norm == "voltar":
        return reset_to_menu(state)

    if state.current_flow == "menu":
        intent = classify_intent(msg_norm)

        if intent == "1" or intent == "explicar":
            state.current_flow = "explicar"
            state.step = ""
            state.context.clear()
            state.fallback_count = 0
            return flow_explicar(state, "")

        if intent == "2" or intent == "resumo":
            state.current_flow = "resumo"
            state.step = ""
            state.context.clear()
            state.fallback_count = 0
            return flow_resumo(state, "")

        if intent == "3" or intent == "contestacao":
            state.current_flow = "contestacao"
            state.step = ""
            state.context.clear()
            state.fallback_count = 0
            return flow_contestacao(state, "")

        if intent == "4":
            state.fallback_count = 0
            return help_message()

        return fallback(state)

    if state.current_flow == "explicar":
        state.fallback_count = 0
        return flow_explicar(state, msg_norm)

    if state.current_flow == "resumo":
        state.fallback_count = 0
        return flow_resumo(state, msg_norm)

    if state.current_flow == "contestacao":
        state.fallback_count = 0
        return flow_contestacao(state, msg_norm)

    return reset_to_menu(state)


def main() -> None:
    state = BotState()
    logger = ChatLogger()

    print("Chatbot TP1 - Interpretacao de Extrato Bancario (Regras)")
    print(show_menu())

    while state.running:
        user_msg = input("> ")
        bot_reply = route_to_flow(state, user_msg)
        print(bot_reply)
        logger.log_turn(state.current_flow, user_msg, bot_reply)

    print(f"\nLog salvo em: {logger.path.resolve()}")


if __name__ == "__main__":
    main()