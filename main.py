from datetime import datetime
import secrets
from typing import Optional

from fastapi import (
    FastAPI, HTTPException, Request, Form, Depends, status
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

# Seus imports
from data.repo import plano_repo, usuario_repo, cliente_repo, profissional_repo
from util.security import criar_hash_senha, verificar_senha
from util.auth_decorator import criar_sessao, obter_usuario_logado, requer_autenticacao
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
    max_age=3600,           # 1 hora de sessão
    same_site="lax",
    https_only=False
)

# =================== PÁGINAS INICIAIS ===================
@app.get("/")
async def index(request: Request):
    planos = plano_repo.obter_todos()
    
    # Separar por tipo
    planos_gratuitos = [p for p in planos if p.preco == 0.0]
    planos_pagos = [p for p in planos if p.preco > 0.0]
    
    # Destacar plano mais popular (exemplo: anual)
    plano_destaque = None
    for plano in planos_pagos:
        if plano.duracao_dias >= 365:  # Plano anual
            plano_destaque = plano
            break
    
    return templates.TemplateResponse("inicio/index.html", {
        "request": request,
        "planos": planos,
        "planos_gratuitos": planos_gratuitos, 
        "planos_pagos": planos_pagos,
        "plano_destaque": plano_destaque
    })

@app.get("/sobre")
async def sobre(request: Request):
    return templates.TemplateResponse("inicio/sobre.html", {"request": request})

# main.py - ADICIONAR ROTA
from util.email_service import EmailService

email_service = EmailService()

@app.post("/suporte")
async def enviar_suporte_post(
    request: Request,
    nome: str = Form(...),
    email: str = Form(...),
    assunto: str = Form(...),
    mensagem: str = Form(...)
):
    # Validações
    if not all([nome.strip(), email.strip(), assunto.strip(), mensagem.strip()]):
        return templates.TemplateResponse("inicio/suporte.html", {
            "request": request,
            "erro": "Todos os campos são obrigatórios."
        })
    
    # Enviar email
    sucesso = email_service.enviar_mensagem_suporte(nome, email, assunto, mensagem)
    
    if sucesso:
        return templates.TemplateResponse("inicio/suporte.html", {
            "request": request,
            "sucesso": "Mensagem enviada com sucesso! Responderemos em breve."
        })
    else:
        return templates.TemplateResponse("inicio/suporte.html", {
            "request": request,
            "erro": "Erro no envio. Tente novamente."
        })
    
@app.get("/planos")
async def planos(request: Request):
    try:
        # Buscar todos os planos ativos
        todos_planos = plano_repo.obter_todos()
        
        # Separar planos por tipo (gratuitos vs pagos)
        planos_gratuitos = [p for p in todos_planos if p.preco == 0.0]
        planos_pagos = [p for p in todos_planos if p.preco > 0.0]
        
        # Ordenar planos pagos por preço (do menor para o maior)
        planos_pagos.sort(key=lambda x: x.preco)
        
        # Ordenar planos gratuitos por duração
        planos_gratuitos.sort(key=lambda x: x.duracao_dias, reverse=True)
        
        # Estatísticas para debug (opcional - remover em produção)
        print(f"[DEBUG] Total de planos: {len(todos_planos)}")
        print(f"[DEBUG] Planos gratuitos: {len(planos_gratuitos)}")
        print(f"[DEBUG] Planos pagos: {len(planos_pagos)}")
        
        return templates.TemplateResponse("inicio/planos.html", {
            "request": request,
            "todos_planos": todos_planos,
            "planos_gratuitos": planos_gratuitos,
            "planos_pagos": planos_pagos,
            # Dados adicionais que podem ser úteis
            "total_planos": len(todos_planos),
            "tem_planos_pagos": len(planos_pagos) > 0,
            "tem_planos_gratuitos": len(planos_gratuitos) > 0
        })
    except Exception as e:
        print(f"[ERRO] Erro ao carregar planos: {str(e)}")
        # Em caso de erro, retornar template com listas vazias
        return templates.TemplateResponse("inicio/planos.html", {
            "request": request,
            "todos_planos": [],
            "planos_gratuitos": [],
            "planos_pagos": [],
            "total_planos": 0,
            "tem_planos_pagos": False,
            "tem_planos_gratuitos": False,
            "erro": "Erro ao carregar planos. Tente novamente mais tarde."
        })
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

    cliente = Cliente(usuario_id=usuario_id, plano_id=None)
    cliente_repo.inserir(cliente)

    return RedirectResponse("/login_cliente", status_code=303)

@app.get("/cadastro_profissional")
async def cadastro_profissional_get(request: Request):
    return templates.TemplateResponse("inicio/cadastro_profissional.html", {"request": request})

