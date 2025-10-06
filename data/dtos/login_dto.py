from pydantic import BaseModel, field_validator


class LoginDTO(BaseModel):
    email: str
    senha: str
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, email):
        if  not  email:
            raise ValueError('Email é obrigatório.')
        if '@' not in email or '.' not in email:
            raise ValueError('Email inválido.')
        return email


    @field_validator('senha')
    @classmethod
    def validate_senha(cls, senha):
        if not senha:
            raise ValueError('Senha é obrigatória.')
        if len(senha) < 6:
            raise ValueError('Senha deve ter pelo menos 6 caracteres.')
        return senha