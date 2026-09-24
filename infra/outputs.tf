output "resource_group_name" {
  description = "The name of the resource group"
  value       = azurerm_resource_group.rg.name
}

output "acr_login_server" {
  description = "The login server for the Azure Container Registry"
  value       = azurerm_container_registry.acr.login_server
}

output "aks_cluster_name" {
  description = "The name of the AKS cluster"
  value       = azurerm_kubernetes_cluster.aks.name
}

output "kubelet_identity_object_id" {
  description = "The object ID of the AKS kubelet identity"
  value       = azurerm_kubernetes_cluster.aks.kubelet_identity[0].object_id
}
