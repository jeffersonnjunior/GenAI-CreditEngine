# 🏆 Desafio GenAI-CreditEngine

> **Plataforma Multiagente de Hiperautomação e Concessão de Crédito Báncario**

Você está diante do núcleo de Risco e Onboarding de um Banco Digital (uma *Credit Engine*). O objetivo deste projeto é construir um ecossistema autônomo end-to-end capaz de escalar a esteira de abertura de contas da instituição, resolvendo gargalos críticos de operação através de IA generativa e orquestração de agentes.

---

## 📑 Índice
1. [O Problema de Negócio](#-1-o-problema-de-negócio-a-dor-da-empresa)
2. [O Objetivo (OKR)](#-o-objetivo-okr)
3. [Arquitetura do Sistema](#-2-a-arquitetura-do-sistema-o-desafio-end-to-end)
4. [Restrições e Governança](#-3-restrições-e-governança-hard-mode)
5. [Libs e repos recomendados](#-4-libs-e-repos-recomendados)

---

## 🏢 1. O Problema de Negócio (A Dor da Empresa)

A operação atual enfrenta uma crise sustentada por três gargalos críticos:

* 🚨 **Fraude de Identidade Visuais:** Quadrilhas estão usando edição de imagem e deepfakes documentais básicos para abrir contas com CPFs roubados e dados divergentes. O OCR legado do banco não cruza as informações corretamente.
* ⏳ **Gargalo Humano na Mesa de Crédito:** O sistema atual bloqueia todas as propostas que fogem de um "IF/ELSE" simples. Analistas humanos estão gastando dias revisando PDFs de clientes legítimos para liberar limites de crédito, travando a aquisição de novos usuários.
* 🔌 **Quedas no Ecossistema Externo:** Quando o birô de crédito (Serasa/Boa Vista) ou o Banco Central ficam lentos, a API do banco dá *timeout* e o cliente desiste de abrir a conta.

### 🎯 O Objetivo (OKR)
Construir o **GenAI-CreditEngine**, uma plataforma orquestrada por agentes autônomos capaz de ingerir a proposta, auditar as imagens dos documentos em tempo real e decidir a aprovação ou negação do crédito em segundos. 
O sistema deve emitir cartões de forma **100% autônoma para limites de até R$ 10.000,00** e barrar divergências de identidade com precisão extrema.

---

## 🏗️ 2. A Arquitetura do Sistema (O Desafio End-to-End)

Este ecossistema foi construído do zero, integrando 4 grandes blocos arquiteturais baseados em uma **Arquitetura Modular (Router-Service-Repository)** em FastAPI:

### Fase 1: Ingestão Resiliente e RAG Enterprise (Compliance)
*O banco não pode errar a leitura da própria política de crédito.*

* **O Desafio Técnico:** API base em **FastAPI** assíncrono com loop de *Self-Healing*. Se o payload JSON estourar a validação do Pydantic V2, o LLM intercepta o erro de traceback e corrige a própria estrutura em até 3 tentativas.
* **A Regra de Negócio (RAG):** Manual de compliance indexado em um **ChromaDB**. O Agente usa *Sentence Window Retrieval* combinado com *Reciprocal Rank Fusion (RRF)* para puxar a regra exata antes de calcular o limite.

### Fase 2: O Cérebro Autônomo (ReAct) e Visão Multimodal
*O coração do sistema é cognitivo, não linear.*

* **O Motor de Decisão (LangGraph):** Agente em padrão **ReAct (Reason + Action)**.
* **O Desafio Multimodal:** Leitura de CNH via **Pillow, OpenCV e Modelos de Visão Multimodal** para *Cross-Check* estrito contra fraudes.
* **A Matemática de Risco:** 
  * Score < 300: Limite R$ 0.
  * Score entre 300 e 699: Aprova com limite de 10% da renda.
  * Score > 700: Aprova com limite de 30% da renda (teto).

### Fase 3: Ações Híbridas (APIs vs RPA)
*Integração com sistemas modernos e mainframes legados.*

* **Chamadas de Alta Velocidade:** Emissão de cartão virtual via requisições HTTP assíncronas (`httpx`) para o gateway do banco.
* **A Fila de RPA (Legado):** Despacho de ordem de criação de conta publicando tarefas em um broker **Redis**. Um worker em background (**TaskIQ** ou **Celery**) simula a execução manual do robô no mainframe.

### Fase 4: Especialização (Fine-Tuning), Serving Local e Blindagem
*Velocidade de inferência e alinhamento corporativo absoluto.*

* **O Cérebro Customizado (Unsloth + DPO):** Modelo de 8B (Llama-3) treinado localmente (`SFTTrainer` e `DPOTrainer`) para escrever laudos técnicos.
* **Serving de Produção:** Contêiner **Docker** com **vLLM** (PagedAttention) para alta concorrência.
* **Filtros de Saída:** Laudo final passa pelo **Microsoft Presidio** para mascaramento de CPFs, valores exatos e nomes próprios.

---

## ⚖️ 3. Restrições e Governança (Hard Mode)

Este projeto atende a três regras de ouro de governança para sistemas de IA corporativos:

* **🧱 A Regra do Pydantic Estrito (Zero Alucinação Estrutural)**
  O LLM não responde com texto livre. Todo output final da IA é obrigatoriamente formatado, parseado e devolvido como um objeto **JSON estritamente validado pelo schema do Pydantic V2**.

* **🛡️ A Regra de Contingência Imutável**
  O sistema é fault-tolerant. Em caso de queda da API do birô de crédito, o agente ReAct muda a estratégia e **emite um limite emergencial fixo de R$ 500,00**, gerando um log de degradação estrutural (sem erros 500).

* **⏸️ A Regra do State Management (Human-in-the-Loop)**
  Emissão autônoma limitada ao teto de R$ 10.000,00. Se o cálculo ultrapassar R$ 10.000,01, o nó do **LangGraph** aciona um `interrupt()`. O estado da memória é congelado no **SQLite** e o fluxo aguarda a rota `/override` ser chamada por um analista humano.

---

## 🧰 4. Libs e repos recomendados

Stack curto alinhado ao roadmap do CreditEngine e a projetos futuros. Prioridade de produto > curiosidade de pesquisa.

### Para este projeto (usar no roadmap)

| Prioridade | Lib / repo | Uso no CreditEngine |
|---|---|---|
| Alta | [LangGraph](https://github.com/langchain-ai/langgraph) | Agente ReAct + `interrupt()` HITL (já previsto na arquitetura) |
| Alta | [microsoft/presidio](https://github.com/microsoft/presidio) | Mascaramento de CPF, nomes e valores no laudo |
| Alta | [anomalyco/opencode](https://github.com/anomalyco/opencode) + [multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills) | Agente de código local + práticas Karpathy (acelera o desenvolvimento) |
| Alta | Eval próprio (golden sets / regressão) | Healing + RAG + bandas de risco — crítico antes de fine-tune |
| Média | Ideias de [xjdr-alt/entropix](https://github.com/xjdr-alt/entropix) | Sampling / reasoning na inferência do healer (sem treinar modelo) |
| Média | [Pillow](https://python-pillow.org/) + [OpenCV](https://opencv.org/) + [albumentations](https://github.com/albumentations-team/albumentations) | Visão / CNH e augmentação para antifraude documental |
| Média | [qubvel-org/segmentation_models.pytorch](https://github.com/qubvel-org/segmentation_models.pytorch) | Segmentação de documento (quando a fase multimodal sair do stub) |
| Média | [unslothai/unsloth](https://github.com/unslothai/unsloth) + DPO | Fine-tune local do modelo de laudos (Fase 4) |
| Média | [vllm-project/vllm](https://github.com/vllm-project/vllm) | Serving local de alta concorrência (Docker) |
| Baixa | [Jiayi-Pan/TinyZero](https://github.com/Jiayi-Pan/TinyZero) → [THUDM/slime](https://github.com/THUDM/slime) | Referência de pós-treino / RL quando houver reward + traces |
| Baixa | [patrick-kidger/jaxtyping](https://github.com/patrick-kidger/jaxtyping) | Tipagem de tensores se entrar modelo de score / embeddings próprios |

**Ordem sugerida no CreditEngine:** eval → agente LangGraph + HITL → Presidio → visão (Pillow/OpenCV/albumentations) → Unsloth/DPO → vLLM.

### Para projetos futuros (aprendizado / systems)

| Se você quer… | Comece por |
|---|---|
| Entender LLM de verdade | [karpathy/minGPT](https://github.com/karpathy/minGPT) → [karpathy/nanochat](https://github.com/karpathy/nanochat) → [KellerJordan/modded-nanogpt](https://github.com/KellerJordan/modded-nanogpt) |
| Arquiteturas além de Transformer | [state-spaces/mamba](https://github.com/state-spaces/mamba), [BlinkDL/RWKV-LM](https://github.com/BlinkDL/RWKV-LM), [jzhang38/TinyLlama](https://github.com/jzhang38/TinyLlama) |
| Framework minimalista | [tinygrad/tinygrad](https://github.com/tinygrad/tinygrad); [ml-explore/mlx](https://github.com/ml-explore/mlx) se for Apple Silicon |
| Perf / kernels GPU | [triton-lang/triton](https://github.com/triton-lang/triton) → [deepseek-ai/TileKernels](https://github.com/deepseek-ai/TileKernels) → [ScalingIntelligence/KernelBench](https://github.com/ScalingIntelligence/KernelBench) → [mirage-project/mirage](https://github.com/mirage-project/mirage) |
| Plataforma nova (linguagem + serve) | [modular/modular](https://github.com/modular/modular) (Mojo / MAX) |

**Fora do critical path deste repo:** hardware NPU/ANE, Tenstorrent, openpilot/AV, RE de GPU — ótimo para starred list, não para a esteira de crédito.
