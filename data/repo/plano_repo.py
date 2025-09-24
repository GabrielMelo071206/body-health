from typing import Optional
from data.model.plano_model import Plano
from data.sql.plano_sql import *
from util.db_util import get_connection

def criar_tabela() -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(CRIAR_TABELA_PLANO)
        return cursor.rowcount > 0

def inserir(plano: Plano) -> Optional[int]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(INSERIR_PLANO, (
            plano.nome,
            plano.descricao,  
            plano.preco,
            plano.duracao_dias  
        ))
        conn.commit()
        return cursor.lastrowid
    
def alterar(plano: Plano) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(ALTERAR_PLANO, (
            plano.nome,
            plano.preco,
            plano.id,
            plano.duracao_dias,
            plano.descricao
        ))
        return cursor.rowcount > 0

def excluir(id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(EXCLUIR_PLANO, (id,))
        return cursor.rowcount > 0

def obter_por_id(id: int) -> Optional[Plano]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(OBTER_POR_ID_PLANO, (id,))
        row = cursor.fetchone()
        if row:
            return Plano(
                id=row["id"],
                nome=row["nome"],
                descricao=row["descricao"],
                preco=row["preco"],
                duracao_dias=row["duracao_dias"],
                ativo=row["ativo"]
            )
        return None
    
def obter_por_tipo(self, tipo: str) -> list[Plano]:
    """Obter planos gratuitos ou pagos"""
    with get_connection() as conn:
        cursor = conn.cursor()
        if tipo == "gratuito":
            cursor.execute("SELECT * FROM plano WHERE preco = 0 AND ativo = 1 ORDER BY id")
        else:  # "pago"
            cursor.execute("SELECT * FROM plano WHERE preco > 0 AND ativo = 1 ORDER BY preco")
        
        rows = cursor.fetchall()
        return [
            Plano(
                id=row["id"],
                nome=row["nome"],
                descricao=row["descricao"],
                preco=row["preco"],
                duracao_dias=row["duracao_dias"],
                ativo=row["ativo"]
            ) for row in rows
        ]

def obter_todos() -> list[Plano]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(OBTER_TODOS_PLANO)
        rows = cursor.fetchall()
        return [
            Plano(
                id=row["id"],
                nome=row["nome"],
                descricao=row["descricao"],  
                preco=row["preco"],
                duracao_dias=row["duracao_dias"],  
                ativo=row["ativo"]  
            ) for row in rows
        ]