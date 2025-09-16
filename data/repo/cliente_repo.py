from typing import Optional
from model.cliente_model import Cliente
from model.usuario_model import Usuario
from repo import usuario_repo
from sql.cliente_sql import *
from util.db_util import get_connection

def criar_tabela() -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(CRIAR_TABELA_CLIENTE)
        return cursor.rowcount > 0

def inserir(cliente: Cliente) -> Optional[int]:
    with get_connection() as conn:
        cursor = conn.cursor()
        # Primeiro cria o usuário
        usuario = Usuario(
            id=0,
            nome=cliente.nome,
            email=cliente.email,
            senha=cliente.senha,
            perfil='cliente'
        )
        id_usuario = usuario_repo.inserir(usuario)
        # Depois cria o registro de cliente
        cursor.execute(INSERIR_CLIENTE, (
            id_usuario,
            cliente.plano_id
        ))
        return id_usuario

def alterar(cliente: Cliente) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        usuario = Usuario(
            id=cliente.id,
            nome=cliente.nome,
            email=cliente.email,
            senha=cliente.senha,
            perfil='cliente'
        )
        usuario_repo.alterar(usuario)
        cursor.execute(ALTERAR_CLIENTE, (
            cliente.plano_id,
            cliente.id
        ))
        return cursor.rowcount > 0

def excluir(id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(EXCLUIR_CLIENTE, (id,))
        usuario_repo.excluir(id)
        return cursor.rowcount > 0

def obter_por_id(id: int) -> Optional[Cliente]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(OBTER_POR_ID_CLIENTE, (id,))
        row = cursor.fetchone()
        if row:
            return Cliente(
                id=row["id"],
                plano_id=row["plano_id"],
                nome=row["nome"],
                email=row["email"],
                senha=row["senha"]
            )
        return None

def obter_todos() -> list[Cliente]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(OBTER_TODOS_CLIENTE)
        rows = cursor.fetchall()
        return [
            Cliente(
                id=row["id"],
                plano_id=row["plano_id"],
                nome=row["nome"],
                email=row["email"],
                senha=row["senha"]
            )
            for row in rows
        ]
