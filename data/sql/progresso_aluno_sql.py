CRIAR_TABELA_PROGRESSO_ALUNO = """
CREATE TABLE IF NOT EXISTS progresso_aluno (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    personal_aluno_id INTEGER NOT NULL,
    data_registro TIMESTAMP NOT NULL,
    peso REAL,
    medidas TEXT,
    fotos TEXT,
    observacoes TEXT,
    humor TEXT,
    energia INTEGER,
    FOREIGN KEY (personal_aluno_id) REFERENCES personal_aluno(id) ON DELETE CASCADE
);
"""

INSERIR_PROGRESSO_ALUNO = """
INSERT INTO progresso_aluno (
    personal_aluno_id, data_registro, peso, medidas,
    fotos, observacoes, humor, energia
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
"""

ALTERAR_PROGRESSO_ALUNO = """
UPDATE progresso_aluno
SET personal_aluno_id=?, data_registro=?, peso=?, medidas=?,
    fotos=?, observacoes=?, humor=?, energia=?
WHERE id=?
"""

EXCLUIR_PROGRESSO_ALUNO = """
DELETE FROM progresso_aluno WHERE id=?
"""

OBTER_POR_ID_PROGRESSO_ALUNO = """
SELECT pa.*, u.nome AS aluno_nome
FROM progresso_aluno pa
INNER JOIN personal_aluno pal ON pa.personal_aluno_id = pal.id
INNER JOIN cliente c ON pal.aluno_id = c.id
INNER JOIN usuario u ON c.id = u.id
WHERE pa.id=?
"""

OBTER_TODOS_PROGRESSO_ALUNO = """
SELECT pa.*, u.nome AS aluno_nome
FROM progresso_aluno pa
INNER JOIN personal_aluno pal ON pa.personal_aluno_id = pal.id
INNER JOIN cliente c ON pal.aluno_id = c.id
INNER JOIN usuario u ON c.id = u.id
ORDER BY pa.data_registro DESC
"""

OBTER_POR_ALUNO = """
SELECT * FROM progresso_aluno
WHERE personal_aluno_id=?
ORDER BY data_registro DESC
"""