CRIAR_TABELA_PROFISSIONAL = """
CREATE TABLE IF NOT EXISTS profissional (
    id INTEGER PRIMARY KEY,
    especialidade TEXT,
    FOREIGN KEY (id) REFERENCES usuario(id)
);
"""

INSERIR_PROFISSIONAL = """
INSERT INTO profissional (id, especialidade)
VALUES (?, ?)
"""

ALTERAR_PROFISSIONAL = """
UPDATE profissional
SET especialidade=?
WHERE id=?
"""

EXCLUIR_PROFISSIONAL = """
DELETE FROM profissional
WHERE id=?
"""

OBTER_POR_ID_PROFISSIONAL = """
SELECT p.id, p.especialidade, u.nome, u.email, u.senha
FROM profissional p
INNER JOIN usuario u ON p.id = u.id
WHERE p.id=?
"""

OBTER_TODOS_PROFISSIONAL = """
SELECT p.id, p.especialidade, u.nome, u.email, u.senha
FROM profissional p
INNER JOIN usuario u ON p.id = u.id
ORDER BY u.nome
"""
