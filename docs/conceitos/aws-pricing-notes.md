# Preços dos serviços usados na disciplina (Aula 9)

> **Aviso:** preços mudam e variam por região. Os números abaixo são **ordens de
> grandeza** (região `us-east-1`, 2024–2025) só para você ter **intuição de
> custo** — não são cotação oficial. Confira sempre a
> [calculadora oficial](https://calculator.aws/).

---

## Visão rápida por serviço

| Serviço | Como cobra | Ordem de grandeza | O caro é… |
| --- | --- | --- | --- |
| **EC2** (nós do EKS) | por hora ligada (por tipo) | `t3.small` ≈ US$ 0,02/h | deixar ligado 24/7 |
| **EKS** (control plane) | por hora do cluster | ≈ US$ 0,10/h (~US$ 73/mês) | o cluster existir, mesmo vazio |
| **ELB** (Load Balancer) | por hora + por dado | ≈ US$ 0,02/h + tráfego | esquecer o Service LoadBalancer ligado |
| **S3** | GB armazenado + requisições | ≈ US$ 0,023/GB-mês | volume grande; requisições são centavos |
| **ECR** | GB de imagem armazenada | ≈ US$ 0,10/GB-mês | muitas imagens antigas acumuladas |
| **DynamoDB** (PAY_PER_REQUEST) | por requisição + GB | centavos para a aula | tabela gigante; on-demand é barato p/ pouco uso |
| **Secrets Manager** | por segredo/mês + chamadas | ≈ US$ 0,40/segredo-mês | muitos segredos esquecidos |
| **Data transfer (egress)** | GB que **sai** da AWS | ≈ US$ 0,09/GB | baixar muito dado para fora |

> 📌 **Padrão que se repete:** o que pesa é **tempo ligado** (EKS, EC2, ELB) e
> **egress**. Armazenamento e requisições (S3, ECR, DynamoDB) costumam ser
> centavos no volume de uma aula.

---

## O que mais dói no orçamento de estudo

1. **Cluster EKS esquecido ligado** → control plane (~US$ 0,10/h) **+** nós EC2
   **+** ELB. Um fim de semana esquecido pode passar de US$ 10.
2. **ELB órfão** — você apaga o app mas o Service LoadBalancer continua. Confira
   em *EC2 → Load Balancers*.
3. **Volumes/snapshots EBS** que sobram após deletar nós.

---

## Dicas para gastar pouco (ambiente de estudo)

- **Destrua ao terminar** (a dica que mais economiza): `eksctl delete cluster`,
  `kubectl delete -k infra/k8s/aws/`, `aws dynamodb delete-table`.
- **Nós pequenos e poucos:** `t3.small`/`t3.medium`, 2 nós. Por isso o
  [`hpa.yaml`](../../infra/k8s/aws/hpa.yaml) usa `maxReplicas: 5` (teto de custo).
- **S3 Standard-IA / lifecycle:** para dados pouco acessados, classes mais
  baratas; regra de lifecycle apaga objetos antigos.
- **ECR:** apague tags antigas (lifecycle policy) — você só precisa da `latest`
  e talvez algumas versões.
- **DynamoDB on-demand (`PAY_PER_REQUEST`)** para uso esporádico — não paga
  capacidade reservada parada.
- **Use o crédito do Learner Lab** para o que cobra por hora; o trabalho local
  (Kind, modo `local` de storage/eventos) é **grátis**.

## Veja também

- [`cost-explorer.md`](cost-explorer.md) — ver gastos e criar alertas.
- [`infra-aws-minima-por-semana.md`](infra-aws-minima-por-semana.md) — stack
  mínima por semana.
