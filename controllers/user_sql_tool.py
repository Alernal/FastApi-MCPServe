from typing import Dict, Any
import json
import logging
from mysql.connector import Error, connect
from core.database import get_db_connection

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UserDBError(Exception):
    """Excepción personalizada para errores de base de datos relacionados con usuarios."""
    pass

def validate_update_sql(sql: str) -> None:
    """
    Valida que la sentencia SQL UPDATE no intente modificar campos restringidos.

    Args:
        sql (str): Sentencia SQL tipo UPDATE.

    Raises:
        UserDBError: Si intenta modificar campos no permitidos como 'email'.
    """
    sql_lower = sql.lower()
    if "update" not in sql_lower:
        raise UserDBError("Solo se permiten sentencias UPDATE o SELECT.")

    restricted_fields = ["email"]
    for field in restricted_fields:
        if field in sql_lower:
            raise UserDBError(f"No está permitido modificar el campo '{field}' del usuario.")

def execute_sql_query(sql: str) -> Dict[str, Any]:
    """
    Ejecuta una consulta SELECT sobre la base de datos.

    Args:
        sql (str): Consulta SQL SELECT.

    Returns:
        Dict[str, Any]: Resultado de la consulta.
    """
    if not sql.strip().lower().startswith("select"):
        raise UserDBError("Solo se permiten consultas SELECT para lectura de datos.")

    try:
        with get_db_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute(sql)
                results = cursor.fetchall()
        return {
            "operation": "select",
            "success": True,
            "results": results
        }
    except Error as e:
        logger.error(f"Error ejecutando SELECT: {e}")
        return {
            "operation": "select",
            "success": False,
            "error": str(e)
        }

def execute_sql_update(sql: str) -> Dict[str, Any]:
    """
    Ejecuta una sentencia UPDATE sobre la base de datos.

    Args:
        sql (str): Sentencia SQL UPDATE.

    Returns:
        Dict[str, Any]: Resultado de la actualización.
    """
    validate_update_sql(sql)

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                conn.commit()
                return {
                    "operation": "update",
                    "success": True,
                    "affected_rows": cursor.rowcount
                }
    except (Error, UserDBError) as e:
        logger.error(f"Error ejecutando UPDATE: {e}")
        return {
            "operation": "update",
            "success": False,
            "error": str(e)
        }

def user_sql_tool(query_text: str, token: Any = None) -> str:
    """
    Ejecuta una consulta SQL SELECT o UPDATE sobre la tabla `users`.

    Args:
        query_text (str): Consulta SQL.
        token (Any): Token de autenticación (no utilizado actualmente).

    Returns:
        str: Resultado de la operación en formato JSON.
    """
    try:
        query_lower = query_text.strip().lower()

        if query_lower.startswith("select"):
            result = execute_sql_query(query_text)
        elif query_lower.startswith("update"):
            result = execute_sql_update(query_text)
        else:
            result = {
                "success": False,
                "error": "Solo se permiten consultas SELECT o UPDATE en la tabla users."
            }

        return json.dumps(result, indent=2, default=str)

    except Exception as e:
        logger.error(f"Error general en user_sql_tool: {e}")
        return json.dumps({"error": str(e)}, indent=2)
