from typing import Optional, List
from data.model.usuario_model import Usuario
from data.sql.usuario_sql import *
from util.db_util import get_connection

def criar_tabela() -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(CRIAR_TABELA_USUARIO)
        conn.commit()
        return True

def inserir(usuario: Usuario) -> Optional[int]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(INSERIR_USUARIO, (
            usuario.nome,
            usuario.email,
            usuario.senha,
            usuario.perfil
        ))
        conn.commit()
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
        conn.commit()
        return cursor.rowcount > 0

def excluir(id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(EXCLUIR_USUARIO, (id,))
        conn.commit()
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
                perfil=row["perfil"],
                foto=row["foto"],
                token_redefinicao=row["token_redefinicao"],
                data_token=row["data_token"],
                data_cadastro=row["data_cadastro"]
            )
        return None

def obter_por_email(email: str) -> Optional[Usuario]:
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
                perfil=row["perfil"],
                foto=row["foto"],
                token_redefinicao=row["token_redefinicao"],
                data_token=row["data_token"],
                data_cadastro=row["data_cadastro"]
            )
        return None

def obter_todos() -> List[Usuario]:
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
                perfil=row["perfil"],
                foto=row["foto"],
                token_redefinicao=row["token_redefinicao"],
                data_token=row["data_token"],
                data_cadastro=row["data_cadastro"]
            )
            for row in rows
        ]

def obter_todos_por_perfil(perfil: str) -> List[Usuario]:
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
                perfil=row["perfil"],
                foto=row["foto"],
                token_redefinicao=row["token_redefinicao"],
                data_token=row["data_token"],
                data_cadastro=row["data_cadastro"]
            )
            for row in rows
        ]

def atualizar_senha(usuario_id: int, nova_senha_hash: str) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE usuario SET senha = ? WHERE id = ?", (nova_senha_hash, usuario_id))
        conn.commit()
        return cursor.rowcount > 0

def atualizar_token(usuario_id: int, token: str) -> bool:
    """Atualiza o token de redefinição de senha e a data do token"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE usuario
            SET token_redefinicao = ?, data_token = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (token, usuario_id))
        conn.commit()
        return cursor.rowcount > 0
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def enviar_email_redefinicao(destinatario: str, token: str):
    remetente = "gabrag0987a@gmail.com"
    senha_app = "SUA_SENHA_DE_APP"  # senha de app do Gmail
    link = f"http://localhost:8000/resetar_senha?token={token}"
    msg = MIMEMultipart()
    msg['From'] = remetente
    msg['To'] = destinatario
    msg['Subject'] = "Redefinição de senha"

    corpo = f"Clique no link abaixo para redefinir sua senha:\n\n{link}"
    msg.attach(MIMEText(corpo, 'plain'))

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(remetente, senha_app)
        server.sendmail(remetente, destinatario, msg.as_string())