# Checklist final de autoavaliação — Sprint 3

## 1. Integração e funcionamento técnico — até 50 pts

| Item | Status | Evidência |
|---|---|---|
| Arquitetura hardware/software integrada | ✅ | Arduino + entradas + LDR + LEDs + LCD + Serial + Python |
| Lógica S_sessao implementada | ✅ | Firmware e Python |
| Lógica FINAL implementada | ✅ | Firmware e Python |
| Integração P_74HC | ✅ | Entrada digital D4; validada nos testes 4 e 5 |
| LDR/energia | ✅ | Leitura A0 e limiar de 50% |
| Estados visuais | ✅ | Verde, amarelo e vermelho confirmados |
| LCD | ✅ | Mensagens confirmadas nos 5 cenários |
| Serial | ✅ | Telemetria confirmada |
| Cinco cenários funcionais | ✅ | Executados no Wokwi |
| Validação independente Python | ✅ | Recalcula S_sessao e FINAL |
| Registro/CSV | ✅ | Implementado |
| Demonstração técnica | ⚠️ | Depende da gravação final do vídeo |

### Risco de perda de pontos

Baixo para o que foi testado no Wokwi. O principal risco restante nesta categoria é a apresentação: o vídeo precisa mostrar claramente as mudanças de entrada e as respectivas saídas. Não se deve apresentar a chave P_74HC do Wokwi como se fosse o circuito 74HC físico.

## 2. Justificativa e alinhamento com a disciplina — até 25 pts

| Item | Status |
|---|---|
| Álgebra Booleana | ✅ |
| Lógica digital | ✅ |
| Circuito 74HC | ✅ |
| Automação | ✅ |
| Programação/firmware | ✅ |
| Sensoriamento | ✅ |
| Energia renovável | ✅ |
| Integração hardware/software | ✅ |
| Validação por implementação independente | ✅ |

### Risco de perda de pontos

Baixo a moderado, dependendo da apresentação oral. Explique claramente que existem dois módulos lógicos diferentes (`S_sessao` e `P_74HC`) e que `FINAL` é a regra nova que os integra. Deixe claro que o LDR é um proxy de disponibilidade solar, não uma medição real de potência fotovoltaica.

## 3. Organização do repositório e documentação técnica — até 25 pts

| Item | Status |
|---|---|
| Código Arduino | ✅ |
| Código Python | ✅ |
| diagram.json | ✅ |
| libraries.txt | ✅ |
| Arquitetura | ✅ |
| Protocolo serial | ✅ |
| Resultados | ✅ |
| Tabela verdade | ✅ |
| Roteiro | ✅ |
| README | ✅ |
| Evidências de execução | ✅ |
| entrega.txt | ✅, após preencher os dois links |
| GitHub publicado | ⏳, ação do grupo |
| Vídeo publicado | ⏳, ainda não gravado |

### Risco de perda de pontos

Moderado até o GitHub e vídeo serem finalizados. O conteúdo técnico está organizado, mas a avaliação pode ser prejudicada se o GitHub não tiver a estrutura correta, se o README não explicar como executar, se o vídeo não mostrar evidências ou se os links permanecerem como placeholders.

## Risco técnico residual

A validação confirmada é de simulação Wokwi. Não deve ser afirmado que houve validação elétrica de uma montagem física real do circuito 74HC conectado ao Arduino.

Também não devem ser apresentados como medições reais: `ENERGIA_PCT`, 11 kW e 22 kW. São valores da simulação/política de referência.
