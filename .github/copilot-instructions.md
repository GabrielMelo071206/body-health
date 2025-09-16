# Copilot Instructions for BH FastAPI Project

## Visão Geral
Este projeto é uma aplicação web de e-commerce construída com FastAPI, SQLite e Jinja2. O padrão principal é MVC, com separação clara entre modelos, repositórios, SQL e rotas. O objetivo é manter a organização e facilitar a manutenção.

## Estrutura de Diretórios
- `main.py`: Ponto de entrada, inicializa FastAPI, registra rotas e cria tabelas no banco.
- `data/model/`: Modelos de dados (dataclasses Python).
- `data/repo/`: Repositórios para operações CRUD usando SQL.
- `data/sql/`: Definições de queries SQL separadas por entidade.
- `data/`: Utilitários de banco (`db_util.py`), conexão SQLite.
- `routes/`: Rotas da API (autenticação, entidades, admin).
- `templates/`: Templates Jinja2 para frontend.
- `static/`: Arquivos estáticos (CSS, JS, imagens).
- `dados.db`: Banco SQLite.

## Padrões Arquiteturais
- **Repository Pattern**: Cada entidade tem um repositório dedicado em `data/repo/`.
- **Separação SQL**: Queries ficam em `data/sql/`, facilitando manutenção.
- **Estrutura Model-Repo-SQL-Route**: Para cada entidade, siga:
  - Modelo: `data/model/[entidade]_model.py`
  - Repositório: `data/repo/[entidade]_repo.py`
  - SQL: `data/sql/[entidade]_sql.py`
  - Rotas: `routes/auth_routes.py` ou admin

## Fluxos de Desenvolvimento
- **Instalar dependências**: `pip install -r requirements.txt`
- **Rodar servidor**: `python main.py` (FastAPI com auto-reload)
- **Banco de dados**: Tabelas criadas automaticamente no startup via `criar_tabela()`
- **Debug**: Use prints/logs em repositórios e rotas para depuração rápida.

## Convenções Específicas
- Todas operações de banco usam SQL puro via sqlite3.
- Rotas públicas e admin são separadas; admin segue `/admin/{entidade}`.
- Templates admin ficam em `templates/admin/`.
- Utilitários comuns em `util/` (ex: autenticação, segurança).

## Integrações e Dependências
- **FastAPI**: Backend principal.
- **Jinja2**: Renderização de templates.
- **sqlite3**: Persistência de dados.
- **Uvicorn**: Servidor ASGI (usado implicitamente).

## Exemplos de Padrão
Para criar uma nova entidade:
1. Defina o modelo em `data/model/novaentidade_model.py`
2. Crie SQL em `data/sql/novaentidade_sql.py`
3. Implemente repositório em `data/repo/novaentidade_repo.py`
4. Adicione rotas em `routes/auth_routes.py` ou admin

## Observações
- O projeto não usa ORM, apenas SQL puro.
- O banco é inicializado automaticamente.
- Siga a estrutura Model-Repo-SQL-Route para novas entidades.

---

Se algo estiver incompleto ou pouco claro, peça exemplos ou detalhes sobre fluxos específicos para melhorar esta documentação.