from pydantic import BaseModel, EmailStr, field_validator, ValidationError


class CadastroClienteDTO(BaseModel):
    """DTO para cadastro de cliente com validações"""
    nome: str
    email: EmailStr
    senha: str
    senha_confirm: str

    @field_validator('nome')
    @classmethod
    def validar_nome(cls, nome):
        if not nome.strip():
            raise ValueError('Nome é obrigatório.')
        if len(nome.strip()) < 3:
            raise ValueError('Nome deve ter pelo menos 3 caracteres.')
        if len(nome.strip()) > 100:
            raise ValueError('Nome deve ter no máximo 100 caracteres.')
        return nome.strip()

    @field_validator('senha')
    @classmethod
    def validar_senha(cls, senha):
        if not senha:
            raise ValueError('Senha é obrigatória.')
        if len(senha) < 6:
            raise ValueError('Senha deve ter pelo menos 6 caracteres.')
        if len(senha) > 50:
            raise ValueError('Senha deve ter no máximo 50 caracteres.')
        return senha

    @field_validator('senha_confirm')
    @classmethod
    def validar_senha_confirm(cls, senha_confirm, values):
        senha = values.get('senha')
        if senha_confirm != senha:
            raise ValueError('As senhas não coincidem.')
        return senha_confirm
