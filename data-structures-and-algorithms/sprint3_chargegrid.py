#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""ChargeGrid Intelligence - Sprint 3 com interface gráfica."""

import tkinter as tk
from dataclasses import dataclass, field
from datetime import datetime
from math import isfinite
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText


TARIFA_BASE = 0.805
TIPOS_USUARIO = ("Comum", "Assinante", "Frota", "Visitante")
FATORES_USUARIO = {
    "Comum": 1.00,
    "Assinante": 0.90,
    "Frota": 0.95,
    "Visitante": 1.00,
}
TIPOS_CARREGADOR = {
    "Tipo 2 - AC 7,4 kW": 7.4,
    "Tipo 2 - AC 11 kW": 11.0,
    "Tipo 2 - AC 22 kW": 22.0,
    "CCS2 - DC 50 kW": 50.0,
}
CRITERIOS_ORDENACAO = {
    "ID": "id",
    "Energia consumida": "energia",
    "Custo da sessão": "custo",
    "Tempo de recarga": "tempo",
}

CENARIOS_SIMULACAO = (
    "Operação urbana",
    "Pico de demanda",
    "Frota corporativa",
)

VEICULOS_SIMULACAO = (
    ("BYD Dolphin", "Tipo 2 - AC 11 kW", "Assinante", 0.91, 52),
    ("Volvo EX30", "CCS2 - DC 50 kW", "Comum", 0.88, 34),
    ("Renault Kwid E-Tech", "Tipo 2 - AC 7,4 kW", "Comum", 0.94, 68),
    ("GWM Ora 03", "Tipo 2 - AC 22 kW", "Assinante", 0.82, 46),
    ("Chevrolet Bolt", "CCS2 - DC 50 kW", "Visitante", 0.76, 29),
    ("Nissan Leaf", "Tipo 2 - AC 11 kW", "Frota", 0.86, 61),
    ("Fiat 500e", "Tipo 2 - AC 22 kW", "Comum", 0.79, 42),
    ("JAC E-JS1", "Tipo 2 - AC 7,4 kW", "Assinante", 0.89, 74),
)

ESTACOES_SIMULACAO = (
    "Hub Centro",
    "Estação Paulista",
    "ChargeGrid Norte",
    "Shopping Sul",
)

# Cada valor representa a quantidade física de pontos que podem recarregar
# simultaneamente naquela estação. Veículos excedentes aguardam em fila.
CAPACIDADE_ESTACOES = {
    "Hub Centro": 1,
    "Estação Paulista": 1,
    "ChargeGrid Norte": 1,
    "Shopping Sul": 1,
    "Pátio Corporativo 1": 2,
    "Pátio Corporativo 2": 2,
}

STATUS_SESSAO = ("Na fila", "Ativa", "Finalizada")


@dataclass
class SessaoRecarga:
    """Representa uma sessão armazenada pela estação de recarga."""

    id_sessao: int
    veiculo: str
    tipo_carregador: str
    tipo_usuario: str
    potencia_kw: float
    tempo_minutos: int
    hora_inicio: int
    energia_kwh: float
    tarifa_kwh: float
    custo: float
    status: str = "Finalizada"
    estacao: str = "Hub Central"
    origem: str = "Cadastro manual"
    tempo_restante_minutos: int = 0
    data_registro: str = field(
        default_factory=lambda: datetime.now().strftime("%d/%m/%Y")
    )

    def detalhes(self) -> str:
        """Retorna os dados da sessão em um texto formatado."""

        tempo_decorrido = self.tempo_minutos - self.tempo_restante_minutos
        if self.status == "Na fila":
            andamento = (
                "Progresso: aguardando um carregador disponível\n"
                f"Tempo previsto: {self.tempo_minutos} minutos\n"
            )
        elif self.status == "Ativa":
            andamento = (
                f"Tempo decorrido: {tempo_decorrido} minutos\n"
                f"Tempo restante: {self.tempo_restante_minutos} minutos\n"
            )
        else:
            andamento = f"Tempo de recarga: {self.tempo_minutos} minutos\n"

        em_andamento_simulado = (
            self.origem.startswith("Simulação") and self.status != "Finalizada"
        )
        rotulo_energia = (
            "Energia fornecida" if em_andamento_simulado else "Energia consumida"
        )
        rotulo_custo = (
            "Custo acumulado" if em_andamento_simulado else "Custo da sessão"
        )

        return (
            f"SESSÃO #{self.id_sessao}\n"
            f"{'=' * 48}\n"
            f"Veículo: {self.veiculo}\n"
            f"Estação: {self.estacao}\n"
            f"Carregador: {self.tipo_carregador}\n"
            f"Tipo de usuário: {self.tipo_usuario}\n"
            f"Data do registro: {self.data_registro}\n"
            f"Horário de início: {self.hora_inicio:02d}:00\n"
            f"Potência utilizada: {self.potencia_kw:.2f} kW\n"
            f"{andamento}"
            f"{rotulo_energia}: {self.energia_kwh:.2f} kWh\n"
            f"Tarifa aplicada: R$ {self.tarifa_kwh:.3f}/kWh\n"
            f"{rotulo_custo}: R$ {self.custo:.2f}\n"
            f"Status: {self.status}\n"
            f"Origem: {self.origem}"
        )


def calcular_tarifa(tipo_usuario: str, hora_inicio: int, potencia_kw: float) -> float:
    """Calcula a tarifa por horário, perfil de usuário e potência."""

    tarifa = TARIFA_BASE

    if 18 <= hora_inicio <= 21:
        tarifa *= 1.20

    tarifa *= FATORES_USUARIO[tipo_usuario]

    if potencia_kw > 11:
        tarifa *= 1.10

    return round(tarifa, 3)


def obter_proximo_id(sessoes: list[SessaoRecarga]) -> int:
    """Retorna um ID livre mesmo quando a lista foi reordenada ou filtrada."""

    maior_id = 0
    for sessao in sessoes:
        if sessao.id_sessao > maior_id:
            maior_id = sessao.id_sessao
    return maior_id + 1


def criar_sessao_calculada(
    id_sessao: int,
    veiculo: str,
    tipo_carregador: str,
    tipo_usuario: str,
    potencia_kw: float,
    tempo_minutos: int,
    hora_inicio: int,
    status: str = "Finalizada",
    estacao: str = "Hub Central",
    origem: str = "Cadastro manual",
) -> SessaoRecarga:
    """Cria uma sessão aplicando as mesmas regras a dados manuais e simulados."""

    if id_sessao <= 0:
        raise ValueError("O ID deve ser maior que zero.")
    if not veiculo.strip():
        raise ValueError("A identificação do veículo é obrigatória.")
    if tipo_carregador not in TIPOS_CARREGADOR:
        raise ValueError("Tipo de carregador inválido.")
    if tipo_usuario not in TIPOS_USUARIO:
        raise ValueError("Tipo de usuário inválido.")
    if status not in STATUS_SESSAO:
        raise ValueError("Status inválido.")
    if (
        not isfinite(potencia_kw)
        or potencia_kw <= 0
        or potencia_kw > TIPOS_CARREGADOR[tipo_carregador]
    ):
        raise ValueError("Potência incompatível com o carregador.")
    if tempo_minutos <= 0:
        raise ValueError("O tempo deve ser maior que zero.")
    if hora_inicio not in range(24):
        raise ValueError("A hora deve estar entre 0 e 23.")

    energia_kwh = potencia_kw * (tempo_minutos / 60)
    tarifa_kwh = calcular_tarifa(tipo_usuario, hora_inicio, potencia_kw)
    return SessaoRecarga(
        id_sessao=id_sessao,
        veiculo=veiculo,
        tipo_carregador=tipo_carregador,
        tipo_usuario=tipo_usuario,
        potencia_kw=potencia_kw,
        tempo_minutos=tempo_minutos,
        hora_inicio=hora_inicio,
        energia_kwh=round(energia_kwh, 3),
        tarifa_kwh=tarifa_kwh,
        custo=round(energia_kwh * tarifa_kwh, 2),
        status=status,
        estacao=estacao,
        origem=origem,
        tempo_restante_minutos=(
            0 if status == "Finalizada" else tempo_minutos
        ),
    )


def _sessao_e_simulada(sessao: SessaoRecarga) -> bool:
    return sessao.origem.startswith("Simulação")


def obter_capacidade_estacao(estacao: str) -> int:
    """Retorna a quantidade finita de carregadores de uma estação."""

    return CAPACIDADE_ESTACOES.get(estacao, 1)


def promover_fila_simulacao(sessoes: list[SessaoRecarga]) -> int:
    """Ocupa vagas livres respeitando a ordem FIFO estável pelo ID."""

    estacoes: list[str] = []
    for sessao in sessoes:
        if _sessao_e_simulada(sessao) and sessao.estacao not in estacoes:
            estacoes.append(sessao.estacao)

    promovidas = 0
    for estacao in estacoes:
        quantidade_ativa = 0
        for sessao in sessoes:
            if (
                _sessao_e_simulada(sessao)
                and sessao.estacao == estacao
                and sessao.status == "Ativa"
            ):
                quantidade_ativa += 1

        while quantidade_ativa < obter_capacidade_estacao(estacao):
            primeira_da_fila: SessaoRecarga | None = None
            for sessao in sessoes:
                if (
                    _sessao_e_simulada(sessao)
                    and sessao.estacao == estacao
                    and sessao.status == "Na fila"
                    and (
                        primeira_da_fila is None
                        or sessao.id_sessao < primeira_da_fila.id_sessao
                    )
                ):
                    primeira_da_fila = sessao

            if primeira_da_fila is None:
                break
            primeira_da_fila.status = "Ativa"
            if primeira_da_fila.tempo_restante_minutos <= 0:
                primeira_da_fila.tempo_restante_minutos = (
                    primeira_da_fila.tempo_minutos
                )
            quantidade_ativa += 1
            promovidas += 1

    return promovidas


def _atualizar_consumo_simulado(sessao: SessaoRecarga) -> None:
    tempo_decorrido = sessao.tempo_minutos - sessao.tempo_restante_minutos
    energia = sessao.potencia_kw * (tempo_decorrido / 60)
    sessao.energia_kwh = round(energia, 3)
    sessao.custo = round(energia * sessao.tarifa_kwh, 2)


