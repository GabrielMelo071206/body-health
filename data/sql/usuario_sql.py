CRIAR_TABELA_USUARIO = """
CREATE TABLE IF NOT EXISTS usuario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    senha TEXT NOT NULL,
    perfil TEXT NOT NULL DEFAULT 'cliente',  -- CORRIGIDO: era "tipo"
    foto TEXT,
    token_redefinicao TEXT,
    data_token TIMESTAMP,
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

INSERIR_USUARIO = """
INSERT INTO usuario (nome, email, senha, perfil)
VALUES (?, ?, ?, ?)
"""

ALTERAR_USUARIO = """
UPDATE usuario
SET nome=?, email=?, senha=?, perfil=?
WHERE id=?
"""

EXCLUIR_USUARIO = """
DELETE FROM usuario
WHERE id=?
"""

OBTER_POR_ID_USUARIO = """
SELECT id, nome, email, senha, perfil, foto, token_redefinicao, data_token, data_cadastro
FROM usuario
WHERE id=?
"""

OBTER_TODOS_USUARIO = """
SELECT id, nome, email, senha, perfil, foto, token_redefinicao, data_token, data_cadastro
FROM usuario
ORDER BY nome
"""