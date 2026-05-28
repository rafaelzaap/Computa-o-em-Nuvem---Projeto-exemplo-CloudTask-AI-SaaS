<!-- Área do Banner -->
<div align="center" style="background-color: white; max-width: 70%;">
  <img alt="BANNER do repositório CloudTask AI SaaS — disciplina Computação em Nuvem" title="Banner_CloudTask_AI_SaaS" src=".readme_docs/Banner_Github_NCPU.png" width="100%" />
</div>

<!-- Título e breve descrição do repositório -->
<div align="center">
  <h1>CloudTask AI SaaS</h1>
  <p><b>Projeto-exemplo da disciplina <i>Computação em Nuvem</i> — N-CPU / UNINTER.</b></p>
  <p>Um mini SaaS de gerenciamento de tarefas em <b>Python + FastAPI</b>, evoluído aula a aula até rodar em <b>AWS (ECR, EKS, S3, DynamoDB, CDK)</b>.</p>
</div>

<!-- Ícones ou links das tecnologias usadas -->
<p align="center">
  <a href="https://www.python.org/" title="Python"><img src="https://github.com/get-icon/geticon/raw/master/icons/python.svg" alt="Python" height="21px"></a>
  +
  <a href="https://fastapi.tiangolo.com/" title="FastAPI"><img src="https://github.com/get-icon/geticon/raw/master/icons/fastapi.svg" alt="FastAPI" height="21px"></a>
  +
  <a href="https://www.docker.com/" title="Docker"><img src="https://github.com/get-icon/geticon/raw/master/icons/docker-icon.svg" alt="Docker" height="21px"></a>
  +
  <a href="https://www.postgresql.org/" title="PostgreSQL"><img src="https://github.com/get-icon/geticon/raw/master/icons/postgresql.svg" alt="PostgreSQL" height="21px"></a>
  +
  <a href="https://kubernetes.io/" title="Kubernetes"><img src="https://github.com/get-icon/geticon/raw/master/icons/kubernetes.svg" alt="Kubernetes" height="21px"></a>
  +
  <a href="https://aws.amazon.com/" title="AWS"><img src="https://github.com/get-icon/geticon/raw/master/icons/aws.svg" alt="AWS" height="21px"></a>
</p>

<!-- Escudos de licença e contador de contribuidores -->
<p align="center">
  <a href="https://github.com/N-CPUninter/Computa-o-em-Nuvem---Projeto-exemplo-CloudTask-AI-SaaS/graphs/contributors">
    <img src="https://img.shields.io/github/contributors/N-CPUninter/Computa-o-em-Nuvem---Projeto-exemplo-CloudTask-AI-SaaS?color=%237159c1&logoColor=%237159c1&style=flat" alt="Contributors">
  </a>
  <a href="https://opensource.org/license/gpl-3-0">
    <img src="https://img.shields.io/github/license/N-CPUninter/Computa-o-em-Nuvem---Projeto-exemplo-CloudTask-AI-SaaS?color=%23BD0000" alt="License">
  </a>
</p>

<!-- Descrição do repositório e demais dados -->
## Descrição

Este repositório contém o **projeto-exemplo da disciplina Computação em Nuvem** do curso de Análise e Desenvolvimento de Sistemas (ADS), N-CPU/UNINTER.

O objetivo é construir, ao longo de **12 aulas (6 semanas)**, um pequeno **SaaS de gerenciamento de tarefas (CloudTask AI SaaS)** usando FastAPI, levando a aplicação de um simples `GET /health` local até um deploy completo em **AWS (ECR + EKS + S3 + DynamoDB)** com infraestrutura definida em **AWS CDK**.

O código é **incremental**: cada aula tem sua própria branch contendo apenas o que já foi visto até aquele momento. Isso permite que o aluno acompanhe a evolução sem ser exposto à solução final de uma só vez.

> Foco da disciplina: **Computação em Nuvem aplicada** — não DevOps avançado, não CI/CD profundo, não frontend.

## Stack

- **Linguagem:** Python 3.11+
- **Framework Web:** FastAPI
- **Banco SQL:** PostgreSQL (via Docker)
- **NoSQL / eventos:** DynamoDB (com fallback local em JSON)
- **Object storage:** Amazon S3 (com fallback local em disco)
- **Containers:** Docker + Docker Compose
- **Orquestração:** Kubernetes (Kind/Minikube local → Amazon EKS)
- **Registry:** Amazon ECR
- **IaC:** AWS CDK (Python)

## Roadmap por aula

