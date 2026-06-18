# Prática 17 — Site estático na internet: S3 vs EC2 (demo rápida)

> **Objetivo:** publicar a **mesma página HTML** na internet de **duas formas** e
> comparar: pelo **Amazon S3** (object storage, **sem servidor**, centavos) e por
> uma **instância EC2** (um **servidor de verdade** com Apache, **cobra por
> hora**). Você vê a página no navegador nos dois casos e entende a diferença de
> arquitetura e custo.
>
> **Quando:** Semana 5 (encaixa com a discussão de custo). É uma **demonstração
> rápida** — sobe em segundos (S3) ou ~2 min (EC2) e você apaga em seguida.
>
> 🐚 **Onde rodar — AWS CloudShell:** estes comandos foram pensados para o
> **terminal do console da AWS** (ícone `>_` no topo do console). O CloudShell já
> vem com `aws` configurado e é **bash**, então o HTML inline (`printf`, `<<HTML`)
> funciona direto, sem instalar nada e sem precisar de PowerShell. Abra o
> CloudShell, cole o bloco do caminho que quiser e pronto.
>
> ⚠️ **Custo:**
> - 🟢 **Caminho A (S3):** centavos. Não há compute — o S3 só devolve o arquivo.
> - 🔴 **Caminho B (EC2):** a instância **cobra por hora** enquanto existir.
>   **Apague ao terminar** (a limpeza está no fim de cada caminho).

---

## Conceito em 1 minuto

| | Amazon S3 (Caminho A) | Amazon EC2 (Caminho B) |
| --- | --- | --- |
| O que serve a página | o **próprio S3** (storage) | um **Apache** rodando numa VM |
| Tem servidor? | **não** (serverless) | **sim** (você administra) |
| Processa lógica? | não — só devolve o arquivo | pode (PHP, Python, etc.) |
| Custo | ~zero (centavos por requisição/armazenamento) | **por hora**, ligada ou não |
| Escala | automática, "infinita" | você dimensiona/escala na mão |
| Bom para | **site estático** (HTML/CSS/JS, imagens) | app dinâmico, processamento |

**Regra de ouro:** se a página é **estática** (não muda por usuário, sem
backend), **S3 é o caminho certo** — mais barato, sem manutenção. EC2 só quando
você precisa de um **servidor processando** algo.

---

## Caminho A — 🟢 S3 Static Website (recomendado: sem compute, centavos)

