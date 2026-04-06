/* * Core 0: Controle do PWM (Ponte H)
 * Core 1: Leitura do Encoder e Comunicação Serial
 */
 
#include <Arduino.h>
#define PWM_DELAY   10
#define FREQUENCIA  2000

// Pinos Ponte H
#define PIN_PWM_1  18
#define PIN_PWM_2  19

// Pinos Encoder
#define PIN_ENCODER_A  34
#define PIN_ENCODER_B  35

// Configurações PWM
#define RESOLUCAO  10 // 10 bits (0-1023)

// Variáveis do Encoder
volatile long pulsos = 0;
unsigned long tempoAnterior = 0;
float rpm = 0;
const int pulsosPorVolta = 90;
int last_read_encoder = 0;
int new_value_encoder = 0;
bool update_pwm = true;

// Variáveis do PWM
int pwmVal = 0;
// int pwm2Val = 0;
bool decrescente_pwm = false;


// Handler das Tasks
TaskHandle_t TaskPWM;
TaskHandle_t TaskEncoder;

// Interrupção do Encoder
void IRAM_ATTR registraPulso() {
  new_value_encoder = digitalRead(PIN_ENCODER_A)
  if ((new_value_encoder) && (new_value_encoder != last_value_encoder)) {
    last_value_encoder = new_value_encoder;
    pulsos++;
  }
}

void setup() {
  Serial.begin(115200);

  // Configuração PWM
  ledcAttach(PIN_PWM_1, FREQUENCIA, RESOLUCAO);
  ledcAttach(PIN_PWM_2, FREQUENCIA, RESOLUCAO);

  // Configuração Encoder
  pinMode(PIN_ENCODER_A, INPUT);
  pinMode(PIN_ENCODER_B, INPUT);
  attachInterrupt(digitalPinToInterrupt(PIN_ENCODER_A), registraPulso, RISING);

  // Criação da Task no Core 0 (Controle PWM)
  xTaskCreatePinnedToCore(
    taskControlePWM, "TaskPWM", 10000, NULL, 1, &TaskPWM, 0);

  // Criação da Task no Core 1 (Encoder e Serial)
  xTaskCreatePinnedToCore(
    taskLeituraEncoder, "TaskEncoder", 10000, NULL, 1, &TaskEncoder, 1);
}

// --- TASK CORE 0: CONTROLE DE VELOCIDADE ---
void taskControlePWM(void* pvParameters) {
  while (true) {
    if (update_pwm){
    ledcWrite(PIN_PWM_1, pwmVal);
    ledcWrite(PIN_PWM_2, pwmVal);
    update_pwm = false;
    }
  }
}

// --- TASK CORE 1: ENCODER E SERIAL ---
void taskLeituraEncoder(void* pvParameters) {
  Serial.println("-*-*-*-Crescente-*-*-*-");
  while (true) {
    unsigned long tempoAtual = millis();
    if (tempoAtual - tempoAnterior >= 100) {  // Calcula a cada 100ms

      long contagemAtual = pulsos;

      // Cálculo de RPM: (pulsos no intervalo / pulsos por volta) * (60s / intervalo em s)
      rpm = (float)(contagemAtual * 600.0) / pulsosPorVolta;

      // Report for user the found values
      Serial.prin("PWM: ")
      Serial.print(map(pwmVal,0,1023,0,100),2)
      Serial.print(" | RPM: ");
      Serial.println(rpm,2);

      // Update new PWM values
      // Check direction of test
      if (decrescente_pwm){
        pwmVal++;
      }
      else{
        pwmVal--;
      }
      // Check edge cases
      if (pwmVal<0){
        pwmVal = 0;
        decrescente_pwm = false;
        Serial.println("-*-*-*-Crescente-*-*-*-");
      }
      if (pwmVal > 1023){
        pwmVal = 1023;
        decrescente_pwm = true;
        Serial.println("-*-*-*-Decrescente-*-*-*-");
      }
      // Raise update flag
      update_pwm = true;

      // Release vars and wait for next count
      tempoAnterior = millis();
      pulsos = 0;
    }
    vTaskDelay(pdMS_TO_TICKS(1));  // Evita o Watchdog
  }
}

void loop() {
  // O loop fica vazio pois estamos usando Tasks do FreeRTOS
}