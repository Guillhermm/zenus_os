from zenus_core.tools.file_ops import FileOps
from zenus_core.tools.system_ops import SystemOps
from zenus_core.tools.process_ops import ProcessOps
from zenus_core.tools.text_ops import TextOps
from zenus_core.tools.browser_ops import BrowserOps
from zenus_core.tools.package_ops import PackageOps
from zenus_core.tools.service_ops import ServiceOps
from zenus_core.tools.container_ops import ContainerOps
from zenus_core.tools.git_ops import GitOps
from zenus_core.tools.network_ops import NetworkOps

TOOLS = {
    # Core tools
    "FileOps": FileOps(),
    "SystemOps": SystemOps(),
    "ProcessOps": ProcessOps(),
    "TextOps": TextOps(),
    
    # Extended tools
    "BrowserOps": BrowserOps(),
    "PackageOps": PackageOps(),
    "ServiceOps": ServiceOps(),
    "ContainerOps": ContainerOps(),
    "GitOps": GitOps(),
    "NetworkOps": NetworkOps()
}
