# Kubernetes

## Назначение
Kubernetes используется для оркестрации контейнеризированного приложения Corporate Data Platform.

## Текущая конфигурация
- Deployment: `corporate-data-deployment`
- Используемый образ: `corporate-data-app:2.0`
- Количество экземпляров приложения: 3
- Порт приложения: 8000

## Подключение к базе данных
На данном этапе PostgreSQL продолжает работать как Docker Compose-сервис. Kubernetes-приложение подключается к PostgreSQL через:
```env
DB_HOST=host.docker.internal
DB_PORT=5432
```
Порт PostgreSQL 5432 опубликован в `compose.yaml`.

## Основные команды

Проверка кластера:
```bash
kubectl get nodes
```

Просмотр Pod:
```bash
kubectl get pods
```

Применение конфигурации:
```bash
kubectl apply -f kubernetes/deployment.yaml
```

Просмотр Deployment:
```bash
kubectl get deployments
```

Масштабирование:
```bash
kubectl scale deployment corporate-data-deployment --replicas=3
```

Просмотр журналов:
```bash
kubectl logs ИМЯ_POD
```
