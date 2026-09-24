# Azure Cost Management & Optimization Strategies

Cost efficiency is a first-class architectural requirement for production cloud workloads on Azure Kubernetes Service (AKS). Below are three concrete enterprise optimization strategies and an open-source observability solution.

---

## Strategy 1: AKS Spot Node Pools for Non-Critical & Asynchronous Workers
- **Mechanism:** Provision a secondary node pool using Azure Spot Virtual Machines (`priority = "Spot"`, `eviction_policy = "Delete"`).
- **Cost Reduction:** **60% to 80% discount** compared to standard Pay-As-You-Go pricing.
- **Application Target:** Microservices resilient to eviction and interruption, such as `notification-service`, background report generation, and asynchronous queue consumers.
- **Implementation Pattern:**
  - Use Kubernetes `tolerations` and `nodeSelector` / `nodeAffinity`:
  ```yaml
  nodeSelector:
    kubernetes.azure.com/scalesetpriority: spot
  tolerations:
    - key: "kubernetes.azure.com/scalesetpriority"
      operator: "Equal"
      value: "spot"
      effect: "NoSchedule"
  ```
- **Trade-off Mitigation:** Run core ingress and transactional services (`order-api`) on on-demand nodes, routing background tasks to Spot instances.

---

## Strategy 2: Horizontal Pod Autoscaler (HPA) Coupled with Cluster Autoscaler
- **Mechanism:** Implement dynamic multi-tier autoscaling:
  1. **HPA:** Scales pod replicas based on real-time CPU and Memory utilization (e.g., target 70% CPU).
  2. **Cluster Autoscaler (CA):** Scales Azure VM scale set instances down to the minimum required nodes during off-peak hours (e.g., nights and weekends).
- **Cost Reduction:** **40% to 65% reduction** in compute costs by eliminating idle overhead.
- **Implementation in Terraform:**
  ```hcl
  default_node_pool {
    name                = "default"
    vm_size             = "Standard_B2s"
    enable_auto_scaling = true
    min_count           = 1
    max_count           = 3
  }
  ```
- **Resource Boundary Control:** All pods define strict `requests` (`50m` CPU / `128Mi` RAM) and `limits` (`200m` CPU / `256Mi` RAM), preventing noisy-neighbor starvation and enabling high bin-packing density.

---

## Strategy 3: Azure Reserved VM Instances (RI) for Baseline Workloads
- **Mechanism:** Commit to a 1-year or 3-year term for predictable, 24/7 baseline capacity on AKS system nodes and primary databases.
- **Cost Reduction:**
  - **1-Year Commitment:** Up to **35% to 45% savings**.
  - **3-Year Commitment:** Up to **50% to 55% savings**.
- **Financial Flexibility:** Azure Reserved Instances allow instance size flexibility within the same VM series and can be exchanged or canceled with prorated adjustments.

---

## Strategy 4: Container-Level Cost Observability with OpenCost (OSS)
- **Mechanism:** Deploy **OpenCost** (Cloud Native Computing Foundation Sandbox project) directly into the AKS cluster.
- **Features:**
  - Allocates real-time cloud costs by namespace, deployment, pod, and container label.
  - Reconciles Azure billing rate cards with actual Prometheus resource consumption metrics.
  - Identifies over-provisioned containers where requested CPU/RAM exceeds historical 95th-percentile utilization.
- **Local Deployment Command:**
  ```bash
  helm install opencost oci://quay.io/opencost/opencost-helm-chart \
    --namespace opencost --create-namespace
  ```
