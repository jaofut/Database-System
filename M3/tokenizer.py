class tokenizer:
    def tokeniza(sql):
        PALAVRAS = ["CREATE" , "INSERT" , "UPDATE" , "DELETE", "TRUNCATE" , "INTO" , "FROM" , "TABLE",
                    "WHERE" , "DROP" , "AND" , "OR" , "SELECT", "INT" , "CHAR", "VALUES" ]
        tokens= []
        i = 0
        while i < len(sql):
            c = sql[i]
            if c.isspace(): #pula
                i += 1
            elif c.isalpha():                               # palavra reservada ou nome
                j = i
                while j < len(sql) and (sql[j].isalnum() or sql[j] == "_"): #procura final da palavra
                    j += 1
                p = sql[i:j]
                tokens.append(("PALAVRA", p.upper()) if p.upper() in PALAVRAS else ("NOME", p))
                i = j
            elif c.isdigit():                           # mesmo laço, com isdigit
                j = i
                while j < len(sql) and (sql[j].isalnum() or sql[j] == "_"):
                    j += 1
                p = sql[i:j]
                tokens.append(("NUMERO" , p))
                i = j
            elif c == "'":                                  # texto vai até a próxima aspa
                j = sql.find("'", i + 1)
                if j < 0:
                    raise ErroLexico(f"aspas sem fechamento na posição {i}")
                tokens.append(("TEXTO", sql[i + 1:j]))
                i = j + 1
            elif c in "(),;*=":
                tokens.append(("SIMBOLO", c)); i += 1
            else: raise ErroLexico(f"caractere inesperado {c!r} na posição {i}")
        return tokens + [("FIM", None)]

class ErroLexico(Exception):
    """Exceção lançada quando ocorre erro léxico no comando"""



