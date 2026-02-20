from tools.file_ops import FileOps
from tools.system_ops import SystemOps
from tools.process_ops import ProcessOps
from tools.text_ops import TextOps
from tools.browser_ops import BrowserOps
from tools.package_ops import PackageOps
from tools.service_ops import ServiceOps
from tools.container_ops import ContainerOps
from tools.git_ops import GitOps
from tools.network_ops import NetworkOps

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
