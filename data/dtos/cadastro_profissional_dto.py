from pydantic import BaseModel, EmailStr, field_validator, model_validator
from typing import Dict, Optional
import re


class CadastroProfissionalDTO(BaseModel):
    """DTO para cadastro de profissional com validações completas"""
    nome: str
    email: EmailStr
    senha: str
    senha_confirm: str
    especialidade: str
    registro_profissional: Optional[str] = None
    cpf_cnpj: str

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
        senha_limpa = senha.strip()
        if len(senha_limpa) < 6:
            raise ValueError('Senha deve ter pelo menos 6 caracteres.')
        if len(senha_limpa) > 50:
            raise ValueError('Senha deve ter no máximo 50 caracteres.')
        if ' ' in senha:
            raise ValueError('Senha não pode conter espaços.')
        return senha

    @field_validator('especialidade')
    @classmethod
    def validar_especialidade(cls, esp):
        esp = esp.strip()
        opcoes = [
            "Personal Trainer", "Nutricionista", "Fisioterapeuta",
            "Educador Físico", "Médico do Esporte", "Psicólogo do Esporte", "Outro"
        ]
        if esp not in opcoes:
            raise ValueError(f'Especialidade inválida. Escolha uma das opções: {", ".join(opcoes)}')
        return esp

    @field_validator('cpf_cnpj')
    @classmethod
    def validar_cpf_cnpj(cls, valor):
        if not valor:
            raise ValueError('CPF ou CNPJ é obrigatório.')
        
        # Remover formatação
        valor_limpo = re.sub(r'\D', '', valor)
        
        if len(valor_limpo) == 11:
            if not cls._validar_cpf(valor_limpo):
                raise ValueError('CPF inválido. Verifique os números digitados.')
        elif len(valor_limpo) == 14:
            if not cls._validar_cnpj(valor_limpo):
                raise ValueError('CNPJ inválido. Verifique os números digitados.')
        else:
            raise ValueError('CPF deve ter 11 dígitos ou CNPJ deve ter 14 dígitos.')
        
        return valor_limpo

    @model_validator(mode='after')
    def validar_senhas_coincidem(self):
        """Valida se as senhas coincidem"""
        if self.senha != self.senha_confirm:
            raise ValueError('As senhas não coincidem.')
        return self

    @staticmethod
    def _validar_cpf(cpf: str) -> bool:
        """Valida CPF com algoritmo oficial"""
        if len(cpf) != 11 or cpf == cpf[0] * 11:
            return False
        
        # Validar primeiro dígito
        soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
        resto = (soma * 10) % 11
        resto = 0 if resto == 10 else resto
        if resto != int(cpf[9]):
            return False
        
        # Validar segundo dígito
        soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
        resto = (soma * 10) % 11
        resto = 0 if resto == 10 else resto
        return resto == int(cpf[10])

    @staticmethod
    def _validar_cnpj(cnpj: str) -> bool:
        """Valida CNPJ com algoritmo oficial"""
        if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
            return False
        
        # Validar primeiro dígito
        pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = sum(int(cnpj[i]) * pesos1[i] for i in range(12))
        resto = soma % 11
        dv1 = 0 if resto < 2 else 11 - resto
        
        # Validar segundo dígito
        pesos2 = [6] + pesos1
        soma = sum(int(cnpj[i]) * pesos2[i] for i in range(13))
        resto = soma % 11
        dv2 = 0 if resto < 2 else 11 - resto
        
        return dv1 == int(cnpj[12]) and dv2 == int(cnpj[13])


def validar_cadastro_profissional(data: dict) -> tuple[CadastroProfissionalDTO | None, Dict[str, str] | None]:
    """
    Valida dados do cadastro profissional e retorna todos os erros de uma vez
    
    Returns:
        tuple: (dto_validado, dicionário_de_erros)
               Se válido: (dto, None)
               Se inválido: (None, {'campo': 'mensagem', ...})
    """
    erros = {}
    
    try:
        dto = CadastroProfissionalDTO(**data)
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
                if 'valid email' in mensagem.lower():
                    mensagem = 'Email inválido. Use o formato: seu@email.com'
                elif 'field required' in mensagem.lower():
                    mensagem = f'{campo.capitalize()} é obrigatório.'
                
                erros[str(campo)] = mensagem
        else:
            # Erro genérico
            erros['geral'] = str(e)
        
        return None, erros


def validar_foto_registro(arquivo) -> tuple[bool, str | None]:
    """
    Valida arquivo de foto do registro
    
    Returns:
        tuple: (sucesso, mensagem_de_erro)
    """
    if not arquivo or not arquivo.filename:
        return False, 'Foto do registro é obrigatória.'
    
    # Validar tipo de arquivo
    if arquivo.content_type not in ['image/jpeg', 'image/png', 'image/jpg']:
        return False, 'Apenas arquivos JPG ou PNG são permitidos.'
    
    # Validar tamanho (5MB)
    try:
        arquivo.file.seek(0, 2)  # Move para o final
        tamanho = arquivo.file.tell()
        arquivo.file.seek(0)  # Volta para o início
        
        if tamanho > 5 * 1024 * 1024:
            return False, 'Arquivo muito grande. Tamanho máximo: 5MB.'
    except Exception:
        return False, 'Erro ao validar arquivo. Tente novamente.'
    
    return True, None