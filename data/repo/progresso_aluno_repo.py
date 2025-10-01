from typing import Optional
from data.model.progresso_aluno_model import ProgressoAluno
from data.model.treino_personalizado_model import TreinoPersonalizado
from data.sql.progresso_aluno_sql import *
from data.sql.treino_personalizado import OBTER_TODOS_TREINO_PERSONALIZADO
from util.db_util import get_connection

def criar_tabela() -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(CRIAR_TABELA_PROGRESSO_ALUNO)
        conn.commit()
        return True

def inserir(progresso: ProgressoAluno) -> Optional[int]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(INSERIR_PROGRESSO_ALUNO, (
            progresso.personal_aluno_id,
            progresso.data_registro,
            progresso.peso,
            progresso.medidas,
            progresso.fotos,
            progresso.observacoes,
            progresso.humor,
            progresso.energia
        ))
        conn.commit()
        return cursor.lastrowid

def alterar(progresso: ProgressoAluno) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(ALTERAR_PROGRESSO_ALUNO, (
            progresso.personal_aluno_id,
            progresso.data_registro,
            progresso.peso,
            progresso.medidas,
            progresso.fotos,
            progresso.observacoes,
            progresso.humor,
            progresso.energia,
            progresso.id
        ))
        conn.commit()
        return cursor.rowcount > 0

def excluir(id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(EXCLUIR_PROGRESSO_ALUNO, (id,))
        conn.commit()
        return cursor.rowcount > 0

def obter_por_id(id: int) -> Optional[ProgressoAluno]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(OBTER_POR_ID_PROGRESSO_ALUNO, (id,))
        row = cursor.fetchone()
        if row:
            return ProgressoAluno(
                id=row["id"],
                personal_aluno_id=row["personal_aluno_id"],
                data_registro=row["data_registro"],
                peso=row["peso"],
                medidas=row["medidas"],
                fotos=row["fotos"],
                observacoes=row["observacoes"],
                humor=row["humor"],
                energia=row["energia"]
            )
        return None

def obter_todos() -> list[ProgressoAluno]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(OBTER_TODOS_PROGRESSO_ALUNO)
        rows = cursor.fetchall()
        return [
            ProgressoAluno(
                id=row["id"],
                personal_aluno_id=row["personal_aluno_id"],
                data_registro=row["data_registro"],
                peso=row["peso"],
                medidas=row["medidas"],
                fotos=row["fotos"],
                observacoes=row["observacoes"],
                humor=row["humor"],
                energia=row["energia"]
            ) for row in rows
        ]

def obter_por_aluno(personal_aluno_id: int) -> list[ProgressoAluno]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(OBTER_POR_ALUNO, (personal_aluno_id,))
        rows = cursor.fetchall()
        return [
            ProgressoAluno(
                id=row["id"],
                personal_aluno_id=row["personal_aluno_id"],
                data_registro=row["data_registro"],
                peso=row["peso"],
                medidas=row["medidas"],
                fotos=row["fotos"],
                observacoes=row["observacoes"],
                humor=row["humor"],
                energia=row["energia"]
            ) for row in rows
        ]

def obter_todos() -> list[TreinoPersonalizado]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(OBTER_TODOS_TREINO_PERSONALIZADO)
        rows = cursor.fetchall()
        return [
            TreinoPersonalizado(
                id=row["id"],
                personal_aluno_id=row["personal_aluno_id"],
                nome=row["nome"],
                descricao=row["descricao"],
                objetivo=row["objetivo"],
                nivel_dificuldade=row["nivel_dificuldade"],
                duracao_semanas=row["duracao_semanas"],
                dias_semana=row["dias_semana"],
                divisao_treino=row["divisao_treino"],
                observacoes=row["observacoes"],
                status=row["status"],
                data_inicio=row["data_inicio"],
                data_fim=row["data_fim"],
                criado_em=row["criado_em"],
                atualizado_em=row["atualizado_em"]
            ) for row in rows
        ]

def obter_por_aluno(personal_aluno_id: int) -> list[TreinoPersonalizado]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(OBTER_POR_ALUNO, (personal_aluno_id,))
        rows = cursor.fetchall()
        return [
            TreinoPersonalizado(
                id=row["id"],
                personal_aluno_id=row["personal_aluno_id"],
                nome=row["nome"],
                descricao=row["descricao"],
                objetivo=row["objetivo"],
                nivel_dificuldade=row["nivel_dificuldade"],
                duracao_semanas=row["duracao_semanas"],
                dias_semana=row["dias_semana"],
                divisao_treino=row["divisao_treino"],
                observacoes=row["observacoes"],
                status=row["status"],
                data_inicio=row["data_inicio"],
                data_fim=row["data_fim"],
                criado_em=row["criado_em"],
                atualizado_em=row["atualizado_em"]
            ) for row in rows
        ]