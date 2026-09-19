# Arquitetura — Sprint 3

## Lógicas

```text
S_sessao = (AUTH · VAGA) + (VAGA · ENERGIA)

P_74HC = D · ((A + B) · (C' + A))

FINAL = S_sessao · (PRIORIDADE' + P_74HC)
```

## Fluxo validado no Wokwi

```text
Entradas digitais + LDR
          |
          v
       Arduino
          |
   +------+------+
   |             |
S_sessao       P_74HC
   |             |
   +------+------+
          |
        FINAL
          |
     +----+----+
     |         |
   LEDs       LCD
          |
          v
     Serial 9600
          |
          v
        Python
```

## Cinco cenários executados

1. Sessão normal → verde / `RECARGA OK`
2. Energia baixa → amarelo / `LIMITADA`
3. Sem vaga → vermelho / `BLOQUEADA`
4. Prioridade liberada → verde / `PRIORIDADE OK`
5. Prioridade bloqueada → vermelho / `BLOQUEADA`

Os cinco cenários foram executados no Wokwi e confirmados conforme o comportamento esperado.

## Limite da integração

No Wokwi, `P_74HC` é representado por uma chave que fornece o nível lógico externo ao D4. Em uma montagem física, a saída do circuito 74HC deve ser conectada ao D4 com referência de GND comum.

O circuito 74HC não é reconstruído internamente no Wokwi nesta versão; o objetivo da simulação é validar a integração do seu sinal de saída com o firmware.
