"""
Kubernetes Manifest Generator - GitOps-ready K8s configurations.

Features:
- Deployment with rolling updates
- Service manifests
- ArgoCD Application for GitOps
- Resource limits and health checks
"""

import logging
from typing import Any, AsyncIterator, Dict

import yaml

from .base import BaseGenerator

logger = logging.getLogger(__name__)


class KubernetesGenerator(BaseGenerator):
    """Generate Kubernetes manifests with ArgoCD integration."""

    @property
    def name(self) -> str:
        return "kubernetes"

    async def generate(self, task_request: str) -> Dict[str, Any]:
        """Generate Kubernetes manifests."""
        logger.info("Generating Kubernetes manifests...")

        app_name = self._extract_app_name(task_request)
        namespace = "default"
        replicas = 3

        deployment = self._build_deployment(app_name, namespace, replicas)
        service = self._build_service(app_name, namespace)
        argocd_app = self._build_argocd_application(app_name, namespace)

        return {
            "deployment.yaml": yaml.dump(deployment),
            "service.yaml": yaml.dump(service),
            "argocd-application.yaml": yaml.dump(argocd_app),
            "gitops_enabled": True,
            "features": [
                "Rolling updates (zero-downtime)",
                "Resource limits enforced",
                "Health checks configured",
                "ArgoCD auto-sync enabled",
                "Self-healing enabled",
            ],
        }

    async def generate_streaming(self, task_request: str) -> AsyncIterator[Dict[str, Any]]:
        """Generate Kubernetes manifests with streaming output."""
        yield {"type": "status", "data": "☸️ Kubernetes Generator starting..."}

        app_name = self._extract_app_name(task_request)
        namespace = "default"

        yield {"type": "thinking", "data": f"Generating manifests for: {app_name}\n"}

        yield {"type": "status", "data": "📦 Building Deployment manifest..."}
        deployment = self._build_deployment(app_name, namespace, 3)

        yield {"type": "status", "data": "🔌 Building Service manifest..."}
        service = self._build_service(app_name, namespace)

        yield {"type": "status", "data": "🔄 Configuring ArgoCD GitOps..."}
        argocd_app = self._build_argocd_application(app_name, namespace)

        yield {"type": "verdict", "data": "\n\n✅ Kubernetes manifests ready for GitOps"}

        yield {
            "type": "result",
            "data": {
                "deployment.yaml": yaml.dump(deployment),
                "service.yaml": yaml.dump(service),
                "argocd-application.yaml": yaml.dump(argocd_app),
                "gitops_enabled": True,
            },
        }

    def _extract_app_name(self, request: str) -> str:
        """Extract app name from request or use default."""
        # Simplified - would parse request more carefully
        return "api-service"

    def _build_deployment(self, app_name: str, namespace: str, replicas: int) -> Dict[str, Any]:
        """Build Deployment manifest."""
        return {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": app_name,
                "namespace": namespace,
                "labels": {"app": app_name},
            },
            "spec": {
                "replicas": replicas,
                "strategy": {
                    "type": "RollingUpdate",
                    "rollingUpdate": {
                        "maxSurge": 1,
                        "maxUnavailable": 0,
                    },
                },
                "selector": {"matchLabels": {"app": app_name}},
                "template": {
                    "metadata": {"labels": {"app": app_name}},
                    "spec": {
                        "containers": [
                            {
                                "name": app_name,
                                "image": f"{app_name}:latest",
                                "ports": [{"containerPort": 8000}],
                                "resources": {
                                    "requests": {"memory": "128Mi", "cpu": "250m"},
                                    "limits": {"memory": "512Mi", "cpu": "500m"},
                                },
                                "livenessProbe": {
                                    "httpGet": {"path": "/health", "port": 8000},
                                    "initialDelaySeconds": 15,
                                    "periodSeconds": 20,
                                },
                                "readinessProbe": {
                                    "httpGet": {"path": "/ready", "port": 8000},
                                    "initialDelaySeconds": 5,
                                    "periodSeconds": 10,
                                },
                            }
                        ],
                    },
                },
            },
        }

    def _build_service(self, app_name: str, namespace: str) -> Dict[str, Any]:
        """Build Service manifest."""
        return {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": f"{app_name}-svc",
                "namespace": namespace,
            },
            "spec": {
                "selector": {"app": app_name},
                "ports": [{"protocol": "TCP", "port": 80, "targetPort": 8000}],
                "type": "ClusterIP",
            },
        }

    def _build_argocd_application(self, app_name: str, namespace: str) -> Dict[str, Any]:
        """Build ArgoCD Application manifest."""
        return {
            "apiVersion": "argoproj.io/v1alpha1",
            "kind": "Application",
            "metadata": {
                "name": f"{app_name}-gitops",
                "namespace": "argocd",
            },
            "spec": {
                "destination": {
                    "namespace": namespace,
                    "server": "https://kubernetes.default.svc",
                },
                "source": {
                    "repoURL": "https://github.com/your-org/platform-gitops",
                    "path": f"apps/{app_name}",
                    "targetRevision": "main",
                },
                "syncPolicy": {
                    "automated": {
                        "prune": True,
                        "selfHeal": True,
                    },
                },
            },
        }
