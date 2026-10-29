from parser import Parser, ErroSintatico
from tokenizer import tokenizer
import unittest
def parse(sql): #função que auxilia o teste
    return Parser(tokenizer.tokeniza(sql)).comando() 


class TestParserCreate(unittest.TestCase): #Testa o parsing de comandos CREATE TABLE

    def test_create_uma_coluna_int(self):
        arvore = parse("CREATE TABLE alunos (id INT)")
        self.assertEqual(arvore["op"],      "CREATE")
        self.assertEqual(arvore["tabela"],  "alunos")
        self.assertEqual(arvore["colunas"], [("id", "INT", 4)])

    def test_create_uma_coluna_char(self):
        arvore = parse("CREATE TABLE produtos (nome CHAR(50))")
        self.assertEqual(arvore["op"],      "CREATE")
        self.assertEqual(arvore["tabela"],  "produtos")
        self.assertEqual(arvore["colunas"], [("nome", "CHAR", "50")])

    def test_create_multiplas_colunas(self):
        arvore = parse("CREATE TABLE alunos (id INT, nome CHAR(20))")
        self.assertEqual(len(arvore["colunas"]), 2)
        self.assertEqual(arvore["colunas"][0], ("id",   "INT",  4))
        self.assertEqual(arvore["colunas"][1], ("nome", "CHAR", "20"))

    def test_create_sem_parenteses_lanca_erro(self):
        with self.assertRaises(ErroSintatico):
            parse("CREATE TABLE alunos id INT")

    def test_create_sem_tipo_lanca_erro(self):
        with self.assertRaises(ErroSintatico):
            parse("CREATE TABLE alunos (id)")

    def test_create_com_ponto_e_virgula(self):
        arvore = parse("CREATE TABLE t (id INT);")
        self.assertEqual(arvore["op"], "CREATE")


class TestParserInsert(unittest.TestCase): #Testa INSERT INTO

    def test_insert_valor_numerico(self):
        arvore = parse("INSERT INTO alunos VALUES (1)")
        self.assertEqual(arvore["op"],      "INSERT")
        self.assertEqual(arvore["tabela"],  "alunos")
        self.assertEqual(arvore["valores"], ["1"])

    def test_insert_valor_texto(self):
        arvore = parse("INSERT INTO alunos VALUES ('Maria')")
        self.assertEqual(arvore["valores"], ["Maria"])

    def test_insert_multiplos_valores(self):
        arvore = parse("INSERT INTO alunos VALUES (1, 'Joao')")
        self.assertEqual(arvore["valores"], ["1", "Joao"])

    def test_insert_sem_into_lanca_erro(self):
        with self.assertRaises(ErroSintatico):
            parse("INSERT alunos VALUES (1)")

    def test_insert_sem_values_lanca_erro(self):
        with self.assertRaises(ErroSintatico):
            parse("INSERT INTO alunos (1)")

    def test_insert_com_ponto_e_virgula(self):
        arvore = parse("INSERT INTO t VALUES (42);")
        self.assertEqual(arvore["op"], "INSERT")
        self.assertEqual(arvore["tabela"], "t")
        self.assertEqual(arvore["valores"] , ["42"])

    def test_insert_tabela_correta(self):
        arvore = parse("INSERT INTO produtos VALUES (5, 'Caneta')")
        self.assertEqual(arvore["tabela"], "produtos")


