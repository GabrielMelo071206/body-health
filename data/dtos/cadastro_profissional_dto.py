from pydantic import BaseModel, EmailStr, ValidationError, field_validator
from fastapi import UploadFile
import re

class CadastroProfissionalDTO(BaseModel):
    nome: str
    email: EmailStr
    senha: str
    senha_confirm: str
    especialidade: str
    registro_profissional: str | None = None
    cpf_cnpj: str
    foto_registro: UploadFile  # Aqui usamos UploadFile

    @field_validator('nome')
    @classmethod
    def validar_nome(cls, nome):
        nome = nome.strip()
        if len(nome) < 3:
            raise ValueError('Nome deve ter pelo menos 3 caracteres.')
        if len(nome) > 100:
            raise ValueError('Nome deve ter no máximo 100 caracteres.')
        return nome

    @field_validator('senha')
    @classmethod
    def validar_senha(cls, senha):
        senha = senha.strip()
        if len(senha) < 6:
            raise ValueError('Senha deve ter pelo menos 6 caracteres.')
        if ' ' in senha:
            raise ValueError('Senha não pode conter espaços.')
        return senha

    @field_validator('senha_confirm')
    @classmethod
    def validar_senha_confirm(cls, senha_confirm, info):
        senha = info.data.get('senha')
        if senha_confirm != senha:
            raise ValueError('As senhas não coincidem.')
        return senha_confirm

    @field_validator('especialidade')
    @classmethod
    def validar_especialidade(cls, esp):
        esp = esp.strip()
        opcoes = [
            "Personal Trainer", "Nutricionista", "Fisioterapeuta",
            "Educador Físico", "Médico do Esporte", "Psicólogo do Esporte", "Outro"
        ]
        if esp not in opcoes:
            raise ValueError('Especialidade inválida.')
        return esp

    @field_validator('cpf_cnpj')
    @classmethod
    def validar_cpf_cnpj(cls, valor):
        valor = re.sub(r'\D', '', valor)
        if len(valor) == 11:
            if not cls.validar_cpf(valor):
                raise ValueError('CPF inválido.')
        elif len(valor) == 14:
            if not cls.validar_cnpj(valor):
                raise ValueError('CNPJ inválido.')
        else:
            raise ValueError('CPF ou CNPJ inválido.')
        return valor

    @field_validator('foto_registro')
    @classmethod
    def validar_foto(cls, foto: UploadFile):
        if not foto:
            raise ValueError('Foto do registro é obrigatória.')
        if foto.content_type not in ['image/jpeg', 'image/png']:
            raise ValueError('Apenas arquivos JPG ou PNG são permitidos.')
        # Limite de 5MB
        foto.file.seek(0, 2)  # Move para o final
        tamanho = foto.file.tell()
        foto.file.seek(0)
        if tamanho > 5 * 1024 * 1024:
            raise ValueError('Arquivo muito grande. Máximo 5MB.')
        return foto

    # Funções auxiliares
    @staticmethod
    def validar_cpf(cpf):
        if len(cpf) != 11 or cpf == cpf[0]*11:
            return False
        soma = sum(int(cpf[i])*(10-i) for i in range(9))
        resto = (soma*10) % 11
        resto = 0 if resto == 10 else resto
        if resto != int(cpf[9]):
            return False
        soma = sum(int(cpf[i])*(11-i) for i in range(10))
        resto = (soma*10) % 11
        resto = 0 if resto == 10 else resto
        return resto == int(cpf[10])

    @staticmethod
    def validar_cnpj(cnpj):
        if len(cnpj) != 14 or cnpj == cnpj[0]*14:
            return False
        pesos1 = [5,4,3,2,9,8,7,6,5,4,3,2]
        soma = sum(int(cnpj[i])*pesos1[i] for i in range(12))
        resto = soma % 11
        dv1 = 0 if resto < 2 else 11 - resto
        pesos2 = [6]+pesos1
        soma = sum(int(cnpj[i])*pesos2[i] for i in range(13))
        resto = soma % 11
        dv2 = 0 if resto < 2 else 11 - resto
        return dv1 == int(cnpj[12]) and dv2 == int(cnpj[13])


# Função utilitária para validar e retornar todos os erros de uma vez
def validar_cadastro_profissional(data: dict):
    erros = {}
    try:
        dto = CadastroProfissionalDTO(**data)
        return dto, None
    except ValidationError as e:
        for err in e.errors():
            campo = err['model_path'][0] if 'model_path' in err else err['loc'][0]
            erros[campo] = err['msg']
        return None, erros
