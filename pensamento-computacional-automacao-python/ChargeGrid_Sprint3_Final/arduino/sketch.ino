/*
  ChargeGrid Intelligence — Sprint 3
  Prototipagem Funcional e Integração

  INTEGRAÇÃO:
    - Módulo de sessão:
        S_sessao = (AUTH · VAGA) + (VAGA · ENERGIA)

    - Módulo 74HC/Tinkercad da Sprint 2:
        P_74HC = D · ((A_solar + B_bateria) · (C_pico' + A_solar))

      O resultado P_74HC chega ao Arduino como um sinal digital externo.
      Neste firmware, P_74HC é ATIVO EM NÍVEL ALTO:
        HIGH -> P_74HC = 1
        LOW  -> P_74HC = 0

    - Nova regra de integração da Sprint 3:
        FINAL = S_sessao · (PRIORIDADE' + P_74HC)

  IMPORTANTE:
    AUTH, VAGA e PRIORIDADE são entradas locais com INPUT_PULLUP,
    portanto são ativas em nível baixo:
      LOW  -> valor lógico 1
      HIGH -> valor lógico 0

    P_74HC é diferente: ele vem de uma saída lógica do circuito 74HC,
    portanto é lido diretamente:
      HIGH -> valor lógico 1
      LOW  -> valor lógico 0

  ENERGIA:
    O LDR é apenas um sensor/proxy de disponibilidade solar.
    O firmware transforma a leitura ADC em um percentual NORMALIZADO:
      0 ADC   -> 100%
      1023 ADC -> 0%

    Assim, mais luz => maior "energia disponível".
    ENERGIA = 1 quando ENERGIA_PCT >= 50%.

    Isso NÃO representa kW reais nem uma medição de geração fotovoltaica.

  TELEMETRIA:
    CG,AUTH,VAGA,ENERGIA,S_SESSAO,PRIORIDADE,P_74HC,FINAL,ENERGIA_PCT
    Exemplo:
    CG,1,1,1,1,0,1,1,80
*/

#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// -----------------------------
// Entradas
// -----------------------------
const byte PIN_AUTH       = 2;   // INPUT_PULLUP: LOW = 1 lógico
const byte PIN_VAGA       = 3;   // INPUT_PULLUP: LOW = 1 lógico
const byte PIN_74HC_OK    = 4;   // saída externa do 74HC: HIGH = 1 lógico
const byte PIN_PRIORIDADE = 5;   // INPUT_PULLUP: LOW = 1 lógico
const byte PIN_LDR        = A0;  // sensor de disponibilidade solar

// -----------------------------
// Saídas
// -----------------------------
const byte LED_VERDE    = 8;   // autorizada
const byte LED_AMARELO  = 9;   // limitada
const byte LED_VERMELHO = 10;  // bloqueada

// -----------------------------
// Temporização
// -----------------------------
const unsigned long INTERVALO_TELEMETRIA_MS = 1000;

// LCD I2C 16x2, endereço padrão do módulo Wokwi
LiquidCrystal_I2C lcd(0x27, 16, 2);

unsigned long ultimoEnvio = 0;

// ---------------------------------------------------------
// Converte a entrada INPUT_PULLUP para lógica positiva.
// ---------------------------------------------------------
int lerAtivoBaixo(byte pino) {
  return (digitalRead(pino) == LOW) ? 1 : 0;
}

// ---------------------------------------------------------
// Calcula a lógica de sessão herdada.
// S_sessao = (AUTH · VAGA) + (VAGA · ENERGIA)
// ---------------------------------------------------------
int calcularSessao(int auth, int vaga, int energia) {
  return (auth && vaga) || (vaga && energia);
}

// ---------------------------------------------------------
// Nova regra de integração da Sprint 3.
// FINAL = S_sessao · (PRIORIDADE' + P_74HC)
// ---------------------------------------------------------
int calcularFinal(int sSessao, int prioridade, int p74hc) {
  return sSessao && ((!prioridade) || p74hc);
}

// ---------------------------------------------------------
// Converte ADC do LDR em um percentual normalizado.
// O módulo fotoresistor do Wokwi reduz a tensão AO quando
// aumenta a iluminação; por isso a escala é invertida.
// ---------------------------------------------------------
int calcularEnergiaPct(int ldr) {
  int pct = map(ldr, 1023, 0, 0, 100);
  return constrain(pct, 0, 100);
}

