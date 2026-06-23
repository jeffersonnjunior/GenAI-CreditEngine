# Manual de Compliance — Política de Crédito GenAI CreditEngine

## 1. Categorias por Região e Score

Clientes da região Sul com Score acima de 700 têm direito à categoria Black, com limite de até 30% da renda mensal comprovada.

Clientes da região Sudeste com Score entre 650 e 699 são elegíveis à categoria Gold, com limite de até 20% da renda mensal comprovada.

Clientes da região Norte ou Nordeste com Score acima de 600 recebem categoria Silver, com limite de até 15% da renda mensal comprovada.

Clientes da região Centro-Oeste com Score acima de 550 são aprovados na categoria Standard, com limite de até 10% da renda mensal comprovada.

## 2. Limites por Faixa de Score

Score abaixo de 300 implica negação automática de crédito, com limite zero independentemente da renda.

Score entre 300 e 499 autoriza limite emergencial de até 10% da renda mensal comprovada, sujeito a análise documental.

Score entre 500 e 699 autoriza limite de até 10% da renda mensal comprovada para todas as regiões sem categoria especial.

Score igual ou acima de 700 autoriza limite de até 30% da renda mensal comprovada, respeitando o teto regulatório de R$ 10.000,00.

## 3. Contingência e Degradação

Em caso de indisponibilidade do birô de crédito (Serasa, Boa Vista ou Banco Central), o sistema deve aplicar limite emergencial fixo de R$ 500,00 e registrar log de degradação estrutural.

Timeouts superiores a 5 segundos em integrações externas devem ser tratados como indisponibilidade parcial, acionando política de contingência.

## 4. Fraude e Identidade

Divergência entre o nome informado no cadastro e o nome extraído do documento de identidade implica bloqueio imediato por suspeita de fraude documental.

CPF inválido, duplicado ou com restrição ativa no birô impede a concessão de qualquer limite de crédito.

## 5. Human-in-the-Loop

Limites calculados acima de R$ 10.000,00 exigem aprovação manual de analista de crédito antes da emissão do cartão.

Propostas com renda mensal comprovada inferior a R$ 1.000,00 são direcionadas automaticamente para fila de revisão manual.
