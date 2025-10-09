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
    Valida dados de login e retorna todos os erros de uma vez
    
    Returns:
        tuple: (dto_validado, dicionário_de_erros)
               Se válido: (dto, None)
               Se inválido: (None, {'campo': 'mensagem', ...})
    """
    erros = {}
    
    try:
        dto = LoginDTO(**data)
        return dto, None
    except Exception as e:
        # Capturar erros do Pydantic
        if hasattr(e, 'errors'):
            for erro in e.errors():
                # Pegar o nome do campo
                campo = erro['loc'][-1] if erro['loc'] else 'geral'
                
                # Pegar a mensagem de erro
                mensagem = erro['msg']
                
                # Se for erro customizado, extrair mensagem
                if 'value_error' in erro['type'] or 'assertion_error' in erro['type']:
                    if 'ctx' in erro and 'error' in erro['ctx']:
                        mensagem = str(erro['ctx']['error'])
                
                # Formatar mensagens padrão do Pydantic
                if 'field required' in mensagem.lower():
                    mensagem = f'{campo.capitalize()} é obrigatório.'
                
                erros[str(campo)] = mensagem
        else:
            # Erro genérico
            erros['geral'] = str(e)
        
        return None, erros