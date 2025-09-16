CRIAR_TABELA_USUARIO = """
CREATE TABLE IF NOT EXISTS usuario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    senha TEXT NOT NULL,
    tipo TEXT NOT NULL  -- 'cliente', 'profissional' ou 'admin'
);
"""

INSERIR_USUARIO = """
INSERT INTO usuario (nome, email, senha, tipo)
VALUES (?, ?, ?, ?)
"""

ALTERAR_USUARIO = """
UPDATE usuario
SET nome=?, email=?, senha=?, tipo=?
WHERE id=?
"""

EXCLUIR_USUARIO = """
DELETE FROM usuario
WHERE id=?
"""

OBTER_POR_ID_USUARIO = """
SELECT id, nome, email, senha, tipo
FROM usuario
WHERE id=?
"""

OBTER_TODOS_USUARIO = """
SELECT id, nome, email, senha, tipo
FROM usuario
ORDER BY nome
"""
