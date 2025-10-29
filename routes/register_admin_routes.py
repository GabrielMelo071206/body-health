from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, Request, Form, Depends, UploadFile, File, status
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
from util.email_service_gmail import email_service_gmail
from data.dtos.cadastro_cliente_dto import validar_cadastro_cliente
from data.dtos.cadastro_profissional_dto import validar_cadastro_profissional, validar_foto_registro
from data.dtos.login_dto import validar_login

templates = Jinja2Templates(directory="templates")








def register_admin_routes(app: FastAPI):
    
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

    @app.get("/admin/test-email")
    @requer_autenticacao(['admin'])
    async def test_email_admin(request: Request, usuario_logado: dict = Depends(obter_usuario_logado)):
        try:
            if email_service_gmail.testar_conexao():
                resultado = {
                    "status": "✅ Sucesso",
                    "mensagem": "Conexão SMTP estabelecida com sucesso!",
                    "servidor": email_service_gmail.smtp_server,
                    "porta": email_service_gmail.smtp_port,
                    "email": email_service_gmail.email
                }
            else:
                resultado = {
                    "status": "❌ Erro", 
                    "mensagem": "Falha na conexão SMTP",
                    "servidor": email_service_gmail.smtp_server,
                    "porta": email_service_gmail.smtp_port,
                    "email": email_service_gmail.email
                }
            
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
        if usuario_repo.obter_por_email(email):
            return templates.TemplateResponse("admin/usuarios/form.html", {
                "request": request,
                "usuario": usuario_logado,
                "titulo": "Criar Novo Usuário",
                "acao": "/admin/usuarios/novo",
                "erro": "Email já cadastrado"
            })
        
        hash_senha = criar_hash_senha(senha)
        usuario = Usuario(
            id=0,
            nome=nome,
            email=email,
            senha=hash_senha,
            perfil=perfil
        )
        
        usuario_id = usuario_repo.inserir(usuario)
        
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
        
        usuario.nome = nome
        usuario.email = email
        usuario.perfil = perfil
        
        if senha and senha.strip():
            usuario.senha = criar_hash_senha(senha)
        
        usuario_repo.alterar(usuario)
        return RedirectResponse("/admin/usuarios", status_code=303)

    @app.post("/admin/usuarios/excluir/{usuario_id}")
    @requer_autenticacao(['admin'])
    async def admin_usuarios_excluir(request: Request, usuario_id: int, usuario_logado: dict = Depends(obter_usuario_logado)):
        if usuario_id == usuario_logado['id']:
            return RedirectResponse("/admin/usuarios?erro=Não é possível excluir seu próprio usuário", status_code=303)
        
        try:
            usuario = usuario_repo.obter_por_id(usuario_id)
            if not usuario:
                return RedirectResponse("/admin/usuarios?erro=Usuário não encontrado", status_code=303)
            
            try:
                if usuario.perfil == "cliente":
                    cliente_repo.excluir(usuario_id)
                elif usuario.perfil == "profissional":
                    profissional_repo.excluir(usuario_id)
            except Exception as e:
                print(f"[AVISO] Não foi possível excluir registros relacionados do usuário {usuario_id}: {str(e)}")
            
            usuario_repo.excluir(usuario_id)
            return RedirectResponse("/admin/usuarios?sucesso=Usuário excluído com sucesso", status_code=303)
                
        except Exception as e:
            print(f"[ERRO] Erro ao excluir usuário {usuario_id}: {str(e)}")
            return RedirectResponse("/admin/usuarios?erro=Erro interno ao excluir usuário", status_code=303)

