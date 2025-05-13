from google.genai import types

async def get_tools_from_mcp():
    tools = [
        types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name="account_sql_query",
                    description = """
                        Ejecuta operaciones SQL o comandos especiales en la tabla de cuentas financieras (`accounts`).

                        ESQUEMA DE LA TABLA:
                        - id: INTEGER PRIMARY KEY (autoincremental)
                        - user_id: INTEGER (ID del usuario, obligatorio)
                        - name: TEXT (nombre de la cuenta, obligatorio)
                        - type: TEXT (tipo de cuenta, obligatorio; valores permitidos: 'cash', 'bank', 'credit', 'other')
                        - currency: TEXT (código de moneda, obligatorio; formato de 3 letras: USD, EUR, COP, etc.)
                        - description: TEXT (descripción opcional de la cuenta)
                        - is_active: BOOLEAN (indica si la cuenta está activa; por defecto TRUE)

                        TIPOS DE CONSULTAS ACEPTADAS:

                        1. **SQL directo**  
                        Puedes ejecutar comandos SQL como SELECT, INSERT, UPDATE o DELETE.  
                        IMPORTANTE: Los comandos SQL deben enviarse exactamente como consultas SQL válidas sin formato JSON.  
                        Ejemplo:  
                        `SELECT * FROM accounts WHERE user_id = 1`
                        `UPDATE accounts SET type = 'bank' WHERE id = 5`

                        FUNCIONALIDADES INTELIGENTES:

                        - Si te dan un campo en otro idioma (por ejemplo, 'Banco' en español), tradúcelo automáticamente al inglés (por ejemplo, 'bank').
                        - Interpreta los errores y aplica correcciones según tu análisis. Si no puedes resolver el problema, solicita al usuario la información necesaria.
                        - Si el ID no se proporciona pero se menciona el **nombre de una cuenta** (por ejemplo, `actualiza la cuenta Nequi`), busca el ID correspondiente a ese nombre antes de proceder.
                        - Comprende campos implícitos del lenguaje natural, como nombres de cuentas, monedas, tipos, etc.
                        - Si hay ambigüedad en los datos (por ejemplo, varias cuentas con el mismo nombre), solicita más precisión al usuario.

                        INDICACIONES DE RESPUESTA:

                        - Da respuestas claras, orientadas al usuario.
                        - No muestres directamente los IDs de los registros, prefiere usar nombres o descripciones.
                        - No manipules el user_id de los registros, el usuario es y sera ese ID.
                    """, 
                    parameters={
                        "type": "object",
                        "properties": {
                            "query_text": {
                                "type": "string",
                                "description": "Consulta SQL o comando para realizar operaciones en la tabla accounts."
                            }
                        },
                        "required": ["query_text"]
                    }
                )
            ]
        )
    ]
    return tools