from typing import Dict, Any
from mysql.connector import Error
import json
import logging
from core.database import get_db_connection

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UserDBError(Exception):
    """Excepción personalizada para errores relacionados con la base de datos de usuarios"""
    pass

def validate_update_sql(sql: str) -> None:
    """
    Valida que el SQL UPDATE no modifique campos no permitidos.
    
    Args:
        sql: Consulta SQL tipo UPDATE.
    
    Raises:
        UserDBError: Si intenta modificar campos restringidos como 'email'.
    """
    sql_lower = sql.lower()
    if "update" not in sql_lower:
        raise UserDBError("Solo se permite ejecutar sentencias UPDATE o SELECT.")
    
    if "email" in sql_lower:
        raise UserDBError("No está permitido modificar el campo 'email' del usuario.")

def execute_sql_query(sql: str) -> Dict[str, Any]:
    """
    Ejecuta una consulta SELECT y retorna los resultados.
    
    Args:
        sql: Consulta SQL SELECT válida.
    
    Returns:
        Diccionario con los resultados o error.
    """
    try:
        if not sql.strip().lower().startswith("select"):
            raise UserDBError("Solo se permiten consultas SELECT para lectura de datos.")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql)
        results = cursor.fetchall()
        cursor.close()
        conn.close()

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
    Ejecuta una sentencia SQL UPDATE (sin permitir cambios en email).
    
    Args:
        sql: Consulta SQL UPDATE válida.
    
    Returns:
        Diccionario con el resultado de la operación.
    """
    try:
        validate_update_sql(sql)

        conn = get_db_connection()
        cursor = conn.cursor()
        affected = cursor.execute(sql)
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
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

def user_sql_tool(query_text: str) -> str:
    """
    Ejecuta una consulta SQL SELECT o UPDATE sobre la tabla `users`.
    
    Args:
        query_text: Consulta SQL válida (SELECT o UPDATE).
    
    Returns:
        Resultado serializado en JSON.
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
