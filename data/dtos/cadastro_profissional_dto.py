from pydantic import BaseModel, field_validator, EmailStr
from typing import Optional


class CadastroProfissionalDTO(BaseModel):
    """DTO para cadastro de profissional com validações"""
    nome: str
    email: EmailStr
    senha: str
    especialidade: str
    registro_profissional: Optional[str] = None
    cpf_cnpj: str
    
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
        # EmailStr já valida o formato
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
    
    @field_validator('especialidade')
    @classmethod
    def validate_especialidade(cls, especialidade):
        if not especialidade or not especialidade.strip():
            raise ValueError('Especialidade é obrigatória.')
        
        especialidades_validas = [
            'Personal Trainer',
            'Nutricionista',
            'Fisioterapeuta',
            'Educador Físico',
            'Médico do Esporte',
            'Psicólogo do Esporte',
            'Outro'
        ]
        
        if especialidade not in especialidades_validas:
            raise ValueError('Especialidade inválida.')
        
        return especialidade
    
    @field_validator('registro_profissional')
    @classmethod
    def validate_registro_profissional(cls, registro):
        # Campo opcional, mas se preenchido, deve ter no mínimo 3 caracteres
        if registro and len(registro.strip()) < 3:
            raise ValueError('Registro profissional deve ter pelo menos 3 caracteres.')
        if registro and len(registro.strip()) > 50:
            raise ValueError('Registro profissional deve ter no máximo 50 caracteres.')
        return registro.strip() if registro else None
    
    @field_validator('cpf_cnpj')
    @classmethod
    def validate_cpf_cnpj(cls, cpf_cnpj):
        if not cpf_cnpj or not cpf_cnpj.strip():
            raise ValueError('CPF/CNPJ é obrigatório.')
        
        # Remove caracteres não numéricos
        apenas_numeros = ''.join(filter(str.isdigit, cpf_cnpj))
        
        # Verifica se tem 11 (CPF) ou 14 (CNPJ) dígitos
        if len(apenas_numeros) not in [11, 14]:
            raise ValueError('CPF deve ter 11 dígitos ou CNPJ deve ter 14 dígitos.')
        
        # Verifica se não são todos números iguais (ex: 111.111.111-11)
        if len(set(apenas_numeros)) == 1:
            raise ValueError('CPF/CNPJ inválido.')
        
        return cpf_cnpj.strip()