| Aula | Branch          | Tema                                  | Entrega principal                         |
| ---: | :-------------- | :------------------------------------ | :---------------------------------------- |
|    1 | `aula-01-final` | FastAPI mínimo                        | `GET /health`, `GET /`, estrutura inicial |
|    2 | `aula-02-final` | Docker                                | `Dockerfile`, `docker-compose.yml`        |
|    3 | `aula-03-final` | PostgreSQL + CRUD                     | SQLAlchemy, model `Task`, CRUD completo   |
|    4 | `aula-04-final` | Config, segurança, VPC/IAM (conceito) | `.env`, `core/config.py`, docs AWS        |
|    5 | `aula-05-final` | Uploads — S3 / local                  | `POST /uploads`, `s3_service.py`          |
|    6 | `aula-06-final` | Kubernetes local                      | Manifests em `infra/k8s/` (Kind/Minikube) |
|    7 | `aula-07-final` | ECR                                   | Script de build + push para ECR           |
|    8 | `aula-08-final` | EKS                                   | Deploy + Service `LoadBalancer`           |
|    9 | `aula-09-final` | Scaling e custos                      | HPA, teste de carga, docs Cost Explorer   |
|   10 | `aula-10-final` | DynamoDB / logs / eventos             | `POST /events`, fallback JSON local       |
|   11 | `aula-11-final` | AWS CDK                               | Stacks S3, ECR, VPC básica                |
|   12 | `aula-12-final` | Entrega final                         | Documentação, checklist LGPD, arquitetura |

Detalhes completos: [`docs/ROADMAP.md`](docs/ROADMAP.md).

Lista fixa das **12 tarefas** (espelha as Issues do GitHub, para consulta offline):
[`docs/TAREFAS.md`](docs/TAREFAS.md).

Exemplos didáticos de referência (Dockerfile, futuro: CDK, K8s, ...):
[`exemplos/`](exemplos/).

## Como o aluno deve usar este repositório

Guia rápido (passo a passo, comandos e pré-requisitos): [`docs/HOW_TO_USE.md`](docs/HOW_TO_USE.md).

**Nunca usou terminal, Docker ou AWS?** Comece pelo guia do absoluto zero —
instalação de todas as ferramentas e configuração do AWS Academy Learner Lab:
[`docs/aws-academy-setup.md`](docs/aws-academy-setup.md).

Resumo:

```bash
# clonar
git clone https://github.com/N-CPUninter/Computa-o-em-Nuvem---Projeto-exemplo-CloudTask-AI-SaaS.git
cd Computa-o-em-Nuvem---Projeto-exemplo-CloudTask-AI-SaaS

# trocar para a aula atual
git checkout aula-01-final

# avançar para a próxima aula
git fetch --all
git checkout aula-02-final
```

Cada branch `aula-XX-final` contém **somente o estado acumulado até aquela aula** e funciona de forma independente.

## Participantes

| [<img src="https://avatars3.githubusercontent.com/u/60905310?s=460&v=4" width="75px;"/>](https://github.com/guipatriota) |
| :------------------------------------------------------------------------------------------------------------------------: |
| [Prof. Guilherme Patriota](https://github.com/guipatriota) |

## Estrutura final do projeto (referência — aula 12)

```text
cloudtask-ai-saas/
├── app/
│   ├── main.py
│   ├── core/            # config, security
│   ├── api/             # routes_health, routes_tasks, routes_uploads, routes_events
│   ├── db/              # database, models, schemas
│   ├── services/        # s3_service, dynamodb_service, task_service
│   └── utils/           # logging
├── infra/
│   ├── docker/
│   ├── k8s/             # local + aws/
│   └── cdk/             # stacks S3, ECR, VPC
├── scripts/             # build-and-push-ecr.sh, load-test
├── tests/
├── docs/                # ROADMAP, HOW_TO_USE, arquitetura, LGPD, etc.
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

> Em branches anteriores à aula 12, só existem as pastas e arquivos correspondentes ao conteúdo já visto.

## Banner do arquivo README.md

Utilize o arquivo [`Banner_Github_NCPU.pptx`](.readme_docs/Banner_Github_NCPU.pptx) da pasta `.readme_docs` para regenerar o `Banner_Github_NCPU.png` com **Título:** `CloudTask AI SaaS` e **Subtítulo:** `Computação em Nuvem`.

Após editar: **Arquivo → Exportar → Alterar o tipo de arquivo → PNG**. Salve com o mesmo nome (`Banner_Github_NCPU.png`) na pasta `.readme_docs/`.

## Contribuições

Se você tiver alguma sugestão, correção de bugs ou melhorias para este projeto didático, sinta-se à vontade para abrir uma issue ou enviar uma pull request. Sua contribuição é muito bem-vinda!

Como este repositório é usado em sala de aula, mantenha o código simples, didático e bem comentado, alinhado ao objetivo pedagógico de cada aula.

## Licença

Este projeto está licenciado sob a [GNU General Public License v3.0](LICENSE).
