# Documentação Técnica de Romhacking — Ephemeral Fantasia (PS2)

Esta documentação detalha a engenharia reversa, os formatos de arquivo e os mecanismos internos do jogo *Ephemeral Fantasia* (lançado no Japão como *Reiselied: Ephemeral Fantasia* pela Konami para o PlayStation 2, versão americana `SLUS-20169`).

---

## 1. Estrutura da Imagem de Disco (ISO DVD-ROM)

A imagem do jogo é um DVD-ROM padrão para PlayStation 2:

* **Tamanho exato:** `1.491.238.912 bytes` (728.144 setores de 2.048 bytes).
* **Setor físico de DVD:** 2.048 bytes (`0x800`).
* **Principais arquivos e LBAs:**
  * **`SLUS_201.69`:** Executável principal (ELF do MIPS Emotion Engine R5900), localizado no setor LBA 565 (offset `0x11A800` na imagem ISO).
  * **`DATA6_US.BIN`:** Container comprimido contendo todos os 868 scripts de diálogos e eventos do jogo, localizado no setor LBA 386669 (offset `0x2F326800`).
  * **`DATA0` e `DATA4`:** Arquivos de dados de interface, fontes, minimapas, bússolas e menus de combate em formato TIM2.

---

## 2. O Container RHZ (`DATA6_US.BIN`)

O arquivo `DATA6_US.BIN` (57.094.144 bytes) é um pacote proprietário da Konami que agrupa os scripts de evento do jogo:

* **Contagem de entradas:** 868 arquivos (numerados de 0 a 867).
* **Tabela de Arquivos (TOC):** O cabeçalho inicial do arquivo indexa o offset relativo e o tamanho de cada entrada interna.
* **Alinhamento de setores:** Cada entrada dentro do pacote é alinhada a múltiplos de 2.048 bytes. Qualquer modificação que altere o tamanho final do arquivo `DATA6_US.BIN` quebra o endereçamento LBA dos arquivos subsequentes na imagem ISO do PS2.

---

## 3. Estrutura dos Scripts de Cena (`.SCR`)

Os arquivos de script de eventos e diálogos possuem a extensão interna `.SCR`:

### Assinatura e Cabeçalho
* **Magic Bytes:** Primeiros 4 bytes = `SCR\x1a` (`0x53 0x43 0x52 0x1A`).
* **Cabeçalho:** 44 bytes estruturados em 11 palavras de 32 bits (little-endian unsigned ints):
  * `words[0]`: Assinatura `SCR\x1a`.
  * `words[1]` a `words[6]`: Ponteiros internos para rotinas da máquina de estados de eventos (câmeras, atores, áudio e transições).
  * `words[7]`: Offset do início da tabela de ponteiros de strings de diálogo.
  * `words[8]`: Offset de término do bloco de texto e início da cauda binária.
  * `words[9]` a `words[10]`: Marcadores e flags de controle de execução.

### Tabela de Strings e Diálogos
* A partir do offset indicado em `words[7]`, encontra-se uma lista de ponteiros relativos de 32 bits. Cada ponteiro aponta para o início de uma string de texto codificada em Windows-1252 / ASCII estendido, terminada com byte nulo (`\x00`).

### Tags de Controle Embutidas
O motor de texto interpreta tags especiais de controle no meio das frases:
* `\x8fc0xRRGGBBAA`: Altera a cor do texto para o valor RGBA em hexadecimal (ex.: `\x8fc0xFFFFFF00` para amarelo de destaque de itens e nomes de locais; `\x8fc0xFFFFFFFF` para retornar ao branco padrão).
* `\x8fcc`: Reseta a formatação de cor para o padrão da caixa de diálogo.
* `¼`: Macro da engine substituída em tempo de execução pelo nome do protagonista (**Mouse**).
* `½`: Macro da engine substituída pelo nome do companheiro (**Patty**).
* `\n`: Quebra de linha forçada.

### Cauda Binária 3D e Proteção contra Travamentos
Nos scripts que controlam cutscenes com modelos tridimensionais, logo após o término do bloco de texto (`words[8]`) existem blocos binários essenciais para o motor gráfico:
* Waypoints de movimentação dos personagens pelo cenário.
* Curvas de interpolação de câmeras cinemáticas.
* Tabelas de gatilhos de animação de modelos poligonais.

Se o texto traduzido se expandir além do orçamento original do arquivo sem recalibragem (`delta > 0`), a cauda binária 3D é empurrada para frente na memória, dessincronizando os ponteiros absolutos do script. Isso causa travamentos com tela preta e a mensagem `NOW LOADING...` infinita (como acontecia na cutscene do casamento no Script 436).

O pipeline do projeto monitora cada cutscene recompilada para garantir que o tamanho final não ultrapasse o original (`delta <= 0`), preenchendo qualquer folga com bytes de preenchimento (`\x00`) e assegurando **zero bytes de diferença** na cauda binária 3D.

---

## 4. O Executável `SLUS_201.69` (Offsets de Memória)

Diversos textos do jogo não ficam no arquivo de scripts, mas diretamente no executável principal do PlayStation 2:

* **Telas de Combate e Menus:** `0x19E000` a `0x1A5B00`.
* **Bestiário de Monstros:** `0x1A5B00` a `0x1A6450`.
  * Total de 160 monstros e chefes.
  * Cada nome possui uma capacidade fixa de 8, 16, 24 ou 32 bytes e deve terminar obrigatoriamente com o byte nulo (`\x00`).
* **Tabela de Itens:** `0x1A6F60` a `0x1A7900`.
  * 148 itens consumíveis, armas, acessórios e itens-chave.
  * Padronizados conforme a tradição de RPGs (como a clássica **`Poção Fênix`** no offset `0x1A7060` e **`Poção Reviver`** no offset `0x1A7050`).
* **Descrições de Itens:** `0x1A9B00` a `0x1AC000`.

---

## 5. Tipografia e Fonte Proporcional (VWF)

* A fonte do jogo original continha apenas caracteres do alfabeto inglês sem acentos.
* Os glifos acentuados necessários para o português do Brasil (á, é, í, ó, ú, â, ê, ô, ã, õ, ç, etc.) foram desenhados e inseridos na tabela de fontes do jogo.
* O motor utiliza largura proporcional de caracteres (Variable Width Font - VWF). A largura útil recomendada para as caixas de diálogo fica entre 480px e 520px. Linhas que ultrapassam esse limite sofrem quebras indesejadas ou cortam na margem da janela, exigindo posicionamento manual de quebras de linha (`\n`).

---

## 6. Texturas e Gráficos TIM2

* As texturas de menus, opções, telas de combate, bússola e minimapas utilizam o formato padrão TIM2 (`.tm2`) da Sony.
* Utilizam paleta indexada de cores (CLUT de 4, 8 ou 16 bits).
* No PlayStation 2, as texturas enviadas para a memória de vídeo do Graphics Synthesizer (GS) passam por um processo de entrelaçamento de blocos (*swizzling*). Para edição gráfica no computador, as texturas são desentrelaçadas (*unswizzled*) em imagem linear, editadas e reentrelaçadas (*swizzled*) na reinserção.
