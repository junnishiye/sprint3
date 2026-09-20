# EV Challenge - GoodWe | Sprint 03

Chatbot de apoio à operação de **eletropostos e carregadores GoodWe**, reconstruído como um **agente de Inteligência Artificial com LangGraph**, utilizando memória por sessão, guardrails de segurança, ferramentas especializadas e seleção de modelo baseada em experimentos.

##  Visão Geral

A Sprint 03 evolui a solução desenvolvida nas Sprints 01 e 02 para uma arquitetura baseada em **agentes de IA**.

O agente é capaz de:

* Responder dúvidas relacionadas à operação de eletropostos e carregadores GoodWe;
* Consultar uma base de conhecimento GoodWe;
* Calcular tempo estimado de recarga;
* Estimar custo de recarga;
* Auxiliar no dimensionamento de eletropostos;
* Manter contexto e memória durante uma sessão;
* Utilizar ferramentas automaticamente por meio de **tool calling**;
* Aplicar guardrails de entrada e saída;
* Detectar tentativas de prompt injection;
* Filtrar possíveis instruções maliciosas presentes nos resultados das ferramentas.

---

##  Arquitetura

```text
START -> guardrail_entrada --(bloqueado)--> END
              |
          (liberado)
              v
           agente  <-->  ferramentas
              |          (loop de tool calling)
              |
      (sem tool_calls)
              v
        guardrail_saida -> END
```

O fluxo principal funciona da seguinte forma:

1. A mensagem do usuário passa pelo `guardrail_entrada`.
2. Caso seja identificada uma solicitação inválida, perigosa ou fora do escopo, o fluxo é encerrado.
3. Caso a entrada seja liberada, ela segue para o agente.
4. O agente pode chamar uma ou mais ferramentas.
5. Os resultados das ferramentas retornam ao agente.
6. O processo continua enquanto existirem `tool_calls`.
7. Quando o agente produz a resposta final, ela passa pelo `guardrail_saida`.
8. A resposta validada é então entregue ao usuário.

---

##  Tecnologias e Framework

O projeto utiliza **LangGraph** para controlar o fluxo do agente.

Principais componentes utilizados:

* `StateGraph`
* `add_messages`
* `add_conditional_edges`
* `MemorySaver`

O LangGraph permite estruturar o comportamento do agente como um grafo, controlando decisões, chamadas de ferramentas, memória e mecanismos de segurança.

---

##  Modelo de IA

Modelo selecionado:

```text
gpt-4o-mini
Temperatura: 0.2
```

A escolha do modelo foi realizada com base nos experimentos documentados em:

```text
relatorio_modelos.md
```

Foram comparados diferentes modelos e configurações considerando critérios como:

* qualidade das respostas;
* segurança;
* memória;
* consumo de tokens;
* latência.

O `gpt-4o-mini` com temperatura `0.2` apresentou o melhor equilíbrio para o cenário avaliado.

---

##  Memória

O agente utiliza `MemorySaver` como checkpointer do LangGraph.

A memória é separada utilizando:

```text
thread_id
```

Cada `thread_id` representa uma sessão ou conversa independente.

Isso permite que o agente mantenha informações mencionadas anteriormente durante a mesma conversa sem misturar o contexto entre usuários ou sessões diferentes.

---

##  Ferramentas do Agente

O agente possui quatro ferramentas principais.

### `buscar_base_goodwe`

Realiza consultas à base de conhecimento relacionada aos equipamentos e soluções GoodWe.

### `calcular_tempo_recarga`

Calcula o tempo estimado necessário para realizar a recarga de um veículo elétrico.

### `estimar_custo_recarga`

Calcula uma estimativa de custo financeiro para uma recarga.

### `dimensionar_eletroposto`

Auxilia no dimensionamento de um eletroposto considerando informações fornecidas pelo usuário.

O agente decide automaticamente quando uma ferramenta deve ser utilizada.

---

##  Guardrails

A solução possui diferentes camadas de proteção.

### Guardrail de Entrada

Responsável por analisar as solicitações antes que elas cheguem ao agente.

Entre as verificações estão:

* prompt injection;
* solicitações fora do escopo;
* tentativas de manipulação das instruções do sistema;
* questões relacionadas à segurança elétrica.

### Guardrail de Saída

Analisa a resposta final antes de entregá-la ao usuário.

Possui mecanismos para:

* evitar vazamento de informações internas;
* impedir exposição de prompts e instruções privadas;
* adicionar disclaimers quando necessário;
* reforçar recomendações relacionadas à segurança elétrica.

### Proteção contra Prompt Injection Indireta

Os resultados retornados pelas ferramentas também passam por uma camada de filtragem.

Isso reduz o risco de uma fonte externa inserir instruções maliciosas tentando modificar o comportamento do agente.

---

##  Estrutura do Projeto

