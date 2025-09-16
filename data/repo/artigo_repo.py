from typing import Optional
from model.artigo_model import Artigo
from sql.artigo_sql import *
from util.db_util import get_connection

def criar_tabela() -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(CRIAR_TABELA_ARTIGO)
        return cursor.rowcount > 0

def inserir(artigo: Artigo) -> Optional[int]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(INSERIR_ARTIGO, (
            artigo.profissional_id,
            artigo.titulo,
            artigo.conteudo,
            artigo.gratuito,
            artigo.data_publicacao
        ))
        return cursor.lastrowid

def alterar(artigo: Artigo) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(ALTERAR_ARTIGO, (
            artigo.titulo,
            artigo.conteudo,
            artigo.gratuito,
            artigo.data_publicacao,
            artigo.id
        ))
        return cursor.rowcount > 0

def excluir(id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(EXCLUIR_ARTIGO, (id,))
        return cursor.rowcount > 0

def obter_por_id(id: int) -> Optional[Artigo]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(OBTER_POR_ID_ARTIGO, (id,))
        row = cursor.fetchone()
        if row:
            return Artigo(
                id=row["id"],
                profissional_id=row["profissional_id"],
                titulo=row["titulo"],
                conteudo=row["conteudo"],
                gratuito=row["gratuito"],
                data_publicacao=row["data_publicacao"]
            )
        return None

def obter_todos() -> list[Artigo]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(OBTER_TODOS_ARTIGO)
        rows = cursor.fetchall()
        return [
            Artigo(
                id=row["id"],
                profissional_id=row["profissional_id"],
                titulo=row["titulo"],
                conteudo=row["conteudo"],
                gratuito=row["gratuito"],
                data_publicacao=row["data_publicacao"]
            ) for row in rows
        ]
