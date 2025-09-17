import datetime
from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import secrets
from typing import Optional

# Seus imports
from data.repo import plano_repo, usuario_repo, cliente_repo, profissional_repo
from util.security import criar_hash_senha, verificar_senha
from util.auth_decorator import criar_sessao, obter_usuario_logado
from data.model.usuario_model import Usuario
from data.model.cliente_model import Cliente
from data.model.profissional_model import Profissional
from data.model.plano_model import Plano

app = FastAPI()

# Configurações
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

SECRET_KEY = secrets.token_urlsafe(32)
app.add_middleware( 
    SessionMiddleware, 
    secret_key=SECRET_KEY, 
    max_age=3600, 
    same_site="lax", 
    https_only=False
)

# =================== PÁGINAS INICIAIS ===================

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("inicio/index.html", {"request": request})

@app.get("/sobre")
async def sobre(request: Request):
    return templates.TemplateResponse("inicio/sobre.html", {"request": request})

@app.get("/planos")
async def planos(request: Request):
    return templates.TemplateResponse("inicio/planos.html", {"request": request})

@app.get("/pagamento")
async def pagamento(request: Request):
    return templates.TemplateResponse("inicio/pagamento.html", {"request": request})

@app.get("/suporte")
async def suporte(request: Request):
    return templates.TemplateResponse("inicio/suporte.html", {"request": request})

# =================== AUTENTICAÇÃO ===================

@app.get("/login")
async def login_get(request: Request):
    return templates.TemplateResponse("inicio/login.html", {"request": request})

@app.get("/login_cliente")
async def login_cliente_get(request: Request):
    return templates.TemplateResponse("inicio/login_cliente.html", {"request": request})

@app.post("/login_cliente")
async def login_cliente_post(request: Request, email: str = Form(...), senha: str = Form(...)):
    usuario = usuario_repo.obter_por_email(email)
    
    if not usuario or usuario.perfil != "cliente" or not verificar_senha(senha, usuario.senha):
        return templates.TemplateResponse(
            "inicio/login_cliente.html", 
            {"request": request, "erro": "Email ou senha inválidos"}
        )
    
    # Criar sessão
    usuario_dict = {
        "id": usuario.id,
        "nome": usuario.nome,
        "email": usuario.email,
        "perfil": usuario.perfil,
        "foto": usuario.foto
    }
    criar_sessao(request, usuario_dict)
    
    return RedirectResponse("/", status_code=303)

@app.get("/login_profissional")
async def login_profissional_get(request: Request):
    return templates.TemplateResponse("inicio/login_profissional.html", {"request": request})

@app.post("/login_profissional")
async def login_profissional_post(request: Request, email: str = Form(...), senha: str = Form(...)):
    usuario = usuario_repo.obter_por_email(email)
    
    if not usuario or usuario.perfil != "profissional" or not verificar_senha(senha, usuario.senha):
        return templates.TemplateResponse(
            "inicio/login_profissional.html", 
            {"request": request, "erro": "Email ou senha inválidos"}
        )
    
    # Criar sessão
    usuario_dict = {
        "id": usuario.id,
        "nome": usuario.nome,
        "email": usuario.email,
        "perfil": usuario.perfil,
        "foto": usuario.foto
    }
    criar_sessao(request, usuario_dict)
    
    return RedirectResponse("/", status_code=303)

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)

# =================== CADASTROS ===================

@app.get("/cadastro_cliente")
async def cadastro_cliente_get(request: Request):
    return templates.TemplateResponse("inicio/cadastro_cliente.html", {"request": request})

@app.post("/cadastro_cliente")
async def cadastro_cliente_post(
    request: Request,
    nome: str = Form(...),
    email: str = Form(...),
    senha: str = Form(...)
):
    if usuario_repo.obter_por_email(email):
        return templates.TemplateResponse(
            "inicio/cadastro_cliente.html", 
            {"request": request, "erro": "Email já cadastrado"}
        )

    hash_senha = criar_hash_senha(senha)
    usuario = Usuario(
        id=0, 
        nome=nome, 
        email=email, 
        senha=hash_senha, 
        perfil="cliente"
    )
    
    usuario_id = usuario_repo.inserir(usuario)
    
    # Criar registro na tabela cliente
    cliente = Cliente(usuario_id=usuario_id, plano_id=None)
    cliente_repo.inserir(cliente)

    return RedirectResponse("/login_cliente", status_code=303)

