# Resultados — Sprint 3

## Validação executada

Os cinco cenários foram executados no Wokwi. Em todos os casos, os LEDs, o LCD e a linha de telemetria serial apresentaram o comportamento esperado.

| Cenário | Entradas principais | S_SESSAO | FINAL | LED | LCD |
|---|---|---:|---:|---|---|
| 1. Sessão normal | AUTH=1, VAGA=1, energia suficiente, prioridade=0 | 1 | 1 | Verde | `RECARGA OK` |
| 2. Energia baixa | AUTH=1, VAGA=1, energia abaixo de 50%, prioridade=0 | 1 | 1 | Amarelo | `LIMITADA` |
| 3. Sem vaga | AUTH=1, VAGA=0 | 0 | 0 | Vermelho | `BLOQUEADA` |
| 4. Prioridade liberada | AUTH=1, VAGA=1, energia suficiente, prioridade=1, P74HC=1 | 1 | 1 | Verde | `PRIORIDADE OK` |
| 5. Prioridade bloqueada | AUTH=1, VAGA=1, energia suficiente, prioridade=1, P74HC=0 | 1 | 0 | Vermelho | `BLOQUEADA` |

## Telemetria

Formato validado:

```text
CG,AUTH,VAGA,ENERGIA,S_SESSAO,PRIORIDADE,P_74HC,FINAL,ENERGIA_PCT
```

A validação confirmou que a linha serial acompanha os cenários esperados.

## Observação sobre valores numéricos

Os valores específicos de `ENERGIA_PCT` e os tempos medidos de resposta do Wokwi não foram registrados numericamente nesta etapa da conversa. Portanto, eles não são inventados nem apresentados como se tivessem sido medidos. Durante a gravação, deve-se mostrar o valor real do Serial Monitor.

## Limites

- A validação é de simulação Wokwi.
- `P_74HC` é representado por uma entrada digital no Wokwi.
- O LDR é um proxy de disponibilidade solar.
- Os valores de potência de 11 kW e 22 kW são referências simuladas.
- OCPP/MODBUS permanecem simulados.