def avancar_tempo_simulacao(
    sessoes: list[SessaoRecarga],
    minutos: int,
) -> dict[str, int]:
    """Avança todas as estações em paralelo e libera vagas imediatamente."""

    if not isinstance(minutos, int) or isinstance(minutos, bool) or minutos <= 0:
        raise ValueError("O avanço deve ser um número inteiro positivo de minutos.")

    finalizadas = 0
    iniciadas = 0
    for sessao in sessoes:
        if (
            _sessao_e_simulada(sessao)
            and sessao.status == "Ativa"
            and sessao.tempo_restante_minutos <= 0
        ):
            sessao.tempo_restante_minutos = 0
            sessao.status = "Finalizada"
            _atualizar_consumo_simulado(sessao)
            finalizadas += 1
    iniciadas += promover_fila_simulacao(sessoes)

    for _minuto in range(minutos):
        ativas = [
            sessao
            for sessao in sessoes
            if _sessao_e_simulada(sessao) and sessao.status == "Ativa"
        ]
        if not ativas:
            break

        for sessao in ativas:
            sessao.tempo_restante_minutos -= 1
            _atualizar_consumo_simulado(sessao)

        for sessao in ativas:
            if sessao.tempo_restante_minutos <= 0:
                sessao.tempo_restante_minutos = 0
                sessao.status = "Finalizada"
                finalizadas += 1

        iniciadas += promover_fila_simulacao(sessoes)

    return {
        "minutos": minutos,
        "finalizadas": finalizadas,
        "iniciadas": iniciadas,
    }


def calcular_ocupacao_simulacao(
    sessoes: list[SessaoRecarga],
) -> dict[str, int]:
    """Resume a capacidade física usada pelas sessões simuladas."""

    estacoes: list[str] = []
    ativas = 0
    na_fila = 0
    for sessao in sessoes:
        if not _sessao_e_simulada(sessao):
            continue
        if sessao.estacao not in estacoes:
            estacoes.append(sessao.estacao)
        if sessao.status == "Ativa":
            ativas += 1
        elif sessao.status == "Na fila":
            na_fila += 1

    if any(estacao in ESTACOES_SIMULACAO for estacao in estacoes):
        for estacao in ESTACOES_SIMULACAO:
            if estacao not in estacoes:
                estacoes.append(estacao)
    if any(estacao.startswith("Pátio Corporativo") for estacao in estacoes):
        for estacao in ("Pátio Corporativo 1", "Pátio Corporativo 2"):
            if estacao not in estacoes:
                estacoes.append(estacao)

    capacidade = 0
    for estacao in estacoes:
        capacidade += obter_capacidade_estacao(estacao)
    return {
        "ativas": ativas,
        "fila": na_fila,
        "capacidade": capacidade,
    }


def gerar_lote_simulacao(
    sessoes_existentes: list[SessaoRecarga],
    quantidade: int = 5,
    cenario: str = CENARIOS_SIMULACAO[0],
    hora_atual: int | None = None,
) -> list[SessaoRecarga]:
    """Monta um lote determinístico de veículos para demonstração da aplicação."""

    if quantidade <= 0:
        return []
    if cenario not in CENARIOS_SIMULACAO:
        raise ValueError("Cenário de simulação inválido.")
    if hora_atual is not None and hora_atual not in range(24):
        raise ValueError("Hora de referência inválida.")

    primeiro_id = obter_proximo_id(sessoes_existentes)
    hora_referencia = datetime.now().hour if hora_atual is None else hora_atual
    lote: list[SessaoRecarga] = []
    ocupacao_por_estacao: dict[str, int] = {}
    estacoes_com_fila: set[str] = set()
    for sessao in sessoes_existentes:
        if not _sessao_e_simulada(sessao):
            continue
        if sessao.status == "Ativa":
            ocupacao_por_estacao[sessao.estacao] = (
                ocupacao_por_estacao.get(sessao.estacao, 0) + 1
            )
        elif sessao.status == "Na fila":
            estacoes_com_fila.add(sessao.estacao)

    for indice in range(quantidade):
        modelo, carregador, usuario, fator_potencia, tempo_base = (
            VEICULOS_SIMULACAO[indice % len(VEICULOS_SIMULACAO)]
        )
        id_sessao = primeiro_id + indice
        estacao = ESTACOES_SIMULACAO[indice % len(ESTACOES_SIMULACAO)]
        tempo = tempo_base
        hora = (hora_referencia - indice) % 24

        if cenario == "Pico de demanda":
            hora = 18 + (indice % 4)
            tempo = max(20, tempo_base - 8)
        elif cenario == "Frota corporativa":
            usuario = "Frota"
            hora = 7 + (indice % 5)
            estacao = f"Pátio Corporativo {1 + (indice % 2)}"

        ocupadas = ocupacao_por_estacao.get(estacao, 0)
        if (
            estacao not in estacoes_com_fila
            and ocupadas < obter_capacidade_estacao(estacao)
        ):
            status = "Ativa"
            ocupacao_por_estacao[estacao] = ocupadas + 1
        else:
            status = "Na fila"
            estacoes_com_fila.add(estacao)

        potencia = round(TIPOS_CARREGADOR[carregador] * fator_potencia, 1)
        sessao = criar_sessao_calculada(
            id_sessao=id_sessao,
            veiculo=f"{modelo} · SIM-{id_sessao:03d}",
            tipo_carregador=carregador,
            tipo_usuario=usuario,
            potencia_kw=potencia,
            tempo_minutos=tempo,
            hora_inicio=hora,
            status=status,
            estacao=estacao,
            origem=f"Simulação · {cenario}",
        )
        sessao.energia_kwh = 0.0
        sessao.custo = 0.0
        lote.append(sessao)

    return lote


def busca_sequencial(sessoes: list[SessaoRecarga], id_procurado: int) -> int:
    """Retorna a posição da sessão ou -1.

    No pior caso, percorre toda a lista. Complexidade: O(n).
    """

    for indice in range(len(sessoes)):
        if sessoes[indice].id_sessao == id_procurado:
            return indice

    return -1


def obter_chave_ordenacao(sessao: SessaoRecarga, criterio: str) -> int | float:
    """Retorna o atributo comparado pelo Bubble Sort."""

    if criterio == "id":
        return sessao.id_sessao
    if criterio == "energia":
        return sessao.energia_kwh
    if criterio == "custo":
        return sessao.custo
    if criterio == "tempo":
        return sessao.tempo_minutos
    raise ValueError("Critério de ordenação inválido.")


def bubble_sort(
    sessoes: list[SessaoRecarga],
    criterio: str,
    crescente: bool = True,
) -> None:
    """Ordena a lista manualmente sem funções prontas de ordenação.

    No pior caso, os dois laços percorrem a lista. Complexidade: O(n²).
    """

    quantidade = len(sessoes)

    for passagem in range(quantidade - 1):
        houve_troca = False

        for indice in range(quantidade - 1 - passagem):
            valor_atual = obter_chave_ordenacao(sessoes[indice], criterio)
            proximo_valor = obter_chave_ordenacao(sessoes[indice + 1], criterio)

            fora_de_ordem = (
                valor_atual > proximo_valor
                if crescente
                else valor_atual < proximo_valor
            )

            if fora_de_ordem:
                sessoes[indice], sessoes[indice + 1] = (
                    sessoes[indice + 1],
                    sessoes[indice],
                )
                houve_troca = True

        if not houve_troca:
            break


def calcular_estatisticas(sessoes: list[SessaoRecarga]) -> dict[str, object] | None:
    """Calcula os indicadores a partir das sessões da lista."""

    if not sessoes:
        return None

    energia_total = 0.0
    faturamento_total = 0.0
    maior_consumo = sessoes[0]
    menor_consumo = sessoes[0]

    for sessao in sessoes:
        energia_total += sessao.energia_kwh
        faturamento_total += sessao.custo

        if sessao.energia_kwh > maior_consumo.energia_kwh:
            maior_consumo = sessao
        if sessao.energia_kwh < menor_consumo.energia_kwh:
            menor_consumo = sessao

    return {
        "quantidade": len(sessoes),
        "energia_total": energia_total,
        "faturamento_total": faturamento_total,
        "custo_medio": faturamento_total / len(sessoes),
        "maior_consumo": maior_consumo,
        "menor_consumo": menor_consumo,
    }


def gerar_relatorio_texto(sessoes: list[SessaoRecarga]) -> str:
    """Gera um relatório com sessões, estatísticas e algoritmos."""

    linhas = [
        "RELATÓRIO GERAL - CHARGEGRID INTELLIGENCE",
        "=" * 72,
        f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
        f"Quantidade de sessões armazenadas: {len(sessoes)}",
        "",
        "SESSÕES",
        "-" * 72,
    ]

    if not sessoes:
        linhas.append("Nenhuma sessão cadastrada.")
    else:
        for sessao in sessoes:
            em_andamento_simulado = (
                _sessao_e_simulada(sessao) and sessao.status != "Finalizada"
            )
            rotulo_energia = (
                "Energia fornecida" if em_andamento_simulado else "Energia"
            )
            rotulo_custo = (
                "Custo acumulado" if em_andamento_simulado else "Custo"
            )
            linhas.extend(
                [
                    f"ID: {sessao.id_sessao}",
                    f"Veículo: {sessao.veiculo}",
                    f"Estação: {sessao.estacao}",
                    f"Usuário: {sessao.tipo_usuario}",
                    f"Carregador: {sessao.tipo_carregador}",
                    f"Potência: {sessao.potencia_kw:.2f} kW",
                    f"Tempo: {sessao.tempo_minutos} minutos",
                    f"Tempo restante: {sessao.tempo_restante_minutos} minutos",
                    f"{rotulo_energia}: {sessao.energia_kwh:.2f} kWh",
                    f"Tarifa: R$ {sessao.tarifa_kwh:.3f}/kWh",
                    f"{rotulo_custo}: R$ {sessao.custo:.2f}",
                    f"Status: {sessao.status}",
                    f"Origem: {sessao.origem}",
                    "-" * 72,
                ]
            )

    estatisticas = calcular_estatisticas(sessoes)
    linhas.extend(["", "ESTATÍSTICAS", "-" * 72])

    if estatisticas is None:
        linhas.append("Não existem dados para calcular estatísticas.")
    else:
        maior = estatisticas["maior_consumo"]
        menor = estatisticas["menor_consumo"]
        linhas.extend(
            [
                f"Sessões realizadas: {estatisticas['quantidade']}",
                f"Energia total fornecida: {estatisticas['energia_total']:.2f} kWh",
                f"Faturamento total: R$ {estatisticas['faturamento_total']:.2f}",
                f"Custo médio: R$ {estatisticas['custo_medio']:.2f}",
                f"Maior consumo: {maior.energia_kwh:.2f} kWh (sessão #{maior.id_sessao})",
                f"Menor consumo: {menor.energia_kwh:.2f} kWh (sessão #{menor.id_sessao})",
            ]
        )

    linhas.extend(
        [
            "",
            "ALGORITMOS UTILIZADOS",
            "-" * 72,
            "Busca Sequencial: O(n) no pior caso.",
            "Bubble Sort: O(n²) no pior caso.",
        ]
    )
    return "\n".join(linhas)


