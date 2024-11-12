import stactools.core
from stactools.cli.registry import Registry
from stactools.glad_glclu2020.stac import create_collection, create_item

__all__ = ["create_collection", "create_item"]

stactools.core.use_fsspec()


def register_plugin(registry: Registry) -> None:
    from stactools.glad_glclu2020 import commands

    registry.register_subcommand(commands.create_gladglclu2020_command)
