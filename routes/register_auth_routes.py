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

templates = Jinja2Templates(directory="templates")



def register_auth_routes(app: FastAPI):
    
    @app.get("/login")
    async def login_get(request: Request):
        return templates.TemplateResponse("inicio/login.html", {"request": request})

    @app.get("/login_cliente")
    async def login_cliente_get(request: Request):
        return templates.TemplateResponse("inicio/login_cliente.html", {"request": request})

    @app.post("/login_cliente")
    async def login_cliente_post(
        request: Request, 
        email: str = Form(...), 
        senha: str = Form(...)
    ):
        dados_formulario = {"email": email}
        dto, erros = validar_login({"email": email, "senha": senha})
        
        if erros:
            return templates.TemplateResponse("inicio/login_cliente.html", {
                "request": request,
                "erros": erros,
                "dados": dados_formulario
            })
        
        usuario = usuario_repo.obter_por_email(dto.email)
        
        if not usuario or usuario.perfil != "cliente":
            return templates.TemplateResponse("inicio/login_cliente.html", {
                "request": request,
                "erro": "Email ou senha inválidos.",
                "dados": dados_formulario
            })
        
        if not verificar_senha(dto.senha, usuario.senha):
            return templates.TemplateResponse("inicio/login_cliente.html", {
                "request": request,
                "erro": "Email ou senha inválidos.",
                "dados": dados_formulario
            })
        
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
    async def login_profissional_post(
        request: Request, 
        email: str = Form(...), 
        senha: str = Form(...)
    ):
        dados_formulario = {"email": email}
        dto, erros = validar_login({"email": email, "senha": senha})
        
        if erros:
            return templates.TemplateResponse("inicio/login_profissional.html", {
                "request": request,
                "erros": erros,
                "dados": dados_formulario
            })
        
        usuario = usuario_repo.obter_por_email(dto.email)
        
        if not usuario or usuario.perfil != "profissional":
            return templates.TemplateResponse("inicio/login_profissional.html", {
                "request": request,
                "erro": "Email ou senha inválidos.",
                "dados": dados_formulario
            })
        
        if not verificar_senha(dto.senha, usuario.senha):
            return templates.TemplateResponse("inicio/login_profissional.html", {
                "request": request,
                "erro": "Email ou senha inválidos.",
                "dados": dados_formulario
            })
        
        usuario_dict = {
            "id": usuario.id,
            "nome": usuario.nome,
            "email": usuario.email,
            "perfil": usuario.perfil,
            "foto": usuario.foto
        }
        criar_sessao(request, usuario_dict)
        return RedirectResponse("/personal/dashboard", status_code=303)

    @app.get("/cadastro_cliente")
    async def cadastro_cliente_get(request: Request):
        return templates.TemplateResponse("inicio/cadastro_cliente.html", {"request": request})

    @app.post("/cadastro_cliente")
    async def cadastro_cliente_post(
        request: Request,
        nome: str = Form(...),
        email: str = Form(...),
        senha: str = Form(...),
        senha_confirm: str = Form(...)
    ):
        dados_formulario = {"nome": nome, "email": email}
        data = {"nome": nome, "email": email, "senha": senha, "senha_confirm": senha_confirm}
        dto, erros = validar_cadastro_cliente(data)
        
        if not erros:
            erros = {}
        
        if usuario_repo.obter_por_email(email.strip().lower()):
            erros['email'] = 'Este email já está cadastrado. Faça login ou use outro email.'
        
        if erros:
            return templates.TemplateResponse("inicio/cadastro_cliente.html", {
                "request": request,
                "erros": erros,
                "dados": dados_formulario
            })
        
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

    @app.get("/cadastro_profissional")
    async def cadastro_profissional_get(request: Request):
        return templates.TemplateResponse("inicio/cadastro_profissional.html", {"request": request})

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
        dados_formulario = {
            "nome": nome,
            "email": email,
            "especialidade": especialidade,
            "registro_profissional": registro_profissional,
            "cpf_cnpj": cpf_cnpj
        }
        
        data = {
            "nome": nome,
            "email": email,
            "senha": senha,
            "senha_confirm": senha_confirm,
            "especialidade": especialidade,
            "registro_profissional": registro_profissional,
            "cpf_cnpj": cpf_cnpj
        }
        
        dto, erros = validar_cadastro_profissional(data)
        
        if not erros:
            erros = {}
        
        foto_valida, erro_foto = validar_foto_registro(foto_registro)
        if not foto_valida:
            erros['foto_registro'] = erro_foto
        
        if usuario_repo.obter_por_email(email.strip().lower()):
            erros['email'] = 'Este email já está cadastrado. Faça login ou use outro email.'
        
        if erros:
            return templates.TemplateResponse("inicio/cadastro_profissional.html", {
                "request": request,
                "erros": erros,
                "dados": dados_formulario
            })
        
        try:
            path_foto = await salvar_foto_registro(foto_registro)
            hash_senha = criar_hash_senha(dto.senha)
            usuario = Usuario(
                id=0,
                nome=dto.nome,
                email=dto.email,
                senha=hash_senha,
                perfil="profissional"
            )
            usuario_id = usuario_repo.inserir(usuario)
            
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

    @app.get("/login_admin")
    async def login_admin_get(request: Request):
        return templates.TemplateResponse("admin/login_admin.html", {"request": request})

    @app.post("/login_admin")
    async def login_admin_post(request: Request, email: str = Form(...), senha: str = Form(...)):
        dados_formulario = {"email": email}
        dto, erros = validar_login({"email": email, "senha": senha})
        
        if erros:
            return templates.TemplateResponse("admin/login_admin.html", {
                "request": request,
                "erros": erros,
                "dados": dados_formulario
            })
        
        usuario = usuario_repo.obter_por_email(dto.email)
        
        if not usuario or usuario.perfil != "admin":
            return templates.TemplateResponse("admin/login_admin.html", {
                "request": request,
                "erro": "Email ou senha inválidos.",
                "dados": dados_formulario
            })
        
        if not verificar_senha(dto.senha, usuario.senha):
            return templates.TemplateResponse("admin/login_admin.html", {
                "request": request,
                "erro": "Email ou senha inválidos.",
                "dados": dados_formulario
            })
        
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

    @app.get("/perfil")
    @requer_autenticacao()
    async def perfil(request: Request, usuario_logado: dict = Depends(obter_usuario_logado)):
        return templates.TemplateResponse("perfil.html", {
            "request": request,
            "usuario": usuario_logado
        })

    @app.get("/recuperar_senha")
    async def recuperar_senha_get(request: Request):
        mensagem = request.query_params.get('mensagem')
        erro = request.query_params.get('erro')
        return templates.TemplateResponse("inicio/recuperar_senha.html", {
            "request": request,
            "mensagem": mensagem,
            "erro": erro
        })

    @app.post("/recuperar_senha")
    async def recuperar_senha_post(request: Request, email: str = Form(...)):
        usuario = usuario_repo.obter_por_email(email.strip().lower())
        
        if not usuario:
            return RedirectResponse(
                url="/recuperar_senha?erro=Email não encontrado no sistema.",
                status_code=303
            )

        try:
            nova_senha = gerar_senha_aleatoria(8)
            usuario.senha = criar_hash_senha(nova_senha)
            usuario_repo.alterar(usuario)
            
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

    @app.get("/test-email-quick")
    async def test_email_quick():
        try:
            if email_service.testar_conexao():
                return {"status": "✅ Conexão OK", "service": "Body Health Email"}
            else:
                return {"status": "❌ Conexão FALHOU", "service": "Body Health Email"}
        except Exception as e:
            return {"status": f"❌ ERRO: {str(e)}", "service": "Body Health Email"}


