from typing import Optional
from model.dieta_model import Dieta
from sql.dieta_sql import *
from util.db_util import get_connection

def criar_tabela() -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(CRIAR_TABELA_DIETA)
        return cursor.rowcount > 0

def inserir(dieta: Dieta) -> Optional[int]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(INSERIR_DIETA, (
            dieta.nome,
            dieta.descricao,
            dieta.gratuito
        ))
        return cursor.lastrowid

def alterar(dieta: Dieta) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(ALTERAR_DIETA, (
            dieta.nome,
            dieta.descricao,
            dieta.gratuito,
            dieta.id
        ))
        return cursor.rowcount > 0

def excluir(id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(EXCLUIR_DIETA, (id,))
        return cursor.rowcount > 0

def obter_por_id(id: int) -> Optional[Dieta]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(OBTER_POR_ID_DIETA, (id,))
        row = cursor.fetchone()
        if row:
            return Dieta(
                id=row["id"],
                nome=row["nome"],
                descricao=row["descricao"],
                gratuito=row["gratuito"]
            )
        return None

def obter_todos() -> list[Dieta]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(OBTER_TODOS_DIETA)
        rows = cursor.fetchall()
        return [
            Dieta(
                id=row["id"],
                nome=row["nome"],
                descricao=row["descricao"],
                gratuito=row["gratuito"]
            )
            for row in rows
        ]
