from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
from routes import register_routes
import os

# Carregar variáveis de ambiente (.env)
load_dotenv()

app = FastAPI()

# ✅ Middleware de sessão
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "chave-super-secreta")  # valor padrão caso não exista no .env
)

# Templates e arquivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Registrar todas as rotas
register_routes(app)

# Página inicial opcional (teste rápido)
@app.get("/")
def home():
    return {"status": "Servidor funcionando!"}
