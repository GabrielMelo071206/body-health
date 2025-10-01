from typing import Optional
from data.model.personal_aluno_model import PersonalAluno
from data.sql.personal_aluno_sql import *
from util.db_util import get_connection

def criar_tabela() -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(CRIAR_TABELA_PERSONAL_ALUNO)
        conn.commit()
        return True

def inserir(personal_aluno: PersonalAluno) -> Optional[int]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(INSERIR_PERSONAL_ALUNO, (
            personal_aluno.personal_id,
            personal_aluno.aluno_id,
            personal_aluno.data_inicio,
            personal_aluno.data_fim,
            personal_aluno.status,
            personal_aluno.objetivo,
            personal_aluno.observacoes
        ))
        conn.commit()
        return cursor.lastrowid

def alterar(personal_aluno: PersonalAluno) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(ALTERAR_PERSONAL_ALUNO, (
            personal_aluno.personal_id,
            personal_aluno.aluno_id,
            personal_aluno.data_inicio,
            personal_aluno.data_fim,
            personal_aluno.status,
            personal_aluno.objetivo,
            personal_aluno.observacoes,
            personal_aluno.id
        ))
        conn.commit()
        return cursor.rowcount > 0

def excluir(id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(EXCLUIR_PERSONAL_ALUNO, (id,))
        conn.commit()
        return cursor.rowcount > 0

def obter_por_id(id: int) -> Optional[PersonalAluno]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(OBTER_POR_ID_PERSONAL_ALUNO, (id,))
        row = cursor.fetchone()
        if row:
            return PersonalAluno(
                id=row["id"],
                personal_id=row["personal_id"],
                aluno_id=row["aluno_id"],
                data_inicio=row["data_inicio"],
                data_fim=row["data_fim"],
                status=row["status"],
                objetivo=row["objetivo"],
                observacoes=row["observacoes"]
            )
        return None

def obter_todos() -> list[PersonalAluno]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(OBTER_TODOS_PERSONAL_ALUNO)
        rows = cursor.fetchall()
        return [
            PersonalAluno(
                id=row["id"],
                personal_id=row["personal_id"],
                aluno_id=row["aluno_id"],
                data_inicio=row["data_inicio"],
                data_fim=row["data_fim"],
                status=row["status"],
                objetivo=row["objetivo"],
                observacoes=row["observacoes"]
            ) for row in rows
        ]

def obter_alunos_por_personal(personal_id: int) -> list[PersonalAluno]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(OBTER_ALUNOS_POR_PERSONAL, (personal_id,))
        rows = cursor.fetchall()
        return [
            PersonalAluno(
                id=row["id"],
                personal_id=row["personal_id"],
                aluno_id=row["aluno_id"],
                data_inicio=row["data_inicio"],
                data_fim=row["data_fim"],
                status=row["status"],
                objetivo=row["objetivo"],
                observacoes=row["observacoes"]
            ) for row in rows
        ]
