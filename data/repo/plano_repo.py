from typing import Optional
from data.model.plano_model import Plano
from data.sql.plano_sql import *
from util.db_util import get_connection

def criar_tabela() -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(CRIAR_TABELA_PLANO)
        return cursor.rowcount > 0

def inserir(plano: Plano) -> Optional[int]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(INSERIR_PLANO, (
            plano.nome,
            plano.preco
        ))
        return cursor.lastrowid

def alterar(plano: Plano) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(ALTERAR_PLANO, (
            plano.nome,
            plano.preco,
            plano.id
        ))
        return cursor.rowcount > 0

def excluir(id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(EXCLUIR_PLANO, (id,))
        return cursor.rowcount > 0

def obter_por_id(id: int) -> Optional[Plano]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(OBTER_POR_ID_PLANO, (id,))
        row = cursor.fetchone()
        if row:
            return Plano(
                id=row["id"],
                nome=row["nome"],
                preco=row["preco"]
            )
        return None

def obter_todos() -> list[Plano]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(OBTER_TODOS_PLANO)
        rows = cursor.fetchall()
        return [
            Plano(
                id=row["id"],
                nome=row["nome"],
                preco=row["preco"]
            ) for row in rows
        ]
