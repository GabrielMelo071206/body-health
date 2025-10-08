# data/dtos/cadastro_cliente_dto.py
from pydantic import BaseModel, field_validator, EmailStr
from typing import Optional


class CadastroClienteDTO(BaseModel):
    """DTO para cadastro de cliente com validações"""
    nome: str
    email: EmailStr  # Valida formato de email automaticamente
    senha: str
    
    @field_validator('nome')
    @classmethod
    def validate_nome(cls, nome):
        if not nome or not nome.strip():
            raise ValueError('Nome é obrigatório.')
        if len(nome.strip()) < 3:
            raise ValueError('Nome deve ter pelo menos 3 caracteres.')
        if len(nome.strip()) > 100:
            raise ValueError('Nome deve ter no máximo 100 caracteres.')
        return nome.strip()
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, email):
        if not email or not email.strip():
            raise ValueError('Email é obrigatório.')
        # EmailStr já valida o formato, apenas limpamos espaços
        return email.strip().lower()
    
    @field_validator('senha')
    @classmethod
    def validate_senha(cls, senha):
        if not senha:
            raise ValueError('Senha é obrigatória.')
        if len(senha) < 6:
            raise ValueError('Senha deve ter pelo menos 6 caracteres.')
        if len(senha) > 50:
            raise ValueError('Senha deve ter no máximo 50 caracteres.')
        return senha