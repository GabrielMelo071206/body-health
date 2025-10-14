from datetime import datetime
import secrets
from typing import Optional

from data.dtos import cadastro_cliente_dto
from data.dtos.cadastro_profissional_dto import CadastroProfissionalDTO
from fastapi import (
    FastAPI, File, HTTPException, Request, Form, Depends, UploadFile, status
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from starlette.middleware.sessions import SessionMiddleware

# Seus imports
from data.dtos.login_dto import LoginDTO
from data.repo import plano_repo, usuario_repo, cliente_repo, profissional_repo
from util.file_upload import salvar_foto_registro
from util.security import criar_hash_senha, verificar_senha, gerar_senha_aleatoria
from util.auth_decorator import criar_sessao, obter_usuario_logado, requer_autenticacao
from data.model.usuario_model import Usuario
from data.model.cliente_model import Cliente
from data.model.profissional_model import Profissional
from data.model.plano_model import Plano
from data.repo import (
    personal_repo, 
    personal_aluno_repo, 
    treino_personalizado_repo,
    avaliacao_fisica_repo,
    progresso_aluno_repo,
    sessao_treino_repo
)
from data.model.personal_model import Personal
from data.model.personal_aluno_model import PersonalAluno
from data.model.treino_personalizado_model import TreinoPersonalizado
from data.model.avaliacao_fisica_model import AvaliacaoFisica
from data.model.progresso_aluno_model import ProgressoAluno
# ========== IMPORTAÇÃO DO NOVO EMAIL SERVICE ==========
from util.email_service import email_service

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

@app.get("/suporte")
async def suporte_get(request: Request):
    """Página de suporte - GET"""
    # Capturar mensagens da URL (success/error redirects)
    sucesso = request.query_params.get('sucesso')
    erro = request.query_params.get('erro')
    
    return templates.TemplateResponse("inicio/suporte.html", {
        "request": request,
        "sucesso": sucesso,
        "erro": erro
    })

# ========== ROTA DE SUPORTE ATUALIZADA ==========
@app.post("/suporte")
async def enviar_suporte_post(
    request: Request,
    nome: str = Form(...),
    email: str = Form(...),
    assunto: str = Form(...),
    mensagem: str = Form(...)
):
    """Processa formulário de suporte com novo email service"""
    
    # Validações básicas
    if not all([nome.strip(), email.strip(), assunto.strip(), mensagem.strip()]):
        return RedirectResponse(
            url="/suporte?erro=Todos os campos são obrigatórios.",
            status_code=303
        )
    
    # Validação de tamanho da mensagem
    if len(mensagem.strip()) < 10:
        return RedirectResponse(
            url="/suporte?erro=A mensagem deve ter pelo menos 10 caracteres.",
            status_code=303
        )
    
    # Enviar email usando o novo serviço
    try:
        sucesso, resultado = email_service.enviar_mensagem_suporte(
            nome=nome.strip(),
            email_usuario=email.strip(),
            assunto=assunto.strip(),
            mensagem=mensagem.strip()
        )
        
        if sucesso:
            return RedirectResponse(
                url="/suporte?sucesso=" + resultado,
                status_code=303
            )
        else:
            return RedirectResponse(
                url="/suporte?erro=" + resultado,
                status_code=303
            )
            
    except Exception as e:
        print(f"[ERRO SUPORTE] {e}")
        return RedirectResponse(
            url="/suporte?erro=Erro interno do sistema. Tente novamente.",
            status_code=303
        )

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

# Substitua a rota @app.get("/pagamento") existente por esta:

@app.get("/pagamento")
async def pagamento(request: Request, plano_id: Optional[int] = None):
    """Página de pagamento com planos do banco de dados"""
    try:
        # Buscar todos os planos pagos do banco
        todos_planos = plano_repo.obter_todos()
        planos_pagos = [p for p in todos_planos if p.preco > 0.0]
        
        # Ordenar por preço
        planos_pagos.sort(key=lambda x: x.preco)
        
        # Se foi passado um plano_id específico, selecionar ele
        plano_selecionado = None
        if plano_id:
            plano_selecionado = plano_repo.obter_por_id(plano_id)
        
        # Se não tem plano selecionado, pegar o primeiro da lista
        if not plano_selecionado and planos_pagos:
            plano_selecionado = planos_pagos[0]
        
        return templates.TemplateResponse("inicio/pagamento.html", {
            "request": request,
            "planos_pagos": planos_pagos,
            "plano_selecionado": plano_selecionado,
            "tem_planos": len(planos_pagos) > 0
        })
        
    except Exception as e:
        print(f"[ERRO] Erro ao carregar página de pagamento: {str(e)}")
        return templates.TemplateResponse("inicio/pagamento.html", {
            "request": request,
            "planos_pagos": [],
            "plano_selecionado": None,
            "tem_planos": False,
            "erro": "Erro ao carregar planos. Tente novamente mais tarde."
        })

# =================== AUTENTICAÇÃO ===================
@app.get("/login")
async def login_get(request: Request):
    return templates.TemplateResponse("inicio/login.html", {"request": request})

# =================== CADASTRO E LOGIN - REFATORADO ===================
# Substitua as rotas correspondentes no seu main.py

from data.dtos.cadastro_cliente_dto import validar_cadastro_cliente
from data.dtos.cadastro_profissional_dto import (
    validar_cadastro_profissional, 
    validar_foto_registro
)
from data.dtos.login_dto import validar_login

# =================== LOGIN CLIENTE ===================
@app.get("/login_cliente")
async def login_cliente_get(request: Request):
    return templates.TemplateResponse("inicio/login_cliente.html", {
        "request": request
    })


@app.post("/login_cliente")
async def login_cliente_post(
    request: Request, 
    email: str = Form(...), 
    senha: str = Form(...)
):
    """Login de cliente com validação completa"""
    
    # Preservar dados do formulário
    dados_formulario = {"email": email}
    
    # Validar dados com DTO
    dto, erros = validar_login({"email": email, "senha": senha})
    
    if erros:
        return templates.TemplateResponse("inicio/login_cliente.html", {
            "request": request,
            "erros": erros,
            "dados": dados_formulario
        })
    
    # Buscar usuário
    usuario = usuario_repo.obter_por_email(dto.email)
    
    if not usuario or usuario.perfil != "cliente":
        return templates.TemplateResponse("inicio/login_cliente.html", {
            "request": request,
            "erro": "Email ou senha inválidos.",
            "dados": dados_formulario
        })
    
    # Verificar senha
    if not verificar_senha(dto.senha, usuario.senha):
        return templates.TemplateResponse("inicio/login_cliente.html", {
            "request": request,
            "erro": "Email ou senha inválidos.",
            "dados": dados_formulario
        })
    
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


# =================== LOGIN PROFISSIONAL ===================
@app.get("/login_profissional")
async def login_profissional_get(request: Request):
    return templates.TemplateResponse("inicio/login_profissional.html", {
        "request": request
    })


@app.post("/login_profissional")
async def login_profissional_post(
    request: Request, 
    email: str = Form(...), 
    senha: str = Form(...)
):
    """Login de profissional com validação completa"""
    
    dados_formulario = {"email": email}
    
    # Validar dados
    dto, erros = validar_login({"email": email, "senha": senha})
    
    if erros:
        return templates.TemplateResponse("inicio/login_profissional.html", {
            "request": request,
            "erros": erros,
            "dados": dados_formulario
        })
    
    # Buscar usuário
    usuario = usuario_repo.obter_por_email(dto.email)
    
    if not usuario or usuario.perfil != "profissional":
        return templates.TemplateResponse("inicio/login_profissional.html", {
            "request": request,
            "erro": "Email ou senha inválidos.",
            "dados": dados_formulario
        })
    
    # Verificar senha
    if not verificar_senha(dto.senha, usuario.senha):
        return templates.TemplateResponse("inicio/login_profissional.html", {
            "request": request,
            "erro": "Email ou senha inválidos.",
            "dados": dados_formulario
        })
    
    # Criar sessão
    usuario_dict = {
        "id": usuario.id,
        "nome": usuario.nome,
        "email": usuario.email,
        "perfil": usuario.perfil,
        "foto": usuario.foto
    }
    criar_sessao(request, usuario_dict)
    
    return RedirectResponse("/personal/dashboard", status_code=303)


# =================== CADASTRO CLIENTE ===================
@app.get("/cadastro_cliente")
async def cadastro_cliente_get(request: Request):
    return templates.TemplateResponse("inicio/cadastro_cliente.html", {
        "request": request
    })

@app.post("/cadastro_cliente")
async def cadastro_cliente_post(
    request: Request,
    nome: str = Form(...),
    email: str = Form(...),
    senha: str = Form(...),
    senha_confirm: str = Form(...)
):
    """Cadastro de cliente com validação completa de todos os campos"""
    
    # Preservar dados do formulário
    dados_formulario = {
        "nome": nome,
        "email": email
    }
    
    # Montar dados para validação
    data = {
        "nome": nome,
        "email": email,
        "senha": senha,
        "senha_confirm": senha_confirm
    }
    
    # PASSO 1: Validar TODOS os campos primeiro
    dto, erros = validar_cadastro_cliente(data)
    
    # PASSO 2: Se houver erros de validação, adicionar verificação de email duplicado
    if not erros:
        erros = {}
    
    # Verificar se email já existe (ADICIONAR ao dicionário de erros existente)
    if usuario_repo.obter_por_email(email.strip().lower()):
        erros['email'] = 'Este email já está cadastrado. Faça login ou use outro email.'
    
    # Se houver QUALQUER erro (validação OU email duplicado), exibir TODOS
    if erros:
        return templates.TemplateResponse("inicio/cadastro_cliente.html", {
            "request": request,
            "erros": erros,
            "dados": dados_formulario
        })
    
    # Criar usuário (só chega aqui se NÃO houver erros)
    try:
        hash_senha = criar_hash_senha(dto.senha)
        usuario = Usuario(
            id=0,
            nome=dto.nome,
            email=dto.email,
            senha=hash_senha,
            perfil="cliente"
        )
        usuario_id = usuario_repo.inserir(usuario)
        
        # Criar registro de cliente
        cliente = Cliente(usuario_id=usuario_id)
        cliente_repo.inserir(cliente)
        
        return RedirectResponse("/login_cliente?sucesso=Cadastro realizado com sucesso!", status_code=303)
        
    except Exception as e:
        print(f"[ERRO] Cadastro cliente: {str(e)}")
        return templates.TemplateResponse("inicio/cadastro_cliente.html", {
            "request": request,
            "erro": "Erro ao realizar cadastro. Tente novamente.",
            "dados": dados_formulario
        })


# =================== CADASTRO PROFISSIONAL ===================
@app.get("/cadastro_profissional")
async def cadastro_profissional_get(request: Request):
    return templates.TemplateResponse("inicio/cadastro_profissional.html", {
        "request": request
    })


@app.post("/cadastro_profissional")
async def cadastro_profissional_post(
    request: Request,
    nome: str = Form(...),
    email: str = Form(...),
    senha: str = Form(...),
    senha_confirm: str = Form(...),
    especialidade: str = Form(...),
    registro_profissional: Optional[str] = Form(None),
    cpf_cnpj: str = Form(...),
    foto_registro: UploadFile = File(...)
):
    """Cadastro de profissional com validação completa de todos os campos"""
    
    # Preservar dados do formulário
    dados_formulario = {
        "nome": nome,
        "email": email,
        "especialidade": especialidade,
        "registro_profissional": registro_profissional,
        "cpf_cnpj": cpf_cnpj
    }
    
    # Montar dados para validação (sem foto)
    data = {
        "nome": nome,
        "email": email,
        "senha": senha,
        "senha_confirm": senha_confirm,
        "especialidade": especialidade,
        "registro_profissional": registro_profissional,
        "cpf_cnpj": cpf_cnpj
    }
    
    # PASSO 1: Validar TODOS os campos de texto primeiro
    dto, erros = validar_cadastro_profissional(data)
    
    # Inicializar dicionário de erros se não existir
    if not erros:
        erros = {}
    
    # PASSO 2: Validar foto (ADICIONAR ao dicionário existente)
    foto_valida, erro_foto = validar_foto_registro(foto_registro)
    if not foto_valida:
        erros['foto_registro'] = erro_foto
    
    # PASSO 3: Verificar email duplicado (ADICIONAR ao dicionário existente)
    if usuario_repo.obter_por_email(email.strip().lower()):
        erros['email'] = 'Este email já está cadastrado. Faça login ou use outro email.'
    
    # Se houver QUALQUER erro, exibir TODOS
    if erros:
        return templates.TemplateResponse("inicio/cadastro_profissional.html", {
            "request": request,
            "erros": erros,
            "dados": dados_formulario
        })
    
    # Criar usuário e profissional (só chega aqui se NÃO houver erros)
    try:
        # Salvar foto do registro
        path_foto = await salvar_foto_registro(foto_registro)
        
        # Criar usuário
        hash_senha = criar_hash_senha(dto.senha)
        usuario = Usuario(
            id=0,
            nome=dto.nome,
            email=dto.email,
            senha=hash_senha,
            perfil="profissional"
        )
        usuario_id = usuario_repo.inserir(usuario)
        
        # Criar profissional
        profissional = Profissional(
            id=usuario_id,
            especialidade=dto.especialidade,
            registro_profissional=dto.registro_profissional,
            data_solicitacao=datetime.now(),
            status="pendente",
            cpf_cnpj=dto.cpf_cnpj,
            foto_registro=path_foto
        )
        profissional_repo.inserir(profissional)
        
        return RedirectResponse(
            "/login_profissional?sucesso=Cadastro enviado! Aguarde análise da equipe.",
            status_code=303
        )
        
    except Exception as e:
        print(f"[ERRO] Cadastro profissional: {str(e)}")
        return templates.TemplateResponse("inicio/cadastro_profissional.html", {
            "request": request,
            "erro": "Erro ao realizar cadastro. Tente novamente.",
            "dados": dados_formulario
        })


# =================== LOGIN ADMIN ===================
@app.get("/login_admin")
async def login_admin_get(request: Request):
    return templates.TemplateResponse("admin/login_admin.html", {
        "request": request
    })


@app.post("/login_admin")
async def login_admin_post(
    request: Request,
    email: str = Form(...),
    senha: str = Form(...)
):
    """Login de admin com validação completa"""
    
    dados_formulario = {"email": email}
    
    # Validar dados
    dto, erros = validar_login({"email": email, "senha": senha})
    
    if erros:
        return templates.TemplateResponse("admin/login_admin.html", {
            "request": request,
            "erros": erros,
            "dados": dados_formulario
        })
    
    # Buscar usuário
    usuario = usuario_repo.obter_por_email(dto.email)
    
    if not usuario or usuario.perfil != "admin":
        return templates.TemplateResponse("admin/login_admin.html", {
            "request": request,
            "erro": "Email ou senha inválidos.",
            "dados": dados_formulario
        })
    
    # Verificar senha
    if not verificar_senha(dto.senha, usuario.senha):
        return templates.TemplateResponse("admin/login_admin.html", {
            "request": request,
            "erro": "Email ou senha inválidos.",
            "dados": dados_formulario
        })
    
    # Criar sessão
    usuario_dict = {
        "id": usuario.id,
        "nome": usuario.nome,
        "email": usuario.email,
        "perfil": usuario.perfil,
        "foto": usuario.foto
    }
    criar_sessao(request, usuario_dict)
    
    return RedirectResponse("/admin", status_code=303)

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)


