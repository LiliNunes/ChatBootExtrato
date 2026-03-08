from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple
import unicodedata

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline


CONFIDENCE_THRESHOLD = 0.60


TRAINING_DATA: List[Tuple[str, str]] = [
    # CONSULTAR_SALDO
    ("quero ver meu saldo", "CONSULTAR_SALDO"),
    ("quanto tenho na conta", "CONSULTAR_SALDO"),
    ("mostrar saldo da conta", "CONSULTAR_SALDO"),
    ("qual meu saldo atual", "CONSULTAR_SALDO"),
    ("quanto tenho disponível", "CONSULTAR_SALDO"),
    ("ver saldo da conta", "CONSULTAR_SALDO"),
    ("saldo da conta corrente", "CONSULTAR_SALDO"),
    ("quanto tenho no banco", "CONSULTAR_SALDO"),
    ("pode mostrar meu saldo", "CONSULTAR_SALDO"),
    ("consultar saldo", "CONSULTAR_SALDO"),
    ("queria olhar meu saldo", "CONSULTAR_SALDO"),
    ("me fala o saldo da conta", "CONSULTAR_SALDO"),
    # BLOQUEAR_CARTAO
    ("perdi meu cartão", "BLOQUEAR_CARTAO"),
    ("roubaram meu cartão", "BLOQUEAR_CARTAO"),
    ("quero bloquear meu cartão", "BLOQUEAR_CARTAO"),
    ("cartão foi perdido", "BLOQUEAR_CARTAO"),
    ("preciso cancelar meu cartão", "BLOQUEAR_CARTAO"),
    ("bloquear cartão agora", "BLOQUEAR_CARTAO"),
    ("cartão foi roubado", "BLOQUEAR_CARTAO"),
    ("cartão desapareceu", "BLOQUEAR_CARTAO"),
    ("bloqueio de cartão", "BLOQUEAR_CARTAO"),
    ("como bloquear cartão", "BLOQUEAR_CARTAO"),
    ("sumiu meu cartão", "BLOQUEAR_CARTAO"),
    ("não acho meu cartão", "BLOQUEAR_CARTAO"),
    # AUMENTAR_LIMITE
    ("quero aumentar meu limite", "AUMENTAR_LIMITE"),
    ("preciso de mais limite", "AUMENTAR_LIMITE"),
    ("aumentar limite do cartão", "AUMENTAR_LIMITE"),
    ("revisar limite", "AUMENTAR_LIMITE"),
    ("solicitar aumento de limite", "AUMENTAR_LIMITE"),
    ("limite do cartão insuficiente", "AUMENTAR_LIMITE"),
    ("pedir aumento de limite", "AUMENTAR_LIMITE"),
    ("mais limite no cartão", "AUMENTAR_LIMITE"),
    ("liberar limite maior", "AUMENTAR_LIMITE"),
    ("atualizar limite", "AUMENTAR_LIMITE"),
    ("limite baixo no cartão", "AUMENTAR_LIMITE"),
    ("preciso elevar meu limite", "AUMENTAR_LIMITE"),
]

SENSITIVE_TERMS = ["senha", "cvv", "token", "codigo de seguranca", "código de segurança"]
FINANCIAL_ADVICE_TERMS = ["qual ação eu compro", "qual acao eu compro", "onde investir", "melhor ação", "melhor acao", "o que comprar hoje para lucrar"]
OUT_OF_DOMAIN_HINTS = ["capital da frança", "capital da franca", "banana azul"]


class IntentClassifier:
    def __init__(self) -> None:
        self.pipeline = Pipeline(
            steps=[
                ("tfidf", TfidfVectorizer(lowercase=True, ngram_range=(1, 2))),
                ("clf", LogisticRegression(max_iter=1000, random_state=42)),
            ]
        )
        texts = [normalize(text) for text, _ in TRAINING_DATA]
        labels = [label for _, label in TRAINING_DATA]
        self.pipeline.fit(texts, labels)

    def predict(self, text: str) -> tuple[str, float]:
        text_n = normalize(text)
        probs = self.pipeline.predict_proba([text_n])[0]
        classes = self.pipeline.classes_
        best_idx = probs.argmax()
        return classes[best_idx], float(probs[best_idx])


def strip_accents(text: str) -> str:
    return "".join(
        ch for ch in unicodedata.normalize("NFD", text)
        if unicodedata.category(ch) != "Mn"
    )


def normalize(text: str) -> str:
    text = strip_accents(text or "")
    return " ".join(text.strip().lower().split())


@dataclass
class BotState:
    running: bool = True
    current_flow: str = "menu"
    step: str = ""
    history: list[str] = field(default_factory=list)