@app.get("/cadastro_profissional")
async def cadastro_profissional_get(request: Request):
    return templates.TemplateResponse("inicio/cadastro_profissional.html", {"request": request})

@app.post("/cadastro_profissional")
async def cadastro_profissional_post(
    request: Request,
    nome: str = Form(...),
    email: str = Form(...),
    senha: str = Form(...),
    especialidade: str = Form(...),
    registro_profissional: Optional[str] = Form(None)
):
    # Verifica se o email já está cadastrado
    if usuario_repo.obter_por_email(email):
        return templates.TemplateResponse(
            "inicio/cadastro_profissional.html", 
            {"request": request, "erro": "Email já cadastrado"}
        )

    # Cria hash da senha
    hash_senha = criar_hash_senha(senha)

    # Cria usuário com perfil de profissional
    usuario = Usuario(
        id=0, 
        nome=nome, 
        email=email, 
        senha=hash_senha, 
        perfil="profissional"
    )
    
    # Insere usuário no banco e obtém ID
    usuario_id = usuario_repo.inserir(usuario)
    
    # Cria registro do profissional com status pendente
    from datetime import datetime

    profissional = Profissional(
        id=usuario_id,
        especialidade=especialidade,
        registro_profissional=registro_profissional,
        data_solicitacao=datetime.now(),  # <--- funciona agora
        status="pendente"
    )

    profissional_repo.inserir(profissional)

    # Redireciona para página de login do profissional
    return RedirectResponse("/login_profissional", status_code=303)

from util.auth_decorator import requer_autenticacao

@app.get("/perfil")
@requer_autenticacao()
async def perfil(request: Request, usuario_logado: dict = Depends(obter_usuario_logado)):
    return templates.TemplateResponse("perfil.html", {
        "request": request, 
        "usuario": usuario_logado
    })

# =================== ÁREA DE ADMINISTRAÇÃO ===================

@app.get("/admin")
@requer_autenticacao(['admin'])
async def admin_dashboard(request: Request, usuario_logado: dict = None):
    """Dashboard principal do admin"""
    
    # Estatísticas gerais
    total_usuarios = len(usuario_repo.obter_todos())
    total_clientes = len(cliente_repo.obter_todos())
    total_profissionais = len(profissional_repo.obter_todos())
    total_planos = len(plano_repo.obter_todos())
    
    # Profissionais pendentes de aprovação (você precisa adicionar campo 'ativo' na tabela)
    profissionais_pendentes = profissional_repo.obter_pendentes()
    
    estatisticas = {
        "total_usuarios": total_usuarios,
        "total_clientes": total_clientes,
        "total_profissionais": total_profissionais,
        "total_planos": total_planos,
        "profissionais_pendentes": len(profissionais_pendentes)
    }
    
    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request,
        "usuario": usuario_logado,
        "estatisticas": estatisticas,
        "profissionais_pendentes": profissionais_pendentes[:5]  # Últimos 5
    })

# =================== GESTÃO DE PLANOS ===================

@app.get("/admin/planos")
@requer_autenticacao(['admin'])
async def admin_planos_listar(request: Request, usuario_logado: dict = Depends(obter_usuario_logado)):
    """Listar todos os planos"""
    planos = plano_repo.obter_todos()
    return templates.TemplateResponse("admin/planos/listar.html", {
        "request": request,
        "usuario": usuario_logado,
        "planos": planos
    })

