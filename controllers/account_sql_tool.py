from typing import Dict, Any, List, Optional, Union
from mysql.connector import Error
import json
import logging
from core.database import get_db_connection

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

conn = get_db_connection()

# Constantes
VALID_TYPES = ["cash", "bank", "credit", "other"]
VALID_CURRENCIES = ["USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD", "CNY", "COP", "MXN", "BRL", "ARS"]

class AccountDBError(Exception):
    """Excepción personalizada para errores relacionados con la base de datos de cuentas"""
    pass

def validate_account_data(data: Dict[str, Any]) -> None:
    """
    Valida los datos de la cuenta antes de realizar operaciones de inserción o actualización.
    
    Args:
        data: Diccionario con los datos de la cuenta a validar
    
    Raises:
        AccountDBError: Si hay algún problema con los datos proporcionados
    """
    if 'type' in data and data['type'] not in VALID_TYPES:
        raise AccountDBError(f"Tipo de cuenta inválido. Debe ser uno de: {', '.join(VALID_TYPES)}")
    
    if 'currency' in data and data['currency'] not in VALID_CURRENCIES:
        raise AccountDBError(f"Moneda inválida. Debe ser uno de: {', '.join(VALID_CURRENCIES)}")
    
    if 'is_active' in data and not isinstance(data['is_active'], bool):
        if isinstance(data['is_active'], str):
            if data['is_active'].lower() in ['true', '1', 'yes', 'y']:
                data['is_active'] = True
            elif data['is_active'].lower() in ['false', '0', 'no', 'n']:
                data['is_active'] = False
            else:
                raise AccountDBError("El campo is_active debe ser un valor booleano")
        else:
            raise AccountDBError("El campo is_active debe ser un valor booleano")


