variable "resource_group_name" {
  type        = string
  description = "The name of the resource group"
  default     = "rg-order-platform-prod"
}

variable "location" {
  type        = string
  description = "The Azure Region to deploy resources"
  default     = "eastus"
}

variable "acr_name" {
  type        = string
  description = "The name of the Azure Container Registry"
  default     = "acrorganizationplatform01"
}

variable "aks_cluster_name" {
  type        = string
  description = "The name of the AKS managed cluster"
  default     = "aks-order-platform-cluster"
}

variable "node_count" {
  type        = number
  description = "Initial number of worker nodes"
  default     = 2
}

variable "vm_size" {
  type        = string
  description = "The Virtual Machine size for the AKS node pool"
  default     = "Standard_B2s"
}
