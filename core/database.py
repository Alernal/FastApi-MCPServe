import mysql.connector
from mysql.connector import Error

# Puedes mover este logger si lo tienes definido en otro archivo
import logging
logger = logging.getLogger(__name__)

class AccountDBError(Exception):
    pass

MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'mcp-serve'
}

def get_db_connection():
    """Establece y devuelve una conexión a la base de datos MySQL"""
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        return conn
    except Error as e:
        logger.error(f"Error al conectar a MySQL: {e}")
        raise AccountDBError(f"Error al conectar a MySQL: {e}")
