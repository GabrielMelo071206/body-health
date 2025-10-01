CRIAR_TABELA_AVALIACAO_FISICA = """
CREATE TABLE IF NOT EXISTS avaliacao_fisica (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    personal_aluno_id INTEGER NOT NULL,
    data_avaliacao TIMESTAMP NOT NULL,
    peso REAL,
    altura REAL,
    imc REAL,
    percentual_gordura REAL,
    massa_magra REAL,
    circunferencias TEXT,
    observacoes TEXT,
    proxima_avaliacao TIMESTAMP,
    FOREIGN KEY (personal_aluno_id) REFERENCES personal_aluno(id) ON DELETE CASCADE
);
"""

INSERIR_AVALIACAO_FISICA = """
INSERT INTO avaliacao_fisica (
    personal_aluno_id, data_avaliacao, peso, altura, imc,
    percentual_gordura, massa_magra, circunferencias, 
    observacoes, proxima_avaliacao
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

ALTERAR_AVALIACAO_FISICA = """
UPDATE avaliacao_fisica
SET personal_aluno_id=?, data_avaliacao=?, peso=?, altura=?, imc=?,
    percentual_gordura=?, massa_magra=?, circunferencias=?,
    observacoes=?, proxima_avaliacao=?
WHERE id=?
"""

EXCLUIR_AVALIACAO_FISICA = """
DELETE FROM avaliacao_fisica WHERE id=?
"""

OBTER_POR_ID_AVALIACAO_FISICA = """
SELECT af.*, u.nome AS aluno_nome
FROM avaliacao_fisica af
INNER JOIN personal_aluno pa ON af.personal_aluno_id = pa.id
INNER JOIN cliente c ON pa.aluno_id = c.id
INNER JOIN usuario u ON c.id = u.id
WHERE af.id=?
"""

OBTER_TODOS_AVALIACAO_FISICA = """
SELECT af.*, u.nome AS aluno_nome
FROM avaliacao_fisica af
INNER JOIN personal_aluno pa ON af.personal_aluno_id = pa.id
INNER JOIN cliente c ON pa.aluno_id = c.id
INNER JOIN usuario u ON c.id = u.id
ORDER BY af.data_avaliacao DESC
"""

OBTER_POR_ALUNO = """
SELECT * FROM avaliacao_fisica
WHERE personal_aluno_id=?
ORDER BY data_avaliacao DESC
"""
