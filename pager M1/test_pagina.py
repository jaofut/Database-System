
import hexdump
import os
from service_pager import Pager

arquivo_teste = "banco_teste_pagina.db"
if os.path.exists(arquivo_teste):
    os.remove(arquivo_teste)

pager = Pager(arquivo_teste) 
pager.aloca(1)
pager.escreve(1,"A"*4096)
pager.fecha()
hexdump.hexdump(pager.le(1))
print(len(pager.le(1)),pager.le(1)==b"A"*4096)
print(pager.le(1)[:1])
print(pager.le(2)[:1])
print(os.path.getsize(arquivo_teste) % 4096 == 0)