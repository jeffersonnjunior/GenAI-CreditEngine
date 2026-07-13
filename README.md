# GenAI-CreditEngine

🏆 O DESAFIO MESTRE: GenAI-CreditEngine (Plataforma Multiagente de Hiperautomação e Concessão de Crédito)

🏢 1. O Problema de Negócio (A Dor da Empresa)
Você é o Tech Lead do núcleo de Risco e Onboarding de um Banco Digital (uma *Credit Engine*). A sua instituição tenta escalar a base de clientes, mas a esteira de abertura de contas está colapsando.

O Cenário de Crise:

- **Fraude de Identidade Visuais:** Quadrilhas estão usando edição de imagem e deepfakes documentais básicos para abrir contas com CPFs roubados e dados divergentes. O OCR legado do banco não cruza as informações corretamente.
- **Gargalo Humano na Mesa de Crédito:** O sistema atual bloqueia todas as propostas que fogem de um "IF/ELSE" simples. Analistas humanos estão gastando dias revisando PDFs de clientes legítimos para liberar limites de crédito, travando a aquisição de novos usuários.
- **Quedas no Ecossistema Externo:** Quando o birô de crédito (Serasa/Boa Vista) ou o Banco Central ficam lentos, a API do banco dá *timeout* e o cliente desiste de abrir a conta.

O Seu Objetivo (O OKR):
Construir o **`GenAI-CreditEngine`**, uma plataforma orquestrada por agentes autônomos capaz de ingerir a proposta, auditar as imagens dos documentos em tempo real e decidir a aprovação ou negação do crédito em segundos. O sistema deve emitir cartões de forma 100% autônoma para limites de até R$ 10.000,00 e barrar divergências de identidade com precisão extrema.

🏗️ 2. A Arquitetura do Sistema (O Desafio End-to-End)
Como Tech Lead, você deve construir este ecossistema do zero, integrando 4 grandes blocos arquiteturais baseados em Clean Architecture:

Fase 1: Ingestão Resiliente e RAG Enterprise (Compliance)
O banco não pode errar a leitura da própria política de crédito.

- **O Desafio Técnico:** Subir a API base em FastAPI assíncrono. O payload de entrada com os dados da conta sofre de instabilidade. Você deve implementar um loop de *Self-Healing*: se o JSON estourar a validação do Pydantic V2, o LLM intercepta o erro de traceback e corrige a própria estrutura em até 3 tentativas.
- **A Regra de Negócio (RAG):** O motor não pode inventar taxas ou regras. Você deve indexar o manual de compliance em um ChromaDB. O Agente usará o algoritmo de *Sentence Window Retrieval* combinado com *Reciprocal Rank Fusion (RRF)* para puxar a regra exata (ex: "Clientes do Sul com Score 700 ganham categoria Black") antes de calcular o limite.

Fase 2: O Cérebro Autônomo (ReAct) e Visão Multimodal
O coração do sistema é cognitivo, não linear.

- **O Motor de Decisão (LangGraph):** Você não vai programar a rota. Vai criar um agente em padrão ReAct (Reason + Action). Ele pensa: *"Preciso validar a identidade. Vou acionar a ferramenta OCR"* e depois *"Identidade limpa. Vou puxar a pontuação de crédito"*.
- **O Desafio Multimodal:** O cliente envia a foto da CNH. Usando Pillow, OpenCV e Modelos de Visão Multimodal, o sistema deve ler os dados da foto e fazer um *Cross-Check* estrito. Se a imagem disser "José" e o JSON disser "João", o pipeline aborta por fraude documental.
- **A Matemática de Risco:** O Agente avalia o score. Abaixo de 300? Limite R$ 0. Entre 300 e 699? Aprova com limite de 10% da renda. Acima de 700? Aprova com limite de 30% da renda (teto).

Fase 3: Ações Híbridas (APIs vs RPA)
O banco tem sistemas modernos e mainframes da década de 90. O Agente deve saber conversar com os dois.

- **Chamadas de Alta Velocidade:** Para emitir o cartão virtual, o Agente aciona a ferramenta que dispara uma requisição HTTP assíncrona (`httpx`) para o gateway do banco.
- **A Fila de RPA (Legado):** O banco de dados central não tem API. O Agente deve despachar a ordem de criação da conta publicando uma tarefa em um broker Redis. Um worker em background (`TaskIQ` ou `Celery`) simula a execução manual do robô no mainframe.

Fase 4: Especialização (Fine-Tuning), Serving Local e Blindagem
O sistema precisa de velocidade de inferência e alinhamento corporativo absoluto.

- **O Cérebro Customizado (Unsloth + DPO):** Você vai treinar localmente um modelo de 8B (Llama-3). O objetivo é usar SFTTrainer e DPOTrainer para forçar o modelo a escrever laudos bancários técnicos e rejeitar respostas coloquiais.
- **Serving de Produção:** Subir esse modelo especializado em um contêiner Docker usando vLLM (PagedAttention) para segurar alta concorrência.
- **Filtros de Saída:** O laudo final passa pelo Microsoft Presidio. CPFs, valores exatos de conta e nomes próprios são mascarados antes do JSON final ser devolvido ao usuário ou salvo no banco.

⚖️ 3. As Restrições do Tech Lead (Hard Mode)
Para o seu projeto ser considerado nível Sênior/Lead em Inteligência Artificial, ele não pode violar estas três regras de ouro de governança:

- **A Regra do Pydantic Estrito (Zero Alucinação Estrutural):** O seu LLM não pode responder com texto livre. Todo e qualquer *output* final da IA deve obrigatoriamente ser formatado, parseado e devolvido como um objeto JSON estritamente validado pelo schema do Pydantic V2. Se o agente gerar um laudo fora da formatação, o caso falha.
- **A Regra de Contingência Imutável:** O sistema é *fault-tolerant*. Se você simular a queda da API do birô de crédito (desligar o mock), a sua esteira não pode dar erro 500. O agente ReAct deve perceber a falha de conexão, mudar a estratégia de pensamento e emitir o limite emergencial fixo de R$ 500,00, gerando um log de aviso de degradação estrutural.
- **A Regra do State Management (Human-in-the-Loop):** O Agente tem autonomia para emitir cartões na hora até o teto de R$ 10.000,00. No exato instante em que o cálculo de risco do LLM ultrapassar R$ 10.000,01, o nó do LangGraph deve obrigatoriamente acionar um `interrupt()`. O estado da memória do Agente é congelado no SQLite. O código de emissão do cartão não pode prosseguir até que a rota externa `/override` seja chamada por um "analista". Se um limite de 15k passar sem interrupção, o fluxo está reprovado na homologação.
