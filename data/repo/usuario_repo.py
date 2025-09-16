from typing import Optional
from model.usuario_model import Usuario
from sql.usuario_sql import *
from util.db_util import get_connection

def criar_tabela() -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(CRIAR_TABELA_USUARIO)
        return cursor.rowcount > 0

def inserir(usuario: Usuario) -> Optional[int]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(INSERIR_USUARIO, (
            usuario.nome,
            usuario.email,
            usuario.senha,
            usuario.perfil
        ))
        return cursor.lastrowid

def alterar(usuario: Usuario) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(ALTERAR_USUARIO, (
            usuario.nome,
            usuario.email,
            usuario.senha,
            usuario.perfil,
            usuario.id
        ))
        return cursor.rowcount > 0

def excluir(id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(EXCLUIR_USUARIO, (id,))
        return cursor.rowcount > 0

def obter_por_id(id: int) -> Optional[Usuario]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(OBTER_POR_ID_USUARIO, (id,))
        row = cursor.fetchone()
        if row:
            return Usuario(
                id=row["id"],
                nome=row["nome"],
                email=row["email"],
                senha=row["senha"],
                perfil=row["tipo"]
            )
        return None

def obter_todos() -> list[Usuario]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(OBTER_TODOS_USUARIO)
        rows = cursor.fetchall()
        return [
            Usuario(
                id=row["id"],
                nome=row["nome"],
                email=row["email"],
                senha=row["senha"],
                perfil=row["tipo"]
            )
            for row in rows
        ]
