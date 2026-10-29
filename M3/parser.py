class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.i = 0
    def olha(self):
        return self.tokens[self.i]
    def aceita(self, tipo, valor):
        if self.tokens[self.i] == (tipo, valor):
            self.i += 1
            return True
        return False
    def espera(self, tipo, valor=None):
        t, v = self.tokens[self.i]
        if t != tipo or (valor is not None and v != valor):
            raise ErroSintatico(f"esperava {valor or tipo}, veio {v!r}")
        self.i += 1
        return v
    def valor(self):
        t, v = self.olha()
        if t in ("NUMERO", "TEXTO"):
            self.i += 1
            return v
        raise ErroSintatico(f"esperava valor, veio {v!r}")

    def comando(self):
        _, v = self.olha()
        if v == "CREATE":   arvore = self.create()
        elif v == "INSERT": arvore = self.insert()     # mesmo molde do create, com valor
        elif v == "SELECT": arvore = self.select()
        else: raise ErroSintatico(f"comando desconhecido {v!r}")
        self.aceita("SIMBOLO", ";")
        self.espera("FIM")                            
        return arvore
    
    def create(self):
        self.espera("PALAVRA", "CREATE")
        self.espera("PALAVRA", "TABLE")
        tabela = self.espera("NOME")
        self.espera("SIMBOLO", "(")
        colunas = [self.coluna()]
        while self.aceita("SIMBOLO", ","):
            colunas.append(self.coluna())
        self.espera("SIMBOLO", ")")
        return {"op": "CREATE", "tabela": tabela, "colunas": colunas}

    def coluna(self):
        nome = self.espera("NOME")
        if self.aceita("PALAVRA", "INT"):
            return (nome, "INT", 4)
        self.espera("PALAVRA", "CHAR")
        self.espera("SIMBOLO", "(")
        n = self.espera("NUMERO")
        self.espera("SIMBOLO", ")")
        return (nome, "CHAR", n)
    
    def select(self):
        self.espera("PALAVRA", "SELECT")
        if self.aceita("SIMBOLO", "*"):
            colunas = ["*"]
        else:
            colunas = [self.espera("NOME")]
            while self.aceita("SIMBOLO", ","):
                colunas.append(self.espera("NOME"))
        self.espera("PALAVRA", "FROM")
        tabela = self.espera("NOME")
        where = None
        if self.aceita("PALAVRA", "WHERE"):
            coluna = self.espera("NOME")
            self.espera("SIMBOLO", "=")
            where = (coluna, self.valor())
        return {"op": "SELECT", "colunas": colunas, "tabela": tabela, "where": where}
    def insert(self):
        self.espera("PALAVRA", "INSERT")
        self.espera("PALAVRA", "INTO")
        tabela = self.espera("NOME")
        self.espera("PALAVRA", "VALUES")
        self.espera("SIMBOLO", "(")
        valores = [self.valor()]
        while self.aceita("SIMBOLO", ","):
            valores.append(self.valor())
        self.espera("SIMBOLO", ")")
        return {"op": "INSERT", "tabela": tabela, "valores": valores}
class ErroSintatico(Exception):
        """Exceção lançada quando ocorre erro sintático no comando"""
import tokenizer
def analisa(sql):                                 # o que o resto do minidb chama
    return Parser(tokenizer.tokeniza(sql)).comando()