# Incident Runbook: Readiness Probe Failure

## Symptom
Following a deployment update, the pod remains in `Running` status with `0/1 Ready`. Requests routed through the service fail with HTTP 503 or connection timeouts.

---

## Triage Procedure

### 1. Check Pod Health
Inspect the status and readiness columns:
```bash
kubectl get pods -l app=order-api
```
Example problematic output:
```
NAME                         READY   STATUS    RESTARTS   AGE
order-api-68748d8dbb-m2n9x   0/1     Running   0          4m
```

### 2. Inspect Kubernetes Events
Check warning messages recorded by the kubelet:
```bash
kubectl describe pod -l app=order-api
```
Example event log:
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

### 3. Review Application Logs
Check access logs for rejected health check requests:
```bash
kubectl logs -l app=order-api --tail=20
```
Example log entry:
```
10.244.0.1 - - [24/Sep/2026 13:00:15] "GET /healthz HTTP/1.1" 404 -
```

---

## Root Cause
The microservice exposes health checks on `/health`, whereas the Helm template defined the probe path as `/healthz`. Because the endpoint returned HTTP 404, the kubelet marked the container unready and excluded the pod IP from the Service endpoints list.

---

## Resolution

1. Correct the probe path in `helm/order-platform/templates/order-api.yaml`:
   ```yaml
   readinessProbe:
     httpGet:
       path: /health
       port: http
     initialDelaySeconds: 5
     periodSeconds: 5
   ```

2. Redeploy the chart:
   ```bash
   helm upgrade --install order-platform ./helm/order-platform
   ```

3. Confirm pod readiness:
   ```bash
   kubectl rollout status deployment/order-api --timeout=60s
   kubectl get pods -l app=order-api
   ```
