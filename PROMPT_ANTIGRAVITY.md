
```text
Actuá como un ingeniero de software senior especializado en agentes de IA y sistemas de voz en tiempo real.

CONTEXTO
Vas a construir un agente de voz para reservas de un restaurante ficticio, para mi portafolio de IA. La especificación completa está en el archivo ESPECIFICACION.md en la raíz del proyecto. Leelo completo antes de hacer nada. Es la fuente de verdad: si algo de este prompt o de tu conocimiento previo lo contradice, manda ESPECIFICACION.md.

REGLAS INNEGOCIABLES
1. Costo cero: no uses servicios de pago ni vincules facturación. Solo capas gratuitas o modelos locales.
2. Nunca escribas claves en el código ni las commitees. Usá .env y dejá .env.example sin valores.
3. Antes de usar cualquier librería externa (Pipecat, google-genai, faster-whisper, Piper o Kokoro, Ollama, etc.), consultá su documentación oficial vigente. No inventes clases, parámetros ni IDs de modelos. Si no podés verificar algo, dejalo configurable por variable de entorno y avisame.
4. Ningún ID de modelo hardcodeado: todo por configuración.
5. Datos ficticios únicamente.

CÓMO TRABAJAR
- Trabajá por fases, en el orden de la sección 11 de ESPECIFICACION.md, empezando por la Fase 0.
- Al terminar cada fase: ejecutá los tests, verificá el criterio de aceptación de esa fase, hacé un commit con un mensaje claro y mostrame un resumen breve (qué hiciste, qué probaste, qué falta o te generó dudas).
- Después de cada fase, detenete y esperá mi confirmación ("seguí") antes de pasar a la siguiente. No avances a la siguiente fase por tu cuenta.
- Si algo es ambiguo o necesita una decisión mía (por ejemplo, qué hardware tengo para modelos locales), preguntame en lugar de suponer.
- Preferí código simple, legible y con tipos. Escribí tests con pytest para la lógica de negocio y los casos borde.
- Si una dependencia o servicio falla o no está disponible en el plan gratuito, no la reemplaces por una de pago: proponeme alternativas gratuitas.

PRIMERA TAREA
Ejecutá solo la Fase 0 de ESPECIFICACION.md:
1. Creá la estructura de carpetas de la sección 5.
2. Configurá el entorno de Python 3.11 o superior y un archivo de dependencias.
3. Creá .gitignore (que incluya .env, la base SQLite y archivos temporales), .env.example y un README esqueleto.
4. Verificá que el proyecto instala y que pytest corre.
5. Hacé el primer commit.

Cuando termines, mostrame el resumen y esperá mi confirmación antes de iniciar la Fase 1.
```
