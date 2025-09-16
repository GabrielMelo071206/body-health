from typing import Optional
from data.model.profissional_model import Profissional
from data.model.usuario_model import Usuario
from data.repo import usuario_repo
from data.sql.profissional_sql import *
from util.db_util import get_connection

def criar_tabela() -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(CRIAR_TABELA_PROFISSIONAL)
        return cursor.rowcount > 0


def inserir(prof: Profissional) -> Optional[int]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(INSERIR_PROFISSIONAL, (
            prof.usuario_id,
            prof.especialidade,
            prof.registro_profissional,
            'pendente',   # Valor para 'status'
            None,         # Valor para 'data_solicitacao' (o SQL pode preencher com DEFAULT)
            None,         # Valor para 'data_aprovacao'
            None          # Valor para 'aprovado_por'
        ))
        conn.commit()
        return cursor.lastrowid
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

def obter_pendentes() -> list:
    """Obter profissionais pendentes de aprovação"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(OBTER_PENDENTES)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def obter_todos_com_status() -> list:
    """Obter todos profissionais com status"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(OBTER_TODOS_COM_STATUS)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def aprovar(profissional_id: int, admin_id: int = None) -> bool:
    """Aprovar profissional"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(APROVAR_PROFISSIONAL, (admin_id, profissional_id))
        return cursor.rowcount > 0

def rejeitar(profissional_id: int, admin_id: int = None) -> bool:
    """Rejeitar profissional"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(REJEITAR_PROFISSIONAL, (admin_id, profissional_id))
        return cursor.rowcount > 0

def desativar(profissional_id: int) -> bool:
    """Desativar profissional"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE profissional SET status = 'inativo' WHERE id = ?", (profissional_id,))
        return cursor.rowcount > 0