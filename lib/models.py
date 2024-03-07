from typing import Any, Dict, List

from github_webhooks.schemas import WebhookCommonPayload
from pydantic import BaseModel, ConfigDict


class Env(BaseModel):
    model_config = ConfigDict(extra="allow")


class Plugin(BaseModel):
    """Plugin model"""

    version: str
    enabled: bool = False
    """Wether or not the plugin is enabled"""
    apikey: str = None
    """The API key to use for the plugin, if the plugin requires one"""
    name: str = None
    """The name of the plugin"""
    description: str = None
    """A description of the plugin"""
    options: Dict[str, Any] = {}
    """A dictionary of options to pass to the plugin"""


class PluginRegistry(BaseModel):
    """Plugin registry"""

    crowdsec: Plugin


class Service(BaseModel):
    """Service model"""

    command: str = None
    """The command to run in the service"""
    env: Env = None
    """A dictionary of environment variables to pass to the service"""
    image: str = None
    """The image name plus tag to use for the service"""
    labels: List[str] = []
    """Extra labels to add to the service. Should not interfere with generated traefik labels for ingress."""
    name: str
    passthrough: bool = False
    """Wether or not traffic to this service is forwarded as-is (without terminating SSL)"""
    path_prefix: str = None
    """Should the service be exposed under a specific path?"""
    path_remove: bool = False
    """When set, the path prefix will be removed from the request before forwarding it to the service"""
    port: int = 8080
    """When set, the service will be exposed on this domain."""
    proxyprotocol: bool = True
    """When set, the service will be exposed using the PROXY protocol version 2"""
    volumes: List[str] = []
    """A list of volumes to mount in the service"""
    additional_properties: Dict[str, Any] = {}
    """Additional docker compose properties to pass to the service"""


class Project(BaseModel):
    """Project model"""

    name: str
    description: str = None
    domain: str = None
    entrypoint: str = None
    """When "entrypoint" is set it should point to a service in the "services" list that has an image"""
    services: List[Service] = []


class PingPayload(WebhookCommonPayload):

    zen: str


class WorkflowJobPayload(WebhookCommonPayload):
    class WorkflowJob(BaseModel):
        name: str
        status: str
        conclusion: str | None = None

    workflow_job: WorkflowJob
