import re
import logging
from typing import Dict, Any
from core.database import get_db_connection, AccountDBError

logger = logging.getLogger(__name__)

# Function to validate the SQL query to ensure it's only a SELECT query
def validate_sql_query(query: str) -> bool:
    # Remove comments and standardize whitespace
    query = re.sub(r'--.*', '', query, flags=re.MULTILINE)
    query = re.sub(r'/\*.*?\*/', '', query, flags=re.DOTALL)
    query = query.strip()
    
    # Check if it starts with SELECT
    if not re.match(r'^SELECT\s', query, re.IGNORECASE):
        return False
    
    # Check for dangerous operations
    dangerous_patterns = [
        r'\bDELETE\b', r'\bINSERT\b', r'\bUPDATE\b', r'\bDROP\b', 
        r'\bALTER\b', r'\bCREATE\b', r'\bTRUNCATE\b', r'\bGRANT\b',
        r'\bREVOKE\b', r'\bEXEC\b', r'\bUNION\b'
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            return False
    
    return True

def execute_sql_query(query: str, user_id: int) -> Dict[str, Any]:
    """
    Execute SQL query to retrieve financial information for the user.
    
    Args:
        query: SQL SELECT query to execute
        user_id: ID of the current user (passed by the system)
        
    Returns:
        Dict containing query results or error message
    """
    if not validate_sql_query(query):
        return {
            "success": False,
            "error": "Invalid query. Only SELECT statements are allowed."
        }
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        sql_keywords = {'SELECT', 'FROM', 'WHERE', 'JOIN', 'ON', 'ORDER', 'BY', 'GROUP', 'LIMIT', 'HAVING', 'AS'}
        pattern = r'\b(FROM|JOIN)\s+(\w+)(?:\s+(\w+))?'
                # Solo obtener los alias de la query principal (antes de cualquier subquery)
        main_query_section = query.split("GROUP BY")[0]  # o puedes cortar en 'ORDER BY', según el caso
        tables = {}
        for match in re.finditer(pattern, main_query_section, re.IGNORECASE):
            table = match.group(2)
            alias = match.group(3)
            if alias and alias.upper() not in sql_keywords:
                tables[alias] = table

        # Asegúrate de que sólo uses alias válidos
        user_filters = [f"{alias}.user_id = {user_id}" for alias in tables.keys()]

        user_filter = " AND ".join(user_filters) if user_filters else f"user_id = {user_id}"


        # user_filter = f"user_id = {user_id}"
        upper_query = query.upper()

        if "WHERE" in upper_query:
            modified_query = re.sub(
                r'(WHERE\b)',
                f'\\1 {user_filter} AND',
                query,
                flags=re.IGNORECASE,
                count=1
            )
        else:
            match = re.search(r'\b(ORDER BY|GROUP BY|LIMIT)\b', query, re.IGNORECASE)
            if match:
                idx = match.start()
                modified_query = f"{query[:idx]} WHERE {user_filter} {query[idx:]}"
            else:
                modified_query = f"{query} WHERE {user_filter}"

        # Execute the modified query
        cursor.execute(modified_query)
        results = cursor.fetchall()

        cursor.close()
        conn.close()

        return {
            "success": True,
            "results": results,
            "count": len(results)
        }

    except AccountDBError as e:
        logger.error(f"Database connection error: {str(e)}")
        return {
            "success": False,
            "error": f"Database connection error: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Error executing query: {str(e)}")
        return {
            "success": False,
            "error": f"Error executing query: {str(e)}"
        }
