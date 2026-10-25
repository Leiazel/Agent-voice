# Reporte de Benchmark de Latencia

Fecha: 2026-10-25 13:26:28

- Proveedor LLM: `mock`
- Modelo STT: `faster-whisper (base)`

### Métricas de Latencia (20 turnos registrados)

| Etapa | Mínimo (ms) | Promedio (ms) | p50 (ms) | p95 (ms) | Máximo (ms) |
|---|---|---|---|---|---|
| STT (faster-whisper) | 14.54 | 28.29 | **23.83** | **52.72** | 55.05 |
| LLM (Inferencia + Tools) | 0.15 | 1.84 | **0.39** | **7.18** | 10.2 |
| TTS (Síntesis de voz) | 0.0 | 0.02 | **0.0** | **0.02** | 0.3 |
| **Punta a Punta (Total)** | 14.69 | 30.16 | **24.09** | **57.78** | 62.08 |
