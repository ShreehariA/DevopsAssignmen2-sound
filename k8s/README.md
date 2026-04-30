## Kubernetes manifests (ACEest)

### 1) Create namespace

```bash
kubectl apply -f k8s/namespace.yaml
```

### 2) Rolling update (baseline)

```bash
kubectl apply -f k8s/rolling-deployment.yaml -f k8s/service.yaml
```

### 3) Blue/Green (manual switch)

Apply:

```bash
kubectl apply -f k8s/bluegreen.yaml
```

Switch traffic to green:

```bash
kubectl -n aceest scale deploy/aceest-web-green --replicas=2
kubectl -n aceest patch svc aceest-web-bg -p '{"spec":{"selector":{"app":"aceest-web","track":"green"}}}'
```

Rollback to blue:

```bash
kubectl -n aceest patch svc aceest-web-bg -p '{"spec":{"selector":{"app":"aceest-web","track":"blue"}}}'
```

### 4) Canary (weight by replica ratio)

Apply:

```bash
kubectl apply -f k8s/canary.yaml
```

Increase canary weight:

```bash
kubectl -n aceest scale deploy/aceest-web-canary --replicas=2
```

Rollback canary:

```bash
kubectl -n aceest scale deploy/aceest-web-canary --replicas=0
```

