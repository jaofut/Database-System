import unittest
from tokenizer import tokenizer, ErroLexico

class TestTokenizerPalavrasReservadas(unittest.TestCase):
    """Testa o reconhecimento de todas as palavras reservadas."""

    PALAVRAS_RESERVADAS = [
        "CREATE", "INSERT", "UPDATE", "DELETE", "TRUNCATE",
        "INTO", "FROM", "TABLE", "WHERE", "DROP", "AND", "OR",
        "SELECT", "INT", "CHAR", "VALUES",
    ]

    def test_cada_palavra_reservada(self):
        for palavra in self.PALAVRAS_RESERVADAS:
            with self.subTest(palavra=palavra):
                tokens = tokenizer.tokeniza(palavra)
                self.assertEqual(tokens[0], ("PALAVRA", palavra))

    def test_palavras_reservadas_mistas_sao_normalizadas(self):
        tokens = tokenizer.tokeniza("Select")
        self.assertEqual(tokens[0], ("PALAVRA", "SELECT"))

    def test_entrada_vazia_retorna_so_fim(self):
        tokens = tokenizer.tokeniza("")
        self.assertEqual(tokens, [("FIM", None)])


class TestTokenizerNomes(unittest.TestCase):
    """Testa o reconhecimento de identificadores (NOME)."""

    def test_nome_simples(self):
        tokens = tokenizer.tokeniza("alunos")
        self.assertEqual(tokens[0], ("NOME", "alunos"))

    def test_nome_com_underscore(self):
        tokens = tokenizer.tokeniza("nome_completo")
        self.assertEqual(tokens[0], ("NOME", "nome_completo"))

    def test_nome_com_digito_no_meio(self):
        tokens = tokenizer.tokeniza("col1")
        self.assertEqual(tokens[0], ("NOME", "col1"))

    def test_nome_nao_e_convertido_para_maiuscula(self):
        tokens = tokenizer.tokeniza("MinhaTabela")
        self.assertEqual(tokens[0], ("NOME", "MinhaTabela"))


class TestTokenizerNumeros(unittest.TestCase):
    """Testa o reconhecimento de numeros (NUMERO)."""

    def test_numero_inteiro(self):
        tokens = tokenizer.tokeniza("42")
        self.assertEqual(tokens[0], ("NUMERO", "42"))

    def test_numero_zero(self):
        tokens = tokenizer.tokeniza("0")
        self.assertEqual(tokens[0], ("NUMERO", "0"))

    def test_numero_grande(self):
        tokens = tokenizer.tokeniza("999999")
        self.assertEqual(tokens[0], ("NUMERO", "999999"))


class TestTokenizerTexto(unittest.TestCase):
    """Testa o reconhecimento de literais de texto (TEXTO)."""

    def test_texto_simples(self):
        tokens = tokenizer.tokeniza("'Joao'")
        self.assertEqual(tokens[0], ("TEXTO", "Joao"))

    def test_texto_vazio(self):
        tokens = tokenizer.tokeniza("''")
        self.assertEqual(tokens[0], ("TEXTO", ""))

    def test_texto_com_espacos(self):
        tokens = tokenizer.tokeniza("'ola mundo'")
        self.assertEqual(tokens[0], ("TEXTO", "ola mundo"))

    def test_texto_com_numeros(self):
        tokens = tokenizer.tokeniza("'abc123'")
        self.assertEqual(tokens[0], ("TEXTO", "abc123"))

    def test_aspas_sem_fechamento_lanca_erro(self):
        with self.assertRaises(ErroLexico):
            tokenizer.tokeniza("'sem fechamento")


class TestTokenizerSimbolos(unittest.TestCase):
    """Testa o reconhecimento de simbolos."""

    SIMBOLOS = list("(),;*=")

    def test_cada_simbolo(self):
        for s in self.SIMBOLOS:
            with self.subTest(simbolo=s):
                tokens = tokenizer.tokeniza(s)
                self.assertEqual(tokens[0], ("SIMBOLO", s))

    def test_caractere_invalido_arroba_lanca_erro(self):
        with self.assertRaises(ErroLexico):
            tokenizer.tokeniza("@")

    def test_caractere_invalido_hashtag_lanca_erro(self):
        with self.assertRaises(ErroLexico):
            tokenizer.tokeniza("#")

    def test_caractere_invalido_exclamacao_lanca_erro(self):
        with self.assertRaises(ErroLexico):
            tokenizer.tokeniza("!")


class TestTokenizerComandosCompletos(unittest.TestCase):
    """Testa a tokenizacao de comandos SQL completos."""

    def test_create_table(self):
        sql = "CREATE TABLE alunos ( id INT , nome CHAR(20) )"
        tokens = tokenizer.tokeniza(sql)
        esperados = [
            ("PALAVRA", "CREATE"),
            ("PALAVRA", "TABLE"),
            ("NOME",    "alunos"),
            ("SIMBOLO", "("),
            ("NOME",    "id"),
            ("PALAVRA", "INT"),
            ("SIMBOLO", ","),
            ("NOME",    "nome"),
            ("PALAVRA", "CHAR"),
            ("SIMBOLO", "("),
            ("NUMERO",  "20"),
            ("SIMBOLO", ")"),
            ("SIMBOLO", ")"),
            ("FIM",     None),
        ]
        self.assertEqual(tokens, esperados)

    def test_insert_into(self):
        sql = "INSERT INTO alunos VALUES (1, 'Maria')"
        tokens = tokenizer.tokeniza(sql)
        self.assertEqual(tokens[0], ("PALAVRA", "INSERT"))
        self.assertEqual(tokens[1], ("PALAVRA", "INTO"))
        self.assertEqual(tokens[2], ("NOME",    "alunos"))
        self.assertEqual(tokens[3], ("PALAVRA", "VALUES"))
        self.assertIn(("NUMERO", "1"),     tokens)
        self.assertIn(("TEXTO",  "Maria"), tokens)

    def test_select_com_where(self):
        sql = "SELECT * FROM alunos WHERE id = 1"
        tokens = tokenizer.tokeniza(sql)
        self.assertEqual(tokens[0], ("PALAVRA", "SELECT"))
        self.assertIn(("SIMBOLO", "*"),     tokens)
        self.assertIn(("PALAVRA", "FROM"),  tokens)
        self.assertIn(("PALAVRA", "WHERE"), tokens)
        self.assertIn(("SIMBOLO", "="),     tokens)
        self.assertIn(("NUMERO",  "1"),     tokens)

if __name__ == "__main__":
    unittest.main(verbosity=2)