```bash
REGION=us-east-1
BUCKET=cloudtask-web-$(aws sts get-caller-identity --query Account --output text)-$(date +%s)

# 1. criar o bucket (us-east-1 dispensa LocationConstraint)
aws s3api create-bucket --bucket "$BUCKET" --region "$REGION"

# 2. liberar Block Public Access NESTE bucket
aws s3api put-public-access-block --bucket "$BUCKET" \
  --public-access-block-configuration BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false

# 3. policy pública de leitura — JSON INLINE (sem arquivo)
aws s3api put-bucket-policy --bucket "$BUCKET" --policy '{
  "Version":"2012-10-17",
  "Statement":[{"Sid":"PublicRead","Effect":"Allow","Principal":"*","Action":"s3:GetObject","Resource":"arn:aws:s3:::'"$BUCKET"'/*"}]
}'

# 4. habilitar hospedagem de site estático
aws s3 website "s3://$BUCKET/" --index-document index.html

# 5. enviar o index.html INLINE via stdin (o "-" lê do pipe; nada é gravado em disco)
printf '%s' '<!doctype html><html lang="pt-br"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CloudTask — servido por Amazon S3</title><style>:root{--bg:#0f172a;--card:#1e293b;--ink:#e2e8f0;--muted:#94a3b8;--accent:#38bdf8;--ok:#22c55e;--warn:#f59e0b;--hi:#ef4444}*{box-sizing:border-box;margin:0;padding:0}body{font-family:system-ui,Segoe UI,sans-serif;background:var(--bg);color:var(--ink);line-height:1.5}header{background:#020617;padding:16px 24px;display:flex;align-items:center;justify-content:space-between;border-bottom:2px solid var(--accent);flex-wrap:wrap;gap:8px}header h1{font-size:20px}.logo{color:var(--accent)}.badge{background:var(--accent);color:#020617;font-weight:700;padding:6px 12px;border-radius:999px;font-size:13px}main{max-width:1000px;margin:24px auto;padding:0 16px}.toolbar{display:flex;gap:8px;margin-bottom:20px}.toolbar input{flex:1;padding:10px 12px;border-radius:8px;border:1px solid #334155;background:var(--card);color:var(--ink)}.toolbar button{padding:10px 16px;border:0;border-radius:8px;background:var(--accent);color:#020617;font-weight:700}.board{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}@media(max-width:700px){.board{grid-template-columns:1fr}}.col{background:#0b1220;border:1px solid #1e293b;border-radius:12px;padding:12px}.col h2{font-size:13px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);margin-bottom:10px}.card{background:var(--card);border-radius:10px;padding:12px;margin-bottom:10px;border-left:4px solid var(--accent)}.card h3{font-size:15px;margin-bottom:6px}.card p{font-size:13px;color:var(--muted)}.pill{display:inline-block;font-size:11px;font-weight:700;padding:2px 8px;border-radius:999px;margin-top:8px}.p-hi{background:rgba(239,68,68,.2);color:var(--hi)}.p-md{background:rgba(245,158,11,.2);color:var(--warn)}.p-lo{background:rgba(34,197,94,.2);color:var(--ok)}.arch{margin:28px 0;background:#0b1220;border:1px dashed #334155;border-radius:12px;padding:16px}.arch h2{font-size:14px;color:var(--accent);margin-bottom:10px}.arch pre{font-family:ui-monospace,Consolas,monospace;font-size:12.5px;white-space:pre;overflow-x:auto}footer{text-align:center;color:var(--muted);font-size:12px;padding:24px}</style></head><body><header><h1><span class="logo">&#9729; CloudTask</span> AI SaaS</h1><span class="badge">Servido por Amazon S3</span></header><main><div class="toolbar"><input placeholder="Nova tarefa (somente visual)..." disabled><button disabled>Adicionar</button></div><div class="board"><div class="col"><h2>A fazer</h2><div class="card"><h3>Configurar VPC</h3><p>Subnets publica e privada</p><span class="pill p-hi">alta</span></div><div class="card"><h3>Escrever testes</h3><p>Cobrir as rotas de tarefas</p><span class="pill p-md">media</span></div></div><div class="col"><h2>Fazendo</h2><div class="card"><h3>Deploy no EKS</h3><p>Imagem do ECR + Service</p><span class="pill p-hi">alta</span></div></div><div class="col"><h2>Feito</h2><div class="card"><h3>Upload no S3</h3><p>URL pre-assinada</p><span class="pill p-lo">baixa</span></div><div class="card"><h3>CRUD de tarefas</h3><p>FastAPI + PostgreSQL</p><span class="pill p-md">media</span></div></div></div><div class="arch"><h2>Arquitetura desta entrega (Amazon S3)</h2><pre>  [ Seu navegador ]
        |  HTTP (porta 80, implicita)
        v
  [ Endpoint de site do S3 ]
  http://BUCKET.s3-website-us-east-1.amazonaws.com
        |
        v
  [ Bucket S3 ] --> index.html (objeto publico, somente leitura)

  Sem servidor e sem container: o proprio S3 entrega o arquivo.
  Custo ~zero. Nao processa nada, so devolve o HTML.</pre></div></main><footer>CloudTask AI SaaS &middot; pagina estatica de demonstracao (sem backend) &middot; Computacao em Nuvem / UNINTER</footer></body></html>' \
  | aws s3 cp - "s3://$BUCKET/index.html" --content-type text/html

# 6. a URL pública (SEM porta — S3 website responde na 80/HTTP padrão)
echo "http://$BUCKET.s3-website-$REGION.amazonaws.com"
```

Abra a URL impressa no navegador → a página aparece, servida **direto pelo S3**.

> 💡 **Sem porta na URL:** o endpoint de site do S3 responde em HTTP na **porta
> 80** (implícita). Note que é o endpoint `s3-website-...`, diferente do endpoint
> de API do bucket (`s3.amazonaws.com`).

### 🔥 Limpeza (Caminho A)

```bash
aws s3 rm "s3://$BUCKET" --recursive
aws s3api delete-bucket --bucket "$BUCKET"
```

---

## Caminho B — 🔴 EC2 + user-data inline (fallback, se S3 público for bloqueado)

> Use este caminho quando o **Block Public Access** estiver travado na conta (não
> dá para liberar o bucket), ou só para **ver um servidor de verdade** entregando
> a mesma página. ⚠️ **Cobra por hora** — apague no fim.

