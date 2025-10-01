from typing import Optional
from data.model.sessao_treino_model import SessaoTreino
from data.sql.sessao_treino_sql import *
from util.db_util import get_connection

def criar_tabela() -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(CRIAR_TABELA_SESSAO_TREINO)
        conn.commit()
        return True

def inserir(sessao: SessaoTreino) -> Optional[int]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(INSERIR_SESSAO_TREINO, (
            sessao.treino_id,
            sessao.nome,
            sessao.ordem,
            sessao.dia_semana,
            sessao.descricao,
            sessao.tempo_estimado,
            sessao.status
        ))
        conn.commit()
        return cursor.lastrowid

def alterar(sessao: SessaoTreino) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(ALTERAR_SESSAO_TREINO, (
            sessao.treino_id,
            sessao.nome,
            sessao.ordem,
            sessao.dia_semana,
            sessao.descricao,
            sessao.tempo_estimado,
            sessao.status,
            sessao.id
        ))
        conn.commit()
        return cursor.rowcount > 0

def excluir(id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(EXCLUIR_SESSAO_TREINO, (id,))
        conn.commit()
        return cursor.rowcount > 0

def obter_por_id(id: int) -> Optional[SessaoTreino]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(OBTER_POR_ID_SESSAO_TREINO, (id,))
        row = cursor.fetchone()
        if row:
            return SessaoTreino(
                id=row["id"],
                treino_id=row["treino_id"],
                nome=row["nome"],
                ordem=row["ordem"],
                dia_semana=row["dia_semana"],
                descricao=row["descricao"],
                tempo_estimado=row["tempo_estimado"],
                status=row["status"]
            )
        return None

def obter_todos() -> list[SessaoTreino]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(OBTER_TODOS_SESSAO_TREINO)
        rows = cursor.fetchall()
        return [
            SessaoTreino(
                id=row["id"],
                treino_id=row["treino_id"],
                nome=row["nome"],
                ordem=row["ordem"],
                dia_semana=row["dia_semana"],
                descricao=row["descricao"],
                tempo_estimado=row["tempo_estimado"],
                status=row["status"]
            ) for row in rows
        ]

def obter_por_treino(treino_id: int) -> list[SessaoTreino]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(OBTER_POR_TREINO, (treino_id,))
        rows = cursor.fetchall()
        return [
            SessaoTreino(
                id=row["id"],
                treino_id=row["treino_id"],
                nome=row["nome"],
                ordem=row["ordem"],
                dia_semana=row["dia_semana"],
                descricao=row["descricao"],
                tempo_estimado=row["tempo_estimado"],
                status=row["status"]
            ) for row in rows
        ]

