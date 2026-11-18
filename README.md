# Ephemeral Fantasia (PlayStation 2) — Tradução em Português do Brasil (PT-BR)

Projeto de tradução completa e ferramentas de romhacking para o clássico cult **Ephemeral Fantasia** (lançado no Japão como *Reiselied: Ephemeral Fantasia* pela Konami em 2000 para o PlayStation 2).

---

## 🎮 Sobre o Jogo

*Ephemeral Fantasia* é um RPG único que combina exploração musical, combate por turnos e uma mecânica central de **Loop Temporal de 7 Dias**:

O jogador controla **Mouse**, um jovem bardo errante e ladrão habilidoso acompanhado por **Patty** (seu alaúde mágico falante), contratado para tocar no casamento da Princesa Loreille com o misterioso Lorde Xelpherpolis na ilha de Pandule. Ao término da primeira semana, Mouse descobre que a ilha está presa em um feitiço de tempo selado onde os dias se repetem ciclicamente e a população perde suas memórias recentes.

Cada habitante da ilha possui rotinas horárias próprias ao longo dos sete dias, tornando o mundo dinâmico e repleto de eventos dependentes do relógio em tempo real.

---

## 📊 Status da Tradução

| Componente | Progresso | Detalhes |
| :--- | :---: | :--- |
| **Textos dos Diálogos** | 100% | Todos os 868 scripts e mais de 43.000 falas traduzidos. |
| **Menus e Interface** | 100% | Telas de combate, opções, status, lojas e telas de salvamento. |
| **Itens e Equipamentos** | 100% | 148 itens consumíveis, armas e acessórios (incluindo a clássica *Poção Fênix*). |
| **Bestiário de Monstros** | 100% | 160 monstros e chefes com nomes descritivos sem truncamentos. |
| **Gráficos e Texturas** | 100% | Menus de combate, minimapas, bússolas e telas de configuração (TIM2). |
| **Fontes e Acentuação** | 100% | Fonte proporcional (VWF) com acentuação completa em português (á, é, í, ó, ú, â, ê, ô, ã, õ, ç). |
| **Revisão e Testes em Jogo** | 🟡 Playtest | Testes práticos no emulador PCSX2 e em hardware real. |

---

## 💿 Informações da ROM Recomendada

Para aplicar o patch e compilar a imagem traduzida, utilize uma cópia limpa da ISO americana original:

* **Jogo:** Ephemeral Fantasia (USA)
* **Código do Disco:** `SLUS-20169`
* **Formato:** Imagem ISO de DVD-ROM
* **Tamanho exato:** `1.491.238.912 bytes` (728.144 setores de 2.048 bytes)
* **Setor LBA de DATA6_US.BIN:** `386669` (offset `0x2F326800`)
* **Setor LBA de SLUS_201.69:** `565` (offset `0x11A800`)

---

## 🛠️ Engenharia Reversa e Detalhes Técnicos

A tradução deste jogo envolveu o desenvolvimento de ferramentas próprias para desvendar os formatos da Konami no PS2:

1. **O Container RHZ (`DATA6_US.BIN`):** Pacote com 868 scripts de diálogos empacotados em setores de 2KB. O arquivo recompilado mantém estritamente os 57.094.144 bytes originais para não deslocar outros arquivos na ISO.
2. **Scripts de Cena (`.SCR`):** Formato binário proprietário com cabeçalho de 44 bytes, tabelas de ponteiros relativos e blocos de comandos de cores hexadecimais (` c`). O projeto possui proteção de cauda binária 3D para evitar que a expansão de textos desloque os waypoints de cutscenes (prevenindo travamentos com tela de loading infinita).
3. **Executável (`SLUS_201.69`):** Contém strings de tamanho fixo em memória para menus, habilidades, itens e bestiário completo.
4. **Sistema de Fontes e Largura Proporcional (VWF):** Fonte acentuada desenhada para o português com balanceamento de largura para evitar quebras anormais nas caixas de diálogo.
5. **Texturas TIM2:** Extração, desentrelaçamento de memória de vídeo do Graphics Synthesizer (*unswizzling*), edição gráfica e reempacotamento.

Para mais detalhes sobre os formatos binários, consulte a [**Documentação Técnica de Formatos**](docs/FORMATOS.md).  
Para detalhes sobre os personagens e vocabulário da ilha, consulte o [**Guia de Personagens**](docs/PERSONAGENS.md).

---

## 🚀 Como Aplicar o Patch / Gerar a ISO Traduzida

### Método 1: Direto via Patch xdelta (Mais rápido e simples)

Caso você queira apenas jogar sem precisar compilar o projeto:

1. Baixe o patch `Ephemeral_Fantasia_PTBR_Beta_v0.9.xdelta` localizado na pasta [`releases/`](releases/).
2. Abra o aplicativo **xdeltaUI** (ou **Delta Patcher**).
3. Selecione o patch `.xdelta`, a sua ISO original limpa americana (`SLUS-20169`) e defina o nome da ISO traduzida de saída.
4. Clique em **Apply patch**.
5. Para o passo a passo detalhado e hashes de validação, consulte o [**Guia de Releases**](releases/README.md).

---

### Método 2: Compilação via Script Python

Para desenvolvedores e romhackers que queiram injetar os bancos de dados diretamente na ISO:

#### Pré-requisitos
* Python 3.10 ou superior instalado.
* Imagem ISO original de *Ephemeral Fantasia (USA)* (`SLUS-20169` / 1.491.238.912 bytes).

#### Passo a Passo

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/Kasszs/ephemeral-fantasia-ps2-Ptbr.git
   cd ephemeral-fantasia-ps2-Ptbr
   ```

2. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Execute o patcher apontando para a sua ISO original:**
   ```bash
   python scripts/patch_iso.py "caminho/para/Ephemeral Fantasia (USA).iso"
   ```

O script criará automaticamente um backup da imagem original e injetará os scripts traduzidos e os patches do executável diretamente na ISO.

---

## 👥 Créditos e Ferramentas

* **Romhacking, Ferramentas e Tradução:** Kasszs
* **Ferramentas Utilizadas:** PCSX2, Ghidra, HxD, Python 3, Pillow, PyQt.
* **Agradecimentos:** À comunidade de romhacking e preservação de jogos de PlayStation 2.
