"""Consola interactiva para interactuar con el agente conversacional."""

import sys
from app.agent.core import VoiceReservationAgent
from app.config import settings


def main() -> None:
    print("=" * 70)
    print("  TRATTORIA BELLA VISTA - CONSOLA INTERACTIVA DEL AGENTE DE VOZ")
    print(f"  Proveedor LLM: {settings.llm_provider}")
    print(f"  Modelo: {settings.gemini_model if settings.llm_provider == 'gemini' else settings.ollama_model}")
    print("  Escribe 'salir' para terminar o 'reiniciar' para nueva conversación.")
    print("=" * 70)

    try:
        agent = VoiceReservationAgent()
    except Exception as e:
        print(f"\n[ERROR] No se pudo inicializar el agente: {e}")
        print("Si estás usando Gemini, asegúrate de configurar GEMINI_API_KEY en tu .env o usar LLM_PROVIDER=mock.")
        sys.exit(1)

    while True:
        try:
            usuario = input("\nUsuario: ").strip()
            if not usuario:
                continue

            if usuario.lower() in ("salir", "exit", "quit"):
                print("\nAgente: ¡Gracias por comunicarte con Trattoria Bella Vista! Que tengas un excelente día.")
                break

            if usuario.lower() in ("reiniciar", "reset"):
                agent.reset()
                print("\n[Historial reiniciado]")
                continue

            respuesta = agent.process_user_message(usuario)
            
            # Mostrar herramientas ejecutadas si las hubo
            if agent.last_tool_executions:
                for te in agent.last_tool_executions:
                    print(f"  [Herramienta ejecutada]: {te.name}({te.args})")

            print(f"\nAgente: {respuesta}")

        except (KeyboardInterrupt, EOFError):
            print("\n\nSesión finalizada.")
            break


if __name__ == "__main__":
    main()
