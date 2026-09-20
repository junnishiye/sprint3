
# ChargeGrid Intelligence — Sprint 3
## Prototipagem Funcional e Integração

> **Versão final auditada**  
> Esta versão corrige inconsistências encontradas no pacote anterior e separa claramente o que foi matematicamente validado, o que foi executado em Python e o que ainda precisa ser testado no Arduino/Wokwi.

---

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

O ponto central não é apenas repetir a lógica anterior, mas mostrar o fluxo de informação entre hardware/simulação e software.

---

## 3. Lógicas utilizadas

### 3.1 Módulo de sessão

Regra herdada:

```text
S_sessao = (AUTH · VAGA) + (VAGA · ENERGIA)
```

Onde:

- `AUTH` = usuário autenticado;
- `VAGA` = vaga disponível;
- `ENERGIA` = disponibilidade energética suficiente.

### 3.2 Módulo 74HC/Tinkercad

Regra herdada:

```text
P_74HC = D · ((A + B) · (C' + A))
```

Onde:

- `A` = energia solar;
- `B` = bateria acima de 40%;
- `C` = horário de pico;
- `D` = equipamento prioritário.

**Importante:** os sinais A/B/C/D pertencem ao submódulo 74HC. Eles não podem ser reconstruídos a partir de AUTH/VAGA/ENERGIA/PRIORIDADE.

### 3.3 Nova integração da Sprint 3

A regra criada para integrar os módulos é:

```text
FINAL = S_sessao · (PRIORIDADE' + P_74HC)
```

Consequência:

- `PRIORIDADE=0` -> `FINAL=S_sessao`;
- `PRIORIDADE=1` -> `FINAL=S_sessao · P_74HC`.

Assim, o 74HC só interfere na autorização final quando existe solicitação prioritária.

---

## 4. Auditoria da versão anterior

Foram encontrados os seguintes problemas no pacote anterior:

### 4.1 P74HC estava com polaridade invertida no Arduino

O código anterior tratava:

```cpp
LOW -> P_74HC = 1
HIGH -> P_74HC = 0
```

Isso é incompatível com a interpretação normal de uma saída lógica 74HC ativa em nível alto.

**Correção:** nesta versão:

```cpp
P_74HC = HIGH ? 1 : 0;
```

### 4.2 O Wokwi não tinha entradas reais para PRIORIDADE e P74HC

O firmware lia D4 e D5, mas o `diagram.json` anterior não disponibilizava controles ligados a esses pinos.

**Correção:** o diagrama final possui quatro chaves:
- AUTH;
- VAGA;
- PRIORIDADE;
- P74HC.

No caso de P74HC, a chave apenas simula o nível lógico que, em uma montagem física, virá do circuito 74HC.

### 4.3 Os pinos dos pushbuttons do diagrama anterior estavam ambíguos

A documentação atual do Wokwi identifica os contatos do pushbutton como `1.l`, `1.r`, `2.l` e `2.r`.

**Correção:** esta versão usa `wokwi-slide-switch`, simplificando a reprodução dos estados 0/1.

### 4.4 A direção do LDR estava incorreta

No módulo fotoresistor, maior iluminação reduz a leitura analógica AO. Portanto, tratar ADC alto como “mais energia” invertia o significado físico.

**Correção:** a leitura é normalizada de forma inversa:

```text
0 ADC    -> 100%
1023 ADC -> 0%
```

Isso representa apenas um **proxy de disponibilidade solar**, não geração elétrica real.

### 4.5 O limiar do firmware não estava alinhado ao controle Python

O código anterior usava aproximadamente ADC=500 para `ENERGIA`, enquanto o Python usava 50%.

**Correção:** ambos usam exatamente:

```text
ENERGIA = 1 quando ENERGIA_PCT >= 50
```

### 4.6 O modo serial anterior perdia as linhas ao pressionar Ctrl+C

A versão anterior acumulava as linhas em uma função que não devolvia os dados quando a interrupção ocorria.

