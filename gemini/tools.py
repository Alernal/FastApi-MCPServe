from google.genai import types


async def get_tools_from_mcp():
    tools = [
        types.Tool(
            function_declarations=[
                 {
                    "name": "execute_sql_query",
                    "description": "Executes a SQL query to retrieve financial information for the user",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "SQL SELECT query to execute. Only SELECT statements are allowed."
                            }
                        },
                        "required": ["query"]
                    }
                }
            ]
        ),
        types.Tool(
            function_declarations=[
                {
                    "name": "get_time_info",
                    "description": "Obtienes la fecha actual mas informacion de la zona horaria de Bogota.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                        },
                        "required": []
                    }
                }
            ]
        )
    ]
    return tools
