from typing import Optional
from data.model.personal_model import Personal
from data.sql.personal_sql import *
from util.db_util import get_connection

def criar_tabela() -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(CRIAR_TABELA_PERSONAL)
        conn.commit()
        return True

def inserir(personal: Personal) -> Optional[int]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(INSERIR_PERSONAL, (
            personal.profissional_id,
            personal.cref,
            personal.especialidades,
            personal.biografia,
            personal.anos_experiencia,
            personal.valor_mensalidade,
            personal.status,
            personal.data_cadastro,
            personal.foto_perfil,
            personal.avaliacoes_media,
            personal.total_alunos
        ))
        conn.commit()
        return cursor.lastrowid

def alterar(personal: Personal) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(ALTERAR_PERSONAL, (
            personal.profissional_id,
            personal.cref,
            personal.especialidades,
            personal.biografia,
            personal.anos_experiencia,
            personal.valor_mensalidade,
            personal.status,
            personal.foto_perfil,
            personal.avaliacoes_media,
            personal.total_alunos,
            personal.id
        ))
        conn.commit()
        return cursor.rowcount > 0

def excluir(id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(EXCLUIR_PERSONAL, (id,))
        conn.commit()
        return cursor.rowcount > 0

def obter_por_id(id: int) -> Optional[Personal]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(OBTER_POR_ID_PERSONAL, (id,))
        row = cursor.fetchone()
        if row:
            return Personal(
                id=row["id"],
                profissional_id=row["profissional_id"],
                cref=row["cref"],
                especialidades=row["especialidades"],
                biografia=row["biografia"],
                anos_experiencia=row["anos_experiencia"],
                valor_mensalidade=row["valor_mensalidade"],
                status=row["status"],
                data_cadastro=row["data_cadastro"],
                foto_perfil=row["foto_perfil"],
                avaliacoes_media=row["avaliacoes_media"],
                total_alunos=row["total_alunos"]
            )
        return None


def obter_todos() -> list[Personal]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(OBTER_TODOS_PERSONAL)
        rows = cursor.fetchall()
        return [
            Personal(
                id=row["id"],
                profissional_id=row["profissional_id"],
                cref=row["cref"],
                especialidades=row["especialidades"],
                biografia=row["biografia"],
                anos_experiencia=row["anos_experiencia"],
                valor_mensalidade=row["valor_mensalidade"],
                status=row["status"],
                data_cadastro=row["data_cadastro"],
                foto_perfil=row["foto_perfil"],
                avaliacoes_media=row["avaliacoes_media"],
                total_alunos=row["total_alunos"]
            ) for row in rows
        ]

def obter_por_profissional(profissional_id: int) -> Optional[Personal]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(OBTER_POR_PROFISSIONAL, (profissional_id,))
        row = cursor.fetchone()
        if row:
            return Personal(
                id=row["id"],
                profissional_id=row["profissional_id"],
                cref=row["cref"],
                especialidades=row["especialidades"],
                biografia=row["biografia"],
                anos_experiencia=row["anos_experiencia"],
                valor_mensalidade=row["valor_mensalidade"],
                status=row["status"],
                data_cadastro=row["data_cadastro"],
                foto_perfil=row["foto_perfil"],
                avaliacoes_media=row["avaliacoes_media"],
                total_alunos=row["total_alunos"]
            )
        return None