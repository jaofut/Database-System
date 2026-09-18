from service import serializador
import hexdump
import os
from service_pager import Pager

arquivo_teste = "banco_teste_hexdump.db"
if os.path.exists(arquivo_teste):
    os.remove(arquivo_teste)

pager = Pager(arquivo_teste)
pager.aloca(0)
pager.escreve_registro_unico(0, 0, "bebeto")
pager.escreve_registro_unico(0, 1, "kaka")
pager.escreve_registro_unico(0, 2, "romario")
pager.escreve_registro_unico(0,3,pager.serializador(20260001))

pager.fecha()

hexdump.hexdump(pager.le(0))






    
