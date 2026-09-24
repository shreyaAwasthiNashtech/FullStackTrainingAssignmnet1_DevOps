# Order Processing Platform

Containerised microservices platform built with Python Flask, Docker, Terraform, Helm, and Kubernetes. The project demonstrates multi-service architecture, least-privilege container security, declarative infrastructure as code, automated testing, and CI/CD pipelines.

---

## 1. Repository Structure

```
order-processing-platform/
├── .github/
│   └── workflows/
│       └── ci-cd.yml                     # GitHub Actions workflow
├── docs/
│   ├── architecture.md                   # Architecture & service discovery
│   ├── cost-optimization.md              # Azure cost management & OpenCost
│   └── troubleshooting.md                # Readiness probe runbook
├── helm/
│   └── order-platform/
│       ├── Chart.yaml                    # Chart definition
│       ├── values.yaml                   # Configuration values & resource limits
│       └── templates/
│           ├── notification-service.yaml # Deployment & Service (Port 5002)
│           ├── order-api.yaml            # Deployment & Service (Port 5000)
│           └── order-processor.yaml      # Deployment & Service (Port 5001)
├── infra/
│   ├── main.tf                           # Terraform Azure RG, ACR, AKS, Role Assignment
│   ├── outputs.tf                        # Infrastructure output values
│   └── variables.tf                      # Input variables & VM sizing
├── services/
│   ├── notification-service/
│   │   ├── Dockerfile                    # Container build file (UID 8888)
│   │   ├── app.py                        # Service implementation (/notify)
│   │   ├── requirements.txt              # Python dependencies
│   │   └── test_app.py                   # Pytest test suite
│   ├── order-api/
│   │   ├── Dockerfile                    # Container build file (UID 8888)
│   │   ├── app.py                        # Service implementation (/orders)
│   │   ├── requirements.txt              # Python dependencies
│   │   └── test_app.py                   # Pytest test suite
│   └── order-processor/
│       ├── Dockerfile                    # Container build file (UID 8888)
│       ├── app.py                        # Service implementation (/process)
│       ├── requirements.txt              # Python dependencies
│       └── test_app.py                   # Pytest test suite
├── .gitignore                            # Version control exclusion rules
├── Makefile                              # Developer automation shortcuts
├── pytest.ini                            # Test configuration
└── README.md                             # Project documentation
```

---

## 2. Microservice Architecture

```
Client ---> [order-api:5000] ---> [order-processor:5001] ---> [notification-service:5002]
                |                          |                                |
             HTTP 202                   HTTP 200                         HTTP 200
            PROCESSED                  PROCESSED                        DISPATCHED
```

1. **`order-api`**: Ingress service; validates payload schemas, forwards orders to the processor service, and responds with `HTTP 202 Accepted`.
2. **`order-processor`**: Business logic service; validates order IDs, handles order workflow, and invokes the notification service.
3. **`notification-service`**: Notification dispatch service; validates recipient details and dispatches confirmation messages.

---

## 3. Local Development

### Prerequisites
- Docker Engine & WSL2 / Linux
- `kind`
- `kubectl` & `helm`
- Python 3.11+ / `uv`
- `make`

### Quickstart Commands
Common development tasks can be run using `make`:

```bash
make test         # Run pytest across all microservices
make lint         # Run flake8 linter
make build        # Build all three Docker images
make deploy-local # Deploy Helm chart to Kubernetes
make clean        # Remove Helm release
```

### Step-by-Step Setup

1. **Run Unit Tests:**
   ```bash
   uv venv .venv
   source .venv/bin/activate
   uv pip install -r services/order-api/requirements.txt
   pytest services/*/test_app.py
   ```

2. **Build Container Images:**
   ```bash
   docker build -t order-api:v1.0.0 ./services/order-api
   docker build -t order-processor:v1.0.0 ./services/order-processor
   docker build -t notification-service:v1.0.0 ./services/notification-service
   ```

3. **Validate Terraform Configuration:**
   ```bash
   cd infra
   terraform init -backend=false
   terraform validate
   cd ..
   ```

4. **Deploy Locally on kind:**
   ```bash
   kind create cluster --name devops-lab
   kind load docker-image order-api:v1.0.0 --name devops-lab
   kind load docker-image order-processor:v1.0.0 --name devops-lab
   kind load docker-image notification-service:v1.0.0 --name devops-lab

   helm lint helm/order-platform
   helm upgrade --install order-platform ./helm/order-platform

   kubectl rollout status deployment/order-api --timeout=60s
   kubectl rollout status deployment/order-processor --timeout=60s
   kubectl rollout status deployment/notification-service --timeout=60s
   ```

5. **Execute Smoke Test:**
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

## 4. Evaluation Questions & Answers

### Q1: How does inter-service communication and service discovery work across pods?
**Answer:** Microservices communicate using standard HTTP REST over Kubernetes ClusterIP Services. Kubernetes CoreDNS resolves service names (e.g. `http://order-processor:5001/process`) to the virtual IP of the respective ClusterIP service. Kube-proxy routes traffic across available, healthy pod replicas matching the selector `app: <service-name>`.

### Q2: How is container security implemented according to least-privilege principles?
**Answer:**
1. Base images use minimal `python:3.11-slim` without development packages or compilers.
2. Services execute under an unprivileged user `appuser` (UID `8888`), preventing container break-outs from inheriting root privileges on the host.
3. Native `HEALTHCHECK` definitions are built directly into Dockerfiles.
4. CI checks run **Gitleaks** for secret detection and **Aqua Trivy** for filesystem and container vulnerability scans.

### Q3: How do readiness and liveness probes ensure zero-downtime rolling updates?
**Answer:**
- **Liveness Probes:** Restart containers if the application process stops responding.
- **Readiness Probes:** Prevent traffic routing to pods until their internal initialisation is complete. During rolling updates (`helm upgrade`), traffic stays on existing replicas until newly spawned pods pass readiness checks, avoiding dropped requests.

### Q4: How are Azure cloud costs controlled in production AKS deployments?
**Answer:**
1. **Spot Node Pools:** Run non-critical or asynchronous workers (`notification-service`) on Spot instances for 60-80% discounts.
2. **Cluster Autoscaler & HPA:** Automatically adjust replica counts and scale node count between 1 and 3 instances based on real-time CPU/memory utilization, scaling down during off-peak periods.
3. **Reserved VM Instances:** 1-year or 3-year commitments for predictable baseline compute capacity (35-55% savings).
4. **OpenCost:** In-cluster cost allocation mapping container resource requests and usage against cloud billing rates.

### Q5: How is continuous integration and automated quality enforcement structured?
**Answer:** The GitHub Actions workflow (`.github/workflows/ci-cd.yml`) runs four sequential stages:
1. `lint-and-test`: Parallel matrix testing running `flake8` linter and `pytest` unit tests across all microservices.
2. `security-scan`: Secret scanning using Gitleaks and filesystem vulnerability assessment using Trivy.
3. `docker-build-and-scan`: Builds Docker images tagged with `${{ github.sha }}` and scans container layers.
4. `helm-validation`: Executes `helm lint` and dry-run template rendering (`helm template`) before deployment.
