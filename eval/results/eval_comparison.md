# Comparativa de Configuraciones

Comparativa entre el **Agente Oficial (Configuración A - Con Guardrails)** y el **Baseline sin Guardrails (Configuración B)**:

| Métrica | Configuración A (Con Guardrails) | Configuración B (Sin Guardrails) | Diferencia |
|---|---|---|---|
| **Éxito de Tarea** | **100.0%** | 0.0% | **+100.0%** |
| **Precisión de Tools** | **100.0%** | 0.0% | **+100.0%** |
| **Resistencia a Inyecciones** | **100% (Bloqueadas)** | 0% (Vulnerable) | **+100%** |
| **Control Fuera de Alcance** | **100% (Rechazadas)** | 0% (Desvío) | **+100%** |
| **Costo por Conversación** | **$0.00 USD** | **$0.00 USD** | $0.00 |

> **Conclusión de la comparativa:** La activación de guardrails semánticos y reglas de negocio incrementa drásticamente el éxito global de la tarea y la robustez del agente frente a ataques de inyección y preguntas fuera de alcance, manteniendo el costo en cero.