# main.py - MODIFICAR CADASTRO PROFISSIONAL
from fastapi import UploadFile, File
from util.file_upload import salvar_foto_registro, validar_cpf_cnpj

@app.post("/cadastro_profissional")
async def cadastro_profissional_post(
    request: Request,
    nome: str = Form(...),
    email: str = Form(...),
    senha: str = Form(...),
    especialidade: str = Form(...),
    registro_profissional: Optional[str] = Form(None),
    cpf_cnpj: str = Form(...),  # NOVO
    foto_registro: UploadFile = File(...)  # NOVO
):
    try:
        # Validação de email existente
        if usuario_repo.obter_por_email(email):
            return templates.TemplateResponse(
                "inicio/cadastro_profissional.html",
                {"request": request, "erro": "Email já cadastrado"}
            )
        
        # Validar CPF/CNPJ
        if not validar_cpf_cnpj(cpf_cnpj):
            return templates.TemplateResponse(
                "inicio/cadastro_profissional.html",
                {"request": request, "erro": "CPF/CNPJ inválido"}
            )
        
        # Salvar foto
        path_foto = await salvar_foto_registro(foto_registro)
        
        # Criar usuário
        hash_senha = criar_hash_senha(senha)
        usuario = Usuario(
            id=0, nome=nome, email=email,
            senha=hash_senha, perfil="profissional"
        )
        usuario_id = usuario_repo.inserir(usuario)
        
        # Criar profissional com novos campos
        profissional = Profissional(
            id=usuario_id,
            especialidade=especialidade,
            registro_profissional=registro_profissional,
            data_solicitacao=datetime.now(),
            status="pendente",
            cpf_cnpj=cpf_cnpj,  # NOVO
            foto_registro=path_foto  # NOVO
        )
        
        profissional_repo.inserir(profissional)
        
        return RedirectResponse("/login_profissional", status_code=303)
        
    except HTTPException as e:
        return templates.TemplateResponse(
            "inicio/cadastro_profissional.html",
            {"request": request, "erro": e.detail}
        )
    except Exception as e:
        return templates.TemplateResponse(
            "inicio/cadastro_profissional.html",
            {"request": request, "erro": f"Erro interno: {str(e)}"}
        )

# Perfil
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
async def admin_dashboard(request: Request, usuario_logado: dict = Depends(obter_usuario_logado)):
    total_usuarios = len(usuario_repo.obter_todos())
    total_clientes = len(cliente_repo.obter_todos())
    total_profissionais = len(profissional_repo.obter_todos())
    total_planos = len(plano_repo.obter_todos())

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
        "profissionais_pendentes": profissionais_pendentes[:5]
    })

# =================== GESTÃO DE PLANOS ===================
@app.get("/admin/planos")
@requer_autenticacao(['admin'])
async def admin_planos_listar(request: Request, usuario_logado: dict = Depends(obter_usuario_logado)):
    planos = plano_repo.obter_todos()
    return templates.TemplateResponse("admin/planos/listar.html", {
        "request": request,
        "usuario": usuario_logado,
        "planos": planos
    })

@app.get("/admin/planos/novo")
@requer_autenticacao(['admin'])
async def admin_planos_novo_get(request: Request, usuario_logado: dict = Depends(obter_usuario_logado)):
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
    plano = Plano(
        id=plano_id,
        nome=nome,
        descricao=descricao,
        preco=preco,
        duracao_dias=duracao_dias
    )
    plano_repo.alterar(plano)
    return RedirectResponse("/admin/planos", status_code=303)


@app.get("/admin/usuarios{id}")
async def listar_usuarios(request: Request):
    usuarios = usuario_repo.obter_por_id # Buscar do banco
    return templates.TemplateResponse("admin/usuarios.html", {"request": request, "usuarios": usuarios})

# Página de confirmação
@app.get("/admin/usuarios/excluir/{id}")
async def confirmar_exclusao_usuario(request: Request, id: int):
    usuario = ...  # Buscar usuário pelo ID
    return templates.TemplateResponse("confirmar_exclusao_usuario.html", {"request": request, "usuario": usuario})

# Exclusão real
@app.post("/admin/usuarios/excluir/{id}")
async def excluir_usuario(id: int):
    ...  # Lógica para excluir usuário
    return RedirectResponse(url="/admin/usuarios", status_code=303)




@app.post("/admin/planos/excluir/{plano_id}")
@requer_autenticacao(['admin'])
async def admin_planos_excluir(request: Request, plano_id: int, usuario_logado: dict = Depends(obter_usuario_logado)):
    plano_repo.excluir(plano_id)
    return RedirectResponse("/admin/planos", status_code=303)

