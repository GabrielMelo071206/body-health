CRIAR_TABELA_NUTRICIONISTA = """
CREATE TABLE IF NOT EXISTS nutricionista (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profissional_id INTEGER NOT NULL,
    crn TEXT,
    especialidades TEXT,
    biografia TEXT,
    anos_experiencia INTEGER,
    valor_consulta REAL,
    status TEXT DEFAULT 'ativo',
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    foto_perfil TEXT,
    avaliacoes_media REAL,
    total_pacientes INTEGER DEFAULT 0,
    FOREIGN KEY (profissional_id) REFERENCES profissional(id) ON DELETE CASCADE
);
"""

INSERIR_NUTRICIONISTA = """
INSERT INTO nutricionista (
    profissional_id, crn, especialidades, biografia, 
    anos_experiencia, valor_consulta, status, data_cadastro,
    foto_perfil, avaliacoes_media, total_pacientes
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

ALTERAR_NUTRICIONISTA = """
UPDATE nutricionista
SET profissional_id=?, crn=?, especialidades=?, biografia=?,
    anos_experiencia=?, valor_consulta=?, status=?, 
    foto_perfil=?, avaliacoes_media=?, total_pacientes=?
WHERE id=?
"""

EXCLUIR_NUTRICIONISTA = """
DELETE FROM nutricionista WHERE id=?
"""

OBTER_POR_ID_NUTRICIONISTA = """
SELECT n.*, u.nome, u.email, prof.especialidade
FROM nutricionista n
INNER JOIN profissional prof ON n.profissional_id = prof.id
INNER JOIN usuario u ON prof.id = u.id
WHERE n.id=?
"""

OBTER_TODOS_NUTRICIONISTA = """
SELECT n.*, u.nome, u.email, prof.especialidade
FROM nutricionista n
INNER JOIN profissional prof ON n.profissional_id = prof.id
INNER JOIN usuario u ON prof.id = u.id
WHERE n.status = 'ativo'
ORDER BY u.nome
"""

OBTER_POR_PROFISSIONAL = """
SELECT * FROM nutricionista WHERE profissional_id=?
"""