```bash
REGION=us-east-1
AMI=$(aws ssm get-parameters --region "$REGION" \
  --names /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64 \
  --query "Parameters[0].Value" --output text)
VPC=$(aws ec2 describe-vpcs --region "$REGION" --filters Name=isDefault,Values=true --query "Vpcs[0].VpcId" --output text)
SUBNET=$(aws ec2 describe-subnets --region "$REGION" --filters Name=vpc-id,Values="$VPC" --query "Subnets[0].SubnetId" --output text)

# SG abrindo a porta 80 para a internet
SG=$(aws ec2 create-security-group --region "$REGION" --group-name web-demo-sg \
  --description "HTTP 80" --vpc-id "$VPC" --query GroupId --output text)
aws ec2 authorize-security-group-ingress --region "$REGION" --group-id "$SG" \
  --protocol tcp --port 80 --cidr 0.0.0.0/0

# EC2 com a página INLINE no user-data
IID=$(aws ec2 run-instances --region "$REGION" \
  --image-id "$AMI" --instance-type t3.micro \
  --security-group-ids "$SG" --subnet-id "$SUBNET" --associate-public-ip-address \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=web-demo}]' \
  --user-data '#!/bin/bash
dnf install -y httpd
systemctl enable --now httpd
cat > /var/www/html/index.html <<HTML
<!doctype html><html lang="pt-br"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CloudTask — servido por Amazon EC2</title><style>:root{--bg:#0f172a;--card:#1e293b;--ink:#e2e8f0;--muted:#94a3b8;--accent:#f59e0b;--ok:#22c55e;--warn:#f59e0b;--hi:#ef4444}*{box-sizing:border-box;margin:0;padding:0}body{font-family:system-ui,Segoe UI,sans-serif;background:var(--bg);color:var(--ink);line-height:1.5}header{background:#020617;padding:16px 24px;display:flex;align-items:center;justify-content:space-between;border-bottom:2px solid var(--accent);flex-wrap:wrap;gap:8px}header h1{font-size:20px}.logo{color:var(--accent)}.badge{background:var(--accent);color:#020617;font-weight:700;padding:6px 12px;border-radius:999px;font-size:13px}main{max-width:1000px;margin:24px auto;padding:0 16px}.toolbar{display:flex;gap:8px;margin-bottom:20px}.toolbar input{flex:1;padding:10px 12px;border-radius:8px;border:1px solid #334155;background:var(--card);color:var(--ink)}.toolbar button{padding:10px 16px;border:0;border-radius:8px;background:var(--accent);color:#020617;font-weight:700}.board{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}@media(max-width:700px){.board{grid-template-columns:1fr}}.col{background:#0b1220;border:1px solid #1e293b;border-radius:12px;padding:12px}.col h2{font-size:13px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);margin-bottom:10px}.card{background:var(--card);border-radius:10px;padding:12px;margin-bottom:10px;border-left:4px solid var(--accent)}.card h3{font-size:15px;margin-bottom:6px}.card p{font-size:13px;color:var(--muted)}.pill{display:inline-block;font-size:11px;font-weight:700;padding:2px 8px;border-radius:999px;margin-top:8px}.p-hi{background:rgba(239,68,68,.2);color:var(--hi)}.p-md{background:rgba(245,158,11,.2);color:var(--warn)}.p-lo{background:rgba(34,197,94,.2);color:var(--ok)}.arch{margin:28px 0;background:#0b1220;border:1px dashed #334155;border-radius:12px;padding:16px}.arch h2{font-size:14px;color:var(--accent);margin-bottom:10px}.arch pre{font-family:ui-monospace,Consolas,monospace;font-size:12.5px;white-space:pre;overflow-x:auto}footer{text-align:center;color:var(--muted);font-size:12px;padding:24px}</style></head><body><header><h1><span class="logo">&#9729; CloudTask</span> AI SaaS</h1><span class="badge">Servido por Amazon EC2</span></header><main><div class="toolbar"><input placeholder="Nova tarefa (somente visual)..." disabled><button disabled>Adicionar</button></div><div class="board"><div class="col"><h2>A fazer</h2><div class="card"><h3>Configurar VPC</h3><p>Subnets publica e privada</p><span class="pill p-hi">alta</span></div><div class="card"><h3>Escrever testes</h3><p>Cobrir as rotas de tarefas</p><span class="pill p-md">media</span></div></div><div class="col"><h2>Fazendo</h2><div class="card"><h3>Deploy no EKS</h3><p>Imagem do ECR + Service</p><span class="pill p-hi">alta</span></div></div><div class="col"><h2>Feito</h2><div class="card"><h3>Upload no S3</h3><p>URL pre-assinada</p><span class="pill p-lo">baixa</span></div><div class="card"><h3>CRUD de tarefas</h3><p>FastAPI + PostgreSQL</p><span class="pill p-md">media</span></div></div></div><div class="arch"><h2>Arquitetura desta entrega (Amazon EC2)</h2><pre>  [ Seu navegador ]
        |  HTTP (porta 80)
        v
  [ Security Group ]  porta 80 aberta para 0.0.0.0/0
        |
        v
  [ Instancia EC2 ]  Amazon Linux 2023 + Apache (httpd)
        |  IP publico, dentro da VPC/Subnet default
        v
  [ /var/www/html/index.html ]

  Um servidor de verdade processa e entrega a pagina.
  Cobra por hora enquanto a instancia existir.</pre></div></main><footer>CloudTask AI SaaS &middot; pagina estatica de demonstracao (sem backend) &middot; Computacao em Nuvem / UNINTER</footer></body></html>
HTML' \
  --query "Instances[0].InstanceId" --output text)

aws ec2 wait instance-running --region "$REGION" --instance-ids "$IID"
IP=$(aws ec2 describe-instances --region "$REGION" --instance-ids "$IID" \
  --query "Reservations[0].Instances[0].PublicIpAddress" --output text)
echo "http://$IP        (espere ~1-2 min o httpd instalar)"
```