class TestParserSelect(unittest.TestCase):
    """Testa o parsing de comandos SELECT."""

    def test_select_todos(self):
        arvore = parse("SELECT * FROM alunos")
        self.assertEqual(arvore["op"],      "SELECT")
        self.assertEqual(arvore["colunas"], ["*"])
        self.assertEqual(arvore["tabela"],  "alunos")
        self.assertIsNone(arvore["where"])

    def test_select_coluna_especifica(self):
        arvore = parse("SELECT nome FROM alunos")
        self.assertEqual(arvore["colunas"], ["nome"])

    def test_select_multiplas_colunas(self):
        arvore = parse("SELECT id, nome FROM alunos")
        self.assertEqual(arvore["colunas"], ["id", "nome"])

    def test_select_com_where_numero(self):
        arvore = parse("SELECT * FROM alunos WHERE id = 1")
        self.assertIsNotNone(arvore["where"])
        self.assertEqual(arvore["where"], ("id", "1"))

    def test_select_com_where_texto(self):
        arvore = parse("SELECT * FROM alunos WHERE nome = 'Maria'")
        self.assertEqual(arvore["where"], ("nome", "Maria"))

    def test_select_retorna_op_select(self):
        arvore = parse("SELECT * FROM t")
        self.assertEqual(arvore["op"], "SELECT")

    def test_select_sem_from_lanca_erro(self):
        with self.assertRaises(ErroSintatico):
            parse("SELECT * alunos")

    def test_select_where_sem_coluna_lanca_erro(self):
        with self.assertRaises(ErroSintatico):
            parse("SELECT * FROM alunos WHERE = 1")

    def test_select_com_ponto_e_virgula(self):
        arvore = parse("SELECT * FROM t;")
        self.assertEqual(arvore["op"], "SELECT")

    def test_select_tabela_correta(self):
        arvore = parse("SELECT * FROM professores")
        self.assertEqual(arvore["tabela"], "professores")

    def test_select_tres_colunas(self):
        arvore = parse("SELECT a, b, c FROM t")
        self.assertEqual(arvore["colunas"], ["a", "b", "c"])


class TestParserComandoDesconhecido(unittest.TestCase):
    """Testa comandos SQL invalidos ou desconhecidos."""

    def test_comando_drop_lanca_erro(self):
        with self.assertRaises(ErroSintatico):
            parse("DROP TABLE alunos")

    def test_comando_update_lanca_erro(self):
        with self.assertRaises(ErroSintatico):
            parse("UPDATE alunos SET id = 1")

    def test_comando_delete_lanca_erro(self):
        with self.assertRaises(ErroSintatico):
            parse("DELETE FROM alunos")

    def test_entrada_vazia_lanca_erro(self):
        with self.assertRaises((ErroSintatico, IndexError, TypeError)):
            parse("")


class TestParserMetodos(unittest.TestCase):
    """Testa os metodos auxiliares do Parser diretamente."""

    def _parser(self, sql):
        return Parser(tokenizer.tokeniza(sql))

    def test_olha_retorna_token_atual(self):
        p = self._parser("SELECT")
        self.assertEqual(p.olha(), ("PALAVRA", "SELECT"))

    def test_aceita_token_correto_retorna_true(self):
        p = self._parser("SELECT")
        self.assertTrue(p.aceita("PALAVRA", "SELECT"))

    def test_aceita_token_errado_retorna_false(self):
        p = self._parser("SELECT")
        self.assertFalse(p.aceita("PALAVRA", "INSERT"))

    def test_aceita_avanca_indice(self):
        p = self._parser("SELECT *")
        p.aceita("PALAVRA", "SELECT")
        self.assertEqual(p.olha(), ("SIMBOLO", "*"))

    def test_espera_token_correto_retorna_valor(self):
        p = self._parser("alunos")
        v = p.espera("NOME")
        self.assertEqual(v, "alunos")

    def test_espera_token_errado_lanca_erro(self):
        p = self._parser("42")
        with self.assertRaises(ErroSintatico):
            p.espera("PALAVRA")

    def test_valor_numero(self):
        p = self._parser("42")
        v = p.valor()
        self.assertEqual(v, "42")

    def test_valor_texto(self):
        p = self._parser("'hello'")
        v = p.valor()
        self.assertEqual(v, "hello")

    def test_valor_invalido_lanca_erro(self):
        p = self._parser("alunos")
        with self.assertRaises(ErroSintatico):
            p.valor()


if __name__ == "__main__":
    unittest.main(verbosity=2)