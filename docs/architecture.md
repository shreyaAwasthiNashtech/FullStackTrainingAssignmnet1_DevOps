# Order Processing Platform - Architecture Documentation

## 1. System Overview
The Order Processing Platform is an event-driven, containerized microservices application built with Python Flask and deployed on Kubernetes (AKS / local kind). The platform handles order ingestion, downstream processing, and asynchronous notifications with complete service isolation, security hardening, and resilient inter-service communication.

---

## 2. Architecture Diagram (ASCII)

```
                       +-----------------------------------+
                       |           External Client         |
                       |       (cURL / HTTP Client)        |
                       +-----------------+-----------------+
                                         |
                                         | POST /orders
                                         v
   +-----------------------------------------------------------------------+
   | Kubernetes Cluster (default namespace)                                |
   |                                                                       |
   |   +---------------------------------------------------------------+   |
   |   | Service: order-api (ClusterIP)                                |   |
   |   | DNS: order-api.default.svc.cluster.local:5000                 |   |
   |   | Pod: order-api (Flask, non-root UID 8888)                     |   |
   |   | Endpoints:                                                    |   |
   |   |   - GET  /health (Liveness/Readiness probe)                   |   |
   |   |   - POST /orders (Ingestion & Validation)                     |   |
   |   +-------------------------------+-------------------------------+   |
   |                                   |                                   |
   |                                   | HTTP POST (sync forwarded)        |
   |                                   | http://order-processor:5001       |
   |                                   v                                   |
   |   +---------------------------------------------------------------+   |
   |   | Service: order-processor (ClusterIP)                          |   |
   |   | DNS: order-processor.default.svc.cluster.local:5001           |   |
   |   | Pod: order-processor (Flask, non-root UID 8888)               |   |
   |   | Endpoints:                                                    |   |
   |   |   - GET  /health (Liveness/Readiness probe)                   |   |
   |   |   - POST /process (Business Logic & State Transition)         |   |
   |   +-------------------------------+-------------------------------+   |
   |                                   |                                   |
   |                                   | HTTP POST (dispatch alert)        |
   |                                   | http://notification-service:5002  |
   |                                   v                                   |
   |   +---------------------------------------------------------------+   |
   |   | Service: notification-service (ClusterIP)                     |   |
   |   | DNS: notification-service.default.svc.cluster.local:5002      |   |
   |   | Pod: notification-service (Flask, non-root UID 8888)          |   |
   |   | Endpoints:                                                    |   |
   |   |   - GET  /health (Liveness/Readiness probe)                   |   |
   |   |   - POST /notify (Alert Distribution)                         |   |
   |   +---------------------------------------------------------------+   |
   +-----------------------------------------------------------------------+
```

---

## 3. Microservice Specifications & Port Allocations

| Service Name | Port | Protocol | Base Image | Security Context | Responsibilities |
|---|---|---|---|---|---|
| **order-api** | `5000` | HTTP/REST | `python:3.11-slim` | Non-root `appuser` (UID 8888) | API Gateway / Ingestion endpoint; validates payload schema; forwards to processor; returns HTTP 202 Accepted. |
| **order-processor** | `5001` | HTTP/REST | `python:3.11-slim` | Non-root `appuser` (UID 8888) | Core state logic; validates `order_id`; triggers notification service; returns HTTP 200 PROCESSED. |
| **notification-service** | `5002` | HTTP/REST | `python:3.11-slim` | Non-root `appuser` (UID 8888) | Notification dispatch engine; validates recipient; generates event alert; returns HTTP 200 DISPATCHED. |

---

## 4. Service Discovery & CoreDNS Networking
In Kubernetes, pods communicate without hardcoded IP addresses through **Kubernetes CoreDNS**:
- Each service is registered under standard Kubernetes FQDN: `<service-name>.<namespace>.svc.cluster.local`.
- Within the same namespace (`default`), services resolve using their short names:
  - `http://order-processor:5001/process`
  - `http://notification-service:5002/notify`
- Environment variables (`ORDER_PROCESSOR_URL`, `NOTIFICATION_SERVICE_URL`) decouple networking targets from source code, enabling environment-specific injection via Helm values.

---

## 5. Data Contracts & Payload Schemas

### 5.1 POST `/orders` (order-api)
- **Request:**
  ```json
  {
    "order_id": "ORD-12345",
    "item": "Mechanical Keyboard",
    "amount": 149.99
  }
  ```
- **Validation Rules:**
  - `order_id` (string, required, non-empty)
  - `item` (string, required, non-empty)
  - `amount` (numeric, required)
- **Response (HTTP 202 Accepted):**
  ```json
  {
    "status": "PROCESSED",
    "order_id": "ORD-12345",
    "message": "Order accepted and processed successfully"
  }
  ```

### 5.2 POST `/process` (order-processor)
- **Request:**
  ```json
  {
    "order_id": "ORD-12345",
    "item": "Mechanical Keyboard",
    "amount": 149.99
  }
  ```
- **Validation Rules:**
  - `order_id` (string, required)
- **Response (HTTP 200 OK):**
  ```json
  {
    "status": "PROCESSED",
    "order_id": "ORD-12345",
    "message": "Order processed successfully"
  }
  ```

### 5.3 POST `/notify` (notification-service)
- **Request:**
  ```json
  {
    "recipient": "user-ORD-12345@example.com",
    "order_id": "ORD-12345",
    "message": "Order ORD-12345 has been processed."
  }
  ```
- **Validation Rules:**
  - `recipient` (string, required, non-empty)
- **Response (HTTP 200 OK):**
  ```json
  {
    "status": "DISPATCHED",
    "recipient": "user-ORD-12345@example.com",
    "message": "Notification dispatched successfully"
  }
  ```