class ChargeGridApp(tk.Tk):
    """Janela principal da aplicação."""

    COR_FUNDO = "#101411"
    COR_MENU = "#151A17"
    COR_CARD = "#1B211D"
    COR_CARD_CLARO = "#222A25"
    COR_CAMPO = "#121713"
    COR_VERDE = "#3ECF8E"
    COR_VERDE_ESCURO = "#249D6D"
    COR_VERDE_SUAVE = "#173B2C"
    COR_AZUL = "#6EE7D8"
    COR_TEXTO = "#F2F5F3"
    COR_TEXTO_FRACO = "#9BA89F"
    COR_BORDA = "#303A33"
    COR_ERRO = "#FB7185"
    COR_ALERTA = "#FBBF24"

    TITULOS_TELA = {
        "cadastro": "Nova sessão de recarga",
        "simulacao": "Central de simulação",
        "sessoes": "Sessões armazenadas",
        "busca": "Buscar sessão",
        "ordenacao": "Ordenar sessões",
        "estatisticas": "Estatísticas da estação",
        "relatorio": "Relatório geral",
    }

    SUBTITULOS_TELA = {
        "cadastro": "Cadastre uma recarga com cálculos e identificador automáticos.",
        "simulacao": "Gere uma operação completa com veículos, estações e status variados.",
        "sessoes": "Acompanhe todos os registros manuais e simulados em um só lugar.",
        "busca": "Localize rapidamente um registro pelo algoritmo de busca sequencial.",
        "ordenacao": "Compare os dados usando a implementação manual do Bubble Sort.",
        "estatisticas": "Visualize os principais indicadores da operação de recarga.",
        "relatorio": "Exporte uma visão consolidada das sessões e dos algoritmos.",
    }

    def __init__(self) -> None:
        super().__init__()
        self.sessoes: list[SessaoRecarga] = []
        self.telas: dict[str, tk.Frame] = {}
        self.botoes_menu: dict[str, tk.Button] = {}
        self.tela_atual = ""
        self.tempo_simulado_minutos = 0
        self.simulacao_automatica = False
        self.timer_simulacao = None

        self.title("ChargeGrid Intelligence - Sprint 3")
        self.geometry("1280x800")
        self.minsize(1080, 700)
        self.configure(bg=self.COR_FUNDO)

        self._configurar_estilos()
        self._construir_layout()
        self._criar_telas()
        self.mostrar_tela("cadastro")

    def _configurar_estilos(self) -> None:
        estilo = ttk.Style(self)
        try:
            estilo.theme_use("clam")
        except tk.TclError:
            pass

        estilo.configure(
            "ChargeGrid.TCombobox",
            fieldbackground=self.COR_CAMPO,
            background=self.COR_CARD_CLARO,
            foreground=self.COR_TEXTO,
            arrowcolor=self.COR_TEXTO,
            bordercolor=self.COR_BORDA,
            lightcolor=self.COR_BORDA,
            darkcolor=self.COR_BORDA,
            padding=8,
            font=("Segoe UI", 10),
        )
        estilo.map(
            "ChargeGrid.TCombobox",
            fieldbackground=[("readonly", self.COR_CAMPO)],
            foreground=[("readonly", self.COR_TEXTO)],
            selectbackground=[("readonly", self.COR_CAMPO)],
            selectforeground=[("readonly", self.COR_TEXTO)],
        )
        estilo.configure(
            "ChargeGrid.Treeview",
            background=self.COR_CAMPO,
            fieldbackground=self.COR_CAMPO,
            foreground=self.COR_TEXTO,
            rowheight=34,
            borderwidth=0,
            font=("Segoe UI", 9),
        )
        estilo.map(
            "ChargeGrid.Treeview",
            background=[("selected", self.COR_VERDE_ESCURO)],
            foreground=[("selected", "#FFFFFF")],
        )
        estilo.configure(
            "ChargeGrid.Treeview.Heading",
            background=self.COR_CARD_CLARO,
            foreground=self.COR_TEXTO,
            relief="flat",
            padding=10,
            font=("Segoe UI", 9, "bold"),
        )
        estilo.map(
            "ChargeGrid.Treeview.Heading",
            background=[("active", self.COR_BORDA)],
        )
        estilo.configure(
            "ChargeGrid.Vertical.TScrollbar",
            background=self.COR_CARD_CLARO,
            troughcolor=self.COR_CARD,
            bordercolor=self.COR_CARD,
            arrowcolor=self.COR_TEXTO_FRACO,
        )
        estilo.configure(
            "ChargeGrid.Horizontal.TScrollbar",
            background=self.COR_CARD_CLARO,
            troughcolor=self.COR_CARD,
            bordercolor=self.COR_CARD,
            arrowcolor=self.COR_TEXTO_FRACO,
        )

    def _construir_layout(self) -> None:
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.menu_lateral = tk.Frame(self, bg=self.COR_MENU, width=248)
        self.menu_lateral.grid(row=0, column=0, sticky="nsw")
        self.menu_lateral.grid_propagate(False)

        marca = tk.Frame(self.menu_lateral, bg=self.COR_MENU)
        marca.pack(fill="x", padx=22, pady=(24, 28))
        logo = tk.Canvas(
            marca,
            width=46,
            height=46,
            bg=self.COR_MENU,
            highlightthickness=0,
        )
        logo.pack(side="left")
        logo.create_arc(
            5,
            5,
            40,
            40,
            start=42,
            extent=276,
            style="arc",
            outline=self.COR_VERDE,
            width=6,
        )
        logo.create_line(27, 12, 27, 34, fill=self.COR_AZUL, width=2)
        for posicao_y in (13, 23, 33):
            logo.create_oval(
                24,
                posicao_y - 3,
                30,
                posicao_y + 3,
                fill=self.COR_AZUL,
                outline=self.COR_MENU,
            )
        textos_marca = tk.Frame(marca, bg=self.COR_MENU)
        textos_marca.pack(side="left", padx=(10, 0))
        tk.Label(
            textos_marca,
            text="ChargeGrid",
            bg=self.COR_MENU,
            fg=self.COR_TEXTO,
            font=("Segoe UI", 14, "bold"),
        ).pack(anchor="w")
        tk.Label(
            textos_marca,
            text="ENERGY INTELLIGENCE",
            bg=self.COR_MENU,
            fg=self.COR_VERDE,
            font=("Segoe UI", 7, "bold"),
        ).pack(anchor="w")

        opcoes = (
            ("cadastro", "+   Nova sessão"),
            ("simulacao", ">   Simulação"),
            ("sessoes", "#   Listar sessões"),
            ("busca", "?   Buscar sessão"),
            ("ordenacao", "↕   Ordenar sessões"),
            ("estatisticas", "▥   Estatísticas"),
            ("relatorio", "=   Relatório geral"),
        )
        for nome, texto in opcoes:
            botao = tk.Button(
                self.menu_lateral,
                text=texto,
                command=lambda tela=nome: self.mostrar_tela(tela),
                bg=self.COR_MENU,
                fg=self.COR_TEXTO_FRACO,
                activebackground=self.COR_CARD,
                activeforeground=self.COR_TEXTO,
                bd=0,
                relief="flat",
                anchor="w",
                padx=22,
                pady=12,
                cursor="hand2",
                font=("Segoe UI", 10),
            )
            botao.pack(fill="x", padx=10, pady=2)
            self._configurar_hover_menu(botao, nome)
            self.botoes_menu[nome] = botao

        rodape_menu = tk.Frame(self.menu_lateral, bg=self.COR_MENU)
        rodape_menu.pack(side="bottom", fill="x", padx=10, pady=(0, 16))
        separador = tk.Frame(rodape_menu, bg=self.COR_BORDA, height=1)
        separador.pack(fill="x", padx=12, pady=(0, 12))
        tk.Label(
            rodape_menu,
            text="●  Sistema operacional",
            bg=self.COR_MENU,
            fg=self.COR_VERDE,
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor="w", padx=14, pady=(0, 7))
        botao_encerrar = tk.Button(
            rodape_menu,
            text="×   Encerrar",
            command=self.encerrar,
            bg=self.COR_MENU,
            fg=self.COR_ERRO,
            activebackground=self.COR_CARD,
            activeforeground=self.COR_ERRO,
            bd=0,
            relief="flat",
            anchor="w",
            padx=22,
            pady=12,
            cursor="hand2",
            font=("Segoe UI", 10),
        )
        botao_encerrar.pack(fill="x")
        self._configurar_hover(botao_encerrar, self.COR_MENU, self.COR_CARD)

        self.area_principal = tk.Frame(self, bg=self.COR_FUNDO)
        self.area_principal.grid(row=0, column=1, sticky="nsew")
        self.area_principal.grid_rowconfigure(1, weight=1)
        self.area_principal.grid_columnconfigure(0, weight=1)

        cabecalho = tk.Frame(self.area_principal, bg=self.COR_FUNDO)
        cabecalho.grid(row=0, column=0, sticky="ew", padx=34, pady=(23, 18))
        cabecalho.grid_columnconfigure(0, weight=1)
        titulos = tk.Frame(cabecalho, bg=self.COR_FUNDO)
        titulos.grid(row=0, column=0, sticky="w")
        self.label_titulo = tk.Label(
            titulos,
            text="",
            bg=self.COR_FUNDO,
            fg=self.COR_TEXTO,
            font=("Segoe UI", 21, "bold"),
        )
        self.label_titulo.pack(anchor="w")
        self.label_subtitulo = tk.Label(
            titulos,
            text="",
            bg=self.COR_FUNDO,
            fg=self.COR_TEXTO_FRACO,
            font=("Segoe UI", 9),
        )
        self.label_subtitulo.pack(anchor="w", pady=(4, 0))

        acoes_cabecalho = tk.Frame(cabecalho, bg=self.COR_FUNDO)
        acoes_cabecalho.grid(row=0, column=1, sticky="e")
        self._botao_primario(
            acoes_cabecalho,
            "▶  Simular agora",
            self.executar_simulacao_rapida,
        ).pack(side="left", padx=(0, 10))
        self.label_quantidade = tk.Label(
            acoes_cabecalho,
            text="0 sessões armazenadas",
            bg=self.COR_CARD_CLARO,
            fg=self.COR_VERDE,
            padx=14,
            pady=10,
            font=("Segoe UI", 9, "bold"),
        )
        self.label_quantidade.pack(side="left")

        self.container_telas = tk.Frame(self.area_principal, bg=self.COR_FUNDO)
        self.container_telas.grid(row=1, column=0, sticky="nsew", padx=34, pady=(0, 28))
        self.container_telas.grid_rowconfigure(0, weight=1)
        self.container_telas.grid_columnconfigure(0, weight=1)

    def _criar_telas(self) -> None:
        criadores = {
            "cadastro": self._criar_tela_cadastro,
            "simulacao": self._criar_tela_simulacao,
            "sessoes": self._criar_tela_sessoes,
            "busca": self._criar_tela_busca,
            "ordenacao": self._criar_tela_ordenacao,
            "estatisticas": self._criar_tela_estatisticas,
            "relatorio": self._criar_tela_relatorio,
        }
        for nome, criador in criadores.items():
            tela = tk.Frame(self.container_telas, bg=self.COR_FUNDO)
            tela.grid(row=0, column=0, sticky="nsew")
            self.telas[nome] = tela
            criador(tela)

    def _card(self, parent: tk.Widget) -> tk.Frame:
        return tk.Frame(
            parent,
            bg=self.COR_CARD,
            highlightbackground=self.COR_BORDA,
            highlightthickness=1,
        )

    def _label_campo(self, parent: tk.Widget, texto: str) -> tk.Label:
        return tk.Label(
            parent,
            text=texto,
            bg=self.COR_CARD,
            fg=self.COR_TEXTO_FRACO,
            font=("Segoe UI", 9, "bold"),
        )

    def _entrada(self, parent: tk.Widget, variavel: tk.StringVar) -> tk.Entry:
        return tk.Entry(
            parent,
            textvariable=variavel,
            bg=self.COR_CAMPO,
            fg=self.COR_TEXTO,
            insertbackground=self.COR_TEXTO,
            highlightbackground=self.COR_BORDA,
            highlightcolor=self.COR_VERDE,
            highlightthickness=1,
            relief="flat",
            font=("Segoe UI", 10),
            readonlybackground=self.COR_CAMPO,
        )

    @staticmethod
    def _configurar_hover(
        botao: tk.Button,
        cor_normal: str,
        cor_hover: str,
    ) -> None:
        botao.bind("<Enter>", lambda _evento: botao.config(bg=cor_hover))
        botao.bind("<Leave>", lambda _evento: botao.config(bg=cor_normal))

    def _configurar_hover_menu(self, botao: tk.Button, nome_tela: str) -> None:
        def entrar(_evento) -> None:
            if self.tela_atual != nome_tela:
                botao.config(bg=self.COR_CARD)

        def sair(_evento) -> None:
            cor = self.COR_CARD if self.tela_atual == nome_tela else self.COR_MENU
            botao.config(bg=cor)

        botao.bind("<Enter>", entrar)
        botao.bind("<Leave>", sair)

    def _botao_primario(self, parent: tk.Widget, texto: str, comando) -> tk.Button:
        botao = tk.Button(
            parent,
            text=texto,
            command=comando,
            bg=self.COR_VERDE,
            fg="#06250F",
            activebackground="#56DDA0",
            activeforeground="#06250F",
            bd=0,
            relief="flat",
            padx=20,
            pady=10,
            cursor="hand2",
            font=("Segoe UI", 10, "bold"),
        )
        self._configurar_hover(botao, self.COR_VERDE, "#56DDA0")
        return botao

    def _botao_secundario(self, parent: tk.Widget, texto: str, comando) -> tk.Button:
        botao = tk.Button(
            parent,
            text=texto,
            command=comando,
            bg=self.COR_CARD_CLARO,
            fg=self.COR_TEXTO,
            activebackground=self.COR_BORDA,
            activeforeground=self.COR_TEXTO,
            bd=0,
            relief="flat",
            padx=16,
            pady=9,
            cursor="hand2",
            font=("Segoe UI", 9, "bold"),
        )
        self._configurar_hover(botao, self.COR_CARD_CLARO, self.COR_BORDA)
        return botao

    def _criar_tela_cadastro(self, tela: tk.Frame) -> None:
        tela.grid_columnconfigure(0, weight=1)
        tela.grid_rowconfigure(0, weight=1)
        card = self._card(tela)
        card.grid(row=0, column=0, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_columnconfigure(1, weight=1)

        tk.Label(
            card,
            text="Dados da sessão",
            bg=self.COR_CARD,
            fg=self.COR_TEXTO,
            font=("Segoe UI", 15, "bold"),
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=28, pady=(23, 4))
        tk.Label(
            card,
            text="Preencha os campos. Energia e custo serão calculados automaticamente.",
            bg=self.COR_CARD,
            fg=self.COR_TEXTO_FRACO,
            font=("Segoe UI", 9),
        ).grid(row=1, column=0, columnspan=2, sticky="w", padx=28, pady=(0, 18))

        self.var_id = tk.StringVar(value="1")
        self.var_veiculo = tk.StringVar()
        self.var_carregador = tk.StringVar(value=next(iter(TIPOS_CARREGADOR)))
        self.var_potencia = tk.StringVar(value="7,4")
        self.var_tempo = tk.StringVar(value="60")
        self.var_hora = tk.StringVar(value=str(datetime.now().hour))
        self.var_usuario = tk.StringVar(value=TIPOS_USUARIO[0])
        self.var_status = tk.StringVar(value="Finalizada")

        self._adicionar_entrada_formulario(
            card,
            "ID da sessão  ·  gerado automaticamente",
            self.var_id,
            2,
            0,
            somente_leitura=True,
        )
        self.entrada_veiculo = self._adicionar_entrada_formulario(
            card, "Identificação do veículo", self.var_veiculo, 2, 1
        )
        self._adicionar_combo_formulario(
            card,
            "Tipo de carregador",
            self.var_carregador,
            tuple(TIPOS_CARREGADOR.keys()),
            4,
            0,
            self._atualizar_limite_potencia,
        )
        self._adicionar_combo_formulario(
            card, "Tipo de usuário", self.var_usuario, TIPOS_USUARIO, 4, 1
        )
        self._adicionar_entrada_formulario(
            card, "Potência utilizada (kW)", self.var_potencia, 6, 0
        )
        self._adicionar_entrada_formulario(
            card, "Tempo de recarga (minutos)", self.var_tempo, 6, 1
        )
        self._adicionar_entrada_formulario(
            card, "Hora de início (0 a 23)", self.var_hora, 8, 0
        )
        self._adicionar_combo_formulario(
            card,
            "Status da sessão",
            self.var_status,
            ("Ativa", "Finalizada"),
            8,
            1,
        )

        self.label_limite = tk.Label(
            card,
            text="Limite do carregador selecionado: 7,4 kW",
            bg=self.COR_CARD,
            fg=self.COR_AZUL,
            font=("Segoe UI", 9),
        )
        self.label_limite.grid(
            row=9, column=0, columnspan=2, sticky="w", padx=28, pady=(4, 12)
        )

        previa = tk.Frame(
            card,
            bg=self.COR_CARD_CLARO,
            highlightbackground=self.COR_BORDA,
            highlightthickness=1,
        )
        previa.grid(row=10, column=0, columnspan=2, sticky="ew", padx=28, pady=(0, 12))
        for coluna in range(3):
            previa.grid_columnconfigure(coluna, weight=1, uniform="previa")

        self.var_previa_energia = tk.StringVar(value="7,40 kWh")
        self.var_previa_tarifa = tk.StringVar(value="R$ 0,805/kWh")
        self.var_previa_custo = tk.StringVar(value="R$ 5,96")
        itens_previa = (
            ("ENERGIA ESTIMADA", self.var_previa_energia),
            ("TARIFA APLICADA", self.var_previa_tarifa),
            ("CUSTO ESTIMADO", self.var_previa_custo),
        )
        for coluna, (titulo, variavel) in enumerate(itens_previa):
            bloco = tk.Frame(previa, bg=self.COR_CARD_CLARO)
            bloco.grid(row=0, column=coluna, sticky="ew", padx=16, pady=12)
            tk.Label(
                bloco,
                text=titulo,
                bg=self.COR_CARD_CLARO,
                fg=self.COR_TEXTO_FRACO,
                font=("Segoe UI", 7, "bold"),
            ).pack(anchor="w")
            tk.Label(
                bloco,
                textvariable=variavel,
                bg=self.COR_CARD_CLARO,
                fg=self.COR_VERDE if coluna == 2 else self.COR_TEXTO,
                font=("Segoe UI", 12, "bold"),
            ).pack(anchor="w", pady=(3, 0))

        botoes = tk.Frame(card, bg=self.COR_CARD)
        botoes.grid(row=11, column=0, columnspan=2, sticky="ew", padx=28, pady=(2, 22))
        self._botao_primario(botoes, "Cadastrar sessão", self.cadastrar_sessao).pack(
            side="left"
        )
        self._botao_secundario(botoes, "Limpar campos", self.limpar_formulario).pack(
            side="left", padx=(10, 0)
        )

        for variavel in (
            self.var_potencia,
            self.var_tempo,
            self.var_hora,
            self.var_usuario,
        ):
            variavel.trace_add("write", self._atualizar_previa_cadastro)
        self._atualizar_previa_cadastro()

    def _adicionar_entrada_formulario(
        self,
        card: tk.Frame,
        titulo: str,
        variavel: tk.StringVar,
        linha: int,
        coluna: int,
        somente_leitura: bool = False,
    ) -> tk.Entry:
        bloco = tk.Frame(card, bg=self.COR_CARD)
        bloco.grid(
            row=linha,
            column=coluna,
            sticky="ew",
            padx=(28 if coluna == 0 else 14, 14 if coluna == 0 else 28),
            pady=7,
        )
        bloco.grid_columnconfigure(0, weight=1)
        self._label_campo(bloco, titulo).grid(row=0, column=0, sticky="w", pady=(0, 6))
        entrada = self._entrada(bloco, variavel)
        entrada.grid(row=1, column=0, sticky="ew", ipady=8)
        if somente_leitura:
            entrada.config(state="readonly", fg=self.COR_TEXTO_FRACO)
        return entrada

    def _adicionar_combo_formulario(
        self,
        card: tk.Frame,
        titulo: str,
        variavel: tk.StringVar,
        valores: tuple[str, ...],
        linha: int,
        coluna: int,
        comando=None,
    ) -> None:
        bloco = tk.Frame(card, bg=self.COR_CARD)
        bloco.grid(
            row=linha,
            column=coluna,
            sticky="ew",
            padx=(28 if coluna == 0 else 14, 14 if coluna == 0 else 28),
            pady=7,
        )
        bloco.grid_columnconfigure(0, weight=1)
        self._label_campo(bloco, titulo).grid(row=0, column=0, sticky="w", pady=(0, 6))
        combo = ttk.Combobox(
            bloco,
            textvariable=variavel,
            values=valores,
            state="readonly",
            style="ChargeGrid.TCombobox",
        )
        combo.grid(row=1, column=0, sticky="ew")
        if comando is not None:
            combo.bind("<<ComboboxSelected>>", comando)

    def _criar_tela_simulacao(self, tela: tk.Frame) -> None:
        tela.grid_columnconfigure(0, weight=1)
        tela.grid_rowconfigure(2, weight=1)

        painel = self._card(tela)
        painel.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        painel.grid_columnconfigure(0, weight=1)
        apresentacao = tk.Frame(painel, bg=self.COR_CARD)
        apresentacao.grid(row=0, column=0, sticky="w", padx=22, pady=17)
        tk.Label(
            apresentacao,
            text="DEMONSTRAÇÃO INSTANTÂNEA",
            bg=self.COR_CARD,
            fg=self.COR_VERDE,
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor="w")
        tk.Label(
            apresentacao,
            text="Simule a operação de uma rede de recarga",
            bg=self.COR_CARD,
            fg=self.COR_TEXTO,
            font=("Segoe UI", 14, "bold"),
        ).pack(anchor="w", pady=(3, 2))
        tk.Label(
            apresentacao,
            text=(
                "Avance o relógio para concluir recargas e liberar vagas para a fila."
            ),
            bg=self.COR_CARD,
            fg=self.COR_TEXTO_FRACO,
            font=("Segoe UI", 9),
        ).pack(anchor="w")

        controles = tk.Frame(painel, bg=self.COR_CARD)
        controles.grid(row=1, column=0, sticky="ew", padx=22, pady=(0, 16))
        self.var_cenario_simulacao = tk.StringVar(value=CENARIOS_SIMULACAO[0])
        self.var_quantidade_simulacao = tk.StringVar(value="5 veículos")
        for coluna, (titulo, variavel, valores) in enumerate(
            (
                ("Cenário", self.var_cenario_simulacao, CENARIOS_SIMULACAO),
                (
                    "Quantidade",
                    self.var_quantidade_simulacao,
                    ("3 veículos", "5 veículos", "8 veículos"),
                ),
            )
        ):
            bloco = tk.Frame(controles, bg=self.COR_CARD)
            bloco.grid(row=0, column=coluna, sticky="ew", padx=(0, 9))
            self._label_campo(bloco, titulo).pack(anchor="w", pady=(0, 5))
            ttk.Combobox(
                bloco,
                textvariable=variavel,
                values=valores,
                state="readonly",
                width=19 if coluna == 0 else 11,
                style="ChargeGrid.TCombobox",
            ).pack(fill="x")
        self._botao_primario(
            controles,
            "▶  Gerar cenário",
            self.gerar_simulacao,
        ).grid(row=0, column=2, sticky="s", pady=(20, 0))
        self._botao_secundario(
            controles,
            "+15 min",
            lambda: self.avancar_simulacao(15),
        ).grid(row=0, column=3, sticky="s", padx=(9, 0), pady=(20, 0))
        self.botao_tempo_automatico = self._botao_secundario(
            controles,
            "▶  Rodar tempo",
            self.alternar_tempo_automatico,
        )
        self.botao_tempo_automatico.grid(
            row=0,
            column=4,
            sticky="s",
            padx=(9, 0),
            pady=(20, 0),
        )

        indicadores = tk.Frame(tela, bg=self.COR_FUNDO)
        indicadores.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        for coluna in range(5):
            indicadores.grid_columnconfigure(coluna, weight=1, uniform="simulacao")
        self.vars_simulacao = {
            "tempo": tk.StringVar(value="T+0 min"),
            "ocupacao": tk.StringVar(value="0/4"),
            "fila": tk.StringVar(value="0"),
            "potencia": tk.StringVar(value="0,0 kW"),
            "energia": tk.StringVar(value="0,0 kWh"),
        }
        configuracoes = (
            ("TEMPO DECORRIDO", "tempo", self.COR_TEXTO),
            ("CARREGADORES", "ocupacao", self.COR_VERDE),
            ("NA FILA", "fila", self.COR_ALERTA),
            ("POTÊNCIA EM USO", "potencia", self.COR_AZUL),
            ("ENERGIA FORNECIDA", "energia", self.COR_TEXTO),
        )
        for coluna, (titulo, chave, cor) in enumerate(configuracoes):
            card = self._card(indicadores)
            card.grid(
                row=0,
                column=coluna,
                sticky="ew",
                padx=(0 if coluna == 0 else 5, 0 if coluna == 4 else 5),
            )
            tk.Label(
                card,
                text=titulo,
                bg=self.COR_CARD,
                fg=self.COR_TEXTO_FRACO,
                font=("Segoe UI", 7, "bold"),
            ).pack(anchor="w", padx=16, pady=(13, 4))
            tk.Label(
                card,
                textvariable=self.vars_simulacao[chave],
                bg=self.COR_CARD,
                fg=cor,
                font=("Segoe UI", 15, "bold"),
            ).pack(anchor="w", padx=16, pady=(0, 13))

        tabela_card = self._card(tela)
        tabela_card.grid(row=2, column=0, sticky="nsew")
        tabela_card.grid_rowconfigure(1, weight=1)
        tabela_card.grid_columnconfigure(0, weight=1)
        topo_tabela = tk.Frame(tabela_card, bg=self.COR_CARD)
        topo_tabela.grid(row=0, column=0, columnspan=2, sticky="ew", padx=16, pady=(13, 4))
        topo_tabela.grid_columnconfigure(0, weight=1)
        self.label_status_simulacao = tk.Label(
            topo_tabela,
            text="Pronto para gerar o primeiro cenário.",
            bg=self.COR_CARD,
            fg=self.COR_TEXTO_FRACO,
            font=("Segoe UI", 9),
        )
        self.label_status_simulacao.grid(row=0, column=0, sticky="w")
        self._botao_secundario(
            topo_tabela,
            "Limpar simulados",
            self.limpar_simulacao,
        ).grid(row=0, column=1, sticky="e")

        colunas = (
            "id",
            "veiculo",
            "estacao",
            "usuario",
            "carregador",
            "energia",
            "restante",
            "custo",
            "status",
        )
        self.tree_simulacao = ttk.Treeview(
            tabela_card,
            columns=colunas,
            show="headings",
            height=8,
            style="ChargeGrid.Treeview",
        )
        titulos = {
            "id": "ID",
            "veiculo": "Veículo",
            "estacao": "Estação",
            "usuario": "Usuário",
            "carregador": "Carregador",
            "energia": "Energia",
            "restante": "Restante",
            "custo": "Custo",
            "status": "Status",
        }
        larguras = {
            "id": 50,
            "veiculo": 175,
            "estacao": 130,
            "usuario": 85,
            "carregador": 160,
            "energia": 88,
            "restante": 82,
            "custo": 82,
            "status": 80,
        }
        for coluna in colunas:
            self.tree_simulacao.heading(coluna, text=titulos[coluna])
            self.tree_simulacao.column(
                coluna,
                width=larguras[coluna],
                minwidth=50,
                anchor="w" if coluna in ("veiculo", "estacao", "carregador") else "center",
            )
        self.tree_simulacao.tag_configure("par", background=self.COR_CAMPO)
        self.tree_simulacao.tag_configure("impar", background="#171D19")
        self.tree_simulacao.tag_configure("ativa", foreground=self.COR_VERDE)
        self.tree_simulacao.tag_configure("fila", foreground=self.COR_ALERTA)
        self.tree_simulacao.tag_configure("finalizada", foreground=self.COR_TEXTO_FRACO)
        self.tree_simulacao.bind("<Double-1>", self.mostrar_detalhes_simulado)
        self.tree_simulacao.grid(row=1, column=0, sticky="nsew", padx=(16, 0), pady=(4, 0))

        rolagem_vertical = ttk.Scrollbar(
            tabela_card,
            orient="vertical",
            command=self.tree_simulacao.yview,
            style="ChargeGrid.Vertical.TScrollbar",
        )
        rolagem_vertical.grid(row=1, column=1, sticky="ns", padx=(0, 16), pady=(4, 0))
        rolagem_horizontal = ttk.Scrollbar(
            tabela_card,
            orient="horizontal",
            command=self.tree_simulacao.xview,
            style="ChargeGrid.Horizontal.TScrollbar",
        )
        rolagem_horizontal.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=16,
            pady=(0, 13),
        )
        self.tree_simulacao.configure(
            yscrollcommand=rolagem_vertical.set,
            xscrollcommand=rolagem_horizontal.set,
        )

    def _criar_treeview(self, parent: tk.Widget, altura: int = 14) -> ttk.Treeview:
        colunas = (
            "id",
            "veiculo",
            "usuario",
            "potencia",
            "tempo",
            "energia",
            "custo",
            "status",
        )
        tree = ttk.Treeview(
            parent,
            columns=colunas,
            show="headings",
            height=altura,
            style="ChargeGrid.Treeview",
        )
        titulos = {
            "id": "ID",
            "veiculo": "Veículo",
            "usuario": "Usuário",
            "potencia": "Potência",
            "tempo": "Tempo",
            "energia": "Energia",
            "custo": "Custo",
            "status": "Status",
        }
        larguras = {
            "id": 55,
            "veiculo": 165,
            "usuario": 95,
            "potencia": 90,
            "tempo": 85,
            "energia": 95,
            "custo": 90,
            "status": 90,
        }
        for coluna in colunas:
            tree.heading(coluna, text=titulos[coluna])
            tree.column(coluna, width=larguras[coluna], minwidth=55, anchor="center")
        tree.column("veiculo", anchor="w")
        tree.tag_configure("par", background=self.COR_CAMPO)
        tree.tag_configure("impar", background="#171D19")
        tree.tag_configure("ativa", foreground=self.COR_VERDE)
        tree.tag_configure("fila", foreground=self.COR_ALERTA)
        tree.tag_configure("finalizada", foreground=self.COR_TEXTO_FRACO)
        return tree

    def _criar_tela_sessoes(self, tela: tk.Frame) -> None:
        tela.grid_rowconfigure(1, weight=1)
        tela.grid_columnconfigure(0, weight=1)
        barra = tk.Frame(tela, bg=self.COR_FUNDO)
        barra.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        tk.Label(
            barra,
            text="Duplo clique em uma sessão para visualizar todos os detalhes.",
            bg=self.COR_FUNDO,
            fg=self.COR_TEXTO_FRACO,
            font=("Segoe UI", 9),
        ).pack(side="left")
        self._botao_secundario(barra, "Atualizar tabela", self.atualizar_tabela).pack(
            side="right"
        )
        card = self._card(tela)
        card.grid(row=1, column=0, sticky="nsew")
        card.grid_rowconfigure(0, weight=1)
        card.grid_columnconfigure(0, weight=1)
        self.tree_sessoes = self._criar_treeview(card)
        self.tree_sessoes.grid(row=0, column=0, sticky="nsew", padx=(16, 0), pady=16)
        self.tree_sessoes.bind("<Double-1>", self.mostrar_detalhes_selecionado)
        rolagem = ttk.Scrollbar(
            card,
            orient="vertical",
            command=self.tree_sessoes.yview,
            style="ChargeGrid.Vertical.TScrollbar",
        )
        rolagem.grid(row=0, column=1, sticky="ns", padx=(0, 16), pady=16)
        rolagem_horizontal = ttk.Scrollbar(
            card,
            orient="horizontal",
            command=self.tree_sessoes.xview,
            style="ChargeGrid.Horizontal.TScrollbar",
        )
        rolagem_horizontal.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 12))
        self.tree_sessoes.configure(
            yscrollcommand=rolagem.set,
            xscrollcommand=rolagem_horizontal.set,
        )

    def _criar_tela_busca(self, tela: tk.Frame) -> None:
        tela.grid_columnconfigure(0, weight=1)
        tela.grid_rowconfigure(1, weight=1)
        busca_card = self._card(tela)
        busca_card.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        self.var_busca = tk.StringVar()
        self._label_campo(busca_card, "ID da sessão").pack(
            side="left", padx=(22, 10), pady=20
        )
        entrada = self._entrada(busca_card, self.var_busca)
        entrada.pack(side="left", fill="x", expand=True, ipady=8, pady=16)
        entrada.bind("<Return>", lambda _evento: self.buscar_sessao())
        self._botao_primario(busca_card, "Buscar", self.buscar_sessao).pack(
            side="left", padx=18, pady=14
        )
        resultado_card = self._card(tela)
        resultado_card.grid(row=1, column=0, sticky="nsew")
        resultado_card.grid_rowconfigure(0, weight=1)
        resultado_card.grid_columnconfigure(0, weight=1)
        self.texto_busca = ScrolledText(
            resultado_card,
            bg=self.COR_CAMPO,
            fg=self.COR_TEXTO,
            insertbackground=self.COR_TEXTO,
            relief="flat",
            font=("Consolas", 11),
            padx=20,
            pady=18,
            wrap="word",
        )
        self.texto_busca.grid(row=0, column=0, sticky="nsew", padx=16, pady=16)
        self._definir_texto(self.texto_busca, "Digite um ID para localizar uma sessão.")

    def _criar_tela_ordenacao(self, tela: tk.Frame) -> None:
        tela.grid_columnconfigure(0, weight=1)
        tela.grid_rowconfigure(1, weight=1)
        controles = self._card(tela)
        controles.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        self.var_criterio = tk.StringVar(value="ID")
        self.var_ordem = tk.StringVar(value="Crescente")
        self._adicionar_combo_ordenacao(
            controles, "Critério", self.var_criterio, tuple(CRITERIOS_ORDENACAO.keys())
        )
        self._adicionar_combo_ordenacao(
            controles, "Ordem", self.var_ordem, ("Crescente", "Decrescente")
        )
        self._botao_primario(controles, "Aplicar Bubble Sort", self.ordenar_sessoes).pack(
            side="left", padx=22, pady=(30, 16)
        )
        card_tabela = self._card(tela)
        card_tabela.grid(row=1, column=0, sticky="nsew")
        card_tabela.grid_rowconfigure(0, weight=1)
        card_tabela.grid_columnconfigure(0, weight=1)
        self.tree_ordenacao = self._criar_treeview(card_tabela, altura=11)
        self.tree_ordenacao.grid(
            row=0, column=0, sticky="nsew", padx=(16, 0), pady=(16, 8)
        )
        rolagem = ttk.Scrollbar(
            card_tabela,
            orient="vertical",
            command=self.tree_ordenacao.yview,
            style="ChargeGrid.Vertical.TScrollbar",
        )
        rolagem.grid(row=0, column=1, sticky="ns", padx=(0, 16), pady=(16, 8))
        rolagem_horizontal = ttk.Scrollbar(
            card_tabela,
            orient="horizontal",
            command=self.tree_ordenacao.xview,
            style="ChargeGrid.Horizontal.TScrollbar",
        )
        rolagem_horizontal.grid(row=1, column=0, sticky="ew", padx=16)
        self.tree_ordenacao.configure(
            yscrollcommand=rolagem.set,
            xscrollcommand=rolagem_horizontal.set,
        )
        tk.Label(
            card_tabela,
            text=(
                "Bubble Sort manual: dois laços com complexidade O(n²) no pior caso. "
                "Nenhum recurso pronto de ordenação é utilizado."
            ),
            bg=self.COR_CARD,
            fg=self.COR_AZUL,
            font=("Segoe UI", 9),
        ).grid(row=2, column=0, columnspan=2, sticky="w", padx=18, pady=(8, 14))

    def _adicionar_combo_ordenacao(
        self,
        parent: tk.Frame,
        titulo: str,
        variavel: tk.StringVar,
        valores: tuple[str, ...],
    ) -> None:
        bloco = tk.Frame(parent, bg=self.COR_CARD)
        bloco.pack(side="left", fill="x", expand=True, padx=18, pady=16)
        self._label_campo(bloco, titulo).pack(anchor="w", pady=(0, 5))
        ttk.Combobox(
            bloco,
            textvariable=variavel,
            values=valores,
            state="readonly",
            style="ChargeGrid.TCombobox",
        ).pack(fill="x")

    def _criar_tela_estatisticas(self, tela: tk.Frame) -> None:
        tela.grid_columnconfigure(0, weight=1)
        tela.grid_rowconfigure(1, weight=1)
        barra = tk.Frame(tela, bg=self.COR_FUNDO)
        barra.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        tk.Label(
            barra,
            text="Indicadores calculados exclusivamente com as sessões da lista.",
            bg=self.COR_FUNDO,
            fg=self.COR_TEXTO_FRACO,
            font=("Segoe UI", 9),
        ).pack(side="left")
        self._botao_secundario(barra, "Atualizar", self.atualizar_estatisticas).pack(
            side="right"
        )
        grade = tk.Frame(tela, bg=self.COR_FUNDO)
        grade.grid(row=1, column=0, sticky="nsew")
        for coluna in range(3):
            grade.grid_columnconfigure(coluna, weight=1, uniform="estatistica")
        for linha in range(2):
            grade.grid_rowconfigure(linha, weight=1, uniform="estatistica")

        self.vars_estatisticas: dict[str, tk.StringVar] = {}
        configuracoes = (
            ("quantidade", "Sessões realizadas", "0", 0, 0),
            ("energia", "Energia fornecida", "0,00 kWh", 0, 1),
            ("faturamento", "Faturamento total", "R$ 0,00", 0, 2),
            ("media", "Custo médio", "R$ 0,00", 1, 0),
            ("maior", "Maior consumo", "—", 1, 1),
            ("menor", "Menor consumo", "—", 1, 2),
        )
        for chave, titulo, inicial, linha, coluna in configuracoes:
            card = self._card(grade)
            card.grid(row=linha, column=coluna, sticky="nsew", padx=7, pady=7)
            variavel = tk.StringVar(value=inicial)
            self.vars_estatisticas[chave] = variavel
            tk.Label(
                card,
                text=titulo.upper(),
                bg=self.COR_CARD,
                fg=self.COR_TEXTO_FRACO,
                font=("Segoe UI", 8, "bold"),
            ).pack(anchor="w", padx=20, pady=(22, 8))
            tk.Label(
                card,
                textvariable=variavel,
                bg=self.COR_CARD,
                fg=self.COR_VERDE if chave not in ("maior", "menor") else self.COR_AZUL,
                font=("Segoe UI", 17, "bold"),
                wraplength=220,
                justify="left",
            ).pack(anchor="w", padx=20, pady=(0, 22))

    def _criar_tela_relatorio(self, tela: tk.Frame) -> None:
        tela.grid_columnconfigure(0, weight=1)
        tela.grid_rowconfigure(1, weight=1)
        barra = tk.Frame(tela, bg=self.COR_FUNDO)
        barra.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        self._botao_secundario(barra, "Atualizar relatório", self.atualizar_relatorio).pack(
            side="left"
        )
        self._botao_secundario(barra, "Copiar texto", self.copiar_relatorio).pack(
            side="left", padx=(10, 0)
        )
        self._botao_primario(barra, "Salvar em TXT", self.salvar_relatorio).pack(
            side="right"
        )
        card = self._card(tela)
        card.grid(row=1, column=0, sticky="nsew")
        card.grid_rowconfigure(0, weight=1)
        card.grid_columnconfigure(0, weight=1)
        self.texto_relatorio = ScrolledText(
            card,
            bg=self.COR_CAMPO,
            fg=self.COR_TEXTO,
            insertbackground=self.COR_TEXTO,
            relief="flat",
            font=("Consolas", 9),
            padx=16,
            pady=14,
            wrap="none",
        )
        self.texto_relatorio.grid(row=0, column=0, sticky="nsew", padx=16, pady=16)

    def mostrar_tela(self, nome: str) -> None:
        """Mantém o menu disponível e exibe a tela escolhida."""

        self.tela_atual = nome
        self.telas[nome].tkraise()
        self.label_titulo.config(text=self.TITULOS_TELA[nome])
        self.label_subtitulo.config(text=self.SUBTITULOS_TELA[nome])
        for nome_botao, botao in self.botoes_menu.items():
            if nome_botao == nome:
                botao.config(bg=self.COR_CARD, fg=self.COR_TEXTO)
            else:
                botao.config(bg=self.COR_MENU, fg=self.COR_TEXTO_FRACO)

        if nome == "simulacao":
            self.atualizar_painel_simulacao()
        elif nome == "sessoes":
            self.atualizar_tabela()
        elif nome == "ordenacao":
            self.atualizar_treeview(self.tree_ordenacao)
        elif nome == "estatisticas":
            self.atualizar_estatisticas()
        elif nome == "relatorio":
            self.atualizar_relatorio()

    def _atualizar_limite_potencia(self, _evento=None) -> None:
        tipo_carregador = self.var_carregador.get()
        if tipo_carregador not in TIPOS_CARREGADOR:
            return
        limite = TIPOS_CARREGADOR[tipo_carregador]
        self.label_limite.config(
            text=f"Limite do carregador selecionado: {str(limite).replace('.', ',')} kW"
        )
        if _evento is not None:
            self.var_potencia.set(str(limite).replace(".", ","))
        self._atualizar_previa_cadastro()

    def _atualizar_previa_cadastro(self, *_args) -> None:
        """Atualiza os cálculos sem interromper o usuário durante a digitação."""

        try:
            potencia = float(self.var_potencia.get().strip().replace(",", "."))
            tempo = int(self.var_tempo.get().strip())
            hora = int(self.var_hora.get().strip())
            usuario = self.var_usuario.get()
            carregador = self.var_carregador.get()
            if (
                not isfinite(potencia)
                or potencia <= 0
                or tempo <= 0
                or hora not in range(24)
                or usuario not in TIPOS_USUARIO
                or carregador not in TIPOS_CARREGADOR
                or potencia > TIPOS_CARREGADOR[carregador]
            ):
                raise ValueError
            energia = potencia * (tempo / 60)
            tarifa = calcular_tarifa(usuario, hora, potencia)
            custo = energia * tarifa
        except (ValueError, KeyError):
            self.var_previa_energia.set("—")
            self.var_previa_tarifa.set("—")
            self.var_previa_custo.set("—")
            return

        self.var_previa_energia.set(f"{energia:.2f} kWh".replace(".", ","))
        self.var_previa_tarifa.set(
            f"R$ {tarifa:.3f}/kWh".replace(".", ",")
        )
        self.var_previa_custo.set(f"R$ {custo:.2f}".replace(".", ","))

    def _sincronizar_interface(self) -> None:
        self.atualizar_quantidade()
        self.atualizar_tabela()
        self.atualizar_treeview(self.tree_ordenacao)
        self.atualizar_painel_simulacao()
        self.atualizar_estatisticas()
        self.atualizar_relatorio()
        self.var_id.set(str(obter_proximo_id(self.sessoes)))

    def cadastrar_sessao(self) -> None:
        """Valida o formulário, calcula os valores e adiciona o objeto à lista."""

        try:
            id_sessao = int(self.var_id.get().strip())
            if id_sessao <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("ID inválido", "Digite um ID inteiro maior que zero.")
            return

        if busca_sequencial(self.sessoes, id_sessao) != -1:
            messagebox.showerror(
                "ID duplicado", f"A sessão #{id_sessao} já está cadastrada. Use outro ID."
            )
            return

        veiculo = self.var_veiculo.get().strip()
        if not veiculo:
            messagebox.showerror(
                "Veículo inválido", "A identificação do veículo não pode ficar vazia."
            )
            return

        tipo_carregador = self.var_carregador.get()
        tipo_usuario = self.var_usuario.get()
        status = self.var_status.get()

        if tipo_carregador not in TIPOS_CARREGADOR:
            messagebox.showerror("Carregador inválido", "Escolha um carregador válido.")
            return
        if tipo_usuario not in TIPOS_USUARIO:
            messagebox.showerror("Usuário inválido", "Escolha um tipo de usuário válido.")
            return
        if status not in ("Ativa", "Finalizada"):
            messagebox.showerror("Status inválido", "Escolha um status válido.")
            return

        try:
            potencia_kw = float(self.var_potencia.get().strip().replace(",", "."))
        except ValueError:
            messagebox.showerror(
                "Potência inválida",
                "Digite um valor numérico para a potência.",
            )
            return

        potencia_maxima = TIPOS_CARREGADOR[tipo_carregador]
        if not isfinite(potencia_kw) or potencia_kw <= 0 or potencia_kw > potencia_maxima:
            messagebox.showerror(
                "Potência inválida",
                f"A potência deve ser maior que zero e no máximo {potencia_maxima:.1f} kW.",
            )
            return

        try:
            tempo_minutos = int(self.var_tempo.get().strip())
            if tempo_minutos <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Tempo inválido", "Digite um tempo inteiro maior que zero.")
            return

        try:
            hora_inicio = int(self.var_hora.get().strip())
            if hora_inicio < 0 or hora_inicio > 23:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Horário inválido", "A hora de início deve estar entre 0 e 23."
            )
            return

        nova_sessao = criar_sessao_calculada(
            id_sessao=id_sessao,
            veiculo=veiculo,
            tipo_carregador=tipo_carregador,
            tipo_usuario=tipo_usuario,
            potencia_kw=potencia_kw,
            tempo_minutos=tempo_minutos,
            hora_inicio=hora_inicio,
            status=status,
        )
        self.sessoes.append(nova_sessao)
        self._sincronizar_interface()
        self.limpar_formulario()
        messagebox.showinfo(
            "Sessão cadastrada",
            f"Sessão #{id_sessao} cadastrada com sucesso.\n\n"
            f"Energia calculada: {nova_sessao.energia_kwh:.2f} kWh\n"
            f"Custo calculado: R$ {nova_sessao.custo:.2f}",
        )

    def limpar_formulario(self) -> None:
        self.var_id.set(str(obter_proximo_id(self.sessoes)))
        self.var_veiculo.set("")
        self.var_carregador.set(next(iter(TIPOS_CARREGADOR)))
        limite = TIPOS_CARREGADOR[self.var_carregador.get()]
        self.var_potencia.set(str(limite).replace(".", ","))
        self.var_tempo.set("60")
        self.var_hora.set(str(datetime.now().hour))
        self.var_usuario.set(TIPOS_USUARIO[0])
        self.var_status.set("Finalizada")
        self._atualizar_limite_potencia()
        self.entrada_veiculo.focus_set()

    def executar_simulacao_rapida(self) -> None:
        """Gera o cenário padrão em um único clique a partir do cabeçalho."""

        self.var_cenario_simulacao.set(CENARIOS_SIMULACAO[0])
        self.var_quantidade_simulacao.set("5 veículos")
        self.gerar_simulacao()
        if not self.simulacao_automatica:
            self.alternar_tempo_automatico()

    def gerar_simulacao(self) -> None:
        """Adiciona um lote demonstrativo sem apagar os cadastros do usuário."""

        try:
            quantidade = int(self.var_quantidade_simulacao.get().split()[0])
        except (ValueError, IndexError):
            quantidade = 5
        cenario = self.var_cenario_simulacao.get()
        if cenario not in CENARIOS_SIMULACAO:
            cenario = CENARIOS_SIMULACAO[0]

        havia_simuladas = any(
            _sessao_e_simulada(sessao) for sessao in self.sessoes
        )
        if not havia_simuladas:
            self.tempo_simulado_minutos = 0

        novas_sessoes = gerar_lote_simulacao(
            self.sessoes,
            quantidade=quantidade,
            cenario=cenario,
        )
        if not novas_sessoes:
            return
        self.sessoes.extend(novas_sessoes)
        self._sincronizar_interface()
        self.mostrar_tela("simulacao")

        primeiro_id = novas_sessoes[0].id_sessao
        ultimo_id = novas_sessoes[-1].id_sessao
        resumo = calcular_ocupacao_simulacao(self.sessoes)
        self.label_status_simulacao.config(
            text=(
                f"{quantidade} veículos adicionados · IDs {primeiro_id}–{ultimo_id} · "
                f"{resumo['ativas']}/{resumo['capacidade']} carregadores ocupados · "
                f"{resumo['fila']} na fila"
            ),
            fg=self.COR_VERDE,
        )
        primeiro_item = f"sim-{primeiro_id}"
        if self.tree_simulacao.exists(primeiro_item):
            self.tree_simulacao.selection_set(primeiro_item)
            self.tree_simulacao.see(primeiro_item)

    def limpar_simulacao(self) -> None:
        """Remove apenas os dados criados pela demonstração."""

        self._parar_tempo_automatico()
        quantidade_anterior = len(self.sessoes)
        self.sessoes = [
            sessao
            for sessao in self.sessoes
            if not sessao.origem.startswith("Simulação")
        ]
        removidas = quantidade_anterior - len(self.sessoes)
        self.tempo_simulado_minutos = 0
        self._sincronizar_interface()
        self.label_status_simulacao.config(
            text=(
                f"{removidas} sessões simuladas removidas."
                if removidas
                else "Não há sessões simuladas para remover."
            ),
            fg=self.COR_TEXTO_FRACO,
        )

    def avancar_simulacao(self, minutos: int) -> None:
        """Avança o relógio da demonstração e atualiza todas as telas."""

        em_andamento = [
            sessao
            for sessao in self.sessoes
            if _sessao_e_simulada(sessao)
            and sessao.status in ("Ativa", "Na fila")
        ]
        if not em_andamento:
            self._parar_tempo_automatico()
            self.label_status_simulacao.config(
                text="Gere um cenário ou todas as recargas já foram finalizadas.",
                fg=self.COR_TEXTO_FRACO,
            )
            return

        resultado = avancar_tempo_simulacao(self.sessoes, minutos)
        self.tempo_simulado_minutos += minutos
        self._sincronizar_interface()

        partes = [f"Relógio avançou {minutos} min"]
        if resultado["finalizadas"]:
            partes.append(f"{resultado['finalizadas']} finalizada(s)")
        if resultado["iniciadas"]:
            partes.append(f"{resultado['iniciadas']} saiu(ram) da fila")
        if len(partes) == 1:
            partes.append("recargas em andamento")
        self.label_status_simulacao.config(
            text=" · ".join(partes),
            fg=self.COR_VERDE,
        )

    def alternar_tempo_automatico(self) -> None:
        """Inicia ou pausa o relógio: cada segundo equivale a cinco minutos."""

        if self.simulacao_automatica:
            self._parar_tempo_automatico()
            self.label_status_simulacao.config(
                text="Passagem automática de tempo pausada.",
                fg=self.COR_TEXTO_FRACO,
            )
            return

        em_andamento = any(
            _sessao_e_simulada(sessao)
            and sessao.status in ("Ativa", "Na fila")
            for sessao in self.sessoes
        )
        if not em_andamento:
            self.label_status_simulacao.config(
                text="Gere um cenário antes de iniciar o relógio.",
                fg=self.COR_TEXTO_FRACO,
            )
            return

        self.simulacao_automatica = True
        self.botao_tempo_automatico.config(text="Ⅱ  Pausar")
        self._passo_tempo_automatico()

    def _passo_tempo_automatico(self) -> None:
        self.timer_simulacao = None
        if not self.simulacao_automatica:
            return

        self.avancar_simulacao(5)
        ainda_em_andamento = any(
            _sessao_e_simulada(sessao)
            and sessao.status in ("Ativa", "Na fila")
            for sessao in self.sessoes
        )
        if self.simulacao_automatica and ainda_em_andamento:
            self.timer_simulacao = self.after(1000, self._passo_tempo_automatico)
        else:
            self._parar_tempo_automatico()
            self.label_status_simulacao.config(
                text="Simulação concluída · todos os veículos foram atendidos.",
                fg=self.COR_VERDE,
            )

    def _parar_tempo_automatico(self) -> None:
        if self.timer_simulacao is not None:
            try:
                self.after_cancel(self.timer_simulacao)
            except tk.TclError:
                pass
        self.timer_simulacao = None
        self.simulacao_automatica = False
        if hasattr(self, "botao_tempo_automatico"):
            self.botao_tempo_automatico.config(text="▶  Rodar tempo")

    def atualizar_painel_simulacao(self) -> None:
        simuladas = [
            sessao
            for sessao in self.sessoes
            if _sessao_e_simulada(sessao)
        ]
        ativas = [sessao for sessao in simuladas if sessao.status == "Ativa"]
        resumo = calcular_ocupacao_simulacao(simuladas)
        potencia_ativa = sum(sessao.potencia_kw for sessao in ativas)
        energia_total = sum(sessao.energia_kwh for sessao in simuladas)
        capacidade = resumo["capacidade"] if simuladas else 4
        self.vars_simulacao["tempo"].set(
            f"T+{self.tempo_simulado_minutos} min"
        )
        self.vars_simulacao["ocupacao"].set(
            f"{resumo['ativas']}/{capacidade}"
        )
        self.vars_simulacao["fila"].set(str(resumo["fila"]))
        self.vars_simulacao["potencia"].set(
            f"{potencia_ativa:.1f} kW".replace(".", ",")
        )
        self.vars_simulacao["energia"].set(
            f"{energia_total:.1f} kWh".replace(".", ",")
        )

        for item in self.tree_simulacao.get_children():
            self.tree_simulacao.delete(item)
        for indice, sessao in enumerate(simuladas):
            tags = ["par" if indice % 2 == 0 else "impar"]
            if sessao.status == "Ativa":
                tags.append("ativa")
                restante = f"{sessao.tempo_restante_minutos} min"
            elif sessao.status == "Na fila":
                tags.append("fila")
                posicao = 1
                for outra in simuladas:
                    if (
                        outra.estacao == sessao.estacao
                        and outra.status == "Na fila"
                        and outra.id_sessao < sessao.id_sessao
                    ):
                        posicao += 1
                restante = f"Fila #{posicao}"
            else:
                tags.append("finalizada")
                restante = "Concluída"
            self.tree_simulacao.insert(
                "",
                "end",
                iid=f"sim-{sessao.id_sessao}",
                values=(
                    sessao.id_sessao,
                    sessao.veiculo,
                    sessao.estacao,
                    sessao.tipo_usuario,
                    sessao.tipo_carregador,
                    f"{sessao.energia_kwh:.2f} kWh",
                    restante,
                    f"R$ {sessao.custo:.2f}",
                    sessao.status,
                ),
                tags=tuple(tags),
            )

    def atualizar_quantidade(self) -> None:
        quantidade = len(self.sessoes)
        palavra = "sessão armazenada" if quantidade == 1 else "sessões armazenadas"
        self.label_quantidade.config(text=f"{quantidade} {palavra}")

    def mostrar_detalhes_simulado(self, _evento=None) -> None:
        selecionados = self.tree_simulacao.selection()
        if not selecionados:
            return
        id_sessao = int(selecionados[0].removeprefix("sim-"))
        posicao = busca_sequencial(self.sessoes, id_sessao)
        if posicao != -1:
            messagebox.showinfo(
                "Detalhes da simulação",
                self.sessoes[posicao].detalhes(),
            )

    def atualizar_treeview(self, tree: ttk.Treeview) -> None:
        for item in tree.get_children():
            tree.delete(item)
        for indice, sessao in enumerate(self.sessoes):
            tags = ["par" if indice % 2 == 0 else "impar"]
            if sessao.status == "Ativa":
                tags.append("ativa")
            elif sessao.status == "Na fila":
                tags.append("fila")
            else:
                tags.append("finalizada")
            tree.insert(
                "",
                "end",
                iid=str(sessao.id_sessao),
                values=(
                    sessao.id_sessao,
                    sessao.veiculo,
                    sessao.tipo_usuario,
                    f"{sessao.potencia_kw:.2f} kW",
                    f"{sessao.tempo_minutos} min",
                    f"{sessao.energia_kwh:.2f} kWh",
                    f"R$ {sessao.custo:.2f}",
                    sessao.status,
                ),
                tags=tuple(tags),
            )

    def atualizar_tabela(self) -> None:
        self.atualizar_treeview(self.tree_sessoes)

    def mostrar_detalhes_selecionado(self, _evento=None) -> None:
        selecionados = self.tree_sessoes.selection()
        if not selecionados:
            return
        id_sessao = int(selecionados[0])
        posicao = busca_sequencial(self.sessoes, id_sessao)
        if posicao != -1:
            messagebox.showinfo("Detalhes da sessão", self.sessoes[posicao].detalhes())

    def buscar_sessao(self) -> None:
        """Pesquisa pelo ID usando a busca sequencial manual."""

        try:
            id_procurado = int(self.var_busca.get().strip())
            if id_procurado <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Busca inválida", "Digite um ID inteiro maior que zero.")
            return

        posicao = busca_sequencial(self.sessoes, id_procurado)
        if posicao == -1:
            texto = (
                f"Sessão com ID {id_procurado} não encontrada.\n\n"
                "A busca sequencial percorreu a lista e retornou -1."
            )
        else:
            texto = (
                f"Sessão encontrada na posição {posicao} da lista.\n"
                f"Busca Sequencial: O(n) no pior caso.\n\n"
                f"{self.sessoes[posicao].detalhes()}"
            )
        self._definir_texto(self.texto_busca, texto)

    def ordenar_sessoes(self) -> None:
        """Ordena a lista usando exclusivamente o Bubble Sort manual."""

        if not self.sessoes:
            messagebox.showwarning(
                "Sem sessões", "Cadastre pelo menos uma sessão antes de ordenar."
            )
            return
        criterio = CRITERIOS_ORDENACAO[self.var_criterio.get()]
        crescente = self.var_ordem.get() == "Crescente"
        bubble_sort(self.sessoes, criterio, crescente)
        self.atualizar_tabela()
        self.atualizar_treeview(self.tree_ordenacao)
        messagebox.showinfo(
            "Ordenação concluída",
            f"Sessões ordenadas por {self.var_criterio.get()}, "
            f"em ordem {self.var_ordem.get().lower()}.\n\n"
            "Algoritmo utilizado: Bubble Sort manual - O(n²).",
        )

    def atualizar_estatisticas(self) -> None:
        estatisticas = calcular_estatisticas(self.sessoes)
        if estatisticas is None:
            valores = {
                "quantidade": "0",
                "energia": "0,00 kWh",
                "faturamento": "R$ 0,00",
                "media": "R$ 0,00",
                "maior": "—",
                "menor": "—",
            }
        else:
            maior = estatisticas["maior_consumo"]
            menor = estatisticas["menor_consumo"]
            valores = {
                "quantidade": str(estatisticas["quantidade"]),
                "energia": f"{estatisticas['energia_total']:.2f} kWh",
                "faturamento": f"R$ {estatisticas['faturamento_total']:.2f}",
                "media": f"R$ {estatisticas['custo_medio']:.2f}",
                "maior": f"{maior.energia_kwh:.2f} kWh\nSessão #{maior.id_sessao}",
                "menor": f"{menor.energia_kwh:.2f} kWh\nSessão #{menor.id_sessao}",
            }
        for chave, valor in valores.items():
            self.vars_estatisticas[chave].set(valor)

    def atualizar_relatorio(self) -> None:
        self._definir_texto(self.texto_relatorio, gerar_relatorio_texto(self.sessoes))

    def copiar_relatorio(self) -> None:
        self.clipboard_clear()
        self.clipboard_append(gerar_relatorio_texto(self.sessoes))
        messagebox.showinfo("Relatório copiado", "O relatório foi copiado.")

    def salvar_relatorio(self) -> None:
        caminho = filedialog.asksaveasfilename(
            title="Salvar relatório",
            defaultextension=".txt",
            filetypes=(("Arquivo de texto", "*.txt"), ("Todos os arquivos", "*.*")),
            initialfile="relatorio_chargegrid_sprint3.txt",
        )
        if not caminho:
            return
        try:
            with open(caminho, "w", encoding="utf-8") as arquivo:
                arquivo.write(gerar_relatorio_texto(self.sessoes))
        except OSError as erro:
            messagebox.showerror("Erro ao salvar", f"Não foi possível salvar.\n{erro}")
            return
        messagebox.showinfo("Relatório salvo", "Relatório salvo com sucesso.")

    @staticmethod
    def _definir_texto(campo: ScrolledText, texto: str) -> None:
        campo.config(state="normal")
        campo.delete("1.0", tk.END)
        campo.insert("1.0", texto)
        campo.config(state="disabled")

    def encerrar(self) -> None:
        if messagebox.askyesno("Encerrar", "Deseja encerrar o ChargeGrid?"):
            self._parar_tempo_automatico()
            self.destroy()


def main() -> None:
    app = ChargeGridApp()
    app.mainloop()


if __name__ == "__main__":
    main()
