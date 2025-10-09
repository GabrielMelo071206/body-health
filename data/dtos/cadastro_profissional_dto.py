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
            raise ValueError(f'Especialidade inválida. Escolha uma das opções válidas.')
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
    Valida dados do cadastro profissional e retorna TODOS os erros de uma vez
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
    
    # 5. VALIDAR ESPECIALIDADE
    especialidade = data.get('especialidade', '').strip()
    opcoes_validas = [
        "Personal Trainer", "Nutricionista", "Fisioterapeuta",
        "Educador Físico", "Médico do Esporte", "Psicólogo do Esporte", "Outro"
    ]
    if not especialidade:
        erros['especialidade'] = 'Especialidade é obrigatória.'
    elif especialidade not in opcoes_validas:
        erros['especialidade'] = 'Especialidade inválida. Escolha uma das opções válidas.'
    
    # 6. VALIDAR CPF/CNPJ
    cpf_cnpj = data.get('cpf_cnpj', '')
    if not cpf_cnpj:
        erros['cpf_cnpj'] = 'CPF ou CNPJ é obrigatório.'
    else:
        # Remover formatação
        cpf_cnpj_limpo = re.sub(r'\D', '', cpf_cnpj)
        
        if len(cpf_cnpj_limpo) == 11:
            if not CadastroProfissionalDTO._validar_cpf(cpf_cnpj_limpo):
                erros['cpf_cnpj'] = 'CPF inválido. Verifique os números digitados.'
        elif len(cpf_cnpj_limpo) == 14:
            if not CadastroProfissionalDTO._validar_cnpj(cpf_cnpj_limpo):
                erros['cpf_cnpj'] = 'CNPJ inválido. Verifique os números digitados.'
        else:
            erros['cpf_cnpj'] = 'CPF deve ter 11 dígitos ou CNPJ deve ter 14 dígitos.'
    
    # Se houver erros, retornar
    if erros:
        return None, erros
    
    # Se não houver erros, criar o DTO (já validado)
    try:
        dto = CadastroProfissionalDTO(**data)
        return dto, None
    except Exception as e:
        # Fallback: se mesmo assim der erro, capturar
        erros['geral'] = 'Erro ao processar dados. Verifique os campos.'
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