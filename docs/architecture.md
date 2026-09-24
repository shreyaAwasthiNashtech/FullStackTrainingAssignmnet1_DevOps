# Architecture Specification

## 1. Overview
The order processing platform comprises three decoupled Python Flask microservices running on Kubernetes (Azure Kubernetes Service in production, local kind for development). The services handle order ingestion, processing, and notification dispatch using synchronous HTTP calls and DNS-based service discovery.

---

## 2. Service Topology

```
                       +-----------------------------------+
                       |           External Client         |
                       |              (HTTP/REST)          |
                       +-----------------+-----------------+
                                         |
                                         | POST /orders
                                         v
   +-----------------------------------------------------------------------+
   | Kubernetes Cluster (default namespace)                                |
   |                                                                       |
   |   +---------------------------------------------------------------+   |
   |   | Service: order-api (ClusterIP)                                |   |
   |   | DNS: order-api:5000                                           |   |
   |   | Pod: order-api (Flask, non-root UID 8888)                     |   |
   |   | Endpoints:                                                    |   |
   |   |   - GET  /health (Readiness / Liveness probe)                 |   |
   |   |   - POST /orders (Ingestion & Schema Validation)              |   |
   |   +-------------------------------+-------------------------------+   |
   |                                   |
   |                                   | POST http://order-processor:5001/process
   |                                   v
   |   +---------------------------------------------------------------+   |
   |   | Service: order-processor (ClusterIP)                          |   |
   |   | DNS: order-processor:5001                                     |   |
   |   | Pod: order-processor (Flask, non-root UID 8888)               |   |
   |   | Endpoints:                                                    |   |
   |   |   - GET  /health (Readiness / Liveness probe)                 |   |
   |   |   - POST /process (Workflow Processing)                       |   |
   |   +-------------------------------+-------------------------------+   |
   |                                   |
   |                                   | POST http://notification-service:5002/notify
   |                                   v
   |   +---------------------------------------------------------------+   |
   |   | Service: notification-service (ClusterIP)                     |   |
   |   | DNS: notification-service:5002                                |   |
   |   | Pod: notification-service (Flask, non-root UID 8888)          |   |
   |   | Endpoints:                                                    |   |
   |   |   - GET  /health (Readiness / Liveness probe)                 |   |
   |   |   - POST /notify (Alert Dispatch)                             |   |
   |   +---------------------------------------------------------------+   |
   +-----------------------------------------------------------------------+
```

---

## 3. Service Allocation & Ports

| Service | Port | Protocol | Container Image | Execution Context | Role |
|---|---|---|---|---|---|
| `order-api` | 5000 | HTTP/REST | `order-api:v1.0.0` | `appuser` (UID 8888) | Ingress endpoint; validates incoming JSON payloads; forwards to `order-processor`; returns HTTP 202. |
| `order-processor` | 5001 | HTTP/REST | `order-processor:v1.0.0` | `appuser` (UID 8888) | Validates order identity; triggers customer notifications; returns HTTP 200. |
| `notification-service` | 5002 | HTTP/REST | `notification-service:v1.0.0` | `appuser` (UID 8888) | Validates recipient information; logs and dispatches alerts; returns HTTP 200. |

---

## 4. Networking & Service Discovery
Internal communication relies on Kubernetes CoreDNS:
- CoreDNS registers each ClusterIP service as `<service-name>.<namespace>.svc.cluster.local`.
- Services residing within the same namespace resolve each other via short hostnames:
  - `http://order-processor:5001/process`
  - `http://notification-service:5002/notify`
- Target addresses are passed as environment variables (`ORDER_PROCESSOR_URL`, `NOTIFICATION_SERVICE_URL`) defined in Helm templates, enabling configuration across deployment stages without rebuilding images.

---

## 5. API Schemas & Data Contracts

### 5.1 POST `/orders` (`order-api`)
- Inbound payload:
  ```json
  {
    "order_id": "ORD-1",
    "item": "TestItem",
    "amount": 10
  }
  ```
- Validation criteria:
  - `order_id`: string, required
  - `item`: string, required
  - `amount`: number, required
- Response (`202 Accepted`):
  ```json
  {
    "status": "PROCESSED",
    "order_id": "ORD-1",
    "message": "Order accepted and processed successfully"
  }
  ```

### 5.2 POST `/process` (`order-processor`)
- Inbound payload:
  ```json
  {
    "order_id": "ORD-1"
  }
  ```
- Validation criteria:
  - `order_id`: string, required
- Response (`200 OK`):
  ```json
  {
    "status": "PROCESSED",
    "order_id": "ORD-1",
    "message": "Order processed successfully"
  }
  ```

### 5.3 POST `/notify` (`notification-service`)
- Inbound payload:
  ```json
  {
    "recipient": "user-ORD-1@example.com"
  }
  ```
- Validation criteria:
  - `recipient`: string, required
- Response (`200 OK`):
  ```json
  {
    "status": "DISPATCHED",
    "recipient": "user-ORD-1@example.com",
    "message": "Notification dispatched successfully"
  }
  ```
