from collections import OrderedDict
class Cache:
    def __init__(self, pager, capacidade=16):
        self.pager, self.cap = pager, capacidade
        self.frames = {}              
        self.suja   = set()
        self.fixada = {}              
        self.uso    = OrderedDict()   
        self.acertos = self.faltas = 0

    def fixa(self, n):
        if n in self.frames:
            self.acertos += 1
            self.uso.move_to_end(n)
        else:
            self.faltas += 1
            if len(self.frames) == self.cap:
                self._expulsa()
            self.frames[n] = self.pager.le(n)
            self.uso[n] = True
        self.fixada[n] = self.fixada.get(n, 0) + 1 
        return self.frames[n]

    def solta(self, n, sujou=False):
        if sujou:
            self.suja.add(n)
        self.fixada[n] -= 1

    def _expulsa(self):
        for n in list(self.uso):                  
            if self.fixada.get(n, 0) == 0:
                if n in self.suja:
                    self.pager.escreve(n, self.frames[n])
                    self.suja.discard(n)
                del self.frames[n], self.uso[n]
                return
        raise RuntimeError("todas as páginas estão fixadas")

    def descarrega(self):                         
        for n in list(self.suja):
            self.pager.escreve(n, self.frames[n])
        self.suja.clear()
        self.pager.sync()
    
        








