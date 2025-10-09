from pydantic import BaseModel, EmailStr, field_validator, model_validator
from typing import Dict


class CadastroClienteDTO(BaseModel):
    """DTO para cadastro de cliente com validações completas"""
    nome: str
    email: EmailStr
    senha: str
    senha_confirm: str

    @field_validator('nome')
    @classmethod
    def validar_nome(cls, nome):
        nome = nome.strip()
        if not nome:
            raise ValueError('Nome é obrigatório.')
        if len(nome) < 3:
            raise ValueError('Nome deve ter pelo menos 3 caracteres.')
        if len(nome) > 100:
            raise ValueError('Nome deve ter no máximo 100 caracteres.')
        return nome

    @field_validator('senha')
    @classmethod
    def validar_senha(cls, senha):
        if not senha:
            raise ValueError('Senha é obrigatória.')
        if len(senha) < 6:
            raise ValueError('Senha deve ter pelo menos 6 caracteres.')
        if len(senha) > 50:
            raise ValueError('Senha deve ter no máximo 50 caracteres.')
        if ' ' in senha:
            raise ValueError('Senha não pode conter espaços.')
        return senha

    @model_validator(mode='after')
    def validar_senhas_coincidem(self):
        """Valida se as senhas coincidem após todos os campos serem validados"""
        if self.senha != self.senha_confirm:
            raise ValueError('As senhas não coincidem.')
        return self


def validar_cadastro_cliente(data: dict) -> tuple[CadastroClienteDTO | None, Dict[str, str] | None]:
    """
    Valida dados do cadastro de cliente e retorna TODOS os erros de uma vez
    Valida campo por campo para capturar múltiplos erros simultaneamente
    
    Returns:
        tuple: (dto_validado, dicionário_de_erros)
               Se válido: (dto, None)
               Se inválido: (None, {'campo': 'mensagem', ...})
    """
    erros = {}
    
    # Validar campo por campo manualmente para capturar TODOS os erros
    
    # 1. VALIDAR NOME
    nome = data.get('nome', '').strip()
    if not nome:
        erros['nome'] = 'Nome é obrigatório.'
    elif len(nome) < 3:
        erros['nome'] = 'Nome deve ter pelo menos 3 caracteres.'
    elif len(nome) > 100:
        erros['nome'] = 'Nome deve ter no máximo 100 caracteres.'
    
    # 2. VALIDAR EMAIL
    email = data.get('email', '').strip().lower()
    if not email:
        erros['email'] = 'Email é obrigatório.'
    elif '@' not in email or '.' not in email:
        erros['email'] = 'Email inválido. Use o formato: seu@email.com'
    else:
        partes = email.split('@')
        if len(partes) != 2 or not partes[0] or not partes[1] or '.' not in partes[1]:
            erros['email'] = 'Email inválido. Use o formato: seu@email.com'
    
    # 3. VALIDAR SENHA
    senha = data.get('senha', '')
    if not senha:
        erros['senha'] = 'Senha é obrigatória.'
    elif len(senha) < 6:
        erros['senha'] = 'Senha deve ter pelo menos 6 caracteres.'
    elif len(senha) > 50:
        erros['senha'] = 'Senha deve ter no máximo 50 caracteres.'
    elif ' ' in senha:
        erros['senha'] = 'Senha não pode conter espaços.'
    
    # 4. VALIDAR CONFIRMAÇÃO DE SENHA
    senha_confirm = data.get('senha_confirm', '')
    if not senha_confirm:
        erros['senha_confirm'] = 'Confirmação de senha é obrigatória.'
    elif senha and senha_confirm and senha != senha_confirm:
        erros['senha_confirm'] = 'As senhas não coincidem.'
    
    # Se houver erros, retornar
    if erros:
        return None, erros
    
    # Se não houver erros, criar o DTO (já validado)
    try:
        dto = CadastroClienteDTO(**data)
        return dto, None
    except Exception as e:
        # Fallback: se mesmo assim der erro, capturar
        erros['geral'] = 'Erro ao processar dados. Verifique os campos.'
        return None, erros