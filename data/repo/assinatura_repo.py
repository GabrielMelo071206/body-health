from typing import Optional
from model.assinatura_model import Assinatura
from sql.assinatura_sql import *
from util.db_util import get_connection

def criar_tabela() -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(CRIAR_TABELA_ASSINATURA)
        return cursor.rowcount > 0

def inserir(assinatura: Assinatura) -> Optional[int]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(INSERIR_ASSINATURA, (
            assinatura.cliente_id,
            assinatura.plano_id,
            assinatura.data_inicio,
            assinatura.data_fim,
            assinatura.status
        ))
        return cursor.lastrowid

def alterar(assinatura: Assinatura) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(ALTERAR_ASSINATURA, (
            assinatura.plano_id,
            assinatura.data_inicio,
            assinatura.data_fim,
            assinatura.status,
            assinatura.id
        ))
        return cursor.rowcount > 0

def excluir(id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(EXCLUIR_ASSINATURA, (id,))
        return cursor.rowcount > 0

def obter_por_id(id: int) -> Optional[Assinatura]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(OBTER_POR_ID_ASSINATURA, (id,))
        row = cursor.fetchone()
        if row:
            return Assinatura(
                id=row["id"],
                cliente_id=row["cliente_id"],
                plano_id=row["plano_id"],
                data_inicio=row["data_inicio"],
                data_fim=row["data_fim"],
                status=row["status"]
            )
        return None

def obter_todos() -> list[Assinatura]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(OBTER_TODOS_ASSINATURA)
        rows = cursor.fetchall()
        return [
            Assinatura(
                id=row["id"],
                cliente_id=row["cliente_id"],
                plano_id=row["plano_id"],
                data_inicio=row["data_inicio"],
                data_fim=row["data_fim"],
                status=row["status"]
            ) for row in rows
        ]
