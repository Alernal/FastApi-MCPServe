import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)
load_dotenv()

class AccountDBError(Exception):
    pass

MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST'),
    'user': os.getenv('MYSQL_USER'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'database': os.getenv('MYSQL_DATABASE')
}

def get_db_connection():
    """Establece y devuelve una conexión a la base de datos MySQL"""
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        return conn
    except Error as e:
        logger.error(f"Error al conectar a MySQL: {e}")
        raise AccountDBError(f"Error al conectar a MySQL: {e}")
