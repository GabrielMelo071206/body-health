# startup.py - Script de inicialização do Body Health
"""
Script para configurar e inicializar o sistema Body Health
- Verifica dependências
- Configura banco de dados
- Testa serviço de email
- Cria usuário admin se necessário
"""

import sys
import os
import subprocess
from pathlib import Path

def verificar_dependencias():
    """Verifica se todas as dependências estão instaladas"""
    print("🔍 Verificando dependências...")
    
    try:
        import fastapi
        import uvicorn
        import jinja2
        import passlib
        import sqlite3
        print("✅ Dependências básicas encontradas")
        return True
    except ImportError as e:
        print(f"❌ Dependência faltando: {e}")
        print("💡 Execute: pip install -r requirements.txt")
        return False

def verificar_estrutura_diretorios():
    """Verifica e cria diretórios necessários"""
    print("📁 Verificando estrutura de diretórios...")
    
    diretorios = [
        "static",
        "static/uploads", 
        "static/uploads/profissionais",
        "templates",
        "templates/admin",
        "templates/inicio",
        "data",
        "util"
    ]
    
    for diretorio in diretorios:
        path = Path(diretorio)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            print(f"📂 Criado: {diretorio}")
        else:
            print(f"✅ Existe: {diretorio}")

def inicializar_banco():
    """Inicializa banco de dados se necessário"""
    print("🗄️ Verificando banco de dados...")
    
    try:
        from data.repo import usuario_repo, plano_repo
        
        # Verificar se há usuários
        usuarios = usuario_repo.obter_todos()
        print(f"📊 Usuários existentes: {len(usuarios)}")
        
        # Verificar se há planos
        planos = plano_repo.obter_todos()
        print(f"📋 Planos existentes: {len(planos)}")
        
        return True
    except Exception as e:
        print(f"❌ Erro no banco: {e}")
        return False

def criar_admin_se_necessario():
    """Cria usuário admin se não existir"""
    print("👤 Verificando usuário administrador...")
    
    try:
        from util.criar_admin import criar_admin_padrao
        
        if criar_admin_padrao():
            print("✅ Usuário admin criado com sucesso!")
            print("📧 Email: admin@admin.com")
            print("🔐 Senha: admin123")
            print("⚠️ IMPORTANTE: Altere a senha após o primeiro login!")
        else:
            print("ℹ️ Usuário admin já existe")
        
        return True
    except Exception as e:
        print(f"❌ Erro ao criar admin: {e}")
        return False

def testar_email_service():
    """Testa o serviço de email"""
    print("📧 Testando serviço de email...")
    
    try:
        from util.email_service import email_service
        
        if email_service.testar_conexao():
            print("✅ Serviço de email configurado corretamente!")
            print(f"📮 Servidor: {email_service.smtp_server}:{email_service.smtp_port}")
            print(f"📧 Email: {email_service.email}")
            return True
        else:
            print("⚠️ Problema na configuração do email")
            print("💡 Verifique o código de app no arquivo util/email_service.py")
            return False
            
    except Exception as e:
        print(f"❌ Erro no serviço de email: {e}")
        return False

def criar_arquivo_env():
    """Cria arquivo .env se não existir"""
    print("⚙️ Verificando arquivo de configuração...")
    
    env_path = Path(".env")
    if not env_path.exists():
        env_content = """# .env - Configurações do Body Health
# IMPORTANTE: Não commit este arquivo no Git (adicione ao .gitignore)

# Configurações de Email
BODY_HEALTH_EMAIL=bodyhealth619@gmail.com
BODY_HEALTH_APP_PASSWORD=mlsn.db4526ae6121f8b073ce1e4114eec60fdfb114fe5943921ce62290543f6a4666

# Configurações do Sistema
DEBUG=True
SECRET_KEY=sua_chave_secreta_aqui

# Configurações de Upload
MAX_FILE_SIZE=5242880  # 5MB em bytes
UPLOAD_PATH=static/uploads

# URLs de Redirecionamento
LOGIN_REDIRECT_URL=/dashboard
LOGOUT_REDIRECT_URL=/
"""
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(env_content)
        print("✅ Arquivo .env criado")
    else:
        print("ℹ️ Arquivo .env já existe")

def verificar_gitignore():
    """Verifica e atualiza .gitignore"""
    print("📝 Verificando .gitignore...")
    
    gitignore_path = Path(".gitignore")
    gitignore_content = """# Body Health - Arquivos a ignorar
.env
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so
.DS_Store
dados.db
static/uploads/profissionais/*
!static/uploads/profissionais/.gitkeep
.vscode/
.idea/
*.log
"""
    
    if not gitignore_path.exists():
        with open(gitignore_path, 'w', encoding='utf-8') as f:
            f.write(gitignore_content)
        print("✅ Arquivo .gitignore criado")
    else:
        print("ℹ️ Arquivo .gitignore já existe")

def main():
    """Função principal de inicialização"""
    print("🚀 BODY HEALTH - INICIALIZAÇÃO DO SISTEMA")
    print("=" * 50)
    
    # Lista de verificações
    verificacoes = [
        ("Dependências", verificar_dependencias),
        ("Estrutura de Diretórios", verificar_estrutura_diretorios),
        ("Banco de Dados", inicializar_banco),
        ("Usuário Admin", criar_admin_se_necessario),
        ("Serviço de Email", testar_email_service),
        ("Arquivo .env", criar_arquivo_env),
        ("GitIgnore", verificar_gitignore)
    ]
    
    resultados = []
    
    for nome, funcao in verificacoes:
        print(f"\n🔧 {nome}:")
        try:
            resultado = funcao()
            resultados.append((nome, resultado))
        except Exception as e:
            print(f"❌ Erro crítico em {nome}: {e}")
            resultados.append((nome, False))
    
    # Relatório final
    print("\n" + "=" * 50)
    print("📊 RELATÓRIO FINAL:")
    print("=" * 50)
    
    sucessos = 0
    for nome, resultado in resultados:
        status = "✅ OK" if resultado else "❌ ERRO"
        print(f"{status:8} | {nome}")
        if resultado:
            sucessos += 1
    
    print(f"\n📈 Sucessos: {sucessos}/{len(resultados)}")
    
    if sucessos == len(resultados):
        print("\n🎉 SISTEMA PRONTO PARA USO!")
        print("\n🚀 Para iniciar:")
        print("   python main.py")
        print("\n🌐 Acesse: http://localhost:8000")
        print("👤 Admin: admin@admin.com | admin123")
    else:
        print("\n⚠️ ALGUNS PROBLEMAS ENCONTRADOS")
        print("   Verifique os erros acima antes de continuar")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()