# =================== GESTÃO DE PROFISSIONAIS ===================
@app.get("/admin/profissionais")
@requer_autenticacao(['admin'])
async def admin_profissionais_listar(request: Request, usuario_logado: dict = Depends(obter_usuario_logado)):
    profissionais = profissional_repo.obter_todos_com_status()
    return templates.TemplateResponse("admin/profissionais/listar.html", {
        "request": request,
        "usuario": usuario_logado,
        "profissionais": profissionais
    })

@app.get("/admin/profissionais/pendentes")
@requer_autenticacao(['admin'])
async def ver_profissionais_pendentes(request: Request, usuario_logado: dict = Depends(obter_usuario_logado)):
    profissionais = profissional_repo.obter_pendentes()
    return templates.TemplateResponse(
        "admin/profissionais/perndentes.html",
        {"request": request, "usuario": usuario_logado, "profissionais": profissionais}
    )

@app.post("/admin/profissionais/aprovar/{prof_id}")
@requer_autenticacao(['admin'])
async def aprovar_profissional(request: Request, prof_id: int, usuario_logado: dict = Depends(obter_usuario_logado)):
    admin_id = usuario_logado["id"]
    sucesso = profissional_repo.aprovar(prof_id, admin_id)
    if not sucesso:
        raise HTTPException(status_code=404, detail="Profissional não encontrado ou não aprovado")
    return RedirectResponse(url="/admin/profissionais/pendentes", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/admin/profissionais/rejeitar/{prof_id}")
@requer_autenticacao(['admin'])
async def rejeitar_profissional(request: Request, prof_id: int, usuario_logado: dict = Depends(obter_usuario_logado)):
    admin_id = usuario_logado["id"]
    sucesso = profissional_repo.rejeitar(prof_id, admin_id)
    if not sucesso:
        raise HTTPException(status_code=404, detail="Profissional não encontrado ou não rejeitado")
    return RedirectResponse(url="/admin/profissionais/pendentes", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/admin/profissionais/desativar/{profissional_id}")
@requer_autenticacao(['admin'])
async def admin_profissionais_desativar(request: Request, profissional_id: int, usuario_logado: dict = Depends(obter_usuario_logado)):
    profissional_repo.desativar(profissional_id)
    return RedirectResponse("/admin/profissionais", status_code=303)

# =================== GESTÃO DE USUÁRIOS ===================
@app.get("/admin/usuarios")
@requer_autenticacao(['admin'])
async def admin_usuarios_listar(request: Request, usuario_logado: dict = Depends(obter_usuario_logado)):
    usuarios = usuario_repo.obter_todos()
    return templates.TemplateResponse("admin/usuarios/listar.html", {
        "request": request,
        "usuario": usuario_logado,
        "usuarios": usuarios
    })

@app.post("/admin/usuarios/excluir/{usuario_id}")
@requer_autenticacao(['admin'])
async def admin_usuarios_excluir(request: Request, usuario_id: int, usuario_logado: dict = Depends(obter_usuario_logado)):
    if usuario_id == usuario_logado['id']:
        return RedirectResponse("/admin/usuarios", status_code=303)
    usuario_repo.excluir(usuario_id)
    return RedirectResponse("/admin/usuarios", status_code=303)

# =================== AUTENTICAÇÃO ADMIN ===================
@app.get("/login_admin")
async def login_admin_get(request: Request):
    return templates.TemplateResponse("admin/login_admin.html", {"request": request})

@app.post("/login_admin")
async def login_admin_post(request: Request, email: str = Form(...), senha: str = Form(...)):
    usuario = usuario_repo.obter_por_email(email)

    if not usuario or usuario.perfil != "admin" or not verificar_senha(senha, usuario.senha):
        return templates.TemplateResponse(
            "admin/login_admin.html",
            {"request": request, "erro": "Email ou senha inválidos"}
        )

    usuario_dict = {
        "id": usuario.id,
        "nome": usuario.nome,
        "email": usuario.email,
        "perfil": usuario.perfil,
        "foto": usuario.foto
    }
    criar_sessao(request, usuario_dict)
    return RedirectResponse("/admin", status_code=303)

# =================== RECUPERAÇÃO DE SENHA ===================
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

    token = secrets.token_urlsafe(32)
    usuario_repo.atualizar_token(usuario.id, token)
    usuario_repo.enviar_email_redefinicao(usuario.email, token)

    return templates.TemplateResponse(
        "inicio/recuperar_senha.html",
        {"request": request, "sucesso": "Um email com o link de redefinição foi enviado!"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