def execute_sql_query(sql: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
    """
    Ejecuta una consulta SQL SELECT y devuelve los resultados como una lista de diccionarios.
    
    Args:
        sql: Consulta SQL a ejecutar
        params: Parámetros para la consulta SQL
        
    Returns:
        Lista de diccionarios con los resultados de la consulta
    """
    try:
        # Verificar que sea una consulta SELECT
        if not sql.strip().lower().startswith("select"):
            raise AccountDBError("Solo se permiten consultas SELECT para lectura de datos")
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
            
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return results
    except Error as e:
        logger.error(f"Error ejecutando consulta SQL: {e}")
        raise AccountDBError(f"Error al ejecutar consulta SQL: {e}")

def execute_sql_modification(sql: str, params: Optional[tuple] = None) -> Dict[str, Any]:
    """
    Ejecuta una consulta SQL de modificación (INSERT, UPDATE, DELETE) y devuelve información sobre la operación.
    
    Args:
        sql: Consulta SQL a ejecutar
        params: Parámetros para la consulta SQL
        
    Returns:
        Diccionario con información sobre la operación realizada
    """
    try:
        sql_lowercase = sql.strip().lower()
        
        # Verificar que sea una operación de modificación válida
        if not (sql_lowercase.startswith("insert") or 
                sql_lowercase.startswith("update") or 
                sql_lowercase.startswith("delete")):
            raise AccountDBError("Solo se permiten operaciones INSERT, UPDATE o DELETE para modificación de datos")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
            
        conn.commit()
        
        # Preparar información sobre la operación
        result = {
            "operation": "unknown",
            "affected_rows": cursor.rowcount,
            "success": True
        }
        
        # Identificar la operación realizada
        if sql_lowercase.startswith("insert"):
            result["operation"] = "insert"
            result["last_id"] = cursor.lastrowid
        elif sql_lowercase.startswith("update"):
            result["operation"] = "update"
        elif sql_lowercase.startswith("delete"):
            result["operation"] = "delete"
        
        cursor.close()
        conn.close()
        return result
    except Error as e:
        logger.error(f"Error ejecutando modificación SQL: {e}")
        raise AccountDBError(f"Error al ejecutar modificación SQL: {e}")

def insert_account(account_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Inserta una nueva cuenta en la base de datos.
    
    Args:
        account_data: Diccionario con los datos de la cuenta a insertar
        
    Returns:
        Diccionario con información sobre la operación realizada
    """
    try:
        # Validar datos
        validate_account_data(account_data)
        
        # Campos requeridos
        required_fields = ["user_id", "name", "type", "currency"]
        for field in required_fields:
            if field not in account_data:
                raise AccountDBError(f"Campo requerido faltante: {field}")
        
        # Preparar la consulta
        fields = []
        values = []
        params = []
        
        for key, value in account_data.items():
            if key in ["user_id", "name", "type", "currency", "description", "is_active"]:
                fields.append(key)
                values.append("%s")
                params.append(value)
        
        
        sql = f"INSERT INTO accounts ({', '.join(fields)}) VALUES ({', '.join(values)})"
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(sql, params)
        
        # Obtener el ID del registro insertado
        last_id = cursor.lastrowid
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "operation": "insert",
            "account_id": last_id,
            "success": True,
            "message": f"Cuenta creada con ID: {last_id}"
        }
    except (Error, AccountDBError) as e:
        logger.error(f"Error insertando cuenta: {e}")
        return {
            "operation": "insert",
            "success": False,
            "error": str(e)
        }

def update_account(account_id: int, account_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Actualiza una cuenta existente en la base de datos.
    
    Args:
        account_id: ID de la cuenta a actualizar
        account_data: Diccionario con los datos de la cuenta a actualizar
        
    Returns:
        Diccionario con información sobre la operación realizada
    """
    try:
        # Validar datos
        validate_account_data(account_data)
        
        # Verificar que la cuenta existe
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM accounts WHERE id = %s", (account_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return {
                "operation": "update",
                "success": False,
                "error": f"No existe una cuenta con ID: {account_id}"
            }
        
        # Preparar la consulta
        set_clauses = []
        params = []
        
        for key, value in account_data.items():
            if key in ["user_id", "name", "type", "currency", "description", "is_active"]:
                set_clauses.append(f"{key} = %s")
                params.append(value)
        
        # Agregar el ID al final de los parámetros
        params.append(account_id)
        
        sql = f"UPDATE accounts SET {', '.join(set_clauses)} WHERE id = %s"
        
        cursor.execute(sql, params)
        affected_rows = cursor.rowcount
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "operation": "update",
            "account_id": account_id,
            "affected_rows": affected_rows,
            "success": True,
            "message": f"Cuenta actualizada con ID: {account_id}"
        }
    except (Error, AccountDBError) as e:
        logger.error(f"Error actualizando cuenta: {e}")
        return {
            "operation": "update",
            "success": False,
            "error": str(e)
        }

def delete_account(account_id: int) -> Dict[str, Any]:
    """
    Elimina una cuenta existente de la base de datos.
    
    Args:
        account_id: ID de la cuenta a eliminar
        
    Returns:
        Diccionario con información sobre la operación realizada
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar que la cuenta existe
        cursor.execute("SELECT id FROM accounts WHERE id = %s", (account_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return {
                "operation": "delete",
                "success": False,
                "error": f"No existe una cuenta con ID: {account_id}"
            }
        
        # Eliminar la cuenta
        cursor.execute("DELETE FROM accounts WHERE id = %s", (account_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "operation": "delete",
            "account_id": account_id,
            "success": True,
            "message": f"Cuenta eliminada con ID: {account_id}"
        }
    except Error as e:
        logger.error(f"Error eliminando cuenta: {e}")
        return {
            "operation": "delete",
            "success": False,
            "error": str(e)
        }

def get_account(account_id: int) -> Dict[str, Any]:
    """
    Obtiene los detalles de una cuenta por su ID.
    
    Args:
        account_id: ID de la cuenta a consultar
        
    Returns:
        Diccionario con los detalles de la cuenta o mensaje de error
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM accounts WHERE id = %s", (account_id,))
        account = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if account:
            return {
                "operation": "get",
                "success": True,
                "account": account
            }
        else:
            return {
                "operation": "get",
                "success": False,
                "error": f"No existe una cuenta con ID: {account_id}"
            }
    except Error as e:
        logger.error(f"Error obteniendo cuenta: {e}")
        return {
            "operation": "get",
            "success": False,
            "error": str(e)
        }

