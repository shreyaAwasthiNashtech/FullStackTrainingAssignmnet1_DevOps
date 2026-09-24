# Troubleshooting Incident Post-Mortem & Runbook

## Incident Title: Pod Readiness Failure Post-Deployment Resulting in `0/1 Running` State

---

### 1. Incident Overview
- **Severity:** P2 (Deployment Blocked / Service Unreachable)
- **Component:** `order-api` Deployment in Kubernetes
- **Symptom:** After applying Helm deployment, the pod remained indefinitely in `Running` state with `0/1 Ready`. External requests returned HTTP 503 Service Unavailable / Connection Refused.

---

### 2. Detection & Diagnostic Triage

#### Step 1: Inspect Pod Status
```bash
kubectl get pods -l app=order-api
```
*Output observed:*
```
NAME                         READY   STATUS    RESTARTS   AGE
order-api-68748d8dbb-m2n9x   0/1     Running   0          4m
```

#### Step 2: Investigate Events with `kubectl describe`
```bash
kubectl describe pod -l app=order-api
```
*Events log revealed:*
```
Events:
  Type     Reason     Age                From               Message
  ----     ------     ----               ----               -------
  Normal   Scheduled  4m                 default-scheduler  Successfully assigned default/order-api-68748d8dbb-m2n9x to kind-control-plane
  Normal   Pulled     3m58s              kubelet            Container image "order-api:v1.0.0" already present on machine
  Normal   Created    3m57s              kubelet            Created container order-api
  Normal   Started    3m57s              kubelet            Started container order-api
  Warning  Unhealthy  12s (x24 over 3m)  kubelet            Readiness probe failed: HTTP probe failed with statuscode: 404
```

#### Step 3: Check Container Application Logs
```bash
kubectl logs -l app=order-api --tail=20
```
*Log line discovered:*
```
10.244.0.1 - - [24/Sep/2026 13:00:15] "GET /healthz HTTP/1.1" 404 -
```

---

### 3. Root Cause Analysis (RCA)
- The Flask microservice exposes its health check at `/health` (`@app.route("/health")`).
- The Kubernetes Helm template had an erroneous path configured: `path: /healthz` instead of `path: /health`.
- The kubelet periodically queried `http://<pod-ip>:5000/healthz`, which Flask rejected with `404 Not Found`.
- Kubernetes readiness probes require HTTP status codes `>= 200` and `< 400` to mark the pod ready. Consequently, Kubernetes withheld the pod from the `Endpoints` list of the `order-api` Service, dropping all inbound traffic.

---

### 4. Remediation & Verification

#### Step 1: Update Helm Template
Correct the probe endpoint in `helm/order-platform/templates/order-api.yaml`:
```yaml
readinessProbe:
  httpGet:
    path: /health
    port: http
  initialDelaySeconds: 5
  periodSeconds: 5
```

#### Step 2: Upgrade Helm Release
```bash
helm upgrade --install order-platform ./helm/order-platform
```

#### Step 3: Confirm Pod Convergence
```bash
kubectl rollout status deployment/order-api --timeout=60s
kubectl get pods -l app=order-api
```
*Output confirmed:*
```
deployment "order-api" successfully rolled out
NAME                         READY   STATUS    RESTARTS   AGE
order-api-79dbcc6dc9-x4248   1/1     Running   0          18s
```
