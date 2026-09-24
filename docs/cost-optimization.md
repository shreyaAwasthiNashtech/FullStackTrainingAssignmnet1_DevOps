# Infrastructure Cost Optimisation

This note outlines production cost-reduction strategies for running the order processing platform on Azure Kubernetes Service (AKS).

---

## 1. Spot Node Pools for Asynchronous Workloads
- **Mechanism:** Run stateless, interruptible services on an Azure Spot node pool (`priority = "Spot"`, `eviction_policy = "Delete"`).
- **Savings:** Between 60% and 80% compared with standard on-demand pricing.
- **Suitability:** Suitable for `notification-service` and non-critical asynchronous tasks where evictions can be tolerated without data loss.
- **Configuration:** Apply node affinity and tolerations in deployment manifests:
  ```yaml
  nodeSelector:
    kubernetes.azure.com/scalesetpriority: spot
  tolerations:
    - key: "kubernetes.azure.com/scalesetpriority"
      operator: "Equal"
      value: "spot"
      effect: "NoSchedule"
  ```
- Core transactional workloads (`order-api`) remain on regular on-demand nodes to maintain consistent latency.

---

## 2. Horizontal Pod Autoscaling and Cluster Autoscaler
- **Mechanism:** Combine Horizontal Pod Autoscaling (HPA) with the AKS Cluster Autoscaler.
- **Savings:** Between 40% and 60% by scaling down worker nodes during periods of low activity (e.g. overnight and weekends).
- **Implementation:**
  - HPA adjusts replica counts dynamically based on target CPU thresholds (e.g. 70%).
  - The node pool autoscaler adjusts the virtual machine scale set between minimum and maximum bounds:
    ```hcl
    default_node_pool {
      name                = "default"
      vm_size             = "Standard_B2s"
      enable_auto_scaling = true
      min_count           = 1
      max_count           = 3
      os_disk_size_gb     = 30
    }
    ```
  - Defined resource requests (`50m` CPU / `128Mi` memory) and limits (`200m` CPU / `256Mi` memory) ensure efficient node bin-packing and prevent single pods from starving neighbours.

---

## 3. Azure Reserved VM Instances for Baseline Capacity
- **Mechanism:** Commit to 1-year or 3-year Azure Reserved VM Instances for steady-state system nodes and baseline compute requirements.
- **Savings:**
  - 1-Year Commitment: approximately 35% to 45% discount.
  - 3-Year Commitment: approximately 50% to 55% discount.
- **Operation:** Combine baseline reserved capacity with on-demand and spot nodes for handling burst traffic.

---

## 4. Workload Cost Attribution with OpenCost
- **Mechanism:** Deploy OpenCost into the cluster for granular cost visibility.
- **Capability:**
  - Maps actual Azure billing rate cards to Kubernetes namespace, deployment, and pod resource consumption.
  - Highlights over-provisioned containers where allocated CPU or memory requests consistently exceed actual 95th-percentile usage.
- **Installation:**
  ```bash
  helm install opencost oci://quay.io/opencost/opencost-helm-chart \
    --namespace opencost --create-namespace
  ```
