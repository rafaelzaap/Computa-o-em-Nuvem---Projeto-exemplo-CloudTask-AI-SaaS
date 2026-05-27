# Dockerfile completo e comentado

Mesma aplicação do exemplo `01-minimo`, mas usando as técnicas mais comuns em Dockerfiles de produção. Cada bloco está comentado linha a linha dentro do próprio `Dockerfile`.

## Recursos demonstrados

| Recurso                          | O que ganha                                                    |
| -------------------------------- | -------------------------------------------------------------- |
| **Multi-stage build**            | Imagem final muito menor; sem `gcc`/`build-essential` no runtime. |
| **Cache de camadas**             | Builds rápidos quando apenas o código (não `requirements.txt`) muda. |
| **Usuário não-root**             | Reduz impacto se a aplicação for comprometida.                 |
| **ENV `PYTHONUNBUFFERED`**       | Logs aparecem na hora no `docker logs`.                        |
| **`HEALTHCHECK`**                | Orquestradores reiniciam containers com problema.              |
| **`ENTRYPOINT` + `CMD`**         | Argumentos podem ser sobrescritos sem perder o executável.     |
| **`.dockerignore`**              | Build não leva `.git`, `.venv`, segredos, etc.                 |

## Como rodar

```bash
docker build -t exemplo-completo .
docker run --rm -p 8000:8000 exemplo-completo
curl http://localhost:8000/health
```

## Sobrescrevendo argumentos

Como o `ENTRYPOINT` é fixo em `uvicorn`, mudar a porta no `docker run` é só passar os args:

```bash
docker run --rm -p 9000:9000 exemplo-completo app.main:app --host 0.0.0.0 --port 9000
```

## Inspecionar o tamanho final

```bash
docker images exemplo-completo
# compare com o exemplo-minimo
```

A diferença fica grande quando o `requirements.txt` traz pacotes que compilam (psycopg2, cryptography, numpy, etc.).