@app.get("/admin/planos/novo")
@requer_autenticacao(['admin'])
async def admin_planos_novo_get(request: Request, usuario_logado: dict = Depends(obter_usuario_logado)):
    """Formulário para criar novo plano"""
    return templates.TemplateResponse("admin/planos/form.html", {
        "request": request,
        "usuario": usuario_logado,
        "titulo": "Criar Novo Plano",
        "acao": "/admin/planos/novo"
    })

@app.post("/admin/planos/novo")
@requer_autenticacao(['admin'])
async def admin_planos_novo_post(
    request: Request,
    nome: str = Form(...),
    descricao: str = Form(...),
    preco: float = Form(...),
    duracao_dias: int = Form(...),
    usuario_logado: dict = Depends(obter_usuario_logado)
):
    """Criar novo plano"""
    
    plano = Plano(
        id=0,
        nome=nome,
        descricao=descricao,
        preco=preco,
        duracao_dias=duracao_dias
    )
    
    plano_repo.inserir(plano)
    
    return RedirectResponse("/admin/planos", status_code=303)

@app.get("/admin/planos/editar/{plano_id}")
@requer_autenticacao(['admin'])
async def admin_planos_editar_get(request: Request, plano_id: int, usuario_logado: dict = Depends(obter_usuario_logado)):
    """Formulário para editar plano"""
    plano = plano_repo.obter_por_id(plano_id)
    if not plano:
        return RedirectResponse("/admin/planos", status_code=303)
    
    return templates.TemplateResponse("admin/planos/form.html", {
        "request": request,
        "usuario": usuario_logado,
        "plano": plano,
        "titulo": "Editar Plano",
        "acao": f"/admin/planos/editar/{plano_id}"
    })

@app.post("/admin/planos/editar/{plano_id}")
@requer_autenticacao(['admin'])
async def admin_planos_editar_post(
    request: Request,
    plano_id: int,
    nome: str = Form(...),
    descricao: str = Form(...),
    preco: float = Form(...),
    duracao_dias: int = Form(...),
    usuario_logado: dict = Depends(obter_usuario_logado)
):
    """Atualizar plano"""
    plano = Plano(
        id=plano_id,
        nome=nome,
        descricao=descricao,
        preco=preco,
        duracao_dias=duracao_dias
    )
    
    plano_repo.alterar(plano)
    return RedirectResponse("/admin/planos", status_code=303)

@app.post("/admin/planos/excluir/{plano_id}")
@requer_autenticacao(['admin'])
async def admin_planos_excluir(request: Request, plano_id: int, usuario_logado: dict = Depends(obter_usuario_logado)):
    """Excluir plano"""
    plano_repo.excluir(plano_id)
    return RedirectResponse("/admin/planos", status_code=303)

# =================== GESTÃO DE PROFISSIONAIS ===================

@app.get("/admin/profissionais")
@requer_autenticacao(['admin'])
async def admin_profissionais_listar(request: Request, usuario_logado: dict = Depends(obter_usuario_logado)):
    """Listar todos os profissionais"""
    profissionais = profissional_repo.obter_todos_com_status()
    return templates.TemplateResponse("admin/profissionais/listar.html", {
        "request": request,
        "usuario": usuario_logado,
        "profissionais": profissionais
    })

@app.get("/admin/profissionais/pendentes")
@requer_autenticacao(['admin'])
async def admin_profissionais_pendentes(request: Request, usuario_logado: dict = Depends(obter_usuario_logado)):
    """Listar profissionais pendentes de aprovação"""
    profissionais_pendentes = profissional_repo.obter_pendentes()
    return templates.TemplateResponse("admin/profissionais/perndentes.html", {
        "request": request,
        "usuario": usuario_logado,
        "profissionais": profissionais_pendentes
    })
@app.post("/admin/profissionais/aprovar/{profissional_id}")
@requer_autenticacao(['admin'])
async def admin_profissionais_aprovar(
    request: Request,
    profissional_id: int,
    usuario_logado: dict = Depends(obter_usuario_logado)
):
    """Aprovar profissional"""
    admin_id = usuario_logado["id"]
    profissional_repo.aprovar(profissional_id, admin_id=admin_id)
    return RedirectResponse("/admin/profissionais/pendentes", status_code=303)