// ---------------------------------------------------------
// Atualiza os LEDs.
// Estado 1: FINAL=1 e energia >= 50% -> verde
// Estado 2: FINAL=1 e energia < 50%  -> amarelo
// Estado 3: FINAL=0                  -> vermelho
// ---------------------------------------------------------
void atualizarLeds(int finalOk, int energiaOk) {
  digitalWrite(LED_VERDE, LOW);
  digitalWrite(LED_AMARELO, LOW);
  digitalWrite(LED_VERMELHO, LOW);

  if (finalOk && energiaOk) {
    digitalWrite(LED_VERDE, HIGH);
  } else if (finalOk && !energiaOk) {
    digitalWrite(LED_AMARELO, HIGH);
  } else {
    digitalWrite(LED_VERMELHO, HIGH);
  }
}

// ---------------------------------------------------------
// Mostra o estado no LCD.
// Linha 1: entradas principais.
// Linha 2: estado final.
// ---------------------------------------------------------
void atualizarLCD(int auth, int vaga, int energiaPct,
                  int prioridade, int p74hc, int finalOk) {
  lcd.setCursor(0, 0);
  lcd.print("A:");
  lcd.print(auth);
  lcd.print(" V:");
  lcd.print(vaga);
  lcd.print(" E:");
  if (energiaPct < 100) lcd.print(" ");
  if (energiaPct < 10)  lcd.print(" ");
  lcd.print(energiaPct);
  lcd.print("%");

  // Limpa o restante da primeira linha.
  lcd.print("   ");

  lcd.setCursor(0, 1);

  if (!finalOk) {
    lcd.print("BLOQUEADA       ");
  } else if (energiaPct < 50) {
    lcd.print("LIMITADA        ");
  } else if (prioridade && p74hc) {
    lcd.print("PRIORIDADE OK   ");
  } else {
    lcd.print("RECARGA OK      ");
  }
}

// ---------------------------------------------------------
// Envia uma linha de telemetria CSV.
// Ordem fixa:
// CG,
// AUTH,
// VAGA,
// ENERGIA,
// S_SESSAO,
// PRIORIDADE,
// P_74HC,
// FINAL,
// ENERGIA_PCT
// ---------------------------------------------------------
void enviarTelemetria(int auth, int vaga, int energia,
                      int sSessao, int prioridade, int p74hc,
                      int finalOk, int energiaPct) {
  Serial.print("CG,");
  Serial.print(auth);       Serial.print(",");
  Serial.print(vaga);       Serial.print(",");
  Serial.print(energia);    Serial.print(",");
  Serial.print(sSessao);    Serial.print(",");
  Serial.print(prioridade); Serial.print(",");
  Serial.print(p74hc);     Serial.print(",");
  Serial.print(finalOk);    Serial.print(",");
  Serial.println(energiaPct);
}

void setup() {
  // Entradas ativas em LOW para os controles locais.
  pinMode(PIN_AUTH, INPUT_PULLUP);
  pinMode(PIN_VAGA, INPUT_PULLUP);
  pinMode(PIN_PRIORIDADE, INPUT_PULLUP);

  // P74HC é uma saída lógica externa ativa em HIGH.
  // Em hardware real, a saída do módulo 74HC deve dirigir esse pino.
  // Para evitar flutuação quando o módulo estiver desconectado,
  // recomenda-se um resistor de pull-down externo de ~10 kΩ.
  pinMode(PIN_74HC_OK, INPUT);

  pinMode(PIN_LDR, INPUT);

  pinMode(LED_VERDE, OUTPUT);
  pinMode(LED_AMARELO, OUTPUT);
  pinMode(LED_VERMELHO, OUTPUT);

  Serial.begin(9600);

  lcd.init();
  lcd.backlight();
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("ChargeGrid");
  lcd.setCursor(0, 1);
  lcd.print("Sprint 3");
  delay(1200);
  lcd.clear();
}

void loop() {
  // 1) Leitura das entradas
  int auth       = lerAtivoBaixo(PIN_AUTH);
  int vaga       = lerAtivoBaixo(PIN_VAGA);
  int prioridade = lerAtivoBaixo(PIN_PRIORIDADE);

  // P74HC vem diretamente do circuito lógico.
  int p74hc = (digitalRead(PIN_74HC_OK) == HIGH) ? 1 : 0;

  // 2) Leitura e normalização da energia
  int ldr = analogRead(PIN_LDR);
  int energiaPct = calcularEnergiaPct(ldr);
  int energia = (energiaPct >= 50) ? 1 : 0;

  // 3) Processamento lógico
  int sSessao = calcularSessao(auth, vaga, energia);
  int finalOk = calcularFinal(sSessao, prioridade, p74hc);

  // 4) Atuadores e interface
  atualizarLeds(finalOk, energia);
  atualizarLCD(auth, vaga, energiaPct, prioridade, p74hc, finalOk);

  // 5) Telemetria
  if (millis() - ultimoEnvio >= INTERVALO_TELEMETRIA_MS) {
    ultimoEnvio = millis();

    enviarTelemetria(
      auth, vaga, energia, sSessao,
      prioridade, p74hc, finalOk, energiaPct
    );
  }
}