**Correção:** `serial_loop()` captura a interrupção, retorna as linhas recebidas e `main()` grava o CSV.

---

## 5. Arquitetura

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

Como `P_74HC` é uma saída CMOS, recomenda-se um resistor de pull-down externo (~10 kΩ) no D4 se houver possibilidade de o módulo ficar desconectado.

No Wokwi, a chave P74HC representa o nível lógico da saída do 74HC.

---

## 6. Mapeamento de pinos

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

## 7. Protocolo serial

### Configuração

- Baud: `9600`
- Formato: `8N1`
- Direção demonstrada: Arduino -> Python
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

## 8. Python como verificador independente

O Python **não confia** nos campos `S_SESSAO` e `FINAL` enviados pelo Arduino.

Ele calcula:

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

Se todos forem iguais:

```text
Consistência: OK
```

Caso contrário:

```text
Consistência: DIVERGENTE
```

Isso permite detectar uma divergência real entre firmware e camada Python.

---

## 9. Estados funcionais

A política de automação demonstrativa é:

| Condição | Estado | Potência de referência |
|---|---|---:|
| `FINAL=0` | BLOQUEADA | 0 kW |
| `FINAL=1` e energia <50% | LIMITADA | 11 kW |
| `FINAL=1` e energia >=50% | AUTORIZADA | 22 kW |

Os valores de potência são referências simuladas. Não representam medição elétrica nem controle de um carregador real.

---

## 10. Cenários validados matematicamente

| Cenário | AUTH | VAGA | ENERGIA | S_SESSAO | PRIORIDADE | P_74HC | FINAL |
|---|---:|---:|---:|---:|---:|---:|---:|
| Sessão normal | 1 | 1 | 1 | 1 | 0 | 0 | 1 |
| Energia baixa | 1 | 1 | 0 | 1 | 0 | 0 | 1 |
| Sem vaga | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| Prioridade liberada | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| Prioridade bloqueada | 1 | 1 | 1 | 1 | 1 | 0 | 0 |

### Ponto que não pode ser omitido

`P_74HC` não pode ser matematicamente recalculado a partir das cinco colunas acima.

Para verificar `P_74HC` pela fórmula da Sprint 2 seriam necessários:

```text
A_solar
B_bateria
C_pico
D_prioridade
```

Nos cinco cenários, P_74HC é tratado como **entrada externa já produzida pelo submódulo 74HC**.

Portanto, os cenários 4 e 5 validam a integração da saída do 74HC, mas não constituem uma prova independente da lógica interna do 74HC.

---

## 11. Tabela verdade completa

Gere sob demanda com:

```bash
python python/chargegrid_sprint3.py --truth-table
```

Ela contém as 32 combinações do sistema.

Regra importante:

- se `PRIORIDADE=0`, P_74HC não altera FINAL;
- se `PRIORIDADE=1`, P_74HC passa a ser requisito.

---

## 12. Execução

### 12.1 Python — demonstração

Na raiz do projeto:

```bash
python python/chargegrid_sprint3.py --demo
```

### 12.2 Python — teste exaustivo

```bash
python python/chargegrid_sprint3.py --self-test
```

Resultado esperado:

```text
SELF-TEST OK: 32 combinações verificadas.
Limiar de energia: 49% -> 0 | 50% -> 1
```

### 12.3 Python — tabela verdade

```bash
python python/chargegrid_sprint3.py --truth-table
```

### 12.4 Arduino real

Instale:

```bash
pip install -r python/requirements.txt
```

Depois:

```bash
python python/chargegrid_sprint3.py --serial COM3
```

Substitua `COM3` pela porta correta.

### 12.5 Wokwi

Abra o projeto com:

- `wokwi/sketch.ino`
- `wokwi/diagram.json`
- `wokwi/libraries.txt`

O LCD usa I2C em `0x27`.

O diagrama já deixa o estado inicial configurado para uma sessão normal.

---

## 13. Como reproduzir os cenários no Wokwi

### Sessão normal