# =================== CADASTROS ===================

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

# ========== ROTA ADMIN PARA TESTAR EMAIL ==========
@app.get("/admin/test-email")
@requer_autenticacao(['admin'])
async def test_email_admin(request: Request, usuario_logado: dict = Depends(obter_usuario_logado)):
    """Rota admin para testar configuração de email"""
    
    try:
        # Testar conexão
        if email_service.testar_conexao():
            resultado = {
                "status": "✅ Sucesso",
                "mensagem": "Conexão SMTP estabelecida com sucesso!",
                "servidor": email_service.smtp_server,
                "porta": email_service.smtp_port,
                "email": email_service.email
            }
        else:
            resultado = {
                "status": "❌ Erro", 
                "mensagem": "Falha na conexão SMTP",
                "servidor": email_service.smtp_server,
                "porta": email_service.smtp_port,
                "email": email_service.email
            }
        
        # Retornar template HTML em vez de JSON
        return templates.TemplateResponse("admin/test_email.html", {
            "request": request,
            "usuario": usuario_logado,
            "resultado": resultado
        })
        
    except Exception as e:
        resultado = {
            "status": "❌ Erro Crítico",
            "mensagem": f"Erro inesperado: {str(e)}",
            "servidor": "N/A",
            "porta": "N/A",
            "email": "N/A"
        }
        
        return templates.TemplateResponse("admin/test_email.html", {
            "request": request,
            "usuario": usuario_logado,
            "resultado": resultado
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
async def admin_planos_editar_post(
    request: Request,
    plano_id: int,
    nome: str = Form(...),
    preco: float = Form(...),
    descricao: str = Form(...),
    duracao_dias: int = Form(...)
):
    plano = plano_repo.obter_por_id(plano_id)
    if not plano:
        return RedirectResponse("/admin/planos?erro=Plano não encontrado", status_code=303)

    plano.nome = nome
    plano.descricao = descricao
    plano.preco = preco
    plano.duracao_dias = duracao_dias

    success = plano_repo.alterar(plano)

    if success:
        return RedirectResponse("/admin/planos?sucesso=Plano atualizado com sucesso", status_code=303)
    else:
        return RedirectResponse("/admin/planos?erro=Erro ao atualizar plano", status_code=303)




# Página de confirmação
@app.get("/admin/usuarios/excluir/{usuario_id}")
async def confirmar_exclusao_usuario(request: Request, usuario_id: int):
    usuario = ...  # Buscar usuário pelo ID
    return templates.TemplateResponse("confirmar_exclusao_usuario.html", {"request": request, "usuario": usuario})
# Exclusão real
@app.post("/admin/usuarios/excluir/{usuario_id}")
@requer_autenticacao(['admin'])
async def admin_usuarios_excluir(request: Request, usuario_id: int, usuario_logado: dict = Depends(obter_usuario_logado)):
    # Não permitir que admin exclua a si mesmo
    if usuario_id == usuario_logado['id']:
        return RedirectResponse("/admin/usuarios?erro=Não é possível excluir seu próprio usuário", status_code=303)
    
    try:
        # Verificar se usuário existe
        usuario = usuario_repo.obter_por_id(usuario_id)
        if not usuario:
            return RedirectResponse("/admin/usuarios?erro=Usuário não encontrado", status_code=303)
        
        # Tentar excluir registros relacionados, mas continuar mesmo se falhar
        try:
            if usuario.perfil == "cliente":
                cliente_repo.excluir(usuario_id)
            elif usuario.perfil == "profissional":
                profissional_repo.excluir(usuario_id)
        except Exception as e:
            print(f"[AVISO] Não foi possível excluir registros relacionados do usuário {usuario_id}: {str(e)}")
        
        # Excluir usuário (sempre tenta)
        usuario_repo.excluir(usuario_id)
        
        return RedirectResponse("/admin/usuarios?sucesso=Usuário excluído com sucesso", status_code=303)
            
    except Exception as e:
        print(f"[ERRO] Erro ao excluir usuário {usuario_id}: {str(e)}")
        return RedirectResponse("/admin/usuarios?erro=Erro interno ao excluir usuário", status_code=303)


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
# ====================================================

@app.post("/admin/planos/excluir/{plano_id}")
@requer_autenticacao(['admin'])
async def admin_planos_excluir(request: Request, plano_id: int, usuario_logado: dict = Depends(obter_usuario_logado)):
    try:
        plano = plano_repo.obter_por_id(plano_id)
        if not plano:
            return RedirectResponse("/admin/planos?erro=Plano não encontrado", status_code=303)

        plano_repo.excluir(plano_id)
        return RedirectResponse("/admin/planos?sucesso=Plano excluído com sucesso", status_code=303)

    except Exception as e:
        print(f"[ERRO] Erro ao excluir plano {plano_id}: {str(e)}")
        return RedirectResponse("/admin/planos?erro=Erro interno ao excluir plano", status_code=303)



# ========== RECUPERAÇÃO DE SENHA ATUALIZADA ==========
@app.get("/recuperar_senha", response_class=HTMLResponse)
async def recuperar_senha_get(request: Request):
    """Página de recuperação de senha - GET"""
    # Capturar mensagens da URL (success/error redirects)
    mensagem = request.query_params.get('mensagem')
    erro = request.query_params.get('erro')
    
    return templates.TemplateResponse("inicio/recuperar_senha.html", {
        "request": request,
        "mensagem": mensagem,
        "erro": erro
    })

@app.post("/recuperar_senha", response_class=HTMLResponse)
async def recuperar_senha_post(request: Request, email: str = Form(...)):
    """Processa recuperação de senha com novo email service"""
    
    # Buscar usuário pelo email
    usuario = usuario_repo.obter_por_email(email.strip().lower())
    
    if not usuario:
        return RedirectResponse(
            url="/recuperar_senha?erro=Email não encontrado no sistema.",
            status_code=303
        )

    try:
        # Gerar nova senha temporária
        nova_senha = gerar_senha_aleatoria(8)
        
        # Atualizar no banco de dados
        usuario.senha = criar_hash_senha(nova_senha)
        usuario_repo.alterar(usuario)
        
        # Enviar por email usando o novo serviço
        sucesso, mensagem = email_service.enviar_recuperacao_senha(
            email_usuario=usuario.email,
            nome=usuario.nome,
            nova_senha=nova_senha
        )
        
        if sucesso:
            return RedirectResponse(
                url="/recuperar_senha?mensagem=Nova senha enviada para seu email! Verifique sua caixa de entrada.",
                status_code=303
            )
        else:
            return RedirectResponse(
                url="/recuperar_senha?erro=Erro ao enviar email. Tente novamente mais tarde.",
                status_code=303
            )
            
    except Exception as e:
        print(f"[ERRO RECUPERAÇÃO] {e}")
        return RedirectResponse(
            url="/recuperar_senha?erro=Erro interno do sistema. Tente novamente.",
            status_code=303
        )

# ========== ROTA DE TESTE RÁPIDO (DESENVOLVIMENTO) ==========
@app.get("/test-email-quick")
async def test_email_quick():
    """Teste rápido do email service - apenas para desenvolvimento"""
    try:
        # Teste de conexão
        if email_service.testar_conexao():
            return {"status": "✅ Conexão OK", "service": "Body Health Email"}
        else:
            return {"status": "❌ Conexão FALHOU", "service": "Body Health Email"}
    except Exception as e:
        return {"status": f"❌ ERRO: {str(e)}", "service": "Body Health Email"}

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

@app.get("/admin/usuarios/novo")
@requer_autenticacao(['admin'])
async def admin_usuarios_novo_get(request: Request, usuario_logado: dict = Depends(obter_usuario_logado)):
    return templates.TemplateResponse("admin/usuarios/form.html", {
        "request": request,
        "usuario": usuario_logado,
        "titulo": "Criar Novo Usuário",
        "acao": "/admin/usuarios/novo"
    })

@app.post("/admin/usuarios/novo")
@requer_autenticacao(['admin'])
async def admin_usuarios_novo_post(
    request: Request,
    nome: str = Form(...),
    email: str = Form(...),
    senha: str = Form(...),
    perfil: str = Form(...),
    usuario_logado: dict = Depends(obter_usuario_logado)
):
    # Verificar se email já existe
    if usuario_repo.obter_por_email(email):
        return templates.TemplateResponse("admin/usuarios/form.html", {
            "request": request,
            "usuario": usuario_logado,
            "titulo": "Criar Novo Usuário",
            "acao": "/admin/usuarios/novo",
            "erro": "Email já cadastrado"
        })
    
    # Criar hash da senha
    hash_senha = criar_hash_senha(senha)
    
    # Criar usuário
    usuario = Usuario(
        id=0,
        nome=nome,
        email=email,
        senha=hash_senha,
        perfil=perfil
    )
    
    usuario_id = usuario_repo.inserir(usuario)
    
    # Se for cliente, criar registro na tabela cliente
    if perfil == "cliente":
        cliente = Cliente(usuario_id=usuario_id, id=None)
        cliente_repo.inserir(cliente)
    
    return RedirectResponse("/admin/usuarios", status_code=303)

@app.get("/admin/usuarios/editar/{usuario_id}")
@requer_autenticacao(['admin'])
async def admin_usuarios_editar_get(request: Request, usuario_id: int, usuario_logado: dict = Depends(obter_usuario_logado)):
    usuario = usuario_repo.obter_por_id(usuario_id)
    if not usuario:
        return RedirectResponse("/admin/usuarios", status_code=303)
    
    return templates.TemplateResponse("admin/usuarios/form.html", {
        "request": request,
        "usuario": usuario_logado,
        "usuario_edicao": usuario,
        "titulo": "Editar Usuário",
        "acao": f"/admin/usuarios/editar/{usuario_id}"
    })

@app.post("/admin/usuarios/editar/{usuario_id}")
@requer_autenticacao(['admin'])
async def admin_usuarios_editar_post(
    request: Request,
    usuario_id: int,
    nome: str = Form(...),
    email: str = Form(...),
    senha: str = Form(None),
    perfil: str = Form(...),
    usuario_logado: dict = Depends(obter_usuario_logado)
):
    usuario = usuario_repo.obter_por_id(usuario_id)
    if not usuario:
        return RedirectResponse("/admin/usuarios", status_code=303)
    
    # Verificar se email já existe (exceto para o próprio usuário)
    usuario_email_existente = usuario_repo.obter_por_email(email)
    if usuario_email_existente and usuario_email_existente.id != usuario_id:
        return templates.TemplateResponse("admin/usuarios/form.html", {
            "request": request,
            "usuario": usuario_logado,
            "usuario_edicao": usuario,
            "titulo": "Editar Usuário",
            "acao": f"/admin/usuarios/editar/{usuario_id}",
            "erro": "Email já cadastrado por outro usuário"
        })
    
    # Atualizar dados
    usuario.nome = nome
    usuario.email = email
    usuario.perfil = perfil
    
    # Só atualizar senha se foi informada
    if senha and senha.strip():
        usuario.senha = criar_hash_senha(senha)
    
    usuario_repo.alterar(usuario)
    
    return RedirectResponse("/admin/usuarios", status_code=303)

@app.post("/admin/usuarios/excluir/{usuario_id}")
@requer_autenticacao(['admin'])
async def admin_usuarios_excluir(request: Request, usuario_id: int, usuario_logado: dict = Depends(obter_usuario_logado)):
    # Não permitir que admin exclua a si mesmo
    if usuario_id == usuario_logado['id']:
        return RedirectResponse("/admin/usuarios?erro=Não é possível excluir seu próprio usuário", status_code=303)
    
    try:
        # Verificar se usuário existe
        usuario = usuario_repo.obter_por_id(usuario_id)
        if not usuario:
            return RedirectResponse("/admin/usuarios?erro=Usuário não encontrado", status_code=303)
        
        # Excluir registros relacionados primeiro
        if usuario.perfil == "cliente":
            cliente_repo.excluir(usuario_id)
        elif usuario.perfil == "profissional":
            profissional_repo.excluir(usuario_id)
        
        # Excluir usuário
        success = usuario_repo.excluir(usuario_id)
        
        if success:
            return RedirectResponse("/admin/usuarios?sucesso=Usuário excluído com sucesso", status_code=303)
        else:
            return RedirectResponse("/admin/usuarios?erro=Erro ao excluir usuário", status_code=303)
            
    except Exception as e:
        print(f"[ERRO] Erro ao excluir usuário {usuario_id}: {str(e)}")
        return RedirectResponse("/admin/usuarios?erro=Erro interno ao excluir usuário", status_code=303)
    
# =================== DASHBOARD PERSONAL ===================
@app.get("/personal/dashboard")
@requer_autenticacao(['profissional'])
async def personal_dashboard(request: Request, usuario_logado: dict = Depends(obter_usuario_logado)):
    """Dashboard do Personal Trainer com tratamento completo de erros"""
    
    # Contexto base padrão (sempre funciona mesmo com erros)
    contexto_base = {
        "request": request,
        "usuario": usuario_logado,
        "total_alunos": 0,
        "alunos_ativos": 0,
        "total_treinos": 0,
        "total_avaliacoes": 0,
        "atividades": [],
        "lembretes": [],
        "avaliacoes_media": None
    }
    
    try:
        # Buscar profissional
        profissional = profissional_repo.obter_por_id(usuario_logado['id'])
        if not profissional:
            print(f"[AVISO] Profissional não encontrado para usuário {usuario_logado['id']}")
            return templates.TemplateResponse("personal/dashboard.html", contexto_base)
        
        # Buscar personal (pode não existir ainda)
        personal = personal_repo.obter_por_profissional(profissional.id)
        
        if not personal:
            print(f"[AVISO] Personal não encontrado para profissional {profissional.id}")
            return templates.TemplateResponse("personal/dashboard.html", contexto_base)
        
        # Estatísticas
        alunos = personal_aluno_repo.obter_alunos_por_personal(personal.id)
        total_alunos = len(alunos)
        alunos_ativos = len([a for a in alunos if a.status == 'ativo'])
        
        # Contar treinos
        total_treinos = 0
        for aluno in alunos:
            try:
                treinos = treino_personalizado_repo.obter_por_aluno(aluno.id)
                total_treinos += len(treinos)
            except Exception as e:
                print(f"[ERRO] Erro ao contar treinos do aluno {aluno.id}: {e}")
        
        # Contar avaliações
        total_avaliacoes = 0
        for aluno in alunos:
            try:
                avaliacoes = avaliacao_fisica_repo.obter_por_aluno(aluno.id)
                total_avaliacoes += len(avaliacoes)
            except Exception as e:
                print(f"[ERRO] Erro ao contar avaliações do aluno {aluno.id}: {e}")
        
        # Contexto com dados reais
        contexto_sucesso = {
            "request": request,
            "usuario": usuario_logado,
            "total_alunos": total_alunos,
            "alunos_ativos": alunos_ativos,
            "total_treinos": total_treinos,
            "total_avaliacoes": total_avaliacoes,
            "atividades": [],
            "lembretes": [],
            "avaliacoes_media": personal.avaliacoes_media if hasattr(personal, 'avaliacoes_media') else None
        }
        
        return templates.TemplateResponse("personal/dashboard.html", contexto_sucesso)
        
    except Exception as e:
        print(f"[ERRO] Dashboard Personal: {str(e)}")
        import traceback
        traceback.print_exc()
        return templates.TemplateResponse("personal/dashboard.html", contexto_base)
# =================== GESTÃO DE ALUNOS ===================
@app.get("/personal/alunos")
@requer_autenticacao(['profissional'])
async def personal_alunos_listar(request: Request, usuario_logado: dict = Depends(obter_usuario_logado)):
    """Lista alunos do personal com validação de propriedade"""
    try:
        # Buscar personal do profissional logado
        profissional = profissional_repo.obter_por_id(usuario_logado['id'])
        if not profissional:
            return templates.TemplateResponse("personal/alunos/listar.html", {
                "request": request,
                "usuario": usuario_logado,
                "alunos": [],
                "erro": "Dados de profissional não encontrados"
            })
        
        personal = personal_repo.obter_por_profissional(profissional.id)
        if not personal:
            return templates.TemplateResponse("personal/alunos/listar.html", {
                "request": request,
                "usuario": usuario_logado,
                "alunos": [],
                "aviso": "Cadastro de Personal não encontrado. Entre em contato com o suporte."
            })
        
        # Buscar alunos do personal
        alunos_relacionamento = personal_aluno_repo.obter_alunos_por_personal(personal.id)
        
        # Enriquecer com dados do usuário
        alunos = []
        for rel in alunos_relacionamento:
            try:
                cliente = cliente_repo.obter_por_id(rel.aluno_id)
                if not cliente:
                    continue
                    
                usuario_aluno = usuario_repo.obter_por_id(cliente.usuario_id)
                if not usuario_aluno:
                    continue
                
                # CORREÇÃO: Converter data_inicio para datetime se vier como string
                data_inicio_convertida = rel.data_inicio
                if isinstance(rel.data_inicio, str):
                    try:
                        # Tentar formato ISO (YYYY-MM-DD HH:MM:SS ou YYYY-MM-DD)
                        data_inicio_convertida = datetime.fromisoformat(rel.data_inicio.split('.')[0])
                    except (ValueError, AttributeError):
                        try:
                            # Tentar formato brasileiro (DD/MM/YYYY)
                            data_inicio_convertida = datetime.strptime(rel.data_inicio, '%d/%m/%Y')
                        except ValueError:
                            data_inicio_convertida = None
                
                alunos.append({
                    'id': rel.id,
                    'aluno_id': rel.aluno_id,
                    'nome': usuario_aluno.nome,
                    'email': usuario_aluno.email,
                    'objetivo': rel.objetivo,
                    'data_inicio': data_inicio_convertida,  # Agora é datetime ou None
                    'status': rel.status,
                    'observacoes': rel.observacoes
                })
            except Exception as e:
                print(f"[ERRO] Erro ao processar aluno {rel.aluno_id}: {e}")
                continue
        
        return templates.TemplateResponse("personal/alunos/listar.html", {
            "request": request,
            "usuario": usuario_logado,
            "alunos": alunos
        })
        
    except Exception as e:
        print(f"[ERRO] Listar alunos: {str(e)}")
        import traceback
        traceback.print_exc()
        return templates.TemplateResponse("personal/alunos/listar.html", {
            "request": request,
            "usuario": usuario_logado,
            "alunos": [],
            "erro": "Erro ao carregar lista de alunos"
        })


@app.get("/personal/alunos/novo")
@requer_autenticacao(['profissional'])
async def personal_alunos_novo_get(request: Request, usuario_logado: dict = Depends(obter_usuario_logado)):
    # Buscar lista de clientes disponíveis para vincular
    clientes = cliente_repo.obter_todos()
    clientes_disponiveis = []
    
    for cliente in clientes:
        usuario = usuario_repo.obter_por_id(cliente.usuario_id)
        if usuario:
            clientes_disponiveis.append({
                'id': cliente.usuario_id,
                'nome': usuario.nome,
                'email': usuario.email
            })
    
    return templates.TemplateResponse("personal/alunos/form.html", {
        "request": request,
        "usuario": usuario_logado,
        "aluno": None,
        "clientes_disponiveis": clientes_disponiveis
    })
    

@app.post("/personal/alunos/salvar")
@requer_autenticacao(['profissional'])
async def personal_alunos_salvar(
    request: Request,
    aluno_id: Optional[int] = Form(None),
    cliente_id: Optional[int] = Form(None),  # CORREÇÃO: Agora é opcional
    data_inicio: str = Form(...),
    status: str = Form(...),
    objetivo: Optional[str] = Form(None),
    observacoes: Optional[str] = Form(None),
    usuario_logado: dict = Depends(obter_usuario_logado)
):
    """Salvar aluno com validação completa"""
    try:
        # Buscar ou criar personal do profissional
        profissional = profissional_repo.obter_por_id(usuario_logado['id'])
        if not profissional:
            return RedirectResponse("/personal/alunos?erro=Profissional não encontrado", status_code=303)
        
        personal = personal_repo.obter_por_profissional(profissional.id)
        
        if not personal:
            # Criar novo personal automaticamente
            try:
                personal = Personal(
                    id=0,
                    profissional_id=profissional.id,
                    total_alunos=0
                )
                personal_id = personal_repo.inserir(personal)
                personal.id = personal_id
            except Exception as e:
                print(f"[ERRO] Erro ao criar personal: {e}")
                return RedirectResponse("/personal/alunos?erro=Erro ao criar registro de Personal", status_code=303)
        
        # Validar data
        try:
            data_inicio_dt = datetime.strptime(data_inicio, '%Y-%m-%d')
        except ValueError:
            return RedirectResponse("/personal/alunos?erro=Data inválida", status_code=303)
        
        if aluno_id:
            # EDIÇÃO: Atualizar aluno existente (validar propriedade)
            aluno = personal_aluno_repo.obter_por_id(aluno_id)
            if not aluno or aluno.personal_id != personal.id:
                return RedirectResponse("/personal/alunos?erro=Aluno não encontrado ou acesso negado", status_code=303)
            
            aluno.data_inicio = data_inicio_dt
            aluno.status = status
            aluno.objetivo = objetivo
            aluno.observacoes = observacoes
            personal_aluno_repo.alterar(aluno)
            
            return RedirectResponse("/personal/alunos?sucesso=Aluno atualizado com sucesso", status_code=303)
        else:
            # NOVO: Criar novo relacionamento
            # Validar que cliente_id foi fornecido
            if not cliente_id:
                return RedirectResponse("/personal/alunos?erro=Cliente não selecionado", status_code=303)
            
            # Verificar se cliente já é aluno deste personal
            alunos_existentes = personal_aluno_repo.obter_alunos_por_personal(personal.id)
            for aluno_ex in alunos_existentes:
                if aluno_ex.aluno_id == cliente_id:
                    return RedirectResponse("/personal/alunos?erro=Este cliente já é seu aluno", status_code=303)
            
            # Criar novo relacionamento
            novo_aluno = PersonalAluno(
                id=0,
                personal_id=personal.id,
                aluno_id=cliente_id,
                data_inicio=data_inicio_dt,
                status=status,
                objetivo=objetivo,
                observacoes=observacoes
            )
            personal_aluno_repo.inserir(novo_aluno)
            
            # Atualizar contador
            personal.total_alunos += 1
            personal_repo.alterar(personal)
            
            return RedirectResponse("/personal/alunos?sucesso=Aluno adicionado com sucesso", status_code=303)
            
    except Exception as e:
        print(f"[ERRO] Salvar aluno: {str(e)}")
        import traceback
        traceback.print_exc()
        return RedirectResponse("/personal/alunos?erro=Erro ao salvar aluno", status_code=303)
    
@app.get("/personal/alunos/{aluno_id}")
@requer_autenticacao(['profissional'])
async def personal_alunos_detalhes(
    request: Request, 
    aluno_id: int, 
    usuario_logado: dict = Depends(obter_usuario_logado)
):
    """Detalhes do aluno com validação de propriedade"""
    try:
        # Validar se o aluno pertence ao personal logado
        profissional = profissional_repo.obter_por_id(usuario_logado['id'])
        if not profissional:
            return RedirectResponse("/personal/alunos?erro=Acesso negado", status_code=303)
        
        personal = personal_repo.obter_por_profissional(profissional.id)
        if not personal:
            return RedirectResponse("/personal/alunos?erro=Acesso negado", status_code=303)
        
        # Buscar relacionamento e validar propriedade
        aluno_rel = personal_aluno_repo.obter_por_id(aluno_id)
        if not aluno_rel or aluno_rel.personal_id != personal.id:
            return RedirectResponse("/personal/alunos?erro=Aluno não encontrado ou acesso negado", status_code=303)
        
        # Buscar dados do cliente/usuário
        cliente = cliente_repo.obter_por_id(aluno_rel.aluno_id)
        if not cliente:
            return RedirectResponse("/personal/alunos?erro=Dados do aluno não encontrados", status_code=303)
        
        usuario_aluno = usuario_repo.obter_por_id(cliente.usuario_id)
        if not usuario_aluno:
            return RedirectResponse("/personal/alunos?erro=Dados do aluno não encontrados", status_code=303)
        
        # CORREÇÃO: Converter data_inicio para datetime se vier como string
        data_inicio_convertida = aluno_rel.data_inicio
        if isinstance(aluno_rel.data_inicio, str):
            try:
                data_inicio_convertida = datetime.fromisoformat(aluno_rel.data_inicio.split('.')[0])
            except (ValueError, AttributeError):
                try:
                    data_inicio_convertida = datetime.strptime(aluno_rel.data_inicio, '%d/%m/%Y')
                except ValueError:
                    data_inicio_convertida = None
        
        # Montar objeto aluno
        aluno = {
            'id': aluno_rel.id,
            'aluno_id': aluno_rel.aluno_id,
            'nome': usuario_aluno.nome,
            'email': usuario_aluno.email,
            'objetivo': aluno_rel.objetivo,
            'data_inicio': data_inicio_convertida,  # Agora é datetime ou None
            'status': aluno_rel.status,
            'observacoes': aluno_rel.observacoes
        }
        
        # Buscar treinos ativos
        treinos_ativos = []
        try:
            treinos_ativos = treino_personalizado_repo.obter_por_aluno(aluno_id)
        except Exception as e:
            print(f"[ERRO] Erro ao buscar treinos: {e}")
        
        # Buscar avaliações
        avaliacoes = []
        ultima_avaliacao = None
        try:
            avaliacoes = avaliacao_fisica_repo.obter_por_aluno(aluno_id)
            if avaliacoes:
                ultima_avaliacao = avaliacoes[0].data_avaliacao
        except Exception as e:
            print(f"[ERRO] Erro ao buscar avaliações: {e}")
        
        # Buscar progressos
        progressos = []
        try:
            progressos = progresso_aluno_repo.obter_por_aluno(aluno_id)
        except Exception as e:
            print(f"[ERRO] Erro ao buscar progressos: {e}")
        
        return templates.TemplateResponse("personal/alunos/detalhes.html", {
            "request": request,
            "usuario": usuario_logado,
            "aluno": aluno,
            "treinos_ativos": treinos_ativos,
            "ultima_avaliacao": ultima_avaliacao,
            "avaliacoes": avaliacoes,
            "progressos": progressos
        })
        
    except Exception as e:
        print(f"[ERRO] Detalhes aluno: {str(e)}")
        import traceback
        traceback.print_exc()
        return RedirectResponse("/personal/alunos?erro=Erro ao carregar detalhes do aluno", status_code=303)


@app.get("/personal/alunos/{aluno_id}/editar")
@requer_autenticacao(['profissional'])
async def personal_alunos_editar_get(
    request: Request, 
    aluno_id: int, 
    usuario_logado: dict = Depends(obter_usuario_logado)
):
    """Formulário de edição com validação de propriedade"""
    try:
        # Validar propriedade
        profissional = profissional_repo.obter_por_id(usuario_logado['id'])
        if not profissional:
            return RedirectResponse("/personal/alunos?erro=Acesso negado", status_code=303)
        
        personal = personal_repo.obter_por_profissional(profissional.id)
        if not personal:
            return RedirectResponse("/personal/alunos?erro=Acesso negado", status_code=303)
        
        aluno_rel = personal_aluno_repo.obter_por_id(aluno_id)
        if not aluno_rel or aluno_rel.personal_id != personal.id:
            return RedirectResponse("/personal/alunos?erro=Aluno não encontrado", status_code=303)
        
        # Buscar dados do aluno
        cliente = cliente_repo.obter_por_id(aluno_rel.aluno_id)
        usuario_aluno = usuario_repo.obter_por_id(cliente.usuario_id) if cliente else None
        
        if not usuario_aluno:
            return RedirectResponse("/personal/alunos?erro=Dados do aluno não encontrados", status_code=303)
        
        # CORREÇÃO: Converter data_inicio para datetime se vier como string
        data_inicio_convertida = aluno_rel.data_inicio
        if isinstance(aluno_rel.data_inicio, str):
            try:
                data_inicio_convertida = datetime.fromisoformat(aluno_rel.data_inicio.split('.')[0])
            except (ValueError, AttributeError):
                try:
                    data_inicio_convertida = datetime.strptime(aluno_rel.data_inicio, '%d/%m/%Y')
                except ValueError:
                    data_inicio_convertida = None
        
        aluno = {
            'id': aluno_rel.id,
            'nome': usuario_aluno.nome,
            'email': usuario_aluno.email,
            'objetivo': aluno_rel.objetivo,
            'data_inicio': data_inicio_convertida,  # Agora é datetime ou None
            'status': aluno_rel.status,
            'observacoes': aluno_rel.observacoes
        }
        
        return templates.TemplateResponse("personal/alunos/form.html", {
            "request": request,
            "usuario": usuario_logado,
            "aluno": aluno,
            "clientes_disponiveis": []  # Não precisa ao editar
        })
        
    except Exception as e:
        print(f"[ERRO] Editar aluno GET: {str(e)}")
        import traceback
        traceback.print_exc()
        return RedirectResponse("/personal/alunos?erro=Erro ao carregar aluno", status_code=303)

# =================== GESTÃO COMPLETA DE TREINOS ===================
# Adicione estas rotas após a rota personal_treinos_listar existente

# =================== GESTÃO DE TREINOS - LISTAGEM ===================
@app.get("/personal/treinos")
@requer_autenticacao(['profissional'])
async def personal_treinos_listar(request: Request, usuario_logado: dict = Depends(obter_usuario_logado)):
    """Lista todos os treinos do personal com validação de propriedade"""
    try:
        # Buscar profissional e personal
        profissional = profissional_repo.obter_por_id(usuario_logado['id'])
        if not profissional:
            return templates.TemplateResponse("personal/treinos/listar.html", {
                "request": request,
                "usuario": usuario_logado,
                "treinos": [],
                "erro": "Dados de profissional não encontrados"
            })
        
        personal = personal_repo.obter_por_profissional(profissional.id)
        if not personal:
            return templates.TemplateResponse("personal/treinos/listar.html", {
                "request": request,
                "usuario": usuario_logado,
                "treinos": [],
                "aviso": "Cadastro de Personal não encontrado"
            })
        
        # Buscar todos os alunos do personal
        alunos_relacionamento = personal_aluno_repo.obter_alunos_por_personal(personal.id)
        
        # Buscar treinos de cada aluno
        todos_treinos = []
        for rel in alunos_relacionamento:
            try:
                treinos_aluno = treino_personalizado_repo.obter_por_aluno(rel.id)
                
                # Buscar nome do aluno
                cliente = cliente_repo.obter_por_id(rel.aluno_id)
                usuario_aluno = usuario_repo.obter_por_id(cliente.usuario_id) if cliente else None
                aluno_nome = usuario_aluno.nome if usuario_aluno else 'N/A'
                
                # Adicionar treinos com informações do aluno
                for treino in treinos_aluno:
                    todos_treinos.append({
                        'id': treino.id,
                        'nome': treino.nome,
                        'aluno_nome': aluno_nome,
                        'objetivo': treino.objetivo,
                        'nivel_dificuldade': treino.nivel_dificuldade,
                        'status': treino.status,
                        'criado_em': treino.criado_em,
                        'frequencia_semanal': treino.frequencia_semanal,
                        'duracao_semanas': treino.duracao_semanas
                    })
            except Exception as e:
                print(f"[ERRO] Erro ao buscar treinos do aluno {rel.id}: {e}")
                continue
        
        # Ordenar por data de criação (mais recente primeiro)
        todos_treinos.sort(key=lambda x: x['criado_em'], reverse=True)
        
        return templates.TemplateResponse("personal/treinos/listar.html", {
            "request": request,
            "usuario": usuario_logado,
            "treinos": todos_treinos
        })
        
    except Exception as e:
        print(f"[ERRO] Listar treinos: {str(e)}")
        import traceback
        traceback.print_exc()
        return templates.TemplateResponse("personal/treinos/listar.html", {
            "request": request,
            "usuario": usuario_logado,
            "treinos": [],
            "erro": "Erro ao carregar lista de treinos"
        })

@app.get("/personal/treinos/novo")
@requer_autenticacao(['profissional'])
async def personal_treinos_novo_get(request: Request, usuario_logado: dict = Depends(obter_usuario_logado)):
    """Formulário para criar novo treino"""
    try:
        # Buscar personal
        profissional = profissional_repo.obter_por_id(usuario_logado['id'])
        personal = personal_repo.obter_por_profissional(profissional.id) if profissional else None
        
        if not personal:
            return RedirectResponse("/personal/treinos?erro=Personal não encontrado", status_code=303)
        
        # Buscar alunos do personal
        alunos_rel = personal_aluno_repo.obter_alunos_por_personal(personal.id)
        alunos_disponiveis = []
        
        for rel in alunos_rel:
            cliente = cliente_repo.obter_por_id(rel.aluno_id)
            if cliente:
                usuario_aluno = usuario_repo.obter_por_id(cliente.usuario_id)
                if usuario_aluno:
                    alunos_disponiveis.append({
                        'id': rel.id,
                        'nome': usuario_aluno.nome,
                        'email': usuario_aluno.email
                    })
        
        return templates.TemplateResponse("personal/treinos/form.html", {
            "request": request,
            "usuario": usuario_logado,
            "treino": None,
            "alunos_disponiveis": alunos_disponiveis,
            "titulo": "Criar Novo Treino",
            "acao": "/personal/treinos/salvar"
        })
    except Exception as e:
        print(f"[ERRO] Novo treino GET: {str(e)}")
        return RedirectResponse("/personal/treinos?erro=Erro ao carregar formulário", status_code=303)


@app.post("/personal/treinos/salvar")
@requer_autenticacao(['profissional'])
async def personal_treinos_salvar(
    request: Request,
    treino_id: Optional[int] = Form(None),
    aluno_id: int = Form(...),
    nome: str = Form(...),
    objetivo: str = Form(...),
    nivel_dificuldade: str = Form(...),
    frequencia_semanal: int = Form(...),
    duracao_semanas: int = Form(...),
    descricao: Optional[str] = Form(None),
    observacoes: Optional[str] = Form(None),
    status: str = Form('ativo'),
    usuario_logado: dict = Depends(obter_usuario_logado)
):
    """Salvar treino (criar ou atualizar)"""
    try:
        if treino_id:
            # Atualizar treino existente
            treino = treino_personalizado_repo.obter_por_id(treino_id)
            if treino:
                treino.nome = nome
                treino.objetivo = objetivo
                treino.nivel_dificuldade = nivel_dificuldade
                treino.frequencia_semanal = frequencia_semanal
                treino.duracao_semanas = duracao_semanas
                treino.descricao = descricao
                treino.observacoes = observacoes
                treino.status = status
                treino_personalizado_repo.alterar(treino)
                return RedirectResponse("/personal/treinos?sucesso=Treino atualizado com sucesso", status_code=303)
        else:
            # Criar novo treino
            novo_treino = TreinoPersonalizado(
                id=0,
                aluno_id=aluno_id,
                nome=nome,
                objetivo=objetivo,
                nivel_dificuldade=nivel_dificuldade,
                frequencia_semanal=frequencia_semanal,
                duracao_semanas=duracao_semanas,
                descricao=descricao,
                observacoes=observacoes,
                status=status,
                criado_em=datetime.now()
            )
            treino_personalizado_repo.inserir(novo_treino)
            return RedirectResponse("/personal/treinos?sucesso=Treino criado com sucesso", status_code=303)
            
    except Exception as e:
        print(f"[ERRO] Salvar treino: {str(e)}")
        return RedirectResponse("/personal/treinos?erro=Erro ao salvar treino", status_code=303)


@app.get("/personal/treinos/{treino_id}")
@requer_autenticacao(['profissional'])
async def personal_treinos_detalhes(
    request: Request,
    treino_id: int,
    usuario_logado: dict = Depends(obter_usuario_logado)
):
    """Ver detalhes do treino"""
    try:
        treino = treino_personalizado_repo.obter_por_id(treino_id)
        if not treino:
            return RedirectResponse("/personal/treinos?erro=Treino não encontrado", status_code=303)
        
        # Buscar dados do aluno
        aluno_rel = personal_aluno_repo.obter_por_id(treino.aluno_id)
        aluno_nome = "N/A"
        
        if aluno_rel:
            cliente = cliente_repo.obter_por_id(aluno_rel.aluno_id)
            if cliente:
                usuario_aluno = usuario_repo.obter_por_id(cliente.usuario_id)
                if usuario_aluno:
                    aluno_nome = usuario_aluno.nome
        
        # Buscar sessões de treino (se houver)
        sessoes = sessao_treino_repo.obter_por_treino(treino_id) if hasattr(sessao_treino_repo, 'obter_por_treino') else []
        
        return templates.TemplateResponse("personal/treinos/detalhes.html", {
            "request": request,
            "usuario": usuario_logado,
            "treino": treino,
            "aluno_nome": aluno_nome,
            "sessoes": sessoes
        })
    except Exception as e:
        print(f"[ERRO] Detalhes treino: {str(e)}")
        return RedirectResponse("/personal/treinos?erro=Erro ao carregar detalhes", status_code=303)


@app.get("/personal/treinos/{treino_id}/editar")
@requer_autenticacao(['profissional'])
async def personal_treinos_editar_get(
    request: Request,
    treino_id: int,
    usuario_logado: dict = Depends(obter_usuario_logado)
):
    """Formulário para editar treino"""
    try:
        treino = treino_personalizado_repo.obter_por_id(treino_id)
        if not treino:
            return RedirectResponse("/personal/treinos?erro=Treino não encontrado", status_code=303)
        
        # Buscar personal e alunos
        profissional = profissional_repo.obter_por_id(usuario_logado['id'])
        personal = personal_repo.obter_por_profissional(profissional.id) if profissional else None
        
        alunos_rel = personal_aluno_repo.obter_alunos_por_personal(personal.id) if personal else []
        alunos_disponiveis = []
        
        for rel in alunos_rel:
            cliente = cliente_repo.obter_por_id(rel.aluno_id)
            if cliente:
                usuario_aluno = usuario_repo.obter_por_id(cliente.usuario_id)
                if usuario_aluno:
                    alunos_disponiveis.append({
                        'id': rel.id,
                        'nome': usuario_aluno.nome,
                        'email': usuario_aluno.email
                    })
        
        return templates.TemplateResponse("personal/treinos/form.html", {
            "request": request,
            "usuario": usuario_logado,
            "treino": treino,
            "alunos_disponiveis": alunos_disponiveis,
            "titulo": "Editar Treino",
            "acao": "/personal/treinos/salvar"
        })
    except Exception as e:
        print(f"[ERRO] Editar treino GET: {str(e)}")
        return RedirectResponse("/personal/treinos?erro=Erro ao carregar treino", status_code=303)


@app.post("/personal/treinos/excluir/{treino_id}")
@requer_autenticacao(['profissional'])
async def personal_treinos_excluir(
    request: Request,
    treino_id: int,
    usuario_logado: dict = Depends(obter_usuario_logado)
):
    """Excluir treino"""
    try:
        treino = treino_personalizado_repo.obter_por_id(treino_id)
        if not treino:
            return RedirectResponse("/personal/treinos?erro=Treino não encontrado", status_code=303)
        
        # Excluir sessões relacionadas primeiro (se houver)
        if hasattr(sessao_treino_repo, 'excluir_por_treino'):
            sessao_treino_repo.excluir_por_treino(treino_id)
        
        # Excluir treino
        treino_personalizado_repo.excluir(treino_id)
        
        return RedirectResponse("/personal/treinos?sucesso=Treino excluído com sucesso", status_code=303)
    except Exception as e:
        print(f"[ERRO] Excluir treino: {str(e)}")
        return RedirectResponse("/personal/treinos?erro=Erro ao excluir treino", status_code=303)



# =================== GESTÃO DE AVALIAÇÕES FÍSICAS ===================
@app.get("/personal/avaliacoes")
@requer_autenticacao(['profissional'])
async def personal_avaliacoes_listar(request: Request, usuario_logado: dict = Depends(obter_usuario_logado)):
    try:
        profissional = profissional_repo.obter_por_id(usuario_logado['id'])
        personal = personal_repo.obter_por_profissional(profissional.id) if profissional else None
        
        if not personal:
            return templates.TemplateResponse("personal/avaliacoes/listar.html", {
                "request": request,
                "usuario": usuario_logado,
                "avaliacoes": []
            })
        
        # Buscar todos os alunos e suas avaliações
        alunos = personal_aluno_repo.obter_alunos_por_personal(personal.id)
        todas_avaliacoes = []
        
        for aluno in alunos:
            avaliacoes = avaliacao_fisica_repo.obter_por_aluno(aluno.id)
            for avaliacao in avaliacoes:
                cliente = cliente_repo.obter_por_id(aluno.aluno_id)
                usuario_aluno = usuario_repo.obter_por_id(cliente.usuario_id) if cliente else None
                
                todas_avaliacoes.append({
                    'id': avaliacao.id,
                    'aluno_nome': usuario_aluno.nome if usuario_aluno else 'N/A',
                    'data_avaliacao': avaliacao.data_avaliacao,
                    'peso': avaliacao.peso,
                    'imc': avaliacao.imc,
                    'percentual_gordura': avaliacao.percentual_gordura
                })
        
        # Ordenar por data (mais recente primeiro)
        todas_avaliacoes.sort(key=lambda x: x['data_avaliacao'], reverse=True)
        
        return templates.TemplateResponse("personal/avaliacoes/listar.html", {
            "request": request,
            "usuario": usuario_logado,
            "avaliacoes": todas_avaliacoes
        })
    except Exception as e:
        print(f"[ERRO] Listar avaliações: {str(e)}")
        return templates.TemplateResponse("personal/avaliacoes/listar.html", {
            "request": request,
            "usuario": usuario_logado,
            "avaliacoes": []
        })

# =================== GESTÃO DE PROGRESSOS ===================
@app.get("/personal/progressos")
@requer_autenticacao(['profissional'])
async def personal_progressos_listar(request: Request, usuario_logado: dict = Depends(obter_usuario_logado)):
    try:
        profissional = profissional_repo.obter_por_id(usuario_logado['id'])
        personal = personal_repo.obter_por_profissional(profissional.id) if profissional else None
        
        if not personal:
            return templates.TemplateResponse("personal/progressos/listar.html", {
                "request": request,
                "usuario": usuario_logado,
                "progressos": []
            })
        
        # Buscar progressos de todos os alunos
        alunos = personal_aluno_repo.obter_alunos_por_personal(personal.id)
        todos_progressos = []
        
        for aluno in alunos:
            progressos = progresso_aluno_repo.obter_por_aluno(aluno.id)
            for progresso in progressos:
                cliente = cliente_repo.obter_por_id(aluno.aluno_id)
                usuario_aluno = usuario_repo.obter_por_id(cliente.usuario_id) if cliente else None
                
                todos_progressos.append({
                    'id': progresso.id,
                    'aluno_nome': usuario_aluno.nome if usuario_aluno else 'N/A',
                    'data_registro': progresso.data_registro,
                    'peso': progresso.peso,
                    'humor': progresso.humor,
                    'energia': progresso.energia
                })
        
        # Ordenar por data
        todos_progressos.sort(key=lambda x: x['data_registro'], reverse=True)
        
        return templates.TemplateResponse("personal/progressos/listar.html", {
            "request": request,
            "usuario": usuario_logado,
            "progressos": todos_progressos
        })
    except Exception as e:
        print(f"[ERRO] Listar progressos: {str(e)}")
        return templates.TemplateResponse("personal/progressos/listar.html", {
            "request": request,
            "usuario": usuario_logado,
            "progressos": []
        })

# =================== PERFIL DO PERSONAL ===================
@app.get("/personal/perfil")
@requer_autenticacao(['profissional'])
async def personal_perfil(request: Request, usuario_logado: dict = Depends(obter_usuario_logado)):
    try:
        profissional = profissional_repo.obter_por_id(usuario_logado['id'])
        personal = personal_repo.obter_por_profissional(profissional.id) if profissional else None
        
        return templates.TemplateResponse("personal/perfil.html", {
            "request": request,
            "usuario": usuario_logado,
            "profissional": profissional,
            "personal": personal
        })
    except Exception as e:
        print(f"[ERRO] Perfil personal: {str(e)}")
        return templates.TemplateResponse("personal/perfil.html", {
            "request": request,
            "usuario": usuario_logado,
            "profissional": None,
            "personal": None
        })


if __name__ == "__main__":
    import uvicorn
    print("🚀 Iniciando Body Health com Email Service integrado...")
    print("📧 Email configurado: bodyhealth619@gmail.com")
    print("🔧 Teste o email em: http://localhost:8000/test-email-quick")
    uvicorn.run(app, host="0.0.0.0", port=8000)