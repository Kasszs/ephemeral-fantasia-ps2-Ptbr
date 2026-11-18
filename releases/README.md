# Ephemeral Fantasia (PS2) — Patch de Tradução PT-BR (Versão Beta v0.9)

Patch de tradução em formato **xdelta** para o jogo **Ephemeral Fantasia** (PlayStation 2, versão americana).

---

## 📦 Arquivo do Patch

* **Nome do arquivo:** `Ephemeral_Fantasia_PTBR_Beta_v0.9.xdelta`
* **Tamanho do patch:** `1.283.824 bytes` (~1,22 MB)
* **MD5:** `CC57640306F74668D720979BEFE3BA4F`
* **SHA-1:** `E592AC9EC600D76F32A3945BD8BDBFBD6D695328`

---

## 🔍 Informações da Imagem ISO

Este patch foi gerado e deve ser aplicado **exclusivamente** sobre a cópia limpa e intocada da ISO americana original (padrão Redump):

| Item | ISO Original (Entrada) | ISO Traduzida (Saída) |
| :--- | :--- | :--- |
| **Jogo / Região** | Ephemeral Fantasia (USA) | Ephemeral Fantasia (USA) [PT-BR Beta v0.9] |
| **Serial** | `SLUS-20169` | `SLUS-20169` |
| **Tamanho exato** | `1.491.238.912 bytes` | `1.491.238.912 bytes` |
| **MD5** | `7EC41E4F8F7E6CD21E2D7C19649311EB` | `3E0D6BDE60FEB137141EFD515E8AB8B9` |
| **SHA-1** | `EE5918098409678017F34879B0519CD5A65AA766` | `7AB05607B711DCDC8B4C21D31498CFE9535DD2FC` |

> ⚠️ **Atenção:** Se o hash da sua ISO original for diferente do listado acima, o aplicador acusará erro de soma de verificação (checksum mismatch) ou gerará uma imagem corrompida.

---

## 🛠️ Como Aplicar o Patch

### Método 1: No Windows com xdeltaUI (Recomendado)

1. Baixe o **xdeltaUI** (aplicativo gráfico leve e gratuito).
2. Abra o `xdeltaUI.exe`.
3. No campo **Patch**, clique em *Open...* e selecione o arquivo `Ephemeral_Fantasia_PTBR_Beta_v0.9.xdelta`.
4. No campo **Source File**, clique em *Open...* e selecione a sua imagem ISO original limpa de *Ephemeral Fantasia (USA)*.
5. No campo **Output File**, clique em *...*, escolha onde salvar e digite o nome do arquivo final com a extensão `.iso` (exemplo: `Ephemeral Fantasia (USA) [PT-BR].iso`).
6. Clique no botão **Apply patch**.
7. Aguarde alguns segundos até aparecer a mensagem confirmando que o patch foi aplicado com sucesso (*"File patched successfully"*).

---

### Método 2: No Windows com Delta Patcher

1. Abra o **Delta Patcher**.
2. Em **Original file**, aponte para a ISO original (`.iso`).
3. Em **XDelta patch**, aponte para o arquivo `.xdelta`.
4. Clique em **Apply patch**.

---

### Método 3: Via Linha de Comando (Linux / macOS / Windows CLI)

Caso prefira utilizar o binário oficial `xdelta3` pelo terminal:

```bash
xdelta3 -d -s "Ephemeral Fantasia (USA).iso" "Ephemeral_Fantasia_PTBR_Beta_v0.9.xdelta" "Ephemeral Fantasia (PT-BR).iso"
```

---

## 🎮 Compatibilidade e Execução

A ISO traduzida resultante é 100% compatível com:
* **PCSX2:** Compatibilidade total (versões estáveis e nightly).
* **Hardware Real (PS2):** Compatível com inicialização via OPL (Open PS2 Loader) por USB, SMB (rede) e HD Interno, bem como gravação em DVD-R.

---

## 📌 Status da Versão Beta

### O que está concluído e funcional nesta versão:
* **Textos de Diálogos:** 100% dos 868 arquivos de scripts (`DATA6_US.BIN`) traduzidos para o português do Brasil.
* **Menus e Interfaces:** Menus principais, opções de combate, status de personagens, telas de salvamento e configuração no executável `SLUS_201.69`.
* **Itens e Equipamentos:** Todos os 148 itens, armas e acessórios revisados.
* **Bestiário de Monstros:** Todos os 160 monstros e chefes traduzidos e ajustados.
* **Fontes e Tipografia:** Fonte de largura proporcional (VWF) com acentuação completa em português (á, é, í, ó, ú, â, ê, ô, ã, õ, ç).
* **Gráficos e Texturas:** Menus de combate, minimapas, bússolas de campo e de mapa múndi.
* **Tela de Carregamento (Loading):** Adaptação gráfica da palavra `CARREGANDO` integrada com rotina MIPS em tempo de execução para manter o relógio animado no "O" final.
* **Proteção de Cauda 3D:** Calibração de coordenadas e waypoints em todas as cutscenes do jogo para evitar travamentos ou telas pretas.

### O que define esta versão como **Beta**:
* *Ephemeral Fantasia* é um jogo extenso e não-linear com mecânicas de loop temporal de 7 dias, no qual eventos ocorrem em horários específicos para dezenas de NPCs independentes.
* Podem existir pequenos ajustes contextuais pendentes, nuances de tom em falas específicas ou erros de digitação pontuais que só aparecem em sequências e rotas alternativas raras.
* **Fase de Playtest comunitário:** Esta versão é disponibilizada para que jogadores possam vivenciar a história do início ao fim em português e ajudar a identificar qualquer anomalia.

### Como Reportar Problemas:
Se encontrar qualquer texto com quebra de linha estranha, travamento em cutscene ou erro de digitação, abra uma **Issue** no repositório GitHub com:
1. Dia do ciclo (ex: Dia 2, 14:00) e local onde ocorreu.
2. Nome dos personagens envolvidos.
3. Captura de tela do momento exato (se possível).
