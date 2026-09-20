
# ChargeGrid Intelligence — Sprint 3
## Prototipagem Funcional e Integração

## 1. Equipe

- André Balan Felix dos Santos — RM 571691
- Davi Sinhorini Pacheco — RM 569487
- Gabriel da Silva Silveira — RM 568910
- Henrique de Souza Aragão — RM 570529
- João Vitor Jun Nishiye de Souza — RM 572079

---

## 2. Objetivo da Sprint 3

Demonstrar uma integração funcional entre:

1. lógica de autorização de sessão;
2. circuito lógico 74HC/Tinkercad da Sprint 2;
3. Arduino Uno;
4. sensor LDR;
5. LEDs e LCD;
6. comunicação serial;
7. Python como camada independente de validação e registro.

O ponto central é mostrar o fluxo de informação entre hardware/simulação e software, não apenas repetir a lógica das sprints anteriores.

---

## 3. Lógicas utilizadas

### 3.1 Módulo de sessão

```text
S_sessao = (AUTH · VAGA) + (VAGA · ENERGIA)
```

Onde:

- `AUTH` = usuário autenticado;
- `VAGA` = vaga disponível;
- `ENERGIA` = disponibilidade energética suficiente.

### 3.2 Módulo 74HC/Tinkercad

```text
P_74HC = D · ((A + B) · (C' + A))
```

Onde:

- `A` = energia solar;
- `B` = bateria acima de 40%;
- `C` = horário de pico;
- `D` = equipamento prioritário.

Os sinais A/B/C/D pertencem ao submódulo 74HC e não são reconstruídos a partir de AUTH/VAGA/ENERGIA/PRIORIDADE — `P_74HC` entra na integração como um sinal já produzido por esse módulo.

### 3.3 Integração final

```text
FINAL = S_sessao · (PRIORIDADE' + P_74HC)
```

Consequência:

- `PRIORIDADE=0` → `FINAL=S_sessao`;
- `PRIORIDADE=1` → `FINAL=S_sessao · P_74HC`.

Ou seja, o 74HC só interfere na autorização final quando existe uma solicitação prioritária.

---

## 4. Arquitetura

```text
       Tinkercad / 74HC
       A B C D
          |
          v
       P_74HC
          |
          v
+-----------------------+
|      Arduino Uno      |
|                       |
| AUTH / VAGA           |
| PRIORIDADE            |
| LDR -> ENERGIA_PCT    |
|                       |
| S_sessao              |
| FINAL                 |
+-----------+-----------+
            |
      +-----+-----+
      |           |
      v           v
   LEDs/LCD    Serial 9600
                  |
                  v
          +---------------+
          |    Python     |
          |               |
          | recalcula S   |
          | recalcula F   |
          | valida energia|
          | grava CSV     |
          +---------------+
```

### Integração física

Em uma montagem física:

```text
74HC OUT ----> Arduino D4 (P_74HC)
Arduino GND -> GND comum
Arduino 5V  -> alimentação conforme o circuito
```

Como `P_74HC` é uma saída CMOS, recomenda-se um resistor de pull-down externo (~10 kΩ) no D4 caso o módulo possa ficar desconectado.

No Wokwi, a chave P74HC representa o nível lógico da saída do 74HC.

---

## 5. Mapeamento de pinos

| Pino Arduino | Sinal | Tipo |
|---|---|---|
| D2 | AUTH | entrada ativa em LOW |
| D3 | VAGA | entrada ativa em LOW |
| D4 | P_74HC | entrada lógica ativa em HIGH |
| D5 | PRIORIDADE | entrada ativa em LOW |
| A0 | LDR | entrada analógica |
| D8 | LED verde | saída |
| D9 | LED amarelo | saída |
| D10 | LED vermelho | saída |
| A4 | LCD SDA | I2C |
| A5 | LCD SCL | I2C |

---

## 6. Protocolo serial

### Configuração

- Baud: `9600`
- Formato: `8N1`
- Direção: Arduino → Python
- Frequência: aproximadamente 1 Hz
- Terminador: CRLF

### Formato

```text
CG,AUTH,VAGA,ENERGIA,S_SESSAO,PRIORIDADE,P_74HC,FINAL,ENERGIA_PCT
```

Exemplo:

```text
CG,1,1,1,1,0,1,1,80
```

### Campos

| Campo | Tipo | Valores |
|---|---|---|
| CG | string | `CG` |
| AUTH | int | 0/1 |
| VAGA | int | 0/1 |
| ENERGIA | int | 0/1 |
| S_SESSAO | int | 0/1 |
| PRIORIDADE | int | 0/1 |
| P_74HC | int | 0/1 |
| FINAL | int | 0/1 |
| ENERGIA_PCT | int | 0–100 % |

---

## 7. Python como verificador independente

O Python **não confia** nos campos `S_SESSAO` e `FINAL` enviados pelo Arduino. Ele calcula:

```python
S_calc = (AUTH AND VAGA) OR (VAGA AND ENERGIA)

FINAL_calc = S_calc AND ((NOT PRIORIDADE) OR P_74HC)
```

Depois compara:

```text
Arduino S_SESSAO == Python S_calc
Arduino FINAL    == Python FINAL_calc
Arduino ENERGIA  == Python (ENERGIA_PCT >= 50)
```

Se todos forem iguais, o resultado é `Consistência: OK`; caso contrário, `Consistência: DIVERGENTE` — o que permite detectar qualquer divergência real entre o firmware e a camada Python.

