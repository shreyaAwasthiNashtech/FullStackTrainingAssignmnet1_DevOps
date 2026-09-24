# Order Processing Platform

An enterprise-ready, containerized microservices platform built with Python Flask, Docker, Terraform, Helm, and Kubernetes. The platform demonstrates cloud-native architecture, secure least-privilege containerization, declarative infrastructure as code, automated testing, and comprehensive CI/CD pipelines.

---

## 1. Repository Hierarchy

```
order-processing-platform/
├── .github/
│   └── workflows/
│       └── ci-cd.yml                     # Multi-job GitHub Actions CI/CD pipeline
├── docs/
│   ├── architecture.md                   # Microservices architecture & CoreDNS discovery
│   ├── cost-optimization.md              # Azure cost reduction & OpenCost guide
│   └── troubleshooting.md                # Incident triage runbook (readiness probes)
├── helm/
│   └── order-platform/
│       ├── Chart.yaml                    # Helm chart metadata (v0.1.0)
│       ├── values.yaml                   # Configurable values, replicas & limits
│       └── templates/
│           ├── order-api.yaml            # Deployment & Service (Port 5000)
│           ├── order-processor.yaml      # Deployment & Service (Port 5001)
│           └── notification-service.yaml # Deployment & Service (Port 5002)
├── infra/
│   ├── main.tf                           # Terraform Azure RG, ACR, AKS & Role Assignment
│   ├── outputs.tf                        # Resource IDs, ACR login server, AKS cluster
│   └── variables.tf                      # Configurable parameters & VM sizes
├── services/
│   ├── notification-service/
│   │   ├── Dockerfile                    # Python 3.11 slim non-root container
│   │   ├── app.py                        # Notification dispatch endpoint (/notify)
│   │   ├── requirements.txt              # Flask & Pytest dependencies
│   │   └── test_app.py                   # Pytest unit tests
│   ├── order-api/
│   │   ├── Dockerfile                    # Container definition (Port 5000)
│   │   ├── app.py                        # Ingestion endpoint (/orders)
│   │   ├── requirements.txt              # Flask, Requests, Pytest
│   │   └── test_app.py                   # API unit tests
│   └── order-processor/
│       ├── Dockerfile                    # Container definition (Port 5001)
│       ├── app.py                        # Processing logic (/process)
│       ├── requirements.txt              # Dependencies
│       └── test_app.py                   # Processor unit tests
├── .gitignore                            # Version control exclusion rules
└── README.md                             # Documentation & demo questions
```

---

## 2. Microservice Architecture & Data Flow

```
Client ---> [order-api:5000] ---> [order-processor:5001] ---> [notification-service:5002]
                |                          |                                |
             HTTP 202                   HTTP 200                         HTTP 200
            PROCESSED                  PROCESSED                        DISPATCHED
```

1. **`order-api`**: Public-facing ingress; validates order payload, forwards to processor, and responds immediately with `HTTP 202 Accepted`.
2. **`order-processor`**: Validates business parameters, orchestrates order workflow, and notifies customer service.
3. **`notification-service`**: Formats customer alerts and records event dispatch.

---

## 3. Local Development & Quickstart

### Prerequisites
- Docker Engine & WSL2 / Linux
- `kind` (Kubernetes in Docker)
- `kubectl` & `helm` (v3+)
- Python 3.11+ / `uv`

### Step 1: Run Unit Tests
```bash
uv venv .venv
source .venv/bin/activate
uv pip install -r services/order-api/requirements.txt
pytest -o addopts="--import-mode=importlib" services/*/test_app.py
```

### Step 2: Build Docker Images
```bash
docker build -t order-api:v1.0.0 ./services/order-api
docker build -t order-processor:v1.0.0 ./services/order-processor
docker build -t notification-service:v1.0.0 ./services/notification-service
```

### Step 3: Validate Terraform Infrastructure
```bash
cd infra
terraform init -backend=false
terraform validate
cd ..
```

