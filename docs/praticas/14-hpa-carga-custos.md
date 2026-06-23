# Prática 14 — Escalabilidade (HPA), teste de carga e custos (Aula 9)

> **Objetivo:** ligar o **autoscaling** da API, gerar carga e **ver as réplicas
> subirem e descerem** sozinhas — e depois olhar o custo disso.
>
> **Pré-req:** app rodando no **EKS** ([`12-eks-deploy.md`](12-eks-deploy.md)).
> Funciona também no **Kind** se você instalar o metrics-server (ver §6).
>
> **Versão da API:** `0.5.0`. **Custo:** 💸 segue o do cluster EKS — **destrua ao fim**.

---

## 1. Instalar o metrics-server (pré-requisito do HPA)

O HPA decide escalar olhando o uso de CPU. Quem coleta essa métrica é o
**metrics-server**. Sem ele, o HPA fica com alvo `<unknown>` e **não escala**.

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
# espere ficar pronto e confirme que 'kubectl top' funciona:
kubectl -n kube-system rollout status deploy/metrics-server
kubectl top pods -n cloudtask
```

> 🩺 `kubectl top` dá erro? Espere 1–2 min (o metrics-server leva um tempo para
> coletar). No **Kind**, pode ser preciso o patch `--kubelet-insecure-tls` (ver §6).

✅ **Checkpoint 1:** `kubectl top pods -n cloudtask` mostra CPU/memória dos pods.

---

## 2. Aplicar o HPA

```bash
kubectl apply -f infra/k8s/aws/hpa.yaml
kubectl get hpa -n cloudtask
```

Saída esperada (alvo começa baixo, REPLICAS no mínimo 2):

```text
NAME            REFERENCE                  TARGETS       MINPODS   MAXPODS   REPLICAS
cloudtask-api   Deployment/cloudtask-api   cpu: 2%/60%   2         5         2
```

> Se `TARGETS` aparecer `<unknown>/60%`, o metrics-server ainda não respondeu
> (volte ao §1) **ou** o Deployment não declara `resources.requests.cpu` (o
> nosso declara — ver `deployment-eks.yaml`).

✅ **Checkpoint 2:** HPA criado, `TARGETS` mostrando uma porcentagem (não `<unknown>`).

---

## 3. Gerar carga e observar a escala

Abra **dois terminais**.

**Terminal A — observar (deixe rodando):**
```bash
kubectl get hpa -n cloudtask -w     # acompanha TARGETS e REPLICAS mudando
# (ou, em outra aba) kubectl get pods -n cloudtask -w
```

**Terminal B — disparar carga** contra o DNS do ELB:

**Linux/macOS (bash):**
```bash
LB=$(kubectl get svc cloudtask-api-lb -n cloudtask \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
python scripts/load-test-simple.py --url http://$LB/tasks --concurrency 50 --duration 120
```

**Windows (PowerShell):**
```powershell
$LB = kubectl get svc cloudtask-api-lb -n cloudtask `
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
python scripts/load-test-simple.py --url http://$LB/tasks --concurrency 50 --duration 120
```

**O que observar no Terminal A:**
1. `TARGETS` sobe acima de `60%`.
2. `REPLICAS` cresce `2 → 3 → …` (até no máximo `5`).
3. Pods novos aparecem `Running`.
4. **Ao parar a carga**, depois de ~2 min (janela de estabilização do
   `scaleDown`), `REPLICAS` volta para `2`.

✅ **Checkpoint 3:** réplicas sobem sob carga e voltam ao mínimo depois. É a
**elasticidade** funcionando.

---

## 4. Relacionar com custo

Mais réplicas → mais CPU/memória → podem exigir **mais nós EC2** → **mais
US$/hora**. Por isso o HPA tem `maxReplicas: 5` (teto).

- **Console:** Cost Explorer (filtre por EKS/EC2/ElasticLoadBalancing) e crie um
  **Budget** com alerta — passo a passo em
  [`../conceitos/cost-explorer.md`](../conceitos/cost-explorer.md).
- **Quanto custa o quê:** [`../conceitos/aws-pricing-notes.md`](../conceitos/aws-pricing-notes.md).

✅ **Checkpoint 4:** você consegue dizer **qual serviço** mais pesa (dica: o
cluster EKS + nós EC2 + ELB ligados por hora).

---

## 5. 🔥 Cleanup

```bash
kubectl delete -f infra/k8s/aws/hpa.yaml     # remove só o autoscaler
# ao terminar a aula inteira, destrua o cluster (ver prática 12 §7):
kubectl delete -k infra/k8s/aws/
eksctl delete cluster --name <seu-cluster>
```

---

## 6. (Opcional) HPA no Kind, sem custo

Dá para treinar o HPA **localmente** no Kind ([`10-kubernetes-kind-local.md`](10-kubernetes-kind-local.md)):

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
# no Kind o metrics-server precisa ignorar o TLS do kubelet:
kubectl -n kube-system patch deploy metrics-server --type=json \
  -p='[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]'
```

> ⚠️ O `hpa.yaml` mira o Deployment **`cloudtask-api`** (nome usado no EKS). No
> Kind o Deployment local chama-se **`api`** — ajuste `scaleTargetRef.name` para
> `api` (ou aplique no EKS, onde o nome já bate). Não use `--kubelet-insecure-tls`
> em produção: é só para o ambiente local do Kind.

---

## Se algo der errado

| Sintoma | Causa provável |
| --- | --- |
| `TARGETS: <unknown>/60%` | metrics-server não pronto (§1) ou sem `resources.requests` |
| HPA não passa de `minReplicas` | carga insuficiente — aumente `--concurrency`/`--duration` |
| `kubectl top` dá erro no Kind | falta o patch `--kubelet-insecure-tls` (§6) |
| Réplicas não voltam logo | normal: `scaleDown` espera 2 min (anti-flapping) |
