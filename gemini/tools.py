from google.genai import types

async def get_tools_from_mcp():
    tools = [
        types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name="account_sql_query",
                    description=(
                        "Ejecuta operaciones SQL o comandos especiales sobre la tabla de cuentas financieras (`accounts`). "
                        "Esta tabla contiene información como ID del usuario, nombre, tipo de cuenta, moneda, descripción y estado de actividad. "
                        "Puedes ejecutar consultas SQL estándar como SELECT, INSERT, UPDATE o DELETE, siempre utilizando sintaxis SQL válida (no JSON). "
                        "Por ejemplo: `SELECT * FROM accounts WHERE user_id = 1`, `UPDATE accounts SET type = 'bank' WHERE id = 5`. "
                        "La IA puede traducir automáticamente campos en otros idiomas (por ejemplo, 'Banco' a 'bank'), interpretar errores, resolver ambigüedades, "
                        "y deducir información implícita como el ID de una cuenta a partir de su nombre. "
                        "Si un nombre es ambiguo, se solicitará al usuario mayor precisión. "
                        "Nunca se debe mostrar ni manipular el `user_id` en las respuestas, y las respuestas deben estar centradas en los nombres o descripciones."
                    ),
                    parameters={
                        "type": "object",
                        "properties": {
                            "query_text": {
                                "type": "string",
                                "description": "Consulta SQL o comando para realizar operaciones en la tabla `accounts`.",
                            }
                        },
                        "required": ["query_text"],
                    },
                ),
                types.FunctionDeclaration(
                    name="user_sql_tool",
                    description=(
                        "Permite ejecutar consultas SQL de tipo SELECT o UPDATE sobre la tabla `users`, que contiene información básica del usuario "
                        "como su nombre e email. Solo se permiten comandos SQL válidos, como `SELECT * FROM users WHERE id = 1` o "
                        "`UPDATE users SET name = 'Carlos' WHERE id = 2`. No está permitido modificar el campo `email` ni ejecutar INSERT o DELETE. "
                        "El campo `id` del usuario nunca debe cambiarse y se debe validar que exista. Si hay errores de sintaxis o el ID no existe, "
                        "la respuesta debe indicar claramente la causa. Las respuestas deben ser legibles y enfocadas en ayudar al usuario."
                    ),
                    parameters={
                        "type": "object",
                        "properties": {
                            "query_text": {
                                "type": "string",
                                "description": "Consulta SQL válida de tipo SELECT o UPDATE sobre la tabla `users`.",
                            }
                        },
                        "required": ["query_text"],
                    },
                ),
               types.FunctionDeclaration(
                    name="category_sql_query",
                    description=(
                        "Permite ejecutar consultas SQL de tipo SELECT, INSERT o UPDATE sobre la tabla `categories`, que contiene categorías financieras del usuario. "
                        "Los campos válidos son `name`, `type` (puede ser 'Ingreso' o 'Gasto') y `parent_category_id` (puede ser NULL para categorías raíz). "
                        "Se permiten comandos SQL como `SELECT * FROM categories WHERE type = 'Ingreso'` o "
                        "`INSERT INTO categories (name, type) VALUES ('Salario', 'Ingreso')`, así como "
                        "`UPDATE categories SET name = 'Comida y Bebidas' WHERE id = 3`. "
                        "No se permite ejecutar comandos DELETE ni modificar directamente el campo `id`. "
                        "Es importante validar que el valor de `type` sea correcto ('Ingreso' o 'Gasto'), y si se incluye un `parent_category_id`, verificar que esa categoría exista. "
                        "En caso de errores de sintaxis o referencias inválidas, se debe explicar claramente la causa en la respuesta. "
                        "Las respuestas deben ser claras, útiles y centradas en guiar al usuario."
                    ),
                    parameters={
                        "type": "object",
                        "properties": {
                            "query_text": {
                                "type": "string",
                                "description": "Consulta SQL válida de tipo SELECT, INSERT o UPDATE sobre la tabla `categories`.",
                            }
                        },
                        "required": ["query_text"],
                    },
                ),
            ]
        )
    ]
    return tools