- AUTH = 1
- VAGA = 1
- PRIORIDADE = 0
- P74HC = 0
- LDR em iluminação suficiente

Esperado:

```text
FINAL=1
LED verde
RECARGA OK
```

### Energia baixa

Reduza a iluminação do LDR até:

```text
ENERGIA_PCT < 50
```

Esperado:

```text
FINAL=1
LED amarelo
LIMITADA
```

### Sem vaga

Desative VAGA.

Esperado:

```text
S_SESSAO=0
FINAL=0
LED vermelho
BLOQUEADA
```

### Prioridade liberada

Configure:

```text
PRIORIDADE=1
P_74HC=1
```

com sessão válida.

Esperado:

```text
FINAL=1
LED verde
PRIORIDADE OK
```

### Prioridade bloqueada

Mantenha:

```text
PRIORIDADE=1
```

e altere:

```text
P_74HC=0
```

Esperado:

```text
FINAL=0
LED vermelho
BLOQUEADA
```

---

## 14. Conexão com a disciplina

O protótipo materializa conteúdos de:

- lógica booleana;
- expressões e operações lógicas;
- decomposição de problemas;
- programação estruturada;
- condicionais;
- leitura de entradas;
- processamento de sinais;
- automação;
- comunicação serial;
- validação independente;
- registro de dados em CSV;
- integração entre hardware e software.

O ponto técnico central é a passagem de uma expressão booleana abstrata para uma decisão executada no Arduino e depois verificada por uma segunda implementação em Python.

---

## 15. Limitações e riscos

### Não testado neste ambiente

1. **O Arduino não foi compilado com o toolchain oficial do Arduino neste ambiente.**
2. **O firmware não foi executado de fato no Wokwi neste ambiente.**
3. **O `diagram.json` foi validado como JSON, mas não foi executado pelo simulador Wokwi aqui.**
4. A biblioteca `LiquidCrystal_I2C` precisa estar disponível/instalada no projeto Wokwi.
5. A saída real do circuito 74HC ainda precisa ser ligada fisicamente ao D4 para validar a integração elétrica.
6. O LDR é um proxy de disponibilidade solar; não mede potência fotovoltaica.
7. `ENERGIA_PCT` é uma normalização do ADC, não percentual real de bateria ou geração.
8. Os 11 kW e 22 kW são valores de referência de automação.
9. OCPP/MODBUS das Sprints anteriores não são executados fisicamente nesta integração; permanecem como simulações.
10. O circuito Tinkercad e o Wokwi são dois ambientes complementares. O Wokwi simula a interface com P_74HC por uma chave, não simula internamente o circuito 74HC da Sprint 2.

### Risco que deve ser resolvido antes do vídeo oficial

**Rodar o firmware no Wokwi antes da gravação.**

O resultado mínimo que precisa ser confirmado é:

```text
AUTH=1 VAGA=1 ENERGIA>=50 PRIORIDADE=0 -> LED verde
PRIORIDADE=1 P74HC=1                 -> LED verde
PRIORIDADE=1 P74HC=0                 -> LED vermelho
ENERGIA<50 e FINAL=1                 -> LED amarelo
VAGA=0                               -> LED vermelho
```

Também é necessário confirmar que o Serial Monitor apresenta exatamente nove campos no formato documentado.

---

## 16. Arquivos

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

---

## 17. Conclusão técnica

A arquitetura é matematicamente consistente quando `P_74HC` é tratado como entrada externa e quando as polaridades elétricas são respeitadas.

A integração final é:

```text
Tinkercad/74HC
      |
   P_74HC
      |
      v
Arduino -> S_sessao -> FINAL -> LEDs/LCD
                         |
                         v
                      Serial
                         |
                         v
                      Python
                         |
                         v
                       CSV
```

O ponto que ainda impede chamar o pacote de “validado de ponta a ponta” é a ausência de uma execução real do firmware no Wokwi/Arduino neste ambiente. Essa execução deve ser feita antes da gravação e da entrega oficial.
