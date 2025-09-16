# 🔐 Guia de Implementação de Autenticação e Autorização

Este guia ensina como implementar um sistema completo de autenticação e autorização em sua aplicação FastAPI, baseado no código deste projeto.

## 📋 Índice
1. [Visão Geral](#visão-geral)
2. [Instalação de Dependências](#instalação-de-dependências)
3. [Estrutura do Banco de Dados](#estrutura-do-banco-de-dados)
4. [Implementação Passo a Passo](#implementação-passo-a-passo)
5. [Como Usar](#como-usar)
6. [Exemplos Práticos](#exemplos-práticos)
7. [Troubleshooting](#troubleshooting)

## 🎯 Visão Geral

Este sistema oferece:
- ✅ Login e logout de usuários
- ✅ Cadastro de novos usuários
- ✅ Recuperação de senha por email
- ✅ Perfis de acesso (admin/cliente)
- ✅ Proteção de rotas por perfil
- ✅ Gestão de sessões
- ✅ Hash seguro de senhas

## 📦 Instalação de Dependências

Adicione estas dependências ao seu `requirements.txt`:

```txt
passlib[bcrypt]
python-jose[cryptography]
itsdangerous
```

Ou instale diretamente:

```bash
pip install passlib[bcrypt] python-jose[cryptography] itsdangerous
```

## 🗄️ Estrutura do Banco de Dados

### 1. Tabela de Usuários

Crie a tabela `usuario` no seu banco SQLite com a seguinte estrutura:

```sql
CREATE TABLE IF NOT EXISTS usuario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    senha TEXT NOT NULL,
    perfil TEXT NOT NULL DEFAULT 'cliente',
    foto TEXT,
    token_redefinicao TEXT,
    data_token TIMESTAMP,
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. Tabela de Clientes (opcional)

Se você quiser dados adicionais para clientes:

```sql
CREATE TABLE IF NOT EXISTS cliente (
    id INTEGER PRIMARY KEY,
    cpf TEXT UNIQUE,
    telefone TEXT,
    FOREIGN KEY (id) REFERENCES usuario(id)
);
```

## 🚀 Implementação Passo a Passo

### Passo 1: Copiar Arquivos Essenciais

Copie os seguintes arquivos para seu projeto:

#### 📁 `/util/security.py`
Gerencia hash de senhas e tokens:
```python
# Copie o arquivo completo de util/security.py
# Este arquivo contém:
# - criar_hash_senha(): Cria hash bcrypt
# - verificar_senha(): Valida senha
# - gerar_token(): Gera tokens únicos
# - validar_forca_senha(): Valida complexidade
```

#### 📁 `/util/auth_decorator.py`
Decorator para proteger rotas:
```python
# Copie o arquivo completo de util/auth_decorator.py
# Este arquivo contém:
# - requer_autenticacao(): Decorator para proteger rotas
# - obter_usuario_logado(): Obtém dados do usuário da sessão
# - criar_sessao(): Cria sessão para usuário
```

### Passo 2: Configurar SessionMiddleware

No seu arquivo `main.py`, adicione:

```python
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
```

### Passo 3: Criar Models

#### 📁 `/model/usuario_model.py`
```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class Usuario:
    id: int
    nome: str
    email: str
    senha: str
    perfil: str = 'cliente'
    foto: Optional[str] = None
    token_redefinicao: Optional[str] = None
    data_token: Optional[str] = None
    data_cadastro: Optional[str] = None
```

### Passo 4: Criar Repository

#### 📁 `/repo/usuario_repo.py`
Copie as seguintes funções essenciais:
- `inserir()`: Cadastra novo usuário
- `obter_por_email()`: Busca por email
- `obter_por_id()`: Busca por ID
- `atualizar_senha()`: Atualiza senha
- `obter_todos_por_perfil()`: Lista por perfil

### Passo 5: Implementar Rotas de Autenticação

#### 📁 `/routes/auth_routes.py`

**Rota de Login:**
```python
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
```

**Rota de Logout:**
```python
@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status.HTTP_303_SEE_OTHER)
```

**Rota de Cadastro:**
```python
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
```

### Passo 6: Proteger Rotas

Use o decorator `@requer_autenticacao()` para proteger suas rotas:

```python
from util.auth_decorator import requer_autenticacao

# Rota acessível apenas para usuários logados
@router.get("/perfil")
@requer_autenticacao()
async def get_perfil(request: Request, usuario_logado: dict = None):
    # usuario_logado contém os dados do usuário
    return templates.TemplateResponse(
        "perfil.html",
        {"request": request, "usuario": usuario_logado}
    )

# Rota apenas para administradores
@router.get("/admin/dashboard")
@requer_autenticacao(["admin"])
async def get_admin_dashboard(request: Request, usuario_logado: dict = None):
    return templates.TemplateResponse(
        "admin_dashboard.html",
        {"request": request}
    )

# Rota para múltiplos perfis
@router.get("/relatorios")
@requer_autenticacao(["admin", "gerente"])
async def get_relatorios(request: Request, usuario_logado: dict = None):
    return templates.TemplateResponse(
        "relatorios.html",
        {"request": request}
    )
```

### Passo 7: Templates HTML

#### 📁 `/templates/auth/login.html`
```html
{% extends "base.html" %}
{% block conteudo %}
<div class="container mt-5">
    <div class="row justify-content-center">
        <div class="col-md-6">
            <h2>Login</h2>
            
            {% if erro %}
            <div class="alert alert-danger">{{ erro }}</div>
            {% endif %}
            
            <form method="post" action="/login">
                {% if redirect %}
                <input type="hidden" name="redirect" value="{{ redirect }}">
                {% endif %}
                
                <div class="mb-3">
                    <label for="email" class="form-label">E-mail</label>
                    <input type="email" class="form-control" id="email" 
                           name="email" required>
                </div>
                
                <div class="mb-3">
                    <label for="senha" class="form-label">Senha</label>
                    <input type="password" class="form-control" id="senha" 
                           name="senha" required>
                </div>
                
                <button type="submit" class="btn btn-primary">Entrar</button>
                <a href="/esqueci-senha" class="btn btn-link">Esqueci minha senha</a>
            </form>
        </div>
    </div>
</div>
{% endblock %}
```

#### 📁 Menu Dinâmico no `/templates/base.html`
```html
<!-- Menu para usuário logado -->
{% if request.session.get('usuario') %}
    <!-- Menu Admin -->
    {% if request.session.get('usuario').perfil == 'admin' %}
    <li class="nav-item dropdown">
        <a class="nav-link dropdown-toggle" href="#" data-bs-toggle="dropdown">
            Administrar
        </a>
        <ul class="dropdown-menu">
            <li><a class="dropdown-item" href="/admin/usuarios">Usuários</a></li>
            <li><a class="dropdown-item" href="/admin/relatorios">Relatórios</a></li>
        </ul>
    </li>
    {% endif %}
    
    <!-- Menu do Usuário -->
    <li class="nav-item dropdown">
        <a class="nav-link dropdown-toggle" href="#" data-bs-toggle="dropdown">
            {{ request.session.get('usuario').nome }}
        </a>
        <ul class="dropdown-menu">
            <li><a class="dropdown-item" href="/perfil">Meu Perfil</a></li>
            <li><hr class="dropdown-divider"></li>
            <li><a class="dropdown-item" href="/logout">Sair</a></li>
        </ul>
    </li>
{% else %}
    <!-- Menu para não logados -->
    <a class="nav-link" href="/login">Login</a>
    <a class="nav-link" href="/cadastro">Cadastre-se</a>
{% endif %}
```

## 💡 Como Usar

### 1. Criar Admin Padrão

Crie um script para inserir o primeiro administrador:

```python
# criar_admin.py
from util.security import criar_hash_senha
from repo import usuario_repo
from model.usuario_model import Usuario

def criar_admin_padrao():
    # Verificar se já existe admin
    admins = usuario_repo.obter_todos_por_perfil("admin")
    if not admins:
        senha_hash = criar_hash_senha("admin123")
        admin = Usuario(
            id=0,
            nome="Administrador",
            email="admin@admin.com",
            senha=senha_hash,
            perfil="admin"
        )
        usuario_repo.inserir(admin)
        print("Admin criado: admin@admin.com / admin123")

if __name__ == "__main__":
    criar_admin_padrao()
```

### 2. Registrar Rotas no main.py

```python
from routes import auth_routes, perfil_routes

# Registrar rotas de autenticação
app.include_router(auth_routes.router)
app.include_router(perfil_routes.router)
```

## 📚 Exemplos Práticos

### Exemplo 1: Página Apenas para Clientes Logados

```python
@router.get("/meus-pedidos")
@requer_autenticacao(["cliente"])
async def get_meus_pedidos(request: Request, usuario_logado: dict = None):
    pedidos = pedido_repo.obter_por_cliente(usuario_logado['id'])
    return templates.TemplateResponse(
        "meus_pedidos.html",
        {"request": request, "pedidos": pedidos}
    )
```

### Exemplo 2: Obter Usuário Logado em Qualquer Rota

```python
from util.auth_decorator import obter_usuario_logado

@router.get("/")
async def home(request: Request):
    usuario = obter_usuario_logado(request)
    
    if usuario:
        mensagem = f"Olá, {usuario['nome']}!"
    else:
        mensagem = "Bem-vindo, visitante!"
    
    return templates.TemplateResponse(
        "home.html",
        {"request": request, "mensagem": mensagem}
    )
```

### Exemplo 3: Verificar Perfil Dentro da Função

```python
@router.post("/produto/excluir/{id}")
@requer_autenticacao()
async def excluir_produto(id: int, usuario_logado: dict = None):
    # Verificar permissão adicional
    if usuario_logado['perfil'] != 'admin':
        raise HTTPException(403, "Apenas admins podem excluir produtos")
    
    produto_repo.excluir(id)
    return RedirectResponse("/produtos", status.HTTP_303_SEE_OTHER)
```

## 🔧 Troubleshooting

### Erro: "No module named 'itsdangerous'"
**Solução:** Instale a dependência:
```bash
pip install itsdangerous
```

### Erro: "'dict object' has no attribute 'session'"
**Solução:** Certifique-se de passar `request` real, não um dicionário vazio:
```python
# ❌ Errado
templates.TemplateResponse("page.html", {"request": {}})

# ✅ Correto
templates.TemplateResponse("page.html", {"request": request})
```

### Erro: "Usuario.__init__() got an unexpected keyword argument"
**Solução:** Verifique se o modelo Usuario tem todos os campos necessários:
```python
@dataclass
class Usuario:
    id: int
    nome: str
    email: str
    senha: str
    perfil: str = 'cliente'
    foto: Optional[str] = None
    token_redefinicao: Optional[str] = None
    data_token: Optional[str] = None
    data_cadastro: Optional[str] = None  # Este campo é importante!
```

### Erro: Rota protegida não redireciona para login
**Solução:** Verifique se:
1. SessionMiddleware está configurado no main.py
2. O decorator está antes da função: `@requer_autenticacao()`
3. A função recebe `usuario_logado` como parâmetro

## 🎉 Pronto!

Com estes passos, você terá um sistema completo de autenticação e autorização funcionando em sua aplicação FastAPI!

### Checklist Final:
- [ ] Dependências instaladas
- [ ] Banco de dados com tabela usuario
- [ ] SessionMiddleware configurado
- [ ] Arquivos de util/ copiados
- [ ] Rotas de auth implementadas
- [ ] Templates de login/cadastro criados
- [ ] Admin padrão criado
- [ ] Rotas protegidas com decorator

## 📞 Suporte

Em caso de dúvidas, consulte o código completo no repositório do projeto ou entre em contato com o professor.

---

**Desenvolvido para o curso de Programação para a Web do Ifes Cachoeiro** 🚀