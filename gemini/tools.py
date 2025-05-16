from google.genai import types


async def get_tools_from_mcp():
    tools = [
        types.Tool(
            function_declarations=[
                {
                    "name": "execute_sql_query",
                    "description": """Ejecuta una consulta SQL SELECT sobre la base de datos MYSQL financiera del usuario. Puedes realizar cualquier consulta, grande o compleja, incluyendo múltiples tablas con JOINs si es necesario. Tienes permiso total para consultar toda la información relevante.
                    La estructura del modelo de datos es la siguiente:
                    - **Users(user_id, name, email)**: puedes obtener el nombre del usuario con un SELECT simple y siempre debes dirigirte a él por su nombre, nunca por campos técnicos como "id" o "user_id".
                    - **Accounts(id, user_id, name, type, currency, created_at)**: representa las cuentas del usuario (BANCO, DIGITAL, EFECTIVO, INVERSION, PRESTAMO, OTRO).
                    - **Categories(id, user_id, name, type, parent_category_id)**: categorías de ingreso o gasto que pueden tener jerarquía.
                    - **Transactions(id, user_id, account_id, category_id, amount, date, type, target_account_id)**: todas las transacciones financieras del usuario (Ingreso, Gasto, Transferencia).
                    - **Assets(id, user_id, description, type, acquisition_date, value, notes)**: activos financieros del usuario.
                    - **Goals(id, user_id, name, description, amount, date_init, date_end, account_id)**: metas financieras con fechas e importes esperados.
                    - **Debts(id, user_id, name, amount, interest_percentage, date_init, date_end, description)**: deudas registradas por el usuario.""",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Consulta SQL de tipo SELECT que deseas ejecutar. Solo se permiten consultas SELECT.",
                            }
                        },
                        "required": ["query"],
                    },
                }
            ]
        ),
        types.Tool(
            function_declarations=[
                {
                    "name": "get_time_info",
                    "description": "Obtienes la fecha actual mas informacion de la zona horaria de Bogota.",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                }
            ]
        ),
    ]
    return tools