Abra `http://<IP>` no navegador (após ~1–2 min, tempo do Apache instalar e subir).

> 💡 **Por que esperar:** o `user-data` roda **uma vez** no boot — instala o
> Apache, sobe o serviço e escreve o `index.html`. Antes disso a porta 80 ainda
> não responde.

### 🔥 Limpeza (Caminho B — a ordem importa)

```bash
aws ec2 terminate-instances --region "$REGION" --instance-ids "$IID"
aws ec2 wait instance-terminated --region "$REGION" --instance-ids "$IID"
aws ec2 delete-security-group --region "$REGION" --group-id "$SG"
```

> ⚠️ Termine a **instância antes** de apagar o Security Group (o SG não some
> enquanto estiver em uso pela instância).

---

## Comparando os dois (o que você acabou de ver)

| | S3 (A) | EC2 (B) |
| --- | --- | --- |
| Passos | bucket + policy + upload | AMI + VPC + SG + instância + user-data |
| Tempo até no ar | segundos | ~1–2 min (boot + Apache) |
| Cobra parado? | praticamente não | **sim, por hora** |
| Você administra um SO? | não | **sim** (patches, Apache...) |
| Mesma página? | **sim** — idêntica | **sim** — idêntica |

**A lição:** os dois entregam o **mesmo HTML**, mas o S3 não tem servidor nenhum
por trás — é mais barato, escala sozinho e você não cuida de nada. Para conteúdo
**estático**, S3 ganha. EC2 só faz sentido quando há um **programa rodando** que
precisa de um servidor.

---

## Se algo der errado

| Sintoma | Causa provável | Fix |
| --- | --- | --- |
| `403 Forbidden` na URL do S3 | Block Public Access ainda ligado, ou policy não aplicada | repita os passos 2 e 3 |
| `AccessDenied` ao criar policy pública | conta/Org bloqueia bucket público (comum no Learner Lab) | use o **Caminho B (EC2)** |
| URL do S3 não abre | usou o endpoint errado | tem que ser `s3-website-<região>...`, não `s3.amazonaws.com` |
| `web-demo-sg already exists` | rodou o Caminho B 2× | apague o SG antigo ou troque `--group-name` |
| `http://<IP>` não responde | Apache ainda instalando | espere ~2 min; confira o SG abrindo a 80 |
| EC2 não tem IP público | subnet sem auto-assign | já tratado por `--associate-public-ip-address` |

---

## Próximos passos

| Quero... | Vá em |
| --- | --- |
| Entender S3 a fundo (storage, Data Lake) | [`../conceitos/s3-efs-datalake.md`](../conceitos/s3-efs-datalake.md) |
| Uploads de arquivo pela app (S3 real) | [`06-uploads-modo-s3.md`](06-uploads-modo-s3.md) |
| Console na mão vs script (mesma ideia de automação) | [`16-console-vs-script.md`](16-console-vs-script.md) |
| Limpar custos que escapam | [`99-troubleshooting.md`](99-troubleshooting.md) (seção 💸 Custos) |
