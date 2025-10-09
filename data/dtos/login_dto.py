from pydantic import BaseModel, field_validator
from typing import Dict


class LoginDTO(BaseModel):
    """DTO para login com validações"""
    email: str
    senha: str
    
    @field_validator('email')
    @classmethod
    def validar_email(cls, email):
        if not email or not email.strip():
            raise ValueError('Email é obrigatório.')
        
        email = email.strip().lower()
        
        if '@' not in email or '.' not in email:
            raise ValueError('Email inválido. Use o formato: seu@email.com')
        
        # Validação básica de formato
        partes = email.split('@')
        if len(partes) != 2 or not partes[0] or not partes[1]:
            raise ValueError('Email inválido. Use o formato: seu@email.com')
        
        if '.' not in partes[1]:
            raise ValueError('Email inválido. Use o formato: seu@email.com')
        
        return email

    @field_validator('senha')
    @classmethod
    def validar_senha(cls, senha):
        if not senha:
            raise ValueError('Senha é obrigatória.')
        if len(senha) < 6:
            raise ValueError('Senha deve ter pelo menos 6 caracteres.')
        return senha


def validar_login(data: dict) -> tuple[LoginDTO | None, Dict[str, str] | None]:
    """
    Valida dados de login e retorna TODOS os erros de uma vez
    
    Returns:
        tuple: (dto_validado, dicionário_de_erros)
               Se válido: (dto, None)
               Se inválido: (None, {'campo': 'mensagem', ...})
    """
    erros = {}
    
    # Validar campo por campo manualmente
    
    # 1. VALIDAR EMAIL
    email = data.get('email', '').strip().lower()
    if not email:
        erros['email'] = 'Email é obrigatório.'
    elif '@' not in email or '.' not in email:
        erros['email'] = 'Email inválido. Use o formato: seu@email.com'
    else:
        partes = email.split('@')
        if len(partes) != 2 or not partes[0] or not partes[1] or '.' not in partes[1]:
            erros['email'] = 'Email inválido. Use o formato: seu@email.com'
    
    # 2. VALIDAR SENHA
    senha = data.get('senha', '')
    if not senha:
        erros['senha'] = 'Senha é obrigatória.'
    elif len(senha) < 6:
        erros['senha'] = 'Senha deve ter pelo menos 6 caracteres.'
    
    # Se houver erros, retornar
    if erros:
        return None, erros
    
    # Se não houver erros, criar o DTO
    try:
        dto = LoginDTO(**data)
        return dto, None
    except Exception as e:
        erros['geral'] = 'Erro ao processar dados. Verifique os campos.'
        return None, erros
