from typing import Optional, List
from datetime import datetime
from dataclasses import dataclass
from util.db_util import get_connection
from data.model.profissional_model import Profissional
from data.model.usuario_model import Usuario
from data.repo import usuario_repo
from data.sql.profissional_sql import *

# Função para criar a tabela (chame uma vez no setup)
def criar_tabela() -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(CRIAR_TABELA_PROFISSIONAL)
        conn.commit()
        return True

# Inserir um novo profissional
def inserir(prof: Profissional) -> Optional[int]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(INSERIR_PROFISSIONAL, (
            prof.id,                      # id do usuário já criado
            prof.especialidade,
            prof.registro_profissional,
            prof.status or 'pendente',
            prof.data_solicitacao or None,
            prof.data_aprovacao or None,
            prof.aprovado_por
        ))
        conn.commit()
        return cursor.lastrowid

# Alterar profissional + dados de usuário
def alterar(prof: Profissional, usuario: Usuario) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        # Atualiza dados do usuário
        usuario_repo.alterar(usuario, cursor)
        # Atualiza dados do profissional
        cursor.execute(ALTERAR_PROFISSIONAL, (
            prof.especialidade,
            prof.registro_profissional,
            prof.status,
            prof.data_solicitacao,
            prof.data_aprovacao,
            prof.aprovado_por,
            prof.id
        ))
        conn.commit()
        return cursor.rowcount > 0

# Excluir profissional + usuário
def excluir(id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(EXCLUIR_PROFISSIONAL, (id,))
        usuario_repo.excluir(id, cursor)
        conn.commit()
        return cursor.rowcount > 0

# Obter profissional por ID
def obter_por_id(id: int) -> Optional[Profissional]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(OBTER_POR_ID_PROFISSIONAL, (id,))
        row = cursor.fetchone()
        if row:
            return Profissional(
                id=row["id"],
                especialidade=row["especialidade"],
                registro_profissional=row["registro_profissional"] if "registro_profissional" in row.keys() else None,
                status=row["status"],
                data_solicitacao=row["data_solicitacao"],
                data_aprovacao=row["data_aprovacao"],
                aprovado_por=row["aprovado_por"] if "aprovado_por" in row.keys() else None
            )
        return None

# Obter todos os profissionais
def obter_todos() -> List[Profissional]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(OBTER_TODOS_PROFISSIONAL)
        rows = cursor.fetchall()
        return [
            Profissional(
                id=row["id"],
                especialidade=row["especialidade"],
                registro_profissional=row["registro_profissional"],
                status=row["status"],
                data_solicitacao=row["data_solicitacao"],
                data_aprovacao=row["data_aprovacao"],
                aprovado_por=row["aprovado_por"]
            )
            for row in rows
        ]

# Obter somente pendentes (dicts)
def obter_pendentes() -> list[dict]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(OBTER_PENDENTES)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

# Obter todos com status + nome do admin
def obter_todos_com_status() -> list[dict]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(OBTER_TODOS_COM_STATUS)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
def aprovar(profissional_id: int, admin_id: Optional[int] = None) -> bool:
    if not profissional_id:
        return False

    with get_connection() as conn:
        cursor = conn.cursor()

        # Confirma que o profissional existe e está pendente
        cursor.execute("SELECT id, status FROM profissional WHERE id = ?", (profissional_id,))
        row = cursor.fetchone()
        if not row or row["status"] != "pendente":
            return False

        cursor.execute(APROVAR_PROFISSIONAL, (admin_id, profissional_id))
        conn.commit()
        print(f"[ADMIN] Usuario {admin_id} aprovou profissional {profissional_id}")
        return cursor.rowcount > 0

def rejeitar(profissional_id: int, admin_id: Optional[int] = None) -> bool:
    if not profissional_id:
        return False

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, status FROM profissional WHERE id = ?", (profissional_id,))
        row = cursor.fetchone()
        if not row or row["status"] != "pendente":
            return False

        cursor.execute(REJEITAR_PROFISSIONAL, (admin_id, profissional_id))
        conn.commit()
        print(f"[ADMIN] Usuario {admin_id} rejeitou profissional {profissional_id}")
        return cursor.rowcount > 0


# Desativar profissional (status inativo)
def desativar(profissional_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE profissional SET status = 'inativo' WHERE id = ?", (profissional_id,))
        conn.commit()
        return cursor.rowcount > 0
