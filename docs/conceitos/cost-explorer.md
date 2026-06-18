# Custos na AWS — Cost Explorer e Budgets (Aula 9)

> **Objetivo:** aprender a **ver** quanto a sua conta está gastando e a **avisar
> você** antes de estourar o crédito. Numa disciplina com Learner Lab/conta
> própria, isso evita sustos.

---

## Por que se preocupar com custo

Quase tudo que liga na nuvem **cobra por hora ligado**: o cluster EKS, os nós
EC2, o Load Balancer (ELB). Um cluster esquecido no fim de semana queima crédito
sem ninguém usar. As duas ferramentas abaixo respondem:

1. **Cost Explorer** → "quanto eu já gastei, e com o quê?"
2. **Budgets** → "me avise por e-mail quando eu passar de US$ X."

---

## Cost Explorer

Painel que mostra o gasto ao longo do tempo, com filtros por **serviço** (EKS,
EC2, ELB, S3, ECR, DynamoDB…), por dia/mês, por tag.

### Pelo Console

1. Console AWS → **Billing and Cost Management** → **Cost Explorer**.
2. Na 1ª vez, clique em **Enable Cost Explorer**.
   > ⏳ A AWS leva **até 24 h** para preencher os dados. **Ative no começo da
   > semana** — se ativar no dia da aula, o painel aparece vazio.
3. Em **Explore**, ajuste:
   - **Granularity:** Daily (diário).
   - **Group by → Service:** vê o gasto por serviço (onde está indo o dinheiro).
   - **Filters → Service:** isole EKS / EC2 / ElasticLoadBalancing.

### Pela CLI (conta própria; no Academy pode estar bloqueado)

**Linux/macOS (bash):**
```bash
aws ce get-cost-and-usage \
  --time-period Start=$(date -d '-7 days' +%F),End=$(date +%F) \
  --granularity DAILY \
  --metrics "UnblendedCost" \
  --group-by Type=DIMENSION,Key=SERVICE \
  --output table
```

**Windows (PowerShell):**
```powershell
$start = (Get-Date).AddDays(-7).ToString('yyyy-MM-dd')
$end   = (Get-Date).ToString('yyyy-MM-dd')
aws ce get-cost-and-usage `
  --time-period Start=$start,End=$end `
  --granularity DAILY `
  --metrics "UnblendedCost" `
  --group-by Type=DIMENSION,Key=SERVICE `
  --output table
```

> 🟢 **AWS Academy / Learner Lab:** a API de billing (`ce`, `budgets`) costuma
> ser **negada** pela role `voclabs`, e o Cost Explorer do Console pode não
> abrir. Nesse caso, use o **AWS Academy → Learner Lab → "Used"** (a barra de
> crédito gasto no topo do Lab) como termômetro. A lição de custo é a mesma:
> recurso ligado consome crédito.

---

## Budgets — alerta antes de estourar

Um **Budget** dispara um e-mail quando o gasto previsto/realizado passa de um
limite. É a sua rede de segurança.

### Pelo Console

1. Billing and Cost Management → **Budgets** → **Create budget**.
2. Tipo: **Cost budget** → Monthly.
3. Valor: um teto baixo (ex.: **US$ 5**) para um ambiente de estudo.
4. **Alert threshold:** 80% do valor → adicione seu **e-mail**.
5. Criar. Quando o gasto chegar a 80%, você recebe o aviso.

> 💡 **Por que 80% e não 100%:** o alerta em 80% dá tempo de reagir (destruir
> recursos) **antes** de estourar. Em 100% o estrago já aconteceu.

---

## Regra de ouro da disciplina

> **Subiu, testou, destruiu.** Ao fim de cada aula com recursos na nuvem:
> `kubectl delete -k infra/k8s/aws/`, `eksctl delete cluster ...`, apague tabelas
> DynamoDB e buckets de teste. Custo que não existe não precisa de alerta.

## Veja também

- [`aws-pricing-notes.md`](aws-pricing-notes.md) — quanto custa, por serviço.
- [`infra-aws-minima-por-semana.md`](infra-aws-minima-por-semana.md) — stack
  mínima e custo por semana.
