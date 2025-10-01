from typing import Optional
from data.model.avaliacao_fisica_model import AvaliacaoFisica
from data.sql.avaliacao_fisica_sql import *
from util.db_util import get_connection

def criar_tabela() -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(CRIAR_TABELA_AVALIACAO_FISICA)
        conn.commit()
        return True

def inserir(avaliacao: AvaliacaoFisica) -> Optional[int]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(INSERIR_AVALIACAO_FISICA, (
            avaliacao.personal_aluno_id,
            avaliacao.data_avaliacao,
            avaliacao.peso,
            avaliacao.altura,
            avaliacao.imc,
            avaliacao.percentual_gordura,
            avaliacao.massa_magra,
            avaliacao.circunferencias,
            avaliacao.observacoes,
            avaliacao.proxima_avaliacao
        ))
        conn.commit()
        return cursor.lastrowid

def alterar(avaliacao: AvaliacaoFisica) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(ALTERAR_AVALIACAO_FISICA, (
            avaliacao.personal_aluno_id,
            avaliacao.data_avaliacao,
            avaliacao.peso,
            avaliacao.altura,
            avaliacao.imc,
            avaliacao.percentual_gordura,
            avaliacao.massa_magra,
            avaliacao.circunferencias,
            avaliacao.observacoes,
            avaliacao.proxima_avaliacao,
            avaliacao.id
        ))
        conn.commit()
        return cursor.rowcount > 0

def excluir(id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(EXCLUIR_AVALIACAO_FISICA, (id,))
        conn.commit()
        return cursor.rowcount > 0

def obter_por_id(id: int) -> Optional[AvaliacaoFisica]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(OBTER_POR_ID_AVALIACAO_FISICA, (id,))
        row = cursor.fetchone()
        if row:
            return AvaliacaoFisica(
                id=row["id"],
                personal_aluno_id=row["personal_aluno_id"],
                data_avaliacao=row["data_avaliacao"],
                peso=row["peso"],
                altura=row["altura"],
                imc=row["imc"],
                percentual_gordura=row["percentual_gordura"],
                massa_magra=row["massa_magra"],
                circunferencias=row["circunferencias"],
                observacoes=row["observacoes"],
                proxima_avaliacao=row["proxima_avaliacao"]
            )
        return None

def obter_todos() -> list[AvaliacaoFisica]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(OBTER_TODOS_AVALIACAO_FISICA)
        rows = cursor.fetchall()
        return [
            AvaliacaoFisica(
                id=row["id"],
                personal_aluno_id=row["personal_aluno_id"],
                data_avaliacao=row["data_avaliacao"],
                peso=row["peso"],
                altura=row["altura"],
                imc=row["imc"],
                percentual_gordura=row["percentual_gordura"],
                massa_magra=row["massa_magra"],
                circunferencias=row["circunferencias"],
                observacoes=row["observacoes"],
                proxima_avaliacao=row["proxima_avaliacao"]
            ) for row in rows
        ]

def obter_por_aluno(personal_aluno_id: int) -> list[AvaliacaoFisica]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(OBTER_POR_ALUNO, (personal_aluno_id,))
        rows = cursor.fetchall()
        return [
            AvaliacaoFisica(
                id=row["id"],
                personal_aluno_id=row["personal_aluno_id"],
                data_avaliacao=row["data_avaliacao"],
                peso=row["peso"],
                altura=row["altura"],
                imc=row["imc"],
                percentual_gordura=row["percentual_gordura"],
                massa_magra=row["massa_magra"],
                circunferencias=row["circunferencias"],
                observacoes=row["observacoes"],
                proxima_avaliacao=row["proxima_avaliacao"]
            ) for row in rows
        ]

