from typing import Optional
from data.model.usuario_model import Usuario
from data.sql.usuario_sql import *
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
                perfil=row["perfil"]  # CORRIGIDO: era "tipo"
            )
        return None

def obter_por_email(email: str) -> Optional[Usuario]:
    """FUNÇÃO NOVA - ESSENCIAL"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuario WHERE email = ?", (email,))
        row = cursor.fetchone()
        if row:
            return Usuario(
                id=row["id"],
                nome=row["nome"],
                email=row["email"],
                senha=row["senha"],
                perfil=row["perfil"]  # CORRIGIDO: era "tipo"
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
                perfil=row["perfil"]  # CORRIGIDO: era "tipo"
            )
            for row in rows
        ]

def obter_todos_por_perfil(perfil: str) -> list[Usuario]:
    """FUNÇÃO NOVA - Para admin"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuario WHERE perfil = ? ORDER BY nome", (perfil,))
        rows = cursor.fetchall()
        return [
            Usuario(
                id=row["id"],
                nome=row["nome"],
                email=row["email"],
                senha=row["senha"],
                perfil=row["perfil"]
            )
            for row in rows
        ]

def atualizar_senha(usuario_id: int, nova_senha_hash: str) -> bool:
    """FUNÇÃO NOVA - Para redefinição de senha"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE usuario SET senha = ? WHERE id = ?", (nova_senha_hash, usuario_id))
        return cursor.rowcount > 0