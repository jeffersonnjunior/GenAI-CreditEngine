# Manual de Compliance — Concessão de Crédito (amostra)

Documento interno de exemplo para o RAG do GenAI-CreditEngine.
Não substitui política jurídica real.

## Faixas de score e limite

A concessão de limite é determinística e baseada no score do birô:

- Score abaixo de 300: a proposta deve ser negada e o limite concedido é R$ 0,00.
- Score entre 300 e 699 (inclusive o piso 300): aprovar com limite de 10% da renda mensal declarada.
- Score igual ou superior a 700: aprovar com limite de 30% da renda mensal declarada.

O motor de risco não pode alterar essas faixas sem aprovação de Compliance.

## Contingência de birô indisponível

Quando a API do birô de crédito (Serasa/Boa Vista) estiver indisponível ou em timeout,
o sistema deve degradar de forma controlada:

- Emitir limite emergencial fixo e imutável de R$ 500,00.
- Registrar log de degradação estrutural.
- Não retornar erro HTTP 500 ao cliente por falha do birô.

Essa regra prioriza continuidade do onboarding sob risco limitado.

## Human-in-the-Loop e teto autônomo

Emissão autônoma de cartão é permitida apenas para limites calculados de até R$ 10.000,00.
Se o limite calculado ultrapassar R$ 10.000,01, a esteira deve interromper o fluxo automático
e aguardar override de um analista humano.

## Qualidade do payload de proposta

Propostas com JSON inválido devem passar por self-healing estrutural (correção de tipos e campos)
antes da avaliação de risco. É vedado inventar score, renda ou CPF ausentes no payload original.
Após esgotar as tentativas de reparo, a API deve rejeitar a proposta com erro de validação.

## Uso de evidência de política

Antes de justificar a decisão de crédito, o agente deve recuperar trechos relevantes deste manual
(RAG) e citar a regra aplicada na razão da decisão, preservando rastreabilidade de compliance.
