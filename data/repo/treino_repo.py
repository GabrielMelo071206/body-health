from typing import Optional
from model.treino_model import Treino
from sql.treino_sql import *
from util.db_util import get_connection

def criar_tabela() -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(CRIAR_TABELA_TREINO)
        return cursor.rowcount > 0


def inserir(treino: Treino) -> Optional[int]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(INSERIR_TREINO, (
            treino.nome,
            treino.descricao,
            treino.gratuito
        ))
        return cursor.lastrowid

def alterar(treino: Treino) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(ALTERAR_TREINO, (
            treino.nome,
            treino.descricao,
            treino.gratuito,
            treino.id
        ))
        return cursor.rowcount > 0

def excluir(id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(EXCLUIR_TREINO, (id,))
        return cursor.rowcount > 0

def obter_por_id(id: int) -> Optional[Treino]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(OBTER_POR_ID_TREINO, (id,))
        row = cursor.fetchone()
        if row:
            return Treino(
                id=row["id"],
                nome=row["nome"],
                descricao=row["descricao"],
                gratuito=row["gratuito"]
            )
        return None

def obter_todos() -> list[Treino]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(OBTER_TODOS_TREINO)
        rows = cursor.fetchall()
        return [
            Treino(
                id=row["id"],
                nome=row["nome"],
                descricao=row["descricao"],
                gratuito=row["gratuito"]
            )
            for row in rows
        ]
