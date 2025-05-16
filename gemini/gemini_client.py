import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
from .tools import get_tools_from_mcp
from controllers.execute_sql_query import execute_sql_query
from rich.console import Console
import json

console = Console()

load_dotenv()
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Registro de herramientas
tools_registry = {
    "execute_sql_query": execute_sql_query,
}

# Contexto detallado para el asistente financiero
FINANCIAL_ASSISTANT_CONTEXT = """
Eres un asistente financiero, tu tarea es brindar analisis y recomendaciones financieras a los usuarios.
Puedes consultar la informacion financiera del usuario mediante la herramienta 'execute_sql_query' la cual 
debes ejecutar sin necesidad de pedir el permiso al usuario.

El modelo de base de datos es el siguiente: Users (user_id, name, email) puedes consultar informacion del usuario logueado haciendo un simple select.
Accounts (id, user_id, name, type, currency, created_at) Puedes obtener todas las cuentas del usuario.
Categories (id, user_id, name, type, parent_category_id) Puedes obtener todas las categorias del usuario.
Transactions (id, user_id, account_id, category_id, amount, date, type, target_account_id) Puedes obtener todas las transacciones del usuario.

Con una solo secuencia puedes obtener todas las transactions con sus relaciones de accounts y categories.


No debes nombrar nada de 'ID' o 'user_id' en tus respuestas, ya que el usuario no tiene por que saberlo.

cumple los requerimientos del usuario, si te pide reportes, analisis, estadisticas, etc. debes hacer un analisis profundo de la informacion y brindarle una respuesta completa.

el user_id no es necesario que lo agregues, internamente la secuencias que se ejecuten ya lo tienen.
"""


async def generate_content_from_gemini(
    message: str, user_id: int, max_tool_calls=5, max_retries_per_tool=2
):
    # Usamos el contexto financiero avanzado
    context_message = FINANCIAL_ASSISTANT_CONTEXT

    contents = [
        types.Content(
            role="model", parts=[types.Part(text=context_message)]
        ), 
        types.Content(
            role="user", parts=[types.Part(text=message)]
        ),
    ]

    tools = await get_tools_from_mcp()

    config = types.GenerateContentConfig(
        temperature=0.3,  # Reducimos la temperatura para respuestas más precisas y analíticas
        tools=tools,
    )

    # Obtener la primera respuesta de Gemini
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=contents,
        config=config,
    )

    # Contador para el número total de herramientas usadas
    total_tool_calls = 0
    # Diccionario para rastrear los reintentos por cada herramienta
    tool_retry_counts = {}
    # Diccionario para almacenar datos obtenidos (para referencias futuras)
    collected_data = {}

    # Bucle principal que permite a Gemini realizar múltiples llamadas a herramientas
    while total_tool_calls < max_tool_calls:
        # Verificar si hay llamadas a herramientas en la respuesta actual
        has_tool_call = False

        for part in response.candidates[0].content.parts:
            if hasattr(part, "function_call") and part.function_call:
                has_tool_call = True
                function_call = part.function_call
                function_name = function_call.name
                function_args = function_call.args
                
                # Registrar la herramienta invocada
                tool_key = f"{function_name}:{str(function_args)}"
                tool_retry_counts[tool_key] = tool_retry_counts.get(tool_key, 0) + 1
                retry_count = tool_retry_counts[tool_key]

                # Ejecutar la herramienta y obtener el resultado
                result = None
                result_text = ""
                success = True

                try:
                    if function_name in tools_registry:
                        # Ejecutar la función registrada
                        result = tools_registry[function_name](
                            **function_args, user_id=user_id
                        )
                        result_text = str(result)
                        console.print(user_id)
                    else:
                        result_text = f"Error: La herramienta '{function_name}' no está registrada."
                        success = False
                except Exception as e:
                    result_text = f"Error al ejecutar la herramienta: {str(e)}"
                    success = False

                # Registrar el resultado para diagnóstico
                if success:
                    console.print(
                        f"[bold green]Resultado exitoso de la herramienta[/bold green]"
                    )
                else:
                    console.print(
                        f"[bold red]Error en la herramienta:[/bold red] {result_text}"
                    )

                # Añadir la llamada de función al historial de contenido
                contents.append(
                    types.Content(
                        role="model", parts=[types.Part(function_call=function_call)]
                    )
                )

                # Añadir el resultado al historial de contenido
                function_response_part = types.Part.from_function_response(
                    name=function_name,
                    response={"result": result_text, "success": success},
                )
                contents.append(
                    types.Content(role="user", parts=[function_response_part])
                )

                # Mensaje adicional para guiar a Gemini cuando hay un error
                if not success and retry_count < max_retries_per_tool:
                    retry_guidance = """
                    El último intento con la herramienta falló. Analiza cuidadosamente el mensaje de error y realiza los ajustes necesarios.
                    """
                    contents.append(
                        types.Content(
                            role="user", parts=[types.Part(text=retry_guidance)]
                        )
                    )
                elif total_tool_calls > 0 and success:
                    # Proporcionar contexto adicional para ayudar con análisis más profundo
                    analysis_guidance = f"""
                    Has obtenido datos exitosamente.
                    Actualmente has realizado {total_tool_calls} de {max_tool_calls} consultas disponibles.
                    """
                    contents.append(
                        types.Content(
                            role="user", parts=[types.Part(text=analysis_guidance)]
                        )
                    )

                # Incrementar el contador total de herramientas usadas
                total_tool_calls += 1
                break  # Procesar una herramienta a la vez

        # Si no hubo llamada a herramienta, significa que Gemini está listo para dar una respuesta final
        if not has_tool_call:
            break

        # Verificar si hemos alcanzado el límite de herramientas
        if total_tool_calls >= max_tool_calls:
            # Informar a Gemini que debe dar una respuesta final con lo que tiene
            guidance = f"""
            Has alcanzado el límite máximo de {max_tool_calls} llamadas a herramientas para esta consulta.
            """
            contents.append(
                types.Content(role="user", parts=[types.Part(text=guidance)])
            )

        # Obtener la siguiente respuesta de Gemini
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=contents,
            config=config,
        )

    # Devolvemos la respuesta final
    return response.text