### Step 4: Deploy Locally with kind & Helm
```bash
# Create local Kubernetes cluster
kind create cluster --name devops-lab

# Sideload local container images
kind load docker-image order-api:v1.0.0 --name devops-lab
kind load docker-image order-processor:v1.0.0 --name devops-lab
kind load docker-image notification-service:v1.0.0 --name devops-lab

# Lint and install Helm release
helm lint helm/order-platform
helm upgrade --install order-platform ./helm/order-platform

# Wait for healthy rollout
kubectl rollout status deployment/order-api --timeout=60s
kubectl rollout status deployment/order-processor --timeout=60s
kubectl rollout status deployment/notification-service --timeout=60s
```

### Step 5: Execute End-to-End Smoke Test
```bash
kubectl run curl-test --rm -i --restart=Never --image=curlimages/curl -- \
  http://order-api:5000/orders -X POST \
  -H "Content-Type: application/json" \
  -d '{"order_id":"ORD-1","item":"TestItem","amount":10}'
```
*Expected Output:*
```json
{"message":"Order accepted and processed successfully","order_id":"ORD-1","status":"PROCESSED"}
```

---

## 4. Demo Evaluation Questions & Technical Answers

### Q1: How does inter-service communication and service discovery work across pods?
**Answer:** Microservices communicate using standard HTTP REST over Kubernetes ClusterIP Services. Kubernetes CoreDNS resolves service names (e.g., `http://order-processor:5001/process`) to the virtual IP of the respective ClusterIP service. The kube-proxy / iptables layer routes and load-balances the TCP traffic across all available, ready pod replicas matching the selector `app: <service-name>`.

### Q2: How is container security implemented according to least-privilege principles?
**Answer:** Each Dockerfile:
1. Employs `python:3.11-slim` to eliminate unnecessary OS utilities and compilers.
2. Explicitly provisions and switches to an unprivileged user `appuser` (UID `8888`), preventing container breakout attacks from inheriting host root capabilities.
3. Incorporates native `HEALTHCHECK` definitions.
4. CI pipeline incorporates **Gitleaks** to catch credential leaks and **Aqua Trivy** to perform filesystem and container image vulnerability scans for `CRITICAL` and `HIGH` CVEs.

### Q3: How do readiness and liveness probes ensure zero-downtime rolling updates?
**Answer:** 
- **Liveness Probes** verify the process is alive; if the `/health` endpoint crashes or deadlocks, kubelet restarts the container.
- **Readiness Probes** verify the container is prepared to receive live traffic. During rolling updates (`helm upgrade`), Kubernetes leaves traffic routed to existing pods until new pods pass their readiness checks. If a new version fails readiness (e.g., mismatched path or configuration failure), the rollout pauses and existing traffic remains uninterrupted.

### Q4: How are Azure cloud costs controlled in production AKS deployments?
**Answer:**
1. **Spot Node Pools:** Run non-critical or asynchronous workers (`notification-service`) on Spot instances for 60-80% discounts.
2. **Cluster Autoscaler & HPA:** Automatically adjust replica counts and scale node count between 1 and 3 instances based on real-time CPU/memory utilization, scaling down during off-peak periods.
3. **Reserved VM Instances (RI):** Purchase 1-year or 3-year commitments for predictable baseline system nodes to save 35-55%.
4. **OpenCost:** In-cluster cost observability mapping container resource utilization to Azure billing rates.

### Q5: How is continuous integration and automated quality enforcement structured?
**Answer:** The GitHub Actions workflow (`.github/workflows/ci-cd.yml`) executes four staged, interdependent jobs:
1. `lint-and-test`: Parallel matrix testing running `flake8` linter and `pytest` unit tests across all microservices.
2. `security-scan`: Scans the git history with Gitleaks for leaked secrets and filesystem CVEs with Trivy.
3. `docker-build-and-scan`: Builds Docker images tagged with `${{ github.sha }}` and scans container images.
4. `helm-validation`: Executes `helm lint` and dry-run template rendering (`helm template`) validating Kubernetes manifests prior to CD deployment.