```text
sprint03_goodwe/
│
├── notebooks/
│   └── sprint03_goodwe_agentes.ipynb
│
├── src/
│   ├── goodwe_agente.py
│   └── app_cli.py
│
├── testes/
│   ├── casos_de_teste.md
│   ├── casos_de_teste.json
│   ├── resultados_testes.csv
│   └── resultados_testes.json
│
├── relatorios/
│   └── relatorio_evolucao_sprint03.pdf
│
├── relatorio_modelos.md
├── integrantes.txt
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

### Principais arquivos

| Arquivo                                      | Descrição                                                    |
| -------------------------------------------- | ------------------------------------------------------------ |
| `notebooks/sprint03_goodwe_agentes.ipynb`    | Pipeline completo desenvolvido para execução no Google Colab |
| `src/goodwe_agente.py`                       | Núcleo do agente e definição do grafo LangGraph              |
| `src/app_cli.py`                             | Interface de chat via linha de comando                       |
| `relatorio_modelos.md`                       | Comparação dos modelos utilizados nos experimentos           |
| `testes/casos_de_teste.md`                   | Casos utilizados para validação da solução                   |
| `testes/casos_de_teste.json`                 | Casos de teste em formato estruturado                        |
| `testes/resultados_testes.csv`               | Resultados e métricas dos testes                             |
| `testes/resultados_testes.json`              | Resultados estruturados em JSON                              |
| `relatorios/relatorio_evolucao_sprint03.pdf` | Relatório de evolução da Sprint 03                           |
| `integrantes.txt`                            | Integrantes responsáveis pelo projeto                        |
| `.env.example`                               | Exemplo das variáveis de ambiente necessárias                |
| `requirements.txt`                           | Dependências Python do projeto                               |

---

##  Como Executar Localmente

### 1. Clone o repositório

```bash
git clone <URL_DO_REPOSITORIO>
cd sprint03_goodwe
```

### 2. Crie o ambiente virtual

Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
```

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

Crie o arquivo `.env` a partir do exemplo:

Linux/macOS:

```bash
cp .env.example .env
```

Windows:

```bash
copy .env.example .env
```

Depois, configure a variável:

```env
OPENAI_API_KEY=sua_chave_aqui
```

### 5. Execute o chatbot

```bash
python src/app_cli.py
```

---

## Segurança das Credenciais

As credenciais utilizadas pelo projeto ficam somente no arquivo:

```text
.env
```

Esse arquivo está incluído no `.gitignore` e, portanto, **não deve ser enviado ao GitHub**.

O repositório disponibiliza apenas:

```text
.env.example
```

como referência para configuração.

> Nenhuma API Key ou credencial deve aparecer diretamente no código-fonte.

---

##  Testes

Os testes utilizados para avaliar o agente estão disponíveis em:

```text
testes/casos_de_teste.md
testes/casos_de_teste.json
```

Os resultados das execuções estão disponíveis em:

```text
testes/resultados_testes.csv
testes/resultados_testes.json
```

As avaliações consideram aspectos como:

* qualidade da resposta;
* aderência ao contexto GoodWe;
* segurança;
* utilização da memória;
* comportamento das ferramentas;
* tokens utilizados;
* latência.

---

##  Resultados

Comparação entre a solução anterior e a arquitetura desenvolvida na Sprint 03:

| Métrica            | Sprints 01-02 | Sprint 03 |
| ------------------ | ------------: | --------: |
| Nota média (0-10)  |          6.77 |  **9.73** |
| Nota em segurança  |          5.42 |  **9.92** |
| Nota em memória    |          5.33 |  **9.67** |
| Tokens por turno   |           911 |      1389 |
| Latência por turno |         1.38s |     1.40s |

Os resultados mostram uma evolução significativa principalmente em:

* qualidade geral;
* segurança;
* capacidade de manter contexto;
* confiabilidade das respostas.

A melhoria ocorreu com um aumento no consumo médio de tokens, porém com impacto mínimo na latência observada.

---

##  Evolução da Sprint 03

A principal evolução da Sprint 03 foi a transformação do chatbot tradicional em um agente estruturado com LangGraph.

Entre as melhorias implementadas estão:

* arquitetura baseada em grafo;
* memória persistente por sessão;
* chamadas automáticas de ferramentas;
* guardrails de entrada;
* guardrails de saída;
* proteção contra prompt injection;
* proteção contra prompt injection indireta;
* experimentação e comparação de modelos;
* testes estruturados;
* coleta de métricas;
* organização modular do código.

O detalhamento completo está disponível em:

```text
relatorios/relatorio_evolucao_sprint03.pdf
```

---

##  EV Challenge - GoodWe

Projeto desenvolvido para o **EV Challenge - GoodWe | Sprint 03**, explorando a aplicação prática de agentes de Inteligência Artificial no suporte à operação de carregadores e eletropostos.

A solução combina:

**IA Generativa + LangGraph + Memória + Tools + Guardrails + Testes e Métricas**

com foco em construir uma experiência mais segura, contextual e especializada para o domínio de mobilidade elétrica.