---

## 8. Estados funcionais

| Condição | Estado | Potência de referência |
|---|---|---:|
| `FINAL=0` | BLOQUEADA | 0 kW |
| `FINAL=1` e energia <50% | LIMITADA | 11 kW |
| `FINAL=1` e energia >=50% | AUTORIZADA | 22 kW |

Os valores de potência são referências simuladas e não representam medição elétrica de um carregador real.

---

## 9. Cenários testados

| Cenário | AUTH | VAGA | ENERGIA | S_SESSAO | PRIORIDADE | P_74HC | FINAL |
|---|---:|---:|---:|---:|---:|---:|---:|
| Sessão normal | 1 | 1 | 1 | 1 | 0 | 0 | 1 |
| Energia baixa | 1 | 1 | 0 | 1 | 0 | 0 | 1 |
| Sem vaga | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| Prioridade liberada | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| Prioridade bloqueada | 1 | 1 | 1 | 1 | 1 | 0 | 0 |

Os cinco cenários foram executados no Wokwi e confirmados nos LEDs, no LCD e na linha serial recebida.

**Observação:** nos cenários acima, `P_74HC` é tratado como entrada externa já produzida pelo submódulo 74HC — os cenários 4 e 5 validam a integração dessa saída com o restante do sistema, mas não recalculam a lógica interna do 74HC (que dependeria de A/B/C/D, não disponíveis nesta camada).

---

## 10. Tabela verdade completa

Gere sob demanda com:

```bash
python python/chargegrid_sprint3.py --truth-table
```

Ela contém as 32 combinações do sistema. Regra importante:

- se `PRIORIDADE=0`, P_74HC não altera FINAL;
- se `PRIORIDADE=1`, P_74HC passa a ser requisito.

---

## 11. Execução

### 11.1 Python — demonstração

Na raiz do projeto:

```bash
python python/chargegrid_sprint3.py --demo
```

### 11.2 Python — teste exaustivo

```bash
python python/chargegrid_sprint3.py --self-test
```

Resultado esperado:

```text
SELF-TEST OK: 32 combinações verificadas.
Limiar de energia: 49% -> 0 | 50% -> 1
```

### 11.3 Python — tabela verdade

```bash
python python/chargegrid_sprint3.py --truth-table
```

### 11.4 Arduino real

Instale:

```bash
pip install -r python/requirements.txt
```

Depois:

```bash
python python/chargegrid_sprint3.py --serial COM3
```

Substitua `COM3` pela porta correta.

### 11.5 Wokwi

Abra o projeto com:

- `wokwi/sketch.ino`
- `wokwi/diagram.json`
- `wokwi/libraries.txt`

O LCD usa I2C em `0x27`. O diagrama já deixa o estado inicial configurado para uma sessão normal.

---

## 12. Como reproduzir os cenários no Wokwi

### Sessão normal

```text
AUTH=1, VAGA=1, PRIORIDADE=0, P74HC=0, LDR em iluminação suficiente
```

Esperado: `FINAL=1`, LED verde, LCD "RECARGA OK"

### Energia baixa

Reduza a iluminação do LDR até `ENERGIA_PCT < 50`.

Esperado: `FINAL=1`, LED amarelo, LCD "LIMITADA"

### Sem vaga

Desative VAGA.

Esperado: `S_SESSAO=0`, `FINAL=0`, LED vermelho, LCD "BLOQUEADA"

### Prioridade liberada

```text
PRIORIDADE=1, P_74HC=1, com sessão válida
```

Esperado: `FINAL=1`, LED verde, LCD "PRIORIDADE OK"

### Prioridade bloqueada

Mantenha `PRIORIDADE=1` e altere `P_74HC=0`.

Esperado: `FINAL=0`, LED vermelho, LCD "BLOQUEADA"

---

## 13. Conexão com a disciplina

O protótipo materializa conteúdos de:

- lógica booleana e expressões lógicas;
- decomposição de problemas;
- programação estruturada e condicionais;
- leitura de entradas e processamento de sinais;
- automação e comunicação serial;
- validação independente e registro de dados;
- integração entre hardware e software.

O ponto técnico central é a passagem de uma expressão booleana abstrata para uma decisão executada no Arduino e depois verificada por uma segunda implementação em Python.

---

## 14. Notas e limitações

- O LDR é um proxy de disponibilidade solar; não mede potência fotovoltaica real.
- `ENERGIA_PCT` é uma normalização do ADC, não um percentual real de bateria ou geração.
- Os valores de 11 kW e 22 kW são referências de automação, não medições reais.
- OCPP/MODBUS mencionados nas sprints anteriores permanecem como simulações, não são executados fisicamente nesta integração.
- O circuito Tinkercad e o Wokwi são ambientes complementares: o Wokwi representa a interface com `P_74HC` por meio de uma chave, sem simular internamente o circuito 74HC da Sprint 2.
- A saída real do circuito 74HC ainda precisa ser ligada fisicamente ao D4 para validar a integração elétrica em uma montagem física.

---

## 15. Arquivos

```text
pensamento-computacional-automacao-python/
├── README.md
└── ChargeGrid_Sprint3_Final/
    ├── python/
    │   ├── chargegrid_sprint3.py
    │   ├── requirements.txt
    │   └── resultados_sprint3.csv
    └── wokwi/
        ├── sketch.ino
        ├── diagram.json
        ├── libraries.txt
        └── wokwi_link.txt
```
