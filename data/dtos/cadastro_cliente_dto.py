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
    Valida dados do cadastro de cliente e retorna todos os erros de uma vez
    
    Returns:
        tuple: (dto_validado, dicionário_de_erros)
               Se válido: (dto, None)
               Se inválido: (None, {'campo': 'mensagem', ...})
    """
    erros = {}
    
    try:
        dto = CadastroClienteDTO(**data)
        return dto, None
    except Exception as e:
        # Capturar erros do Pydantic
        if hasattr(e, 'errors'):
            for erro in e.errors():
                # Pegar o nome do campo
                campo = erro['loc'][-1] if erro['loc'] else 'geral'
                
                # Pegar a mensagem de erro
                mensagem = erro['msg']
                
                # Se for erro customizado do ValueError, usar a mensagem
                if 'value_error' in erro['type'] or 'assertion_error' in erro['type']:
                    if 'ctx' in erro and 'error' in erro['ctx']:
                        mensagem = str(erro['ctx']['error'])
                    elif isinstance(erro.get('ctx'), dict) and 'error' in erro['ctx']:
                        mensagem = str(erro['ctx']['error'])
                
                # Formatar mensagens padrão do Pydantic
                if 'valid email' in mensagem.lower():
                    mensagem = 'Email inválido. Use o formato: seu@email.com'
                elif 'field required' in mensagem.lower():
                    mensagem = f'{campo.capitalize()} é obrigatório.'
                
                erros[str(campo)] = mensagem
        else:
            # Erro genérico
            erros['geral'] = str(e)
        
        return None, erros