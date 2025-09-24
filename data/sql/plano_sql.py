CRIAR_TABELA_PLANO = """
CREATE TABLE IF NOT EXISTS plano (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    descricao TEXT,
    preco REAL NOT NULL,
    duracao_dias INTEGER NOT NULL,
    ativo INTEGER DEFAULT 1,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

INSERIR_PLANO = """
INSERT INTO plano (nome, descricao, preco, duracao_dias)
VALUES (?, ?, ?, ?)
"""

ALTERAR_PLANO = """
UPDATE plano
SET nome=?, descricao=?, preco=?, duracao_dias=?
WHERE id=?
"""

EXCLUIR_PLANO = """
DELETE FROM plano
WHERE id=?
"""

OBTER_TODOS_PLANO = """
SELECT id, nome, descricao, preco, duracao_dias, ativo, data_criacao
FROM plano
WHERE ativo = 1
ORDER BY preco
"""

OBTER_POR_ID_PLANO = """
SELECT id, nome, descricao, preco, duracao_dias, ativo, data_criacao
FROM plano
WHERE id=? AND ativo = 1
"""