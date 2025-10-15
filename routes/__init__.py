from datetime import datetime
from typing import Optional
from fastapi import FastAPI, Request, Form, Depends, UploadFile, File, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from data.repo import plano_repo, usuario_repo, cliente_repo, profissional_repo
from data.repo import personal_repo, personal_aluno_repo, treino_personalizado_repo
from data.repo import avaliacao_fisica_repo, progresso_aluno_repo, sessao_treino_repo
from data.model.usuario_model import Usuario
from data.model.cliente_model import Cliente
from data.model.profissional_model import Profissional
from data.model.plano_model import Plano
from data.model.personal_model import Personal
from data.model.personal_aluno_model import PersonalAluno
from data.model.treino_personalizado_model import TreinoPersonalizado
from util.file_upload import salvar_foto_registro
from util.security import criar_hash_senha, verificar_senha, gerar_senha_aleatoria
from util.auth_decorator import criar_sessao, obter_usuario_logado, requer_autenticacao
from util.email_service import email_service
from data.dtos.cadastro_cliente_dto import validar_cadastro_cliente
from data.dtos.cadastro_profissional_dto import validar_cadastro_profissional, validar_foto_registro
from data.dtos.login_dto import validar_login

from fastapi import FastAPI
from .register_public_routes import register_public_routes
from .register_admin_routes import register_admin_routes
from .register_personal_routes import register_personal_routes
from .register_auth_routes import register_auth_routes


def register_routes(app: FastAPI):
    """Registra todas as rotas principais do sistema."""
    register_public_routes(app)
    register_admin_routes(app)
    register_auth_routes(app)
    register_personal_routes(app)



templates = Jinja2Templates(directory="templates")


def register_public_routes(app: FastAPI):
    
    @app.get("/")
    async def index(request: Request):
        planos = plano_repo.obter_todos()
        planos_gratuitos = [p for p in planos if p.preco == 0.0]
        planos_pagos = [p for p in planos if p.preco > 0.0]
        plano_destaque = None
        for plano in planos_pagos:
            if plano.duracao_dias >= 365:
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
        sucesso = request.query_params.get('sucesso')
        erro = request.query_params.get('erro')
        return templates.TemplateResponse("inicio/suporte.html", {
            "request": request,
            "sucesso": sucesso,
            "erro": erro
        })

    @app.post("/suporte")
    async def enviar_suporte_post(
        request: Request,
        nome: str = Form(...),
        email: str = Form(...),
        assunto: str = Form(...),
        mensagem: str = Form(...)
    ):
        if not all([nome.strip(), email.strip(), assunto.strip(), mensagem.strip()]):
            return RedirectResponse(
                url="/suporte?erro=Todos os campos são obrigatórios.",
                status_code=303
            )
        
        if len(mensagem.strip()) < 10:
            return RedirectResponse(
                url="/suporte?erro=A mensagem deve ter pelo menos 10 caracteres.",
                status_code=303
            )
        
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
            todos_planos = plano_repo.obter_todos()
            planos_gratuitos = [p for p in todos_planos if p.preco == 0.0]
            planos_pagos = [p for p in todos_planos if p.preco > 0.0]
            planos_pagos.sort(key=lambda x: x.preco)
            planos_gratuitos.sort(key=lambda x: x.duracao_dias, reverse=True)
            
            print(f"[DEBUG] Total de planos: {len(todos_planos)}")
            print(f"[DEBUG] Planos gratuitos: {len(planos_gratuitos)}")
            print(f"[DEBUG] Planos pagos: {len(planos_pagos)}")
            
            return templates.TemplateResponse("inicio/planos.html", {
                "request": request,
                "todos_planos": todos_planos,
                "planos_gratuitos": planos_gratuitos,
                "planos_pagos": planos_pagos,
                "total_planos": len(todos_planos),
                "tem_planos_pagos": len(planos_pagos) > 0,
                "tem_planos_gratuitos": len(planos_gratuitos) > 0
            })
        except Exception as e:
            print(f"[ERRO] Erro ao carregar planos: {str(e)}")
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
    async def pagamento(request: Request, plano_id: Optional[int] = None):
        try:
            todos_planos = plano_repo.obter_todos()
            planos_pagos = [p for p in todos_planos if p.preco > 0.0]
            planos_pagos.sort(key=lambda x: x.preco)
            
            plano_selecionado = None
            if plano_id:
                plano_selecionado = plano_repo.obter_por_id(plano_id)
            
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