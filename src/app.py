"""ai-agent-registry — FastAPI application."""
from platform_sdk import BaseAgentApp


class RegistryAgentApp(BaseAgentApp):
    service_name = "ai-agent-registry"
    service_title = "ai-agent-registry"
    mcp_servers = {}
    enable_telemetry = True

    def build_dependencies(self, *, bridges, checkpointer, store):
        return {"placeholder": True}

    def routes(self):
        return []


_agent = RegistryAgentApp()
app = _agent.create_app()
