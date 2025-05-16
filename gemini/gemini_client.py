import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
from .tools import get_tools_from_mcp
from controllers.execute_sql_query import execute_sql_query
from controllers.get_time_info import get_time_info
from rich.console import Console
import json

console = Console()

load_dotenv()
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Registro de herramientas
tools_registry = {
    "execute_sql_query": execute_sql_query,
    "get_time_info": get_time_info,
}

# Contexto detallado para el asistente financiero
FINANCIAL_ASSISTANT_CONTEXT = """
Eres un asistente financiero inteligente encargado de brindar análisis detallados y recomendaciones personalizadas a los usuarios. Tu objetivo es ayudarles a comprender, optimizar y planificar mejor su situación financiera, utilizando como base su información personal disponible en la base de datos.

Tienes acceso directo a una base de datos MySQL que contiene las siguientes tablas: Users, Accounts, Categories, Transactions, Assets, Goals, Debts y Payments. Puedes consultar estos datos mediante la herramienta execute_sql_query sin necesidad de pedir autorización adicional. Además, puedes usar get_time_info para obtener la zona horaria de Bogotá cuando trabajes con fechas.

Tu acceso a los datos está permitido y es total, por lo tanto:
- Puedes hacer consultas SQL complejas y eficientes, utilizando correctamente JOINs entre tablas cuando sea necesario.
- Evita hacer múltiples consultas pequeñas por separado; prioriza traer toda la información útil de una sola vez si eso te permite dar un mejor análisis.
- Puedes traer todos los campos necesarios, no te limites a COUNT o SUM cuando requieras un entendimiento completo.
- No incluyas el campo user_id en tus condiciones SQL, ya que será agregado automáticamente por el sistema.

En todo análisis, tu tarea es interpretar los datos con profundidad, detectar patrones, riesgos y oportunidades, y entregar recomendaciones claras, útiles y accionables. Tu lenguaje debe ser profesional, cálido y enfocado en empoderar al usuario para tomar mejores decisiones financieras.

Cuando realices cálculos financieros, matemáticos o estadísticos, sigue estas reglas estrictamente:

1. Nunca inventes datos ni asumas valores que no provengan explícitamente de la base de datos o del usuario.
2. Siempre asegúrate de que los porcentajes que representen proporciones no excedan el 100%.
3. Si tienes múltiples formas de medir (como frecuencia vs. monto), especifica cuál estás utilizando y mantén consistencia.
4. Redondea porcentajes a dos decimales como máximo. Si es necesario, ajusta el último valor para que el total no exceda el 100%.
5. Si no tienes información suficiente, indícalo con claridad. Es preferible mostrar una limitación que entregar una conclusión incorrecta.
6. Nunca generes datos hipotéticos, ni supongas comportamientos financieros sin evidencia concreta en los datos.

Sigue siempre estas reglas y directrices al pie de la letra. Tu enfoque debe ser analítico, confiable y centrado en aportar valor real al usuario.
"""


async def generate_content_from_gemini(
    message: str, user_id: int, max_tool_calls=10, max_retries_per_tool=2
):
    # Usamos el contexto financiero avanzado
    context_message = FINANCIAL_ASSISTANT_CONTEXT

    message_replic = await improve_user_message(message)
    console.print(message_replic)
    contents = [
        types.Content(
            role="model",
            parts=[types.Part(text=context_message.strip())],
        ),
        types.Content(role="user", parts=[types.Part(text=message_replic)]),
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

                console.print(function_args)

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


async def improve_user_message(raw_message: str) -> str:
    improvement_prompt = f"""
Actúa como un profesional en redacción y contexto conversacional.
Tu tarea es reformular el mensaje original que va dirijido a una IA para que sea claro, profesional, preciso y directo,
manteniendo el mismo propósito y contexto del original. No agregues explicaciones, comentarios ni repitas el mensaje original.
Si concideras que el usuario no dio a entender de manera correcta su idea, tarta de interpretarla y mejorar.

Agrega el mensaje de abajo fijo sin modificar:
*Recuerda que puedes usar las herramientas (TE PERMITO LAS DOS HERRAMIENTAS HABILITADAS, NO ME LO CONSULTES) para consultar mi información y dirigirte a mí por mi nombre, siguiendo todas las indicaciones dadas.
Además, si te pedí esto, consulta directamente y entrégame lo solicitado sin pausas innecesarias. Si necesitas mucha información de una o varias tablas, NO te limites a usar múltiples consultas separadas ni solo SUM o COUNT. 
Tienes permiso para hacer consultas grandes, completas, usando JOINs entre las tablas que necesites. Usa una sola consulta si es posible y asegúrate de traer todos los campos relevantes. No te quedes con datos parciales: tu objetivo es comprender mi situación completa y entregarme lo mejor posible.”

Devuelve únicamente el mensaje corregido final, incluyendo esa instrucción.

Mensaje original:
\"\"\"{raw_message}\"\"\"
"""

    # Preparamos los contenidos para la solicitud
    contents = [types.Content(role="user", parts=[types.Part(text=improvement_prompt)])]

    # Configuración para obtener una salida consistente y enfocada
    config = types.GenerateContentConfig(
        temperature=0.2,
    )

    # Solicitud al modelo
    response = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY")
    ).models.generate_content(
        model="gemini-2.0-flash",
        contents=contents,
        config=config,
    )

    # Retornamos solo el texto corregido
    return response.text.strip()
