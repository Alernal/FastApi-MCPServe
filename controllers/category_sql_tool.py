from typing import Dict, Any, List, Optional
from mysql.connector import Error
import json
import logging
from core.database import get_db_connection

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constantes
VALID_CATEGORY_TYPES = ["Ingreso", "Gasto"]

class CategoryDBError(Exception):
    """Excepción personalizada para errores relacionados con la base de datos de categorías"""
    pass

def validate_category_data(data: Dict[str, Any]) -> None:
    """
    Valida los datos de la categoría antes de realizar operaciones de inserción o actualización.
    """
    if 'type' in data and data['type'] not in VALID_CATEGORY_TYPES:
        raise CategoryDBError(f"Tipo de categoría inválido. Debe ser uno de: {', '.join(VALID_CATEGORY_TYPES)}")

def execute_sql_query(sql: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
    try:
        if not sql.strip().lower().startswith("select"):
            raise CategoryDBError("Solo se permiten consultas SELECT")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(sql, params if params else ())
        results = cursor.fetchall()

        cursor.close()
        conn.close()

        return results
    except Error as e:
        logger.error(f"Error ejecutando consulta SQL: {e}")
        raise CategoryDBError(f"Error al ejecutar consulta SQL: {e}")

def execute_sql_modification(sql: str, params: Optional[tuple] = None) -> Dict[str, Any]:
    try:
        sql_lowercase = sql.strip().lower()
        if not any(sql_lowercase.startswith(op) for op in ["insert", "update", "delete"]):
            raise CategoryDBError("Operación no permitida. Solo INSERT, UPDATE o DELETE")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(sql, params if params else ())
        conn.commit()

        result = {
            "operation": "unknown",
            "affected_rows": cursor.rowcount,
            "success": True
        }

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
        raise CategoryDBError(f"Error al ejecutar modificación SQL: {e}")

def insert_category(category_data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        validate_category_data(category_data)

        if "name" not in category_data or "type" not in category_data:
            raise CategoryDBError("Los campos 'name' y 'type' son obligatorios")

        fields = []
        values = []
        params = []

        for key in ["name", "type", "parent_category_id"]:
            if key in category_data:
                fields.append(key)
                values.append("%s")
                params.append(category_data[key])

        sql = f"INSERT INTO categories ({', '.join(fields)}) VALUES ({', '.join(values)})"

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(sql, params)
        last_id = cursor.lastrowid

        conn.commit()
        cursor.close()
        conn.close()

        return {
            "operation": "insert",
            "category_id": last_id,
            "success": True,
            "message": f"Categoría creada con ID: {last_id}"
        }
    except (Error, CategoryDBError) as e:
        logger.error(f"Error insertando categoría: {e}")
        return {
            "operation": "insert",
            "success": False,
            "error": str(e)
        }

def update_category(category_id: int, category_data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        validate_category_data(category_data)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM categories WHERE id = %s", (category_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return {
                "operation": "update",
                "success": False,
                "error": f"No existe una categoría con ID: {category_id}"
            }

        set_clauses = []
        params = []

        for key, value in category_data.items():
            if key in ["name", "type", "parent_category_id"]:
                set_clauses.append(f"{key} = %s")
                params.append(value)

        params.append(category_id)
        sql = f"UPDATE categories SET {', '.join(set_clauses)} WHERE id = %s"

        cursor.execute(sql, params)
        affected_rows = cursor.rowcount

        conn.commit()
        cursor.close()
        conn.close()

        return {
            "operation": "update",
            "category_id": category_id,
            "affected_rows": affected_rows,
            "success": True,
            "message": f"Categoría actualizada con ID: {category_id}"
        }
    except (Error, CategoryDBError) as e:
        logger.error(f"Error actualizando categoría: {e}")
        return {
            "operation": "update",
            "success": False,
            "error": str(e)
        }

def delete_category(category_id: int) -> Dict[str, Any]:
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM categories WHERE id = %s", (category_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return {
                "operation": "delete",
                "success": False,
                "error": f"No existe una categoría con ID: {category_id}"
            }

        cursor.execute("DELETE FROM categories WHERE id = %s", (category_id,))
        conn.commit()

        cursor.close()
        conn.close()

        return {
            "operation": "delete",
            "category_id": category_id,
            "success": True,
            "message": f"Categoría eliminada con ID: {category_id}"
        }
    except Error as e:
        logger.error(f"Error eliminando categoría: {e}")
        return {
            "operation": "delete",
            "success": False,
            "error": str(e)
        }

def get_category(category_id: int) -> Dict[str, Any]:
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM categories WHERE id = %s", (category_id,))
        category = cursor.fetchone()

        cursor.close()
        conn.close()

        if category:
            return {
                "operation": "get",
                "success": True,
                "category": category
            }
        else:
            return {
                "operation": "get",
                "success": False,
                "error": f"No existe una categoría con ID: {category_id}"
            }
    except Error as e:
        logger.error(f"Error obteniendo categoría: {e}")
        return {
            "operation": "get",
            "success": False,
            "error": str(e)
        }

def get_categories(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        sql = "SELECT * FROM categories"
        params = []

        if filters:
            conditions = []
            for key, value in filters.items():
                if key in ["name", "type", "parent_category_id"]:
                    conditions.append(f"{key} = %s")
                    params.append(value)
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)

        cursor.execute(sql, params)
        categories = cursor.fetchall()

        cursor.close()
        conn.close()

        return {
            "operation": "list",
            "success": True,
            "categories": categories,
            "count": len(categories)
        }
    except Error as e:
        logger.error(f"Error listando categorías: {e}")
        return {
            "operation": "list",
            "success": False,
            "error": str(e)
        }

def category_sql_query(query_text: str) -> str:
    try:
        query_lower = query_text.strip().lower()
        result = None

        if query_lower.startswith("select"):
            result = execute_sql_query(query_text)
        elif query_lower.startswith("insert"):
            result = execute_sql_modification(query_text)
        elif query_lower.startswith("update"):
            result = execute_sql_modification(query_text)
        elif query_lower.startswith("delete"):
            result = execute_sql_modification(query_text)
        else:
            parts = query_lower.split()
            command = parts[0] if parts else ""

            if command == "get" and len(parts) > 1:
                try:
                    category_id = int(parts[1])
                    result = get_category(category_id)
                except ValueError:
                    result = {"error": "ID de categoría inválido"}
            elif command == "list":
                filters = {}
                for part in parts[1:]:
                    if "=" in part:
                        key, value = part.split("=", 1)
                        filters[key] = value
                result = get_categories(filters)
            elif command in ["create", "insert"]:
                json_data = query_text[query_text.find("{"):].strip()
                if json_data:
                    try:
                        category_data = json.loads(json_data)
                        result = insert_category(category_data)
                    except json.JSONDecodeError:
                        result = {"error": "Formato JSON inválido"}
                else:
                    result = {"error": "Datos de categoría faltantes"}
            elif command == "update" and len(parts) > 1:
                try:
                    category_id = int(parts[1])
                    json_data = query_text[query_text.find("{"):].strip()
                    if json_data:
                        try:
                            category_data = json.loads(json_data)
                            result = update_category(category_id, category_data)
                        except json.JSONDecodeError:
                            result = {"error": "Formato JSON inválido"}
                    else:
                        result = {"error": "Datos de actualización faltantes"}
                except ValueError:
                    result = {"error": "ID de categoría inválido"}
            elif command == "delete" and len(parts) > 1:
                try:
                    category_id = int(parts[1])
                    result = delete_category(category_id)
                except ValueError:
                    result = {"error": "ID de categoría inválido"}
            else:
                result = {"error": f"Comando desconocido o mal formateado: {command}"}

        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        logger.error(f"Error en category_sql_query: {e}")
        return json.dumps({"error": str(e)}, indent=2)
