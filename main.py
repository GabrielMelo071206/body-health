from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
import secrets

app = FastAPI()

# Gerar chave secreta (em produção, use variável de ambiente!)
SECRET_KEY = secrets.token_urlsafe(32)

# Adicionar middleware de sessão
app.add_middleware(
    SessionMiddleware, 
    secret_key=SECRET_KEY,
    max_age=3600,  # Sessão expira em 1 hora
    same_site="lax",
    https_only=False  # Em produção, mude para True com HTTPS
)

@router.post("/login")
async def post_login(
    request: Request,
    email: str = Form(...),
    senha: str = Form(...),
    redirect: str = Form(None)
):
    usuario = usuario_repo.obter_por_email(email)
    
    if not usuario or not verificar_senha(senha, usuario.senha):
        return templates.TemplateResponse(
            "login.html",
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
    
    # Redirecionar
    if redirect:
        return RedirectResponse(redirect, status.HTTP_303_SEE_OTHER)
    
    if usuario.perfil == "admin":
        return RedirectResponse("/admin", status.HTTP_303_SEE_OTHER)
    
    return RedirectResponse("/", status.HTTP_303_SEE_OTHER)

@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status.HTTP_303_SEE_OTHER)

@router.post("/cadastro")
async def post_cadastro(
    request: Request,
    nome: str = Form(...),
    email: str = Form(...),
    senha: str = Form(...),
    cpf: str = Form(None),
    telefone: str = Form(None)
):
    # Verificar se email já existe
    if usuario_repo.obter_por_email(email):
        return templates.TemplateResponse(
            "cadastro.html",
            {"request": request, "erro": "Email já cadastrado"}
        )
    
    # Criar hash da senha
    senha_hash = criar_hash_senha(senha)
    
    # Criar usuário
    usuario = Usuario(
        id=0,
        nome=nome,
        email=email,
        senha=senha_hash,
        perfil="cliente"
    )
    
    usuario_id = usuario_repo.inserir(usuario)
    
    # Se tiver CPF/telefone, inserir na tabela cliente
    if cpf and telefone:
        cliente = Cliente(
            id=usuario_id,
            cpf=cpf,
            telefone=telefone
        )
        cliente_repo.inserir(cliente)
    
    return RedirectResponse("/login", status.HTTP_303_SEE_OTHER)

from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import secrets
from typing import Optional

# Importar seus repos e utilitários de segurança
from repo.usuario_repo import inserir as inserir_usuario, obter_por_email
from util.security import criar_hash_senha, verificar_senha
from model.usuario_model import Usuario
from model.cliente_model import Cliente
from model.profissional_model import Profissional

app = FastAPI()

# Configurar diretório de arquivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configurar templates
templates = Jinja2Templates(directory="templates")

# Configurar middleware de sessão
SECRET_KEY = secrets.token_urlsafe(32)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, max_age=3600, same_site="lax", https_only=False)


# ----------------- ROTAS PÁGINAS INICIAIS -----------------

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("inicio/index.html", {"request": request})

# ----------------- LOGIN -----------------

@app.get("/login_cliente")
async def login_cliente_get(request: Request):
    return templates.TemplateResponse("inicio/login_cliente.html", {"request": request})

@app.post("/login_cliente")
async def login_cliente_post(request: Request, email: str = Form(...), senha: str = Form(...)):
    usuario = obter_por_email(email)
    if not usuario or usuario.perfil != "cliente" or not verificar_senha(senha, usuario.senha):
        return templates.TemplateResponse("inicio/login_cliente.html", {"request": request, "erro": "Email ou senha inválidos"})
    request.session["usuario_id"] = usuario.id
    request.session["perfil"] = usuario.perfil
    return RedirectResponse("/", status_code=303)


@app.get("/login_profissional")
async def login_profissional_get(request: Request):
    return templates.TemplateResponse("inicio/login_profissional.html", {"request": request})

@app.post("/login_profissional")
async def login_profissional_post(request: Request, email: str = Form(...), senha: str = Form(...)):
    usuario = obter_por_email(email)
    if not usuario or usuario.perfil != "profissional" or not verificar_senha(senha, usuario.senha):
        return templates.TemplateResponse("inicio/login_profissional.html", {"request": request, "erro": "Email ou senha inválidos"})
    request.session["usuario_id"] = usuario.id
    request.session["perfil"] = usuario.perfil
    return RedirectResponse("/", status_code=303)

# ----------------- LOGOUT -----------------

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)


# ----------------- CADASTRO -----------------

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
    if obter_por_email(email):
        return templates.TemplateResponse("inicio/cadastro_cliente.html", {"request": request, "erro": "Email já cadastrado"})

    hash_senha = criar_hash_senha(senha)
    usuario = Usuario(id=0, nome=nome, email=email, senha=hash_senha, perfil="cliente")
    usuario_id = inserir_usuario(usuario)

    cliente = Cliente(usuario_id=usuario_id, plano_id=None)
    # aqui você precisaria chamar cliente_repo.inserir(cliente)

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
    if obter_por_email(email):
        return templates.TemplateResponse("inicio/cadastro_profissional.html", {"request": request, "erro": "Email já cadastrado"})

    hash_senha = criar_hash_senha(senha)
    usuario = Usuario(id=0, nome=nome, email=email, senha=hash_senha, perfil="profissional")
    usuario_id = inserir_usuario(usuario)

    profissional = Profissional(usuario_id=usuario_id, especialidade=especialidade, registro_profissional=registro_profissional)
    # aqui você precisaria chamar profissional_repo.inserir(profissional)

    return RedirectResponse("/login_profissional", status_code=303)
