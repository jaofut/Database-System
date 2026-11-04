class Node:
    def __init__(self, page_id, folha=True):
        self.page_id = page_id
        self.folha = folha
        self.chaves = []
        self.referencias = []    
        self.filhos = []         
        self.proxima = 0        

class ArvoreBMais:
    ASSINATURA = b"BPRID001"

    def __init__(self, cache, ordem=None):
        if type(cache.cap) is not int or cache.cap < 1:
            raise ValueError("O cache precisa comportar ao menos uma página")
        self.cache = cache
        self.tamanho_pagina = cache.pager.tamanho_pag
       
        self.max_ordem = min((self.tamanho_pagina - 16) // 24 + 1,
                             (self.tamanho_pagina - 24) // 16 + 1)
        if self.max_ordem < 3:
            raise ValueError("Página pequena demais para o índice")
        if ordem is not None:
            self._validar_ordem(ordem)
        dados = self._ler_pagina(0)
        if dados == b"":
            self.ordem = self.max_ordem if ordem is None else ordem
            self.raiz = 1
            self.proxima_pagina = 2
            self._salvar_no(Node(1))
            self._salvar_metadados()
        else:
            if len(dados) != self.tamanho_pagina or dados[:8] != self.ASSINATURA:
                raise ValueError("Arquivo não é um índice válido; use um arquivo exclusivo")
            self.raiz = int.from_bytes(dados[8:16], "little")
            self.proxima_pagina = int.from_bytes(dados[16:24], "little")
            self.ordem = int.from_bytes(dados[24:32], "little")
            self._validar_ordem(self.ordem)
            if ordem is not None and ordem != self.ordem:
                raise ValueError("A ordem difere da gravada no índice")
            if not 0 < self.raiz < self.proxima_pagina:
                raise ValueError("Metadados inválidos")
            self._carregar_no(self.raiz)

    def _validar_ordem(self, ordem):
        if type(ordem) is not int or not 3 <= ordem <= self.max_ordem:
            raise ValueError(f"Ordem deve estar entre 3 e {self.max_ordem}")

    def _validar_chave(self, chave):
        if type(chave) is not int or not -(1 << 63) <= chave < (1 << 63):
            raise ValueError("Chave deve ser um inteiro assinado de 64 bits")

    def _validar_referencia(self, page_id, slot_id):
        for numero in (page_id, slot_id):
            if type(numero) is not int or not 0 <= numero < (1 << 64):
                raise ValueError("Página e slot devem ser inteiros não negativos de 64 bits")

    def _ler_pagina(self, page_id):
        dados = self.cache.fixa(page_id)
        try:
            return bytes(dados)
        finally:
            self.cache.solta(page_id)

    def _gravar_pagina(self, page_id, dados):
        if len(dados) > self.tamanho_pagina:
            raise ValueError("Nó excede a capacidade da página")
        self.cache.fixa(page_id)
        try:
            self.cache.frames[page_id] = bytes(dados).ljust(self.tamanho_pagina, b"\x00")
        finally:
            self.cache.solta(page_id, sujou=True)

    def _salvar_metadados(self):
        dados = self.ASSINATURA
        for numero in (self.raiz, self.proxima_pagina, self.ordem):
            dados += numero.to_bytes(8, "little")
        self._gravar_pagina(0, dados)

    def _novo_no(self, folha):
        no = Node(self.proxima_pagina, folha)
        self.proxima_pagina += 1
        return no

    def _salvar_no(self, no):
       
        dados = bytearray([1 if no.folha else 2, 0, 0, 0])
        dados.extend(len(no.chaves).to_bytes(4, "little"))
        dados.extend(no.proxima.to_bytes(8, "little"))
        if not no.folha:
            dados.extend(no.filhos[0].to_bytes(8, "little"))
        for i, chave in enumerate(no.chaves):
            dados.extend(chave.to_bytes(8, "little", signed=True))
            numeros = no.referencias[i] if no.folha else (no.filhos[i + 1],)
            for numero in numeros:
                dados.extend(numero.to_bytes(8, "little"))
        self._gravar_pagina(no.page_id, dados)

    def _carregar_no(self, page_id):
        if not 0 < page_id < self.proxima_pagina:
            raise ValueError("Referência de nó inválida")
        dados = self._ler_pagina(page_id)
        if len(dados) != self.tamanho_pagina or dados[0] not in (1, 2):
            raise ValueError("Página de nó inválida")
        no = Node(page_id, dados[0] == 1)
        quantidade = int.from_bytes(dados[4:8], "little")
        if quantidade >= self.ordem:
            raise ValueError("Quantidade de chaves inválida")
        no.proxima = int.from_bytes(dados[8:16], "little")
        posicao = 16
        if not no.folha:
            no.filhos.append(int.from_bytes(dados[16:24], "little"))
            posicao = 24
        for _ in range(quantidade):
            no.chaves.append(int.from_bytes(dados[posicao:posicao + 8], "little", signed=True))
            pagina = int.from_bytes(dados[posicao + 8:posicao + 16], "little")
            if no.folha:
                slot = int.from_bytes(dados[posicao + 16:posicao + 24], "little")
                no.referencias.append((pagina, slot))
                posicao += 24
            else:
                no.filhos.append(pagina)
                posicao += 16
        return no

    def _posicao(self, chaves, chave, direita=False):
        inicio, fim = 0, len(chaves)
        while inicio < fim:
            meio = (inicio + fim) // 2
            if chaves[meio] < chave or (direita and chaves[meio] == chave):
                inicio = meio + 1
            else:
                fim = meio
        return inicio

    def _encontrar_folha(self, chave):
        no = self._carregar_no(self.raiz)
        while not no.folha:
            no = self._carregar_no(no.filhos[self._posicao(no.chaves, chave, True)])
        return no

    def buscar(self, chave):
        
        self._validar_chave(chave)
        no = self._encontrar_folha(chave)
        i = self._posicao(no.chaves, chave)
        if i < len(no.chaves) and no.chaves[i] == chave:
            return no.referencias[i]
        return None

    def inserir(self, chave, page_id, slot_id):
       
        self._validar_chave(chave)
        self._validar_referencia(page_id, slot_id)
        divisao = self._inserir(self.raiz, chave, (page_id, slot_id))
        if divisao is not None:
            separador, direita = divisao
            nova_raiz = self._novo_no(False)
            nova_raiz.chaves = [separador]
            nova_raiz.filhos = [self.raiz, direita]
            self._salvar_no(nova_raiz)
            self.raiz = nova_raiz.page_id
        self._salvar_metadados()

    def _inserir(self, page_id, chave, referencia):
        no = self._carregar_no(page_id)
        i = self._posicao(no.chaves, chave, not no.folha)
        if no.folha:
            if i < len(no.chaves) and no.chaves[i] == chave:
                no.referencias[i] = referencia
                self._salvar_no(no)
                return None
            no.chaves.insert(i, chave)
            no.referencias.insert(i, referencia)
        else:
            divisao = self._inserir(no.filhos[i], chave, referencia)
            if divisao is None:
                return None
            separador, direita = divisao
            no.chaves.insert(i, separador)
            no.filhos.insert(i + 1, direita)
        if len(no.chaves) < self.ordem:
            self._salvar_no(no)
            return None
        return self._dividir(no)

    def _dividir(self, no):
        meio = len(no.chaves) // 2
        direita = self._novo_no(no.folha)
        if no.folha:
            direita.chaves = no.chaves[meio:]
            direita.referencias = no.referencias[meio:]
            no.chaves = no.chaves[:meio]
            no.referencias = no.referencias[:meio]
            direita.proxima = no.proxima
            no.proxima = direita.page_id
            separador = direita.chaves[0]  
        else:
            separador = no.chaves[meio]    
            direita.chaves = no.chaves[meio + 1:]
            direita.filhos = no.filhos[meio + 1:]
            no.chaves = no.chaves[:meio]
            no.filhos = no.filhos[:meio + 1]
        self._salvar_no(direita)
        self._salvar_no(no)
        return separador, direita.page_id

    def buscar_registro(self, chave, cache_dados):
        
        referencia = self.buscar(chave)
        if referencia is None:
            return None
        page_id, slot_id = referencia
        pager = cache_dados.pager
        inicio = pager.deslocamento(page_id, slot_id) - page_id * pager.tamanho_pag
        fim = inicio + pager.tamanho_registro
        if inicio < pager.tamanho_cabecalho or fim > pager.tamanho_pag:
            raise ValueError("Slot fora da página de dados")
        pagina = cache_dados.fixa(page_id)
        try:
            if len(pagina) < fim:
                raise ValueError("Página de dados ausente ou incompleta")
            return bytes(pagina[inicio:fim])
        finally:
            cache_dados.solta(page_id)

    def descarrega(self):
        self.cache.descarrega()
