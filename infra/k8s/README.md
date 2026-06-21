# CloudTask no Kubernetes local

Este diretório executa a API com duas réplicas e um PostgreSQL efêmero em um
cluster Kind. O banco usa `emptyDir`, portanto os dados são descartados quando
o cluster é removido.

## Pré-requisitos

- Docker Desktop em execução;
- `kubectl`;
- Kind.

## Criar e carregar a imagem

```powershell
kind create cluster --name cloudtask
docker build --target prod -t cloudtask-api:k8s .
kind load docker-image cloudtask-api:k8s --name cloudtask
```

O target `prod` é usado porque contém o código da aplicação dentro da imagem.
O target `dev` depende do volume montado pelo Docker Compose.

## Aplicar e validar

```powershell
kubectl apply -f infra/k8s/namespace.yaml
kubectl apply -f infra/k8s/
kubectl rollout status deployment/cloudtask-db -n cloudtask --timeout=120s
kubectl rollout status deployment/cloudtask-api -n cloudtask --timeout=120s
kubectl get pods,deploy,svc -n cloudtask
```

## Acessar a API

```powershell
kubectl port-forward -n cloudtask svc/cloudtask-api 8080:8000
```

Em outro terminal:

```powershell
curl.exe http://localhost:8080/health
curl.exe http://localhost:8080/health/ready
```

## Logs e auto-healing

```powershell
kubectl logs -n cloudtask deployment/cloudtask-api --tail=50
kubectl delete pod -n cloudtask -l app=cloudtask-api --field-selector=status.phase=Running --wait=false
kubectl get pods -n cloudtask -w
```

O Deployment recria automaticamente os pods apagados e mantém duas réplicas.

## Limpeza

```powershell
kind delete cluster --name cloudtask
```
