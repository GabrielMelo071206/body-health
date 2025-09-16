from typing import Optional
from data.model.cliente_model import Cliente
from data.sql.cliente_sql import *
from util.db_util import get_connection

def criar_tabela() -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(CRIAR_TABELA_CLIENTE)
        return cursor.rowcount > 0

def inserir(cliente: Cliente) -> Optional[int]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(INSERIR_CLIENTE, (
            cliente.usuario_id,  # CORRIGIDO
            cliente.plano_id
        ))
        return cursor.lastrowid

def alterar(cliente: Cliente) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(ALTERAR_CLIENTE, (
            cliente.plano_id,
            cliente.usuario_id  # CORRIGIDO
        ))
        return cursor.rowcount > 0

def excluir(usuario_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(EXCLUIR_CLIENTE, (usuario_id,))
        return cursor.rowcount > 0

def obter_por_id(usuario_id: int) -> Optional[Cliente]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(OBTER_POR_ID_CLIENTE, (usuario_id,))
        row = cursor.fetchone()
        if row:
            return Cliente(
                usuario_id=row["id"],  # CORRIGIDO
                plano_id=row["plano_id"]
            )
        return None

def obter_todos() -> list[Cliente]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(OBTER_TODOS_CLIENTE)
        rows = cursor.fetchall()
        return [
            Cliente(
                usuario_id=row["id"],  # CORRIGIDO
                plano_id=row["plano_id"]
            )
            for row in rows
        ]