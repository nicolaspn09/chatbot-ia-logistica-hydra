import os
import sys
import psycopg2
from dotenv import load_dotenv, find_dotenv
from psycopg2.extras import execute_values


class ConectaPG:
    def __init__(self, sql):
        self.sql = sql


    # Roda query para executar o MySQL
    def conecta_pg(self):
        """
        Roda query para executar o MySQL

        Parameters:
        Sql = string

        Returns:
        tabela_sql = datatable
        """
        script_dir = os.path.dirname(os.path.abspath(__file__))
        load_dotenv(find_dotenv(os.path.join(script_dir, '.env')))

        host = os.getenv("host")  # Endereço do servidor MySQL
        database = os.getenv("database")  # Nome do banco de dados
        user = os.getenv("user")  # Nome de usuário para acessar o banco de dados
        password = os.getenv("password")  # Senha do usuário para acessar o banco de dados
        port = os.getenv("port")

        # Estabelece a conexão com o banco de dados
        connection = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            port=port
        )

        cursor = connection.cursor()
        cursor.execute(self.sql)
        tabela_sql = cursor.fetchall()
        cursor.close()
        connection.close()

        # Retorna o resultado da consulta do SQL para o usuário
        return tabela_sql


    # Roda query para executar o MySQL
    def conecta_pg_insert(self):
        """
        Roda query para executar o MySQL

        Parameters: 
        sql = string
        """
        script_dir = os.path.dirname(os.path.abspath(__file__))
        load_dotenv(find_dotenv(os.path.join(script_dir, '.env')))

        host = os.getenv("host")  # Endereço do servidor MySQL
        database = os.getenv("database")  # Nome do banco de dados
        user = os.getenv("user")  # Nome de usuário para acessar o banco de dados
        password = os.getenv("password")  # Senha do usuário para acessar o banco de dados
        port = os.getenv("port")

        # Estabelece a conexão com o banco de dados
        connection = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            port=port
        )

        cursor = connection.cursor()
        cursor.execute(self.sql)
        connection.commit()
        cursor.close()
        connection.close()
        