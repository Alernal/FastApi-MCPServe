import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
from controllers.account_sql_tool import account_sql_query
from .tools import get_tools_from_mcp
from rich.console import Console

console = Console()

load_dotenv()
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Registro de herramientas
tools_registry = {
    "account_sql_query": account_sql_query,
}

async def generate_content_from_gemini(message: str, max_tool_calls=5, max_retries_per_tool=1):
    context_message = "Eres un asistente financiero. Responde de manera clara y concisa a las preguntas del usuario. Puedes usar múltiples herramientas para resolver una consulta, y si encuentras un error al usar una herramienta, puedes intentar corregir tu enfoque y volver a intentarlo."
    
    contents = [
        types.Content(role="model", parts=[types.Part(text=context_message)]),  # Este es el contexto inicial
        types.Content(role="user", parts=[types.Part(text=message)]),  # Mensaje del usuario
    ]

    tools = await get_tools_from_mcp()

    config = types.GenerateContentConfig(
        temperature=0.5,
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
                
                console.print(f"[bold green]Tool invocada ({total_tool_calls + 1}/{max_tool_calls}):[/bold green] {function_name}")
                console.print(f"[bold blue]Intento {retry_count} para esta configuración de herramienta[/bold blue]")
                
                # Ejecutar la herramienta y obtener el resultado
                result_text = ""
                success = True
                
                try:
                    if function_name in tools_registry:
                        result = tools_registry[function_name](**function_args)
                        result_text = str(result)
                    else:
                        result_text = f"Error: La herramienta '{function_name}' no está registrada."
                        success = False
                except Exception as e:
                    result_text = f"Error al ejecutar la herramienta: {str(e)}"
                    success = False
                
                # Registrar el resultado para diagnóstico
                if success:
                    console.print(f"[bold green]Resultado exitoso de la herramienta[/bold green]")
                else:
                    console.print(f"[bold red]Error en la herramienta:[/bold red] {result_text}")
                
                # Añadir la llamada de función al historial de contenido
                contents.append(types.Content(role="model", parts=[types.Part(function_call=function_call)]))
                
                # Añadir el resultado al historial de contenido
                function_response_part = types.Part.from_function_response(
                    name=function_name,
                    response={"result": result_text, "success": success},
                )
                contents.append(types.Content(role="user", parts=[function_response_part]))
                
                # Mensaje adicional para guiar a Gemini cuando hay un error
                if not success and retry_count < max_retries_per_tool:
                    retry_guidance = """
                    El último intento con la herramienta falló. Puedes:
                    1. Intentar con parámetros diferentes para la misma herramienta.
                    2. Probar con otra herramienta que podría ser más adecuada.
                    3. Continuar con la conversación si ya tienes suficiente información.
                    4. Muy importante: Dale a la herramienta los datos como ellas lo esperan, no como tú lo entiendes.
                    """
                    contents.append(types.Content(role="user", parts=[types.Part(text=retry_guidance)]))
                
                # Incrementar el contador total de herramientas usadas
                total_tool_calls += 1
                break  # Procesar una herramienta a la vez
        
        # Si no hubo llamada a herramienta, significa que Gemini está listo para dar una respuesta final
        if not has_tool_call:
            break
            
        # Verificar si hemos alcanzado el límite de herramientas
        if total_tool_calls >= max_tool_calls:
            # Informar a Gemini que debe dar una respuesta final con lo que tiene
            guidance = """
            Has alcanzado el límite máximo de llamadas a herramientas para esta consulta.
            Por favor, proporciona la mejor respuesta posible con la información que has recopilado hasta ahora.
            """
            contents.append(types.Content(role="user", parts=[types.Part(text=guidance)]))
        
        # Obtener la siguiente respuesta de Gemini
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=contents,
            config=config,
        )
    
    # Devolvemos la respuesta final
    return response.text