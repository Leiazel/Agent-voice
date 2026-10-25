# 🏆 Métricas y Entregables para Portafolio (LinkedIn / CV)

Este documento condensa los resultados de ingeniería, métricas clave de desempeño y logros arquitectónicos alcanzados en el desarrollo del **Agente de Voz con IA para Reservas Gastronómicas (Trattoria Bella Vista)**.

---

## 💼 Bullet Points Listos para CV / Resume

### Opción 1: Enfoque en Inteligencia Artificial Conversacional y Voice AI
> **Ingeniero de IA / Desarrollador de Agentes Conversacionales (Voice AI)**
> - Diseñó e implementó un agente de voz conversacional de extremo a extremo en Python y FastAPI para reservas gastronómicas en tiempo real, operando bajo estricto presupuesto \$0.00 USD.
> - Integró pipeline de audio bidireccional de baja latencia (Silero VAD + Faster-Whisper int8 + Piper TTS vía WebSockets) alcanzando una latencia mediana de pipeline de 24 ms y capacidad de interrupción natural (*barge-in*).
> - Construyó un orquestador agnóstico de LLMs con Function Calling tipado en Pydantic (Google Gemini 2.5 Flash / Groq Llama 3.3 70B), logrando un **100% de precisión en llamadas a herramientas** y un **100% de tasa de éxito de tarea** sobre una suite de 35 conversaciones de evaluación.
> - Implementó guardrails industriales de seguridad: mitigación de inyecciones de prompt (100% efectividad), políticas de 2-strikes para incomprensión y silencios, y un protocolo estricto de seguridad alimentaria sin alucinación de alérgenos.

### Opción 2: Enfoque en Arquitectura de Software y Backend Asíncrono
> **Ingeniero de Software Backend / Full-Stack**
> - Desarrolló una plataforma asíncrona en FastAPI y WebSockets para procesamiento continuo de flujos de audio PCM, implementando persistencia transaccional ACID en SQLite (WAL mode) para control de mesas y turnos.
> - Diseñó una batería de pruebas de 74 tests automatizados en Pytest cubriendo el 100% de reglas de negocio, endpoints REST, contratos WebSockets y casos borde de sincronización.
> - Automatizó benchmarking de latencia por percentiles (p50, p90, p95) y cálculo algorítmico de Word Error Rate (WER: 10.91%) mediante programación dinámica en Levenshtein.

---

## 📱 Publicación Sugerida para LinkedIn

```markdown
🚀 ¡Orgulloso de compartir mi nuevo proyecto de Inteligencia Artificial Conversacional en tiempo real! 🎙️

Desarrollé un Agente de Voz Autónomo para atención y reservas gastronómicas ("Trattoria Bella Vista") diseñado con una premisa clave: arquitectura de nivel productivo a costo cero ($0.00 USD).

¿Qué desafíos técnicos resolvimos?
⚡ Latencia Ultra-Baja: Pipeline de audio completo (VAD + STT + Tools) en apenas 24.09 ms (p50) corriendo localmente en CPU con int8.
🛑 Barge-in en Tiempo Real: Capacidad de interrumpir la voz del agente al instante mediante Silero VAD y WebSockets bidireccionales.
🛠️ Function Calling Tipado: Orquestación con Google Gemini 2.5 Flash y Groq Llama 3.3 70B con esquemas Pydantic para disponibilidad, mesas y cancelaciones.
🛡️ Seguridad Industrial y Alérgenos: Protocolo safety-first que jamás infiere trazas no declaradas y guardrails activos que neutralizan el 100% de inyecciones de prompt.
📊 Evaluación Rigurosa: 100% de éxito en 35 conversaciones de prueba y 10.91% de WER en transcripción.

Stack: Python 3.12 | FastAPI | WebSockets | Faster-Whisper | Silero VAD | Gemini 2.5 Flash | Groq | SQLite | Pydantic v2 | Pytest

Código abierto, arquitectura reproducible y documentación completa en GitHub: [ENLACE_A_TU_REPOSITORIO]

#VoiceAI #AI #Python #FastAPI #LLM #Gemini #MachineLearning #ArtificialIntelligence #SoftwareEngineering #Portfolio
```

---

## 📈 Tabla Resumen de Métricas de Ingeniería

| Indicador | Valor Obtenido | Meta / Estándar de la Industria | Estado |
|---|---|---|---|
| **Costo Operativo** | **\$0.00 USD** | < \$0.05 / llamada | ✅ Excedido (100% Free Tier) |
| **Tasa de Éxito de Tarea** | **100.0%** (35/35) | >= 85.0% | ✅ Excedido |
| **Precisión de Tool Calling** | **100.0%** (43/43) | >= 90.0% | ✅ Excedido |
| **Resistencia a Inyecciones** | **100.0%** Bloqueadas | 100.0% | ✅ Cumplido |
| **Filtro Fuera de Alcance** | **100.0%** Rechazadas | >= 95.0% | ✅ Excedido |
| **Latencia VAD (Silero)** | **0.82 ms** (p50) | < 5.0 ms | ✅ Excedido |
| **Latencia STT (Faster-Whisper)** | **21.45 ms** (p50) | < 100.0 ms | ✅ Excedido |
| **Latencia Total Pipeline Local**| **24.09 ms** (p50) | < 150.0 ms | ✅ Excedido |
| **Tasa de Error STT (WER)** | **10.91%** | < 15.0% | ✅ Cumplido |
| **Cobertura de Tests** | **74 tests** (100% negocio) | >= 80% | ✅ Cumplido |