@app.post("/admin/profissionais/rejeitar/{profissional_id}")
@requer_autenticacao(['admin'])
async def admin_profissionais_rejeitar(request: Request, profissional_id: int, usuario_logado: dict = Depends(obter_usuario_logado)):
    """Rejeitar profissional"""
    profissional_repo.rejeitar(profissional_id)
    return RedirectResponse("/admin/profissionais/pendentes", status_code=303)

@app.post("/admin/profissionais/desativar/{profissional_id}")
@requer_autenticacao(['admin'])
async def admin_profissionais_desativar(request: Request, profissional_id: int, usuario_logado: dict = Depends(obter_usuario_logado)):
    """Desativar profissional"""
    profissional_repo.desativar(profissional_id)
    return RedirectResponse("/admin/profissionais", status_code=303)

# =================== GESTÃO DE USUÁRIOS ===================

@app.get("/admin/usuarios")
@requer_autenticacao(['admin'])
async def admin_usuarios_listar(request: Request, usuario_logado: dict = Depends(obter_usuario_logado)):
    """Listar todos os usuários"""
    usuarios = usuario_repo.obter_todos()
    return templates.TemplateResponse("admin/usuarios/listar.html", {
        "request": request,
        "usuario": usuario_logado,
        "usuarios": usuarios
    })

@app.post("/admin/usuarios/excluir/{usuario_id}")
@requer_autenticacao(['admin'])
async def admin_usuarios_excluir(request: Request, usuario_id: int, usuario_logado: dict = Depends(obter_usuario_logado)):
    """Excluir usuário"""
    # Verificar se não está tentando excluir a si mesmo
    if usuario_id == usuario_logado['id']:
        return RedirectResponse("/admin/usuarios", status_code=303)
    
    usuario_repo.excluir(usuario_id)
    return RedirectResponse("/admin/usuarios", status_code=303)


# =================== AUTENTICAÇÃO ADMIN ===================

@app.get("/login_admin")
async def login_admin_get(request: Request):
    """Exibe o formulário de login para administradores."""
    return templates.TemplateResponse("admin/login_admin.html", {"request": request})

@app.post("/login_admin")
async def login_admin_post(request: Request, email: str = Form(...), senha: str = Form(...)):
    """Processa o login de administradores."""
    usuario = usuario_repo.obter_por_email(email)

    if not usuario or usuario.perfil != "admin" or not verificar_senha(senha, usuario.senha):
        return templates.TemplateResponse(
            "admin/login_admin.html", 
            {"request": request, "erro": "Email ou senha inválidos"}
        )
    
    # Cria a sessão
    usuario_dict = {
        "id": usuario.id,
        "nome": usuario.nome,
        "email": usuario.email,
        "perfil": usuario.perfil,
        "foto": usuario.foto
    }
    criar_sessao(request, usuario_dict)
    
    # Redireciona para o painel do admin
    return RedirectResponse("/admin", status_code=303)


import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

@app.get("/recuperar_senha", response_class=HTMLResponse)
async def recuperar_senha_get(request: Request):
    return templates.TemplateResponse("/inicio/recuperar_senha.html", {"request": request})

@app.post("/recuperar_senha", response_class=HTMLResponse)
async def recuperar_senha_post(request: Request, email: str = Form(...)):
    usuario = usuario_repo.obter_por_email(email)
    if not usuario:
        return templates.TemplateResponse(
            "inicio/recuperar_senha.html",
            {"request": request, "erro": "Email não cadastrado."}
        )

    # Gerar token aleatório
    token = secrets.token_urlsafe(32)
    
    # Salvar token no banco
    usuario_repo.atualizar_token(usuario.id, token)

    # Enviar email
    usuario_repo.enviar_email_redefinicao(usuario.email, token)

    return templates.TemplateResponse(
        "inicio/recuperar_senha.html",
        {"request": request, "sucesso": "Um email com o link de redefinição foi enviado!"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)