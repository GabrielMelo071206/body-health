from typing import Optional
from model.profissional_model import Profissional
from model.usuario_model import Usuario
from repo import usuario_repo
from sql.profissional_sql import *
from util.db_util import get_connection

def criar_tabela() -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(CRIAR_TABELA_PROFISSIONAL)
        return cursor.rowcount > 0

def inserir(prof: Profissional, usuario: Usuario) -> Optional[int]:
    with get_connection() as conn:
        cursor = conn.cursor()
        id_usuario = usuario_repo.inserir(usuario, cursor)
        cursor.execute(INSERIR_PROFISSIONAL, (
            id_usuario,
            prof.especialidade
        ))
        return id_usuario

def alterar(prof: Profissional, usuario: Usuario) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        usuario_repo.alterar(usuario, cursor)
        cursor.execute(ALTERAR_PROFISSIONAL, (
            prof.especialidade,
            prof.id
        ))
        return cursor.rowcount > 0

def excluir(id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(EXCLUIR_PROFISSIONAL, (id,))
        usuario_repo.excluir(id, cursor)
        return cursor.rowcount > 0

def obter_por_id(id: int) -> Optional[Profissional]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(OBTER_POR_ID_PROFISSIONAL, (id,))
        row = cursor.fetchone()
        if row:
            return Profissional(
                id=row["id"],
                especialidade=row["especialidade"],
                nome=row["nome"],
                email=row["email"],
                senha=row["senha"]
            )
        return None

def obter_todos() -> list[Profissional]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(OBTER_TODOS_PROFISSIONAL)
        rows = cursor.fetchall()
        return [
            Profissional(
                id=row["id"],
                especialidade=row["especialidade"],
                nome=row["nome"],
                email=row["email"],
                senha=row["senha"]
            ) for row in rows
        ]
