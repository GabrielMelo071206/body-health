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

    return RedirectResponse("/personal/dashboard", status_code=303)

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

    cliente = Cliente(usuario_id=usuario_id)
    cliente_repo.inserir(cliente)

    return RedirectResponse("/login_cliente", status_code=303)

@app.get("/cadastro_profissional")
async def cadastro_profissional_get(request: Request):
    return templates.TemplateResponse("inicio/cadastro_profissional.html", {"request": request})

# CADASTRO PROFISSIONAL COM UPLOAD
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
    # Definimos um contexto base com a request e a session para garantir que o template funcione
    contexto_base = {
        "request": request,
        "session": request.session,  # CORREÇÃO 1: Adicionamos o objeto session ao contexto
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
        # Buscar dados do personal
        profissional = profissional_repo.obter_por_id(usuario_logado['id'])
        # NOTE: Esta linha pode falhar se a tabela 'personal' não existir
        personal = personal_repo.obter_por_profissional(profissional.id) if profissional else None
        
        if not personal:
            # Retorna o template usando o contexto base
            return templates.TemplateResponse("personal/dashboard.html", contexto_base)
        
        # Estatísticas
        alunos = personal_aluno_repo.obter_alunos_por_personal(personal.id)
        total_alunos = len(alunos)
        alunos_ativos = len([a for a in alunos if a.status == 'ativo'])
        
        # Contar treinos
        total_treinos = 0
        for aluno in alunos:
            treinos = treino_personalizado_repo.obter_por_aluno(aluno.id)
            total_treinos += len(treinos)
        
        # Contar avaliações
        total_avaliacoes = 0
        for aluno in alunos:
            avaliacoes = avaliacao_fisica_repo.obter_por_aluno(aluno.id)
            total_avaliacoes += len(avaliacoes)
        
        # Atividades recentes e Lembretes (adapte se necessário)
        atividades = []
        lembretes = []
        
        # Contexto de sucesso (combina dados reais com o contexto base)
        contexto_sucesso = {
            "request": request,
            "session": request.session, # CORREÇÃO 1: Adicionamos o objeto session ao contexto
            "usuario": usuario_logado,
            "total_alunos": total_alunos,
            "alunos_ativos": alunos_ativos,
            "total_treinos": total_treinos,
            "total_avaliacoes": total_avaliacoes,
            "atividades": atividades,
            "lembretes": lembretes,
            "avaliacoes_media": personal.avaliacoes_media
        }
        
        return templates.TemplateResponse("personal/dashboard.html", contexto_sucesso)
        
    except Exception as e:
        print(f"[ERRO] Dashboard Personal: {str(e)}")
        # Retorna o template usando o contexto base em caso de erro
        return templates.TemplateResponse("personal/dashboard.html", contexto_base)
# =================== GESTÃO DE ALUNOS ===================
@app.get("/personal/alunos")
@requer_autenticacao(['profissional'])
async def personal_alunos_listar(request: Request, usuario_logado: dict = Depends(obter_usuario_logado)):
    try:
        # Buscar personal do profissional logado
        profissional = profissional_repo.obter_por_id(usuario_logado['id'])
        personal = personal_repo.obter_por_profissional(profissional.id) if profissional else None
        
        if not personal:
            return templates.TemplateResponse("personal/alunos/listar.html", {
                "request": request,
                "usuario": usuario_logado,
                "alunos": []
            })
        
        # Buscar alunos do personal com dados do usuário
        alunos_relacionamento = personal_aluno_repo.obter_alunos_por_personal(personal.id)
        
        # Enriquecer com dados do usuário
        alunos = []
        for rel in alunos_relacionamento:
            cliente = cliente_repo.obter_por_id(rel.aluno_id)
            if cliente:
                usuario_aluno = usuario_repo.obter_por_id(cliente.usuario_id)
                if usuario_aluno:
                    alunos.append({
                        'id': rel.id,
                        'aluno_id': rel.aluno_id,
                        'nome': usuario_aluno.nome,
                        'email': usuario_aluno.email,
                        'objetivo': rel.objetivo,
                        'data_inicio': rel.data_inicio,
                        'status': rel.status,
                        'observacoes': rel.observacoes
                    })
        
        return templates.TemplateResponse("personal/alunos/listar.html", {
            "request": request,
            "usuario": usuario_logado,
            "alunos": alunos
        })
    except Exception as e:
        print(f"[ERRO] Listar alunos: {str(e)}")
        return templates.TemplateResponse("personal/alunos/listar.html", {
            "request": request,
            "usuario": usuario_logado,
            "alunos": []
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
    cliente_id: int = Form(...),
    data_inicio: str = Form(...),
    status: str = Form(...),
    objetivo: Optional[str] = Form(None),
    observacoes: Optional[str] = Form(None),
    usuario_logado: dict = Depends(obter_usuario_logado)
):
    try:
        # Buscar personal
        profissional = profissional_repo.obter_por_id(usuario_logado['id'])
        personal = personal_repo.obter_por_profissional(profissional.id)
        
        if not personal:
            return RedirectResponse("/personal/alunos?erro=Personal não encontrado", status_code=303)
        
        # Converter data
        data_inicio_dt = datetime.strptime(data_inicio, '%Y-%m-%d')
        
        if aluno_id:
            # Atualizar aluno existente
            aluno = personal_aluno_repo.obter_por_id(aluno_id)
            if aluno:
                aluno.data_inicio = data_inicio_dt
                aluno.status = status
                aluno.objetivo = objetivo
                aluno.observacoes = observacoes
                personal_aluno_repo.alterar(aluno)
        else:
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
            
            # Atualizar contador de alunos do personal
            personal.total_alunos += 1
            personal_repo.alterar(personal)
        
        return RedirectResponse("/personal/alunos?sucesso=Aluno salvo com sucesso", status_code=303)
    except Exception as e:
        print(f"[ERRO] Salvar aluno: {str(e)}")
        return RedirectResponse("/personal/alunos?erro=Erro ao salvar aluno", status_code=303)

@app.get("/personal/alunos/{aluno_id}")
@requer_autenticacao(['profissional'])
async def personal_alunos_detalhes(
    request: Request, 
    aluno_id: int, 
    usuario_logado: dict = Depends(obter_usuario_logado)
):
    try:
        # Buscar relacionamento
        aluno_rel = personal_aluno_repo.obter_por_id(aluno_id)
        if not aluno_rel:
            return RedirectResponse("/personal/alunos?erro=Aluno não encontrado", status_code=303)
        
        # Buscar dados do cliente/usuário
        cliente = cliente_repo.obter_por_id(aluno_rel.aluno_id)
        usuario_aluno = usuario_repo.obter_por_id(cliente.usuario_id) if cliente else None
        
        if not usuario_aluno:
            return RedirectResponse("/personal/alunos?erro=Dados do aluno não encontrados", status_code=303)
        
        # Montar objeto aluno
        aluno = {
            'id': aluno_rel.id,
            'aluno_id': aluno_rel.aluno_id,
            'nome': usuario_aluno.nome,
            'email': usuario_aluno.email,
            'objetivo': aluno_rel.objetivo,
            'data_inicio': aluno_rel.data_inicio,
            'status': aluno_rel.status,
            'observacoes': aluno_rel.observacoes
        }
        
        # Buscar treinos ativos
        treinos_ativos = treino_personalizado_repo.obter_por_aluno(aluno_id)
        
        # Buscar última avaliação
        avaliacoes = avaliacao_fisica_repo.obter_por_aluno(aluno_id)
        ultima_avaliacao = avaliacoes[0].data_avaliacao if avaliacoes else None
        
        # Buscar progressos
        progressos = progresso_aluno_repo.obter_por_aluno(aluno_id)
        
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
        return RedirectResponse("/personal/alunos?erro=Erro ao carregar detalhes", status_code=303)

@app.get("/personal/alunos/{aluno_id}/editar")
@requer_autenticacao(['profissional'])
async def personal_alunos_editar_get(
    request: Request, 
    aluno_id: int, 
    usuario_logado: dict = Depends(obter_usuario_logado)
):
    try:
        aluno_rel = personal_aluno_repo.obter_por_id(aluno_id)
        if not aluno_rel:
            return RedirectResponse("/personal/alunos?erro=Aluno não encontrado", status_code=303)
        
        cliente = cliente_repo.obter_por_id(aluno_rel.aluno_id)
        usuario_aluno = usuario_repo.obter_por_id(cliente.usuario_id) if cliente else None
        
        aluno = {
            'id': aluno_rel.id,
            'nome': usuario_aluno.nome if usuario_aluno else '',
            'email': usuario_aluno.email if usuario_aluno else '',
            'objetivo': aluno_rel.objetivo,
            'data_inicio': aluno_rel.data_inicio,
            'status': aluno_rel.status,
            'observacoes': aluno_rel.observacoes
        }
        
        return templates.TemplateResponse("personal/alunos/form.html", {
            "request": request,
            "usuario": usuario_logado,
            "aluno": aluno
        })
    except Exception as e:
        print(f"[ERRO] Editar aluno: {str(e)}")
        return RedirectResponse("/personal/alunos?erro=Erro ao carregar aluno", status_code=303)

# =================== GESTÃO DE TREINOS ===================
@app.get("/personal/treinos")
@requer_autenticacao(['profissional'])
async def personal_treinos_listar(request: Request, usuario_logado: dict = Depends(obter_usuario_logado)):
    try:
        profissional = profissional_repo.obter_por_id(usuario_logado['id'])
        personal = personal_repo.obter_por_profissional(profissional.id) if profissional else None
        
        if not personal:
            return templates.TemplateResponse("personal/treinos/listar.html", {
                "request": request,
                "usuario": usuario_logado,
                "treinos": []
            })
        
        # Buscar todos os alunos do personal
        alunos = personal_aluno_repo.obter_alunos_por_personal(personal.id)
        
        # Buscar treinos de cada aluno
        todos_treinos = []
        for aluno in alunos:
            treinos = treino_personalizado_repo.obter_por_aluno(aluno.id)
            for treino in treinos:
                # Buscar nome do aluno
                cliente = cliente_repo.obter_por_id(aluno.aluno_id)
                usuario_aluno = usuario_repo.obter_por_id(cliente.usuario_id) if cliente else None
                
                todos_treinos.append({
                    'id': treino.id,
                    'nome': treino.nome,
                    'aluno_nome': usuario_aluno.nome if usuario_aluno else 'N/A',
                    'objetivo': treino.objetivo,
                    'nivel_dificuldade': treino.nivel_dificuldade,
                    'status': treino.status,
                    'criado_em': treino.criado_em
                })
        
        return templates.TemplateResponse("personal/treinos/listar.html", {
            "request": request,
            "usuario": usuario_logado,
            "treinos": todos_treinos
        })
    except Exception as e:
        print(f"[ERRO] Listar treinos: {str(e)}")
        return templates.TemplateResponse("personal/treinos/listar.html", {
            "request": request,
            "usuario": usuario_logado,
            "treinos": []
        })

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