from typing import Optional
from data.model.treino_personalizado_model import TreinoPersonalizado
from data.sql.treino_personalizado import *
from util.db_util import get_connection

def criar_tabela() -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(CRIAR_TABELA_TREINO_PERSONALIZADO)
        conn.commit()
        return True

def inserir(treino: TreinoPersonalizado) -> Optional[int]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(INSERIR_TREINO_PERSONALIZADO, (
            treino.personal_aluno_id,
            treino.nome,
            treino.descricao,
            treino.objetivo,
            treino.nivel_dificuldade,
            treino.duracao_semanas,
            treino.dias_semana,
            treino.divisao_treino,
            treino.observacoes,
            treino.status,
            treino.data_inicio,
            treino.data_fim,
            treino.criado_em,
            treino.atualizado_em
        ))
        conn.commit()
        return cursor.lastrowid

def alterar(treino: TreinoPersonalizado) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(ALTERAR_TREINO_PERSONALIZADO, (
            treino.personal_aluno_id,
            treino.nome,
            treino.descricao,
            treino.objetivo,
            treino.nivel_dificuldade,
            treino.duracao_semanas,
            treino.dias_semana,
            treino.divisao_treino,
            treino.observacoes,
            treino.status,
            treino.data_inicio,
            treino.data_fim,
            treino.atualizado_em,
            treino.id
        ))
        conn.commit()
        return cursor.rowcount > 0

def excluir(id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(EXCLUIR_TREINO_PERSONALIZADO, (id,))
        conn.commit()
        return cursor.rowcount > 0

def obter_por_id(id: int) -> Optional[TreinoPersonalizado]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(OBTER_POR_ID_TREINO_PERSONALIZADO, (id,))
        row = cursor.fetchone()
        if row:
            return TreinoPersonalizado(
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
            ) 

def obter_por_aluno(id: int) -> Optional[TreinoPersonalizado]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(OBTER_POR_ALUNO, (id,))
        rows = cursor.fetchall()
        treinos = []
        for row in rows:
            treinos.append(TreinoPersonalizado(
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
            ))
        return treinos



# OBTER_POR_ALUNO = """
# SELECT * FROM treino_personalizado
# WHERE personal_aluno_id=? AND status='ativo'
# ORDER BY criado_em DESC
# """