class BankingNLPChatbot:
    def __init__(self) -> None:
        self.state = BotState()
        self.classifier = IntentClassifier()

    def show_welcome(self) -> str:
        return (
            "Chatbot TP3 - Atendimento Financeiro com NLP\n"
            "Modelo: TF-IDF + Logistic Regression\n"
            "Comandos: menu | voltar | reiniciar | sair\n\n"
            f"{self.show_menu()}"
        )

    def show_menu(self) -> str:
        return (
            "MENU PRINCIPAL\n"
            "- Você pode escrever livremente, por exemplo:\n"
            "  • 'quero ver meu saldo'\n"
            "  • 'perdi meu cartão'\n"
            "  • 'quero aumentar meu limite'\n"
            "- Ou usar os comandos: menu, voltar, reiniciar, sair"
        )

    def handle_input(self, user_text: str) -> str:
        text = normalize(user_text)
        self.state.history.append(text)

        global_response = self.handle_global_commands(text)
        if global_response is not None:
            return global_response

        guardrail_response = self.apply_guardrails(text)
        if guardrail_response is not None:
            return guardrail_response

        if self.state.current_flow == "SALDO":
            return self.flow_saldo(text)
        if self.state.current_flow == "BLOQUEIO":
            return self.flow_bloqueio(text)
        if self.state.current_flow == "LIMITE":
            return self.flow_limite(text)

        intent, confidence = self.classifier.predict(text)
        if confidence < CONFIDENCE_THRESHOLD:
            return (
                "Desculpe, não entendi sua solicitação.\n"
                f"Confiança do classificador: {confidence:.2f}\n"
                "Pode reformular ou digitar 'menu'?"
            )

        if intent == "CONSULTAR_SALDO":
            self.state.current_flow = "SALDO"
            self.state.step = "tipo_conta"
            return (
                f"Intenção detectada: {intent}\n"
                f"Confiança: {confidence:.2f}\n"
                "Você quer consultar saldo de:\n"
                "A) Conta corrente\n"
                "B) Poupança"
            )

        if intent == "BLOQUEAR_CARTAO":
            self.state.current_flow = "BLOQUEIO"
            self.state.step = "motivo"
            return (
                f"Intenção detectada: {intent}\n"
                f"Confiança: {confidence:.2f}\n"
                "Seu cartão foi:\n"
                "1) Perdido\n"
                "2) Roubado"
            )

        if intent == "AUMENTAR_LIMITE":
            self.state.current_flow = "LIMITE"
            self.state.step = "tipo_limite"
            return (
                f"Intenção detectada: {intent}\n"
                f"Confiança: {confidence:.2f}\n"
                "Qual tipo de limite você quer tratar?\n"
                "1) Cartão\n"
                "2) Transferência"
            )

        return "Desculpe, não consegui direcionar sua solicitação. Digite 'menu'."

    def handle_global_commands(self, text: str) -> str | None:
        if text == "sair":
            self.state.running = False
            return "Encerrando atendimento. Obrigado!"
        if text == "menu":
            self.state.current_flow = "menu"
            self.state.step = ""
            return self.show_menu()
        if text == "reiniciar":
            self.state = BotState()
            return "Conversa reiniciada com sucesso.\n\n" + self.show_menu()
        if text == "voltar":
            return self.go_back_one_step()
        return None

    def go_back_one_step(self) -> str:
        if self.state.current_flow == "SALDO":
            if self.state.step == "tipo_saldo":
                self.state.step = "tipo_conta"
                return "Voltando uma etapa...\nA) Conta corrente\nB) Poupança"
            self.state.current_flow = "menu"
            self.state.step = ""
            return "Voltando ao menu principal.\n\n" + self.show_menu()

        if self.state.current_flow == "BLOQUEIO":
            if self.state.step == "tipo_bloqueio":
                self.state.step = "motivo"
                return "Voltando uma etapa...\n1) Perdido\n2) Roubado"
            if self.state.step == "confirmacao":
                self.state.step = "tipo_bloqueio"
                return "Voltando uma etapa...\nA) Temporariamente\nB) Definitivamente"
            self.state.current_flow = "menu"
            self.state.step = ""
            return "Voltando ao menu principal.\n\n" + self.show_menu()

        if self.state.current_flow == "LIMITE":
            if self.state.step == "modalidade":
                self.state.step = "tipo_limite"
                return "Voltando uma etapa...\n1) Cartão\n2) Transferência"
            if self.state.step == "confirmacao":
                self.state.step = "modalidade"
                return "Voltando uma etapa...\nA) Temporário\nB) Revisão permanente"
            self.state.current_flow = "menu"
            self.state.step = ""
            return "Voltando ao menu principal.\n\n" + self.show_menu()

        return "Você já está no menu principal."

    def apply_guardrails(self, text: str) -> str | None:
        if any(term in text for term in SENSITIVE_TERMS):
            return (
                "Por segurança, não posso processar senha, CVV, token ou outros dados sensíveis.\n"
                "Remova essas informações e faça a solicitação novamente."
            )

        if any(term in text for term in FINANCIAL_ADVICE_TERMS):
            return (
                "Não posso recomendar investimento personalizado ou dizer qual ativo comprar.\n"
                "Posso explicar conceitos gerais de risco, diversificação e tipos de investimento."
            )

        if any(term in text for term in OUT_OF_DOMAIN_HINTS):
            return (
                "Essa solicitação está fora do domínio deste chatbot financeiro.\n"
                "Digite 'menu' para ver os atendimentos disponíveis."
            )
        return None

    def flow_saldo(self, text: str) -> str:
        if self.state.step == "tipo_conta":
            if text in ("a", "corrente", "conta corrente"):
                self.state.step = "tipo_saldo"
                return "Você deseja consultar:\n1) Saldo disponível\n2) Saldo completo"
            if text in ("b", "poupanca", "poupança"):
                self.state.step = "tipo_saldo"
                return "Você deseja consultar:\n1) Saldo disponível\n2) Saldo completo"
            return "Escolha A) Conta corrente ou B) Poupança."

        if self.state.step == "tipo_saldo":
            if text == "1":
                self.state.current_flow = "menu"
                self.state.step = ""
                return (
                    "Para consultar o saldo disponível, acesse o app ou site oficial do banco, na área de conta.\n"
                    "Este chatbot não exibe valores reais.\n\n" + self.show_menu()
                )
            if text == "2":
                self.state.current_flow = "menu"
                self.state.step = ""
                return (
                    "Para consultar o saldo completo, acesse o app ou site oficial do banco, na área de extrato e saldo.\n"
                    "Este chatbot não inventa números nem acessa sua conta.\n\n" + self.show_menu()
                )
            return "Escolha 1) Saldo disponível ou 2) Saldo completo."

        return self.show_menu()

    def flow_bloqueio(self, text: str) -> str:
        if self.state.step == "motivo":
            if text in ("1", "perdido"):
                self.state.step = "tipo_bloqueio"
                return "Como deseja bloquear?\nA) Temporariamente\nB) Definitivamente"
            if text in ("2", "roubado"):
                self.state.step = "tipo_bloqueio"
                return "Como deseja bloquear?\nA) Temporariamente\nB) Definitivamente"
            return "Escolha 1) Perdido ou 2) Roubado."

        if self.state.step == "tipo_bloqueio":
            if text in ("a", "temporariamente", "temporario", "temporário"):
                self.state.step = "confirmacao"
                return "Confirma o bloqueio temporário? (sim/não)"
            if text in ("b", "definitivamente", "definitivo"):
                self.state.step = "confirmacao"
                return "Confirma o bloqueio definitivo? (sim/não)"
            return "Escolha A) Temporariamente ou B) Definitivamente."

        if self.state.step == "confirmacao":
            if text in ("sim", "s"):
                self.state.current_flow = "menu"
                self.state.step = ""
                return (
                    "Solicitação registrada. Para concluir, acesse o app ou canal oficial do banco na área de cartões e segurança.\n"
                    "Se houver suspeita de fraude, procure atendimento humano imediatamente.\n\n" + self.show_menu()
                )
            if text in ("nao", "não", "n"):
                self.state.current_flow = "menu"
                self.state.step = ""
                return "Operação cancelada pelo usuário.\n\n" + self.show_menu()
            return "Responda com 'sim' ou 'não'."

        return self.show_menu()

    def flow_limite(self, text: str) -> str:
        if self.state.step == "tipo_limite":
            if text == "1":
                self.state.step = "modalidade"
                return "Você quer:\nA) Aumento temporário\nB) Revisão permanente"
            if text == "2":
                self.state.step = "modalidade"
                return "Você quer:\nA) Ajuste temporário\nB) Revisão permanente"
            return "Escolha 1) Cartão ou 2) Transferência."

        if self.state.step == "modalidade":
            if text in ("a", "temporario", "temporário"):
                self.state.step = "confirmacao"
                return "Confirma a solicitação de ajuste temporário? (sim/não)"
            if text in ("b", "revisao permanente", "revisão permanente", "permanente"):
                self.state.step = "confirmacao"
                return "Confirma a solicitação de revisão permanente? (sim/não)"
            return "Escolha A) Temporário ou B) Revisão permanente."

        if self.state.step == "confirmacao":
            if text in ("sim", "s"):
                self.state.current_flow = "menu"
                self.state.step = ""
                return (
                    "Para solicitar aumento de limite, acesse o app do banco e verifique a seção de limites.\n"
                    "O banco poderá analisar renda, histórico e perfil de uso antes da aprovação.\n\n" + self.show_menu()
                )
            if text in ("nao", "não", "n"):
                self.state.current_flow = "menu"
                self.state.step = ""
                return "Solicitação cancelada.\n\n" + self.show_menu()
            return "Responda com 'sim' ou 'não'."

        return self.show_menu()


def main() -> None:
    bot = BankingNLPChatbot()
    print(bot.show_welcome())
    while bot.state.running:
        user_text = input("\nVocê: ")
        response = bot.handle_input(user_text)
        print(f"Bot: {response}")


if __name__ == "__main__":
    main()