def get_accounts(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Obtiene una lista de cuentas según los filtros proporcionados.
    
    Args:
        filters: Diccionario con los filtros a aplicar
        
    Returns:
        Diccionario con la lista de cuentas o mensaje de error
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        sql = "SELECT * FROM accounts"
        params = []
        
        if filters:
            conditions = []
            for key, value in filters.items():
                if key in ["user_id", "name", "type", "currency", "is_active"]:
                    conditions.append(f"{key} = %s")
                    params.append(value)
            
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
        
        cursor.execute(sql, params)
        accounts = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {
            "operation": "list",
            "success": True,
            "accounts": accounts,
            "count": len(accounts)
        }
    except Error as e:
        logger.error(f"Error listando cuentas: {e}")
        return {
            "operation": "list",
            "success": False,
            "error": str(e)
        }


def account_sql_query(query_text: str) -> str:
    """
    Ejecuta una consulta SQL sobre la tabla accounts y devuelve los resultados.
    Esta función es llamada por la herramienta de Gemini.
    
    Args:
        query_text: Consulta SQL o comando para realizar operaciones en la tabla accounts
        
    Returns:
        Resultados de la operación en formato JSON
    """
    try:
       
        # Analizar el tipo de consulta
        query_lower = query_text.strip().lower()
        
        # Ejecutar la consulta apropiada
        result = None
        
        if query_lower.startswith("select"):
            # Consulta SELECT
            result = execute_sql_query(query_text)
        elif query_lower.startswith("insert"):
            # Consulta INSERT
            result = execute_sql_modification(query_text)
        elif query_lower.startswith("update"):
            # Consulta UPDATE
            result = execute_sql_modification(query_text)
        elif query_lower.startswith("delete"):
            # Consulta DELETE
            result = execute_sql_modification(query_text)
        else:
            # Comando específico (no SQL directo)
            parts = query_lower.split()
            command = parts[0] if parts else ""
            
            if command == "get" and len(parts) > 1:
                try:
                    account_id = int(parts[1])
                    result = get_account(account_id)
                except ValueError:
                    result = {"error": "ID de cuenta inválido"}
            elif command == "list":
                filters = {}
                for part in parts[1:]:
                    if "=" in part:
                        key, value = part.split("=", 1)
                        if key == "is_active":
                            value = value.lower() in ["true", "1", "yes", "y"]
                        filters[key] = value
                result = get_accounts(filters)
            elif command == "create" or command == "insert":
                # Extraer el JSON después del comando
                json_data = query_text[query_text.find("{"):].strip()
                if json_data:
                    try:
                        account_data = json.loads(json_data)
                        result = insert_account(account_data)
                    except json.JSONDecodeError:
                        result = {"error": "Formato JSON inválido"}
                else:
                    result = {"error": "Datos de cuenta faltantes"}
            elif command == "update" and len(parts) > 1:
                try:
                    account_id = int(parts[1])
                    json_data = query_text[query_text.find("{"):].strip()
                    if json_data:
                        try:
                            account_data = json.loads(json_data)
                            result = update_account(account_id, account_data)
                        except json.JSONDecodeError:
                            result = {"error": "Formato JSON inválido"}
                    else:
                        result = {"error": "Datos de actualización faltantes"}
                except ValueError:
                    result = {"error": "ID de cuenta inválido"}
            elif command == "delete" and len(parts) > 1:
                try:
                    account_id = int(parts[1])
                    result = delete_account(account_id)
                except ValueError:
                    result = {"error": "ID de cuenta inválido"}
            else:
                result = {"error": f"Comando desconocido o mal formateado: {command}"}
        
        # Formatear la respuesta como JSON
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        logger.error(f"Error en account_sql_query: {e}")
        return json.dumps({"error": str(e)}, indent=2)