from typing import Optional
from data.model.nutricionista_model import Nutricionista
from data.sql.nutricionista_sql import *
from util.db_util import get_connection

def criar_tabela() -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(CRIAR_TABELA_NUTRICIONISTA)
        conn.commit()
        return True

def inserir(nutricionista: Nutricionista) -> Optional[int]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(INSERIR_NUTRICIONISTA, (
            nutricionista.profissional_id,
            nutricionista.crn,
            nutricionista.especialidades,
            nutricionista.biografia,
            nutricionista.anos_experiencia,
            nutricionista.valor_consulta,
            nutricionista.status,
            nutricionista.data_cadastro,
            nutricionista.foto_perfil,
            nutricionista.avaliacoes_media,
            nutricionista.total_pacientes
        ))
        conn.commit()
        return cursor.lastrowid

def alterar(nutricionista: Nutricionista) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(ALTERAR_NUTRICIONISTA, (
            nutricionista.profissional_id,
            nutricionista.crn,
            nutricionista.especialidades,
            nutricionista.biografia,
            nutricionista.anos_experiencia,
            nutricionista.valor_consulta,
            nutricionista.status,
            nutricionista.foto_perfil,
            nutricionista.avaliacoes_media,
            nutricionista.total_pacientes,
            nutricionista.id
        ))
        conn.commit()
        return cursor.rowcount > 0

def excluir(id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(EXCLUIR_NUTRICIONISTA, (id,))
        conn.commit()
        return cursor.rowcount > 0

def obter_por_id(id: int) -> Optional[Nutricionista]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(OBTER_POR_ID_NUTRICIONISTA, (id,))
        row = cursor.fetchone()
        if row:
            return Nutricionista(
                id=row["id"],
                profissional_id=row["profissional_id"],
                crn=row["crn"],
                especialidades=row["especialidades"],
                biografia=row["biografia"],
                anos_experiencia=row["anos_experiencia"],
                valor_consulta=row["valor_consulta"],
                status=row["status"],
                data_cadastro=row["data_cadastro"],
                foto_perfil=row["foto_perfil"],
                avaliacoes_media=row["avaliacoes_media"],
                total_pacientes=row["total_pacientes"]
            )
        return None

def obter_todos() -> list[Nutricionista]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(OBTER_TODOS_NUTRICIONISTA)
        rows = cursor.fetchall()
        return [
            Nutricionista(
                id=row["id"],
                profissional_id=row["profissional_id"],
                crn=row["crn"],
                especialidades=row["especialidades"],
                biografia=row["biografia"],
                anos_experiencia=row["anos_experiencia"],
                valor_consulta=row["valor_consulta"],
                status=row["status"],
                data_cadastro=row["data_cadastro"],
                foto_perfil=row["foto_perfil"],
                avaliacoes_media=row["avaliacoes_media"],
                total_pacientes=row["total_pacientes"]
            ) for row in rows
        ]

def obter_por_profissional(profissional_id: int) -> Optional[Nutricionista]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(OBTER_POR_PROFISSIONAL, (profissional_id,))
        row = cursor.fetchone()
        if row:
            return Nutricionista(
                id=row["id"],
                profissional_id=row["profissional_id"],
                crn=row["crn"],
                especialidades=row["especialidades"],
                biografia=row["biografia"],
                anos_experiencia=row["anos_experiencia"],
                valor_consulta=row["valor_consulta"],
                status=row["status"],
                data_cadastro=row["data_cadastro"],
                foto_perfil=row["foto_perfil"],
                avaliacoes_media=row["avaliacoes_media"],
                total_pacientes=row["total_pacientes"]
            )
        return None