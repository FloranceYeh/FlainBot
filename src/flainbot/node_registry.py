from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass
import importlib
import pkgutil
from typing import Any

from .providers import Transport

NodeConfig = dict[str, Any]
NodePackage = dict[str, Any]
NodeBuilder = Callable[[NodeConfig, "NodeBuildContext"], Any]


@dataclass(frozen=True)
class NodeBuildContext:
    message: str
    transports: dict[str, Transport]
    providers: dict[str, dict[str, Any]]
    personas: dict[str, dict[str, Any]]


class NodePackageRegistry:
    def __init__(self) -> None:
        self._packages: list[NodePackage] = []
        self._builders: dict[str, NodeBuilder] = {}

    def register_package(
        self,
        package: NodePackage,
        builders: dict[str, NodeBuilder],
    ) -> None:
        package_id = package.get("id")
        if package.get("kind") != "package" or not package_id:
            raise ValueError("node package must have kind='package' and an id")
        for node_type, builder in builders.items():
            if node_type in self._builders:
                raise ValueError(f"duplicate node type: {node_type}")
            self._builders[node_type] = builder
        self._packages.append(package)

    def catalog(self) -> list[NodePackage]:
        return deepcopy(self._packages)

    def build(self, node_config: NodeConfig, context: NodeBuildContext) -> Any:
        node_type = node_config["type"]
        builder = self._builders.get(node_type)
        if builder is None:
            raise ValueError(f"unsupported node type: {node_type}")
        return builder(node_config, context)


def discover_node_registry(package_name: str = "flainbot.node_packages") -> NodePackageRegistry:
    package = importlib.import_module(package_name)
    registry = NodePackageRegistry()

    for module_info in pkgutil.iter_modules(package.__path__):
        module = importlib.import_module(f"{package_name}.{module_info.name}")
        node_package = module.get_node_package()
        node_builders = module.get_node_builders()
        registry.register_package(node_package, node_builders)

    return registry
