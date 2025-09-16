# criar_admin.py
from data.repo import usuario_repo
from data.model.usuario_model import Usuario  
from util.security import criar_hash_senha

def criar_admin_inicial():
    """
    Função que cria um usuário administrador inicial
    """
    
    try:
        # 1. Verifica se já existe algum admin no sistema
        admins = usuario_repo.obter_todos_por_perfil("admin")
        print(f"🔍 Verificando admins existentes... Encontrados: {len(admins)}")
        
    except Exception as e:
        print("❌ Erro ao acessar o banco de dados!")
        print(f"💡 Erro: {str(e)}")
        print("⚠️  Você precisa executar primeiro: python criar_banco.py")
        return False
    
    # 2. Se não existe admin, cria um
    if not admins:
        print("🚀 Criando primeiro administrador...")
        
        # 2.1 Criar hash seguro da senha
        senha_hash = criar_hash_senha("admin123")
        print("✅ Senha criptografada gerada")
        
        # 2.2 Criar objeto Usuario
        admin = Usuario(
            id=0,  # 0 = auto increment no banco
            nome="Administrador",
            email="admin@bodyhealth.com", 
            senha=senha_hash,  # Senha já criptografada
            perfil="admin"  # IMPORTANTE: perfil admin
        )
        
        # 2.3 Inserir no banco de dados
        admin_id = usuario_repo.inserir(admin)
        
        if admin_id:
            print("\n🎉 ADMIN CRIADO COM SUCESSO!")
            print("=" * 40)
            print("📧 Email: admin@bodyhealth.com")
            print("🔑 Senha: admin123")
            print("=" * 40)
            print("⚠️  IMPORTANTE: Altere a senha após o primeiro login!")
            print("\n🌐 Acesse: http://localhost:8000/admin")
            return True
        else:
            print("❌ Erro ao inserir admin no banco!")
            return False
    
    # 3. Se já existe admin
    else:
        print("ℹ️  ADMIN JÁ EXISTE!")
        print("=" * 40)
        for admin in admins:
            print(f"👤 Nome: {admin.nome}")
            print(f"📧 Email: {admin.email}")
        print("=" * 40)
        print("🌐 Acesse: http://localhost:8000/admin")
        return False

# Executar quando o script for chamado diretamente
if __name__ == "__main__":
    print("🔐 CRIADOR DE ADMINISTRADOR - Body Health")
    print("=" * 50)
    criar_admin_inicial()