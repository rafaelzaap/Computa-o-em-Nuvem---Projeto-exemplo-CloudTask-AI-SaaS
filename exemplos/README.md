# Exemplos didáticos — CloudTask AI SaaS

Esta pasta reúne **exemplos de referência** para estudo. Não fazem parte do código da aplicação — servem para o aluno ler, copiar e adaptar nas suas próprias entregas.

Cada subpasta cobre uma tecnologia/ferramenta usada na disciplina e contém pelo menos três variantes:

| Variante           | Para quê                                                                 |
| ------------------ | ------------------------------------------------------------------------ |
| `01-minimo`        | Versão mínima funcional. Foco: o essencial, sem distrações.              |
| `02-completo`      | Versão com várias opções comuns e **muitos comentários explicativos**.   |
| `03-cloudtask`     | Versão adaptada ao projeto **CloudTask AI SaaS** (mais próxima do real). |

## Índice

| Tecnologia | Pasta                                  | Status     |
| ---------- | -------------------------------------- | ---------- |
| Dockerfile | [`dockerfile/`](dockerfile/)           | ✅ pronto   |
| Docker Compose | dentro de `dockerfile/03-cloudtask/` | ✅ pronto |
| AWS CDK    | `cdk/`                                 | 🔜 futuro  |
| Kubernetes | `kubernetes/`                          | 🔜 futuro  |
| GitHub Actions | `github-actions/`                  | 🔜 futuro  |

## Como usar

1. Entre na pasta da tecnologia que está estudando.
2. Leia o `README.md` da subpasta.
3. Compare as três variantes lado a lado.
4. Copie o que faz sentido para a sua própria entrega da aula.

> ⚠️ **Não rode os exemplos diretamente em produção.** Eles são didáticos: muitas escolhas (ex.: `RemovalPolicy.DESTROY`, credenciais em variáveis, ausência de TLS) são simplificações conscientes para facilitar o aprendizado.
