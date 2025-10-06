# Manual de Implementação: Toasts e Tratamento de Erros com Pydantic

Este manual explica como implementar um sistema completo de tratamento de exceções global e exibição de toasts para erros de validação em formulários, além de preservar os valores digitados após validação falhar.

---

## 📋 Índice

1. [Visão Geral do Sistema](#visão-geral-do-sistema)
2. [Backend: Tratamento de Exceções](#backend-tratamento-de-exceções)
3. [Backend: Sistema de Flash Messages](#backend-sistema-de-flash-messages)
4. [Frontend: Sistema de Toasts](#frontend-sistema-de-toasts)
5. [Integração: Formulários com Preservação de Dados](#integração-formulários-com-preservação-de-dados)
6. [Exemplos Práticos](#exemplos-práticos)
7. [Troubleshooting](#troubleshooting)

---

## 1. Visão Geral do Sistema

### Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│                         FLUXO COMPLETO                          │
└─────────────────────────────────────────────────────────────────┘

1. Usuário submete formulário
        ↓
2. FastAPI recebe POST request
        ↓
3. Pydantic valida dados (DTO)
        ├─ Sucesso → Processa dados → Redirect com flash success
        └─ Erro → Captura ValidationError
                ↓
4. Backend extrai erros de validação
        ↓
5. Backend preserva dados do formulário
        ↓
6. Retorna template com:
   - Mensagem de erro
   - Dados originais do formulário
        ↓
7. Template renderiza:
   - Formulário com valores preenchidos
   - Toast com mensagem de erro (JavaScript)
```

### Componentes Necessários

**Backend**:
- `util/error_handlers.py` - Decorators para tratamento de erros
- `util/flash_messages.py` - Sistema de mensagens flash
- `util/exceptions.py` - Exceções customizadas
- DTOs Pydantic para validação

**Frontend**:
- `static/js/toast-manager.js` - Sistema de toasts
- `templates/components/toast-handler.html` - Handler automático
- Templates com formulários

---

## 2. Backend: Tratamento de Exceções

### 2.1. Criar Exceções Customizadas

**Arquivo**: `util/exceptions.py`

```python
"""
Exceções customizadas da aplicação
"""

class CaseBemError(Exception):
    """Exceção base para erros da aplicação"""
    def __init__(self, mensagem: str, erro_original: Exception = None):
        self.mensagem = mensagem
        self.erro_original = erro_original
        super().__init__(self.mensagem)


class ValidacaoError(CaseBemError):
    """Erro de validação de dados"""
    def __init__(self, mensagem: str, campo: str = None, valor: any = None):
        super().__init__(mensagem)
        self.campo = campo
        self.valor = valor


class RecursoNaoEncontradoError(CaseBemError):
    """Erro quando um recurso não é encontrado"""
    def __init__(self, recurso: str, identificador: any):
        mensagem = f"{recurso} não encontrado: {identificador}"
        super().__init__(mensagem)
        self.recurso = recurso
        self.identificador = identificador


class BancoDadosError(CaseBemError):
    """Erro relacionado ao banco de dados"""
    def __init__(self, mensagem: str, operacao: str, erro_original: Exception = None):
        super().__init__(mensagem, erro_original)
        self.operacao = operacao
```

### 2.2. Criar Handler de Erros para Rotas

**Arquivo**: `util/error_handlers.py`

```python
"""
Decoradores e handlers para tratamento de erros
"""

import functools
from typing import Callable, Optional
from fastapi import Request
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from util.exceptions import ValidacaoError, RecursoNaoEncontradoError, CaseBemError
from infrastructure.logging import logger
from util.flash_messages import informar_erro, informar_sucesso


def tratar_erro_rota(template_erro: Optional[str] = None,
                     redirect_erro: Optional[str] = None):
    """
    Decorador para tratar erros em rotas web

    Args:
        template_erro: Template para renderizar em caso de erro
        redirect_erro: URL para redirecionar em caso de erro

    Uso:
        @router.post("/cadastro")
        @tratar_erro_rota(template_erro="publico/cadastro.html")
        async def cadastrar(request: Request):
            # Seu código aqui
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            try:
                return await func(request, *args, **kwargs)

            except ValidationError as e:
                # Extrair primeira mensagem de erro do Pydantic
                error_msg = e.errors()[0]["msg"]
                logger.warning("Erro de validação Pydantic",
                             erro=error_msg, rota=str(request.url))

                if template_erro:
                    templates = Jinja2Templates(directory="templates")
                    return templates.TemplateResponse(template_erro, {
                        "request": request,
                        "erro": error_msg
                    })

            except ValidacaoError as e:
                logger.warning("Erro de validação customizado",
                             erro=e, rota=str(request.url))
                informar_erro(request, f"Dados inválidos: {e.mensagem}")

                if template_erro:
                    templates = Jinja2Templates(directory="templates")
                    return templates.TemplateResponse(template_erro, {
                        "request": request,
                        "erro": e.mensagem
                    })

            except RecursoNaoEncontradoError as e:
                logger.info("Recurso não encontrado", erro=e, rota=str(request.url))
                informar_erro(request, e.mensagem)

            except CaseBemError as e:
                logger.error("Erro de negócio", erro=e, rota=str(request.url))
                informar_erro(request, e.mensagem)

            except Exception as e:
                logger.error("Erro inesperado", erro=e, rota=str(request.url))
                informar_erro(request, "Erro interno. Tente novamente.")

            # Fallback para redirect ou template
            if redirect_erro:
                from fastapi.responses import RedirectResponse
                return RedirectResponse(redirect_erro)
            elif template_erro:
                templates = Jinja2Templates(directory="templates")
                return templates.TemplateResponse(template_erro, {
                    "request": request,
                    "erro": "Ocorreu um erro. Tente novamente."
                })

        return wrapper
    return decorator
```

---

## 3. Backend: Sistema de Flash Messages

### 3.1. Implementar Flash Messages

**Arquivo**: `util/flash_messages.py`

```python
"""
Sistema de mensagens flash para FastAPI
Permite enviar mensagens através de redirects usando sessões
"""

from fastapi import Request
from typing import List, Dict, Any


def flash(request: Request, message: str, type: str = "info") -> None:
    """
    Adiciona uma mensagem flash à sessão

    Args:
        request: Objeto Request do FastAPI
        message: Mensagem a ser exibida
        type: Tipo da mensagem (success, danger, warning, info, alert)
    """
    if "flash_messages" not in request.session:
        request.session["flash_messages"] = []

    request.session["flash_messages"].append({
        "text": message,
        "type": type
    })


def informar_sucesso(request: Request, message: str) -> None:
    """Adiciona mensagem de sucesso"""
    flash(request, message, "success")


def informar_erro(request: Request, message: str) -> None:
    """Adiciona mensagem de erro"""
    flash(request, message, "danger")


def informar_aviso(request: Request, message: str) -> None:
    """Adiciona mensagem de aviso"""
    flash(request, message, "warning")


def informar_info(request: Request, message: str) -> None:
    """Adiciona mensagem informativa"""
    flash(request, message, "info")


def get_flashed_messages(request: Request) -> List[Dict[str, Any]]:
    """
    Recupera e remove as mensagens flash da sessão

    Args:
        request: Objeto Request do FastAPI

    Returns:
        Lista de mensagens flash
    """
    messages = request.session.pop("flash_messages", [])
    return messages
```

### 3.2. Configurar SessionMiddleware

**Arquivo**: `main.py`

```python
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
import os

app = FastAPI()

# Configurar middleware de sessão
SECRET_KEY = os.getenv("SECRET_KEY", "sua-chave-secreta-aqui")
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    max_age=3600,  # 1 hora
    same_site="lax",
    https_only=False  # True em produção com HTTPS
)
```

---

## 4. Frontend: Sistema de Toasts

### 4.1. Criar ToastManager

**Arquivo**: `static/js/toast-manager.js`

```javascript
/**
 * Sistema de gerenciamento de toasts
 * Utiliza Bootstrap 5.3 Toast component
 */

class ToastManager {
    constructor() {
        this.container = null;
        this.init();
    }

    init() {
        if (!document.getElementById('toast-container')) {
            this.createContainer();
        }
        this.container = document.getElementById('toast-container');
    }

    createContainer() {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        container.style.marginTop = '80px';
        document.body.appendChild(container);
    }

    /**
     * Exibe um toast
     * @param {string} message - Mensagem a ser exibida
     * @param {string} type - Tipo (success, danger, warning, info, alert)
     * @param {number} duration - Duração em ms (0 = permanente)
     */
    show(message, type = 'info', duration = 5000) {
        const toast = this.createToast(message, type);
        this.container.appendChild(toast);

        const bsToast = new bootstrap.Toast(toast, {
            autohide: duration > 0,
            delay: duration
        });

        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });

        bsToast.show();
        return bsToast;
    }

    createToast(message, type) {
        const toastId = 'toast-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);

        const typeClasses = {
            'success': 'text-bg-success',
            'danger': 'text-bg-danger',
            'warning': 'text-bg-warning',
            'info': 'text-bg-info',
            'alert': 'text-bg-primary'
        };

        const typeIcons = {
            'success': '✓',
            'danger': '✕',
            'warning': '⚠',
            'info': 'ℹ',
            'alert': '!'
        };

        const bgClass = typeClasses[type] || 'text-bg-info';
        const icon = typeIcons[type] || 'ℹ';

        const toastHtml = `
            <div class="toast ${bgClass}" role="alert" aria-live="assertive" aria-atomic="true" id="${toastId}">
                <div class="toast-header">
                    <span class="me-2">${icon}</span>
                    <strong class="me-auto text-body-secondary">${this.getTypeTitle(type)}</strong>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Fechar"></button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            </div>
        `;

        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = toastHtml;
        return tempDiv.firstElementChild;
    }

    getTypeTitle(type) {
        const titles = {
            'success': 'Sucesso',
            'danger': 'Erro',
            'warning': 'Aviso',
            'info': 'Informação',
            'alert': 'Alerta'
        };
        return titles[type] || 'Notificação';
    }

    // Métodos de conveniência
    success(message, duration = 5000) {
        return this.show(message, 'success', duration);
    }

    error(message, duration = 7000) {
        return this.show(message, 'danger', duration);
    }

    warning(message, duration = 6000) {
        return this.show(message, 'warning', duration);
    }

    info(message, duration = 5000) {
        return this.show(message, 'info', duration);
    }
}

// Instância global
window.toastManager = new ToastManager();

// Funções globais para facilitar o uso
window.showToast = function(message, type = 'info', duration = 5000) {
    return window.toastManager.show(message, type, duration);
};

window.showSuccess = function(message, duration = 5000) {
    return window.toastManager.success(message, duration);
};

window.showError = function(message, duration = 7000) {
    return window.toastManager.error(message, duration);
};

window.showWarning = function(message, duration = 6000) {
    return window.toastManager.warning(message, duration);
};

window.showInfo = function(message, duration = 5000) {
    return window.toastManager.info(message, duration);
};
```

### 4.2. Criar Handler Automático de Toasts

**Arquivo**: `templates/components/toast-handler.html`

```html
<!-- Sistema automático de exibição de toasts -->
<script>
document.addEventListener('DOMContentLoaded', function() {
    // Mensagem de sucesso
    {% if sucesso %}
    window.showSuccess(`{{ sucesso|e }}`);
    {% endif %}

    // Mensagem de erro
    {% if erro %}
    window.showError(`{{ erro|e }}`);
    {% endif %}

    // Mensagem de aviso
    {% if warning %}
    window.showWarning(`{{ warning|e }}`);
    {% endif %}

    // Mensagem de informação
    {% if info %}
    window.showInfo(`{{ info|e }}`);
    {% endif %}

    // Múltiplas mensagens (array)
    {% if messages %}
    {% for message in messages %}
    window.showToast(`{{ message.text|e }}`, `{{ message.type|default("info") }}`, {{ message.duration|default(5000) }});
    {% endfor %}
    {% endif %}

    // Mensagens flash (de redirects)
    {% if flash_messages %}
    {% for flash_message in flash_messages %}
    window.showToast(`{{ flash_message.text|e }}`, `{{ flash_message.type|default("info") }}`, {{ flash_message.duration|default(5000) }});
    {% endfor %}
    {% endif %}
});
</script>
```

### 4.3. Incluir Scripts no Template Base

**Arquivo**: `templates/base.html`

```html
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <!-- ... outros imports ... -->
    <link href="/static/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <!-- Seu conteúdo aqui -->

    {% block content %}{% endblock %}

    <!-- Scripts -->
    <script src="/static/js/bootstrap.bundle.min.js"></script>
    <script src="/static/js/toast-manager.js"></script>

    <!-- Handler automático de toasts -->
    {% include 'components/toast-handler.html' %}

    {% block extra_scripts %}{% endblock %}
</body>
</html>
```

---

## 5. Integração: Formulários com Preservação de Dados

### 5.1. Criar DTO Pydantic

**Arquivo**: `dtos/usuario_dtos.py`

```python
from pydantic import BaseModel, Field, field_validator, EmailStr
from typing import Optional


class CadastroUsuarioDTO(BaseModel):
    """DTO para cadastro de usuário"""
    nome: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    senha: str = Field(..., min_length=6)
    confirmar_senha: str = Field(..., min_length=6)
    cpf: Optional[str] = Field(None, max_length=14)
    telefone: Optional[str] = Field(None, max_length=15)

    @field_validator('senha')
    @classmethod
    def validar_senha_forte(cls, v):
        if len(v) < 6:
            raise ValueError('Senha deve ter no mínimo 6 caracteres')
        if not any(c.isdigit() for c in v):
            raise ValueError('Senha deve conter pelo menos um número')
        return v

    @field_validator('confirmar_senha')
    @classmethod
    def senhas_devem_coincidir(cls, v, info):
        if 'senha' in info.data and v != info.data['senha']:
            raise ValueError('As senhas não coincidem')
        return v
```

### 5.2. Implementar Rota com Tratamento de Erros

**Arquivo**: `routes/usuario_routes.py`

```python
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from dtos.usuario_dtos import CadastroUsuarioDTO
from core.services.usuario_service import usuario_service
from util.flash_messages import informar_sucesso, informar_erro
from infrastructure.logging import logger

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/cadastro")
async def exibir_formulario_cadastro(request: Request):
    """Exibe formulário de cadastro"""
    return templates.TemplateResponse("publico/cadastro.html", {
        "request": request,
        "dados": None  # Primeira vez, sem dados
    })


@router.post("/cadastro")
async def processar_cadastro(
    request: Request,
    nome: str = Form(...),
    email: str = Form(...),
    senha: str = Form(...),
    confirmar_senha: str = Form(...),
    cpf: str = Form(None),
    telefone: str = Form(None)
):
    """Processa cadastro de usuário"""

    # Criar dicionário com dados do formulário (para preservar)
    dados_formulario = {
        "nome": nome,
        "email": email,
        "cpf": cpf,
        "telefone": telefone
        # Não inclua senhas aqui (segurança)
    }

    try:
        # Validar dados com Pydantic
        dados = CadastroUsuarioDTO(
            nome=nome,
            email=email,
            senha=senha,
            confirmar_senha=confirmar_senha,
            cpf=cpf,
            telefone=telefone
        )

        # Processar cadastro
        usuario_service.cadastrar(dados)

        # Sucesso - Redirecionar com mensagem flash
        informar_sucesso(request, f"Cadastro realizado com sucesso! Bem-vindo(a), {nome}!")
        return RedirectResponse("/login", status_code=303)

    except ValidationError as e:
        # Extrair mensagens de erro do Pydantic
        erros = []
        for erro in e.errors():
            campo = erro['loc'][0] if erro['loc'] else 'campo'
            mensagem = erro['msg']
            erros.append(f"{campo.capitalize()}: {mensagem}")

        erro_msg = " | ".join(erros)
        logger.warning(f"Erro de validação no cadastro: {erro_msg}")

        # Retornar template com dados preservados e erro
        return templates.TemplateResponse("publico/cadastro.html", {
            "request": request,
            "erro": erro_msg,
            "dados": dados_formulario  # Preservar dados digitados
        })

    except Exception as e:
        logger.error(f"Erro ao processar cadastro: {e}")

        return templates.TemplateResponse("publico/cadastro.html", {
            "request": request,
            "erro": "Erro ao processar cadastro. Tente novamente.",
            "dados": dados_formulario
        })
```

### 5.3. Template com Preservação de Dados

**Arquivo**: `templates/publico/cadastro.html`

```html
{% extends "base.html" %}

{% block title %}Cadastro{% endblock %}

{% block content %}
<div class="container mt-5">
    <div class="row justify-content-center">
        <div class="col-md-6">
            <h2>Cadastro de Usuário</h2>

            <form method="POST" action="/cadastro">
                <!-- Nome -->
                <div class="mb-3">
                    <label for="nome" class="form-label">Nome Completo *</label>
                    <input
                        type="text"
                        class="form-control {% if erro and 'nome' in erro.lower() %}is-invalid{% endif %}"
                        id="nome"
                        name="nome"
                        value="{{ dados.nome if dados else '' }}"
                        required
                    >
                    {% if erro and 'nome' in erro.lower() %}
                    <div class="invalid-feedback">{{ erro }}</div>
                    {% endif %}
                </div>

                <!-- Email -->
                <div class="mb-3">
                    <label for="email" class="form-label">Email *</label>
                    <input
                        type="email"
                        class="form-control {% if erro and 'email' in erro.lower() %}is-invalid{% endif %}"
                        id="email"
                        name="email"
                        value="{{ dados.email if dados else '' }}"
                        required
                    >
                    {% if erro and 'email' in erro.lower() %}
                    <div class="invalid-feedback">{{ erro }}</div>
                    {% endif %}
                </div>

                <!-- CPF -->
                <div class="mb-3">
                    <label for="cpf" class="form-label">CPF</label>
                    <input
                        type="text"
                        class="form-control {% if erro and 'cpf' in erro.lower() %}is-invalid{% endif %}"
                        id="cpf"
                        name="cpf"
                        value="{{ dados.cpf if dados else '' }}"
                        placeholder="000.000.000-00"
                    >
                </div>

                <!-- Telefone -->
                <div class="mb-3">
                    <label for="telefone" class="form-label">Telefone</label>
                    <input
                        type="text"
                        class="form-control"
                        id="telefone"
                        name="telefone"
                        value="{{ dados.telefone if dados else '' }}"
                        placeholder="(00) 00000-0000"
                    >
                </div>

                <!-- Senha -->
                <div class="mb-3">
                    <label for="senha" class="form-label">Senha *</label>
                    <input
                        type="password"
                        class="form-control {% if erro and 'senha' in erro.lower() %}is-invalid{% endif %}"
                        id="senha"
                        name="senha"
                        required
                    >
                    <small class="form-text text-muted">Mínimo 6 caracteres com pelo menos um número</small>
                    {% if erro and 'senha' in erro.lower() %}
                    <div class="invalid-feedback">{{ erro }}</div>
                    {% endif %}
                </div>

                <!-- Confirmar Senha -->
                <div class="mb-3">
                    <label for="confirmar_senha" class="form-label">Confirmar Senha *</label>
                    <input
                        type="password"
                        class="form-control {% if erro and 'confirmar' in erro.lower() %}is-invalid{% endif %}"
                        id="confirmar_senha"
                        name="confirmar_senha"
                        required
                    >
                    {% if erro and 'confirmar' in erro.lower() %}
                    <div class="invalid-feedback">{{ erro }}</div>
                    {% endif %}
                </div>

                <button type="submit" class="btn btn-primary">Cadastrar</button>
                <a href="/" class="btn btn-secondary">Cancelar</a>
            </form>
        </div>
    </div>
</div>
{% endblock %}
```

---

## 6. Exemplos Práticos

### Exemplo 1: Rota Simples com Toast de Sucesso

```python
@router.post("/item/{id}/excluir")
async def excluir_item(request: Request, id: int):
    try:
        item_service.excluir(id)
        informar_sucesso(request, "Item excluído com sucesso!")
        return RedirectResponse("/admin/itens", status_code=303)
    except Exception as e:
        logger.error(f"Erro ao excluir item: {e}")
        informar_erro(request, "Erro ao excluir item")
        return RedirectResponse("/admin/itens", status_code=303)
```

### Exemplo 2: Múltiplos Erros de Validação

```python
@router.post("/formulario-complexo")
async def processar_formulario(request: Request, ...):
    erros = []

    try:
        dados = FormularioDTO(...)
    except ValidationError as e:
        for erro in e.errors():
            campo = erro['loc'][0]
            mensagem = erro['msg']
            erros.append(f"<strong>{campo}:</strong> {mensagem}")

        erro_html = "<br>".join(erros)
        return templates.TemplateResponse("formulario.html", {
            "request": request,
            "erro": erro_html,
            "dados": dados_formulario
        })
```

### Exemplo 3: Toast Manual no Template

```html
<script>
// Exibir toast programaticamente
function confirmarExclusao(id) {
    if (confirm('Tem certeza que deseja excluir?')) {
        fetch(`/item/${id}/excluir`, { method: 'POST' })
            .then(response => {
                if (response.ok) {
                    window.showSuccess('Item excluído com sucesso!');
                    location.reload();
                } else {
                    window.showError('Erro ao excluir item');
                }
            });
    }
}
</script>
```

---

## 7. Troubleshooting

### Problema: Toasts não aparecem

**Solução**:
1. Verifique se `toast-manager.js` está carregado
2. Verifique se Bootstrap 5.3+ está carregado
3. Abra o console do navegador para ver erros JavaScript

### Problema: Dados do formulário não são preservados

**Solução**:
1. Certifique-se de passar `dados` no contexto do template
2. Verifique se os inputs têm `value="{{ dados.campo if dados else '' }}"`

### Problema: Flash messages não funcionam após redirect

**Solução**:
1. Verifique se `SessionMiddleware` está configurado em `main.py`
2. Certifique-se de que `SECRET_KEY` está definida
3. Verifique se `get_flashed_messages()` é chamado no template

### Problema: ValidationError não é capturado

**Solução**:
1. Importe `ValidationError` do Pydantic: `from pydantic import ValidationError`
2. Certifique-se de que o bloco try/except está correto

---

## 📝 Checklist de Implementação

- [ ] Criar `util/exceptions.py` com exceções customizadas
- [ ] Criar `util/error_handlers.py` com decorators
- [ ] Criar `util/flash_messages.py` com sistema de flash
- [ ] Configurar `SessionMiddleware` em `main.py`
- [ ] Criar `static/js/toast-manager.js`
- [ ] Criar `templates/components/toast-handler.html`
- [ ] Incluir scripts no template base
- [ ] Criar DTOs Pydantic para validação
- [ ] Implementar rotas com tratamento de erros
- [ ] Atualizar templates para preservar dados
- [ ] Testar fluxo completo de validação

---

## 🎯 Benefícios desta Implementação

✅ **UX Melhor**: Usuário não perde dados digitados
✅ **Feedback Visual**: Toasts claros e visíveis
✅ **Código Limpo**: Tratamento centralizado de erros
✅ **Manutenível**: Fácil adicionar novos tipos de toast
✅ **Consistente**: Mesmo padrão em toda aplicação
✅ **Acessível**: Mensagens legíveis e com ícones

---

**Última atualização**: 2025-10-01
**Versão**: 1.0
