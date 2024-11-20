import logging
import warnings
from typing import Optional

import click
from click import Command, Group
from pystac import MediaType

from stactools.glad_glclu2020 import stac
from stactools.glad_glclu2020.metadata import (
    DEFAULT_HREF_FORMAT,
    CollectionIDs,
)

logger = logging.getLogger(__name__)


def create_gladglclu2020_command(cli: Group) -> Command:
    """Creates the stactools-glad-glclu2020 command line utility."""

    @cli.group(
        "gladglclu2020",
        help="Generate STAC metadata for the GLAD Global Land Use Land Cover dataset",
        short_help=("Commands for working with stactools-glad-glclu2020"),
    )
    def gladglclu2020() -> None:
        pass

    @gladglclu2020.command(
        "create-collection",
        help=stac.CREATE_COLLECTION_DESCRIPTION,
        short_help="Creates a STAC collection",
    )
    @click.argument("destination")
    @click.option(
        "--type",
        "collection_type",
        type=click.Choice(["annual", "change"], case_sensitive=False),
        required=True,
        help="Type of collection to create",
    )
    @click.option(
        "--media-type",
        type=str,
        help="Media type for the collection",
        default=None,
    )
    @click.option(
        "--sample-asset-href",
        type=str,
        help="Sample asset HREF for the collection for determining the media type of "
        "the assets",
        default=None,
    )
    def create_collection_command(
        destination: str,
        collection_type: str,
        media_type: Optional[str],
        sample_asset_href: Optional[str],
    ) -> None:
        """Creates a STAC Collection

        Args:
            destination: An HREF for the Collection JSON
            id: Collection ID to create
            media_type: Media type for the collection
            sample_asset_href: Sample asset HREF for the collection
        """
        collection_id = (
            CollectionIDs.GLAD_GLCLU2020
            if collection_type == "annual"
            else CollectionIDs.GLAD_GLCLU2020_CHANGE
        )

        if not (sample_asset_href or media_type):
            warnings.warn(
                "No sample_asset_href or media_type provided. "
                f"Defaulting to {MediaType.GEOTIFF} media type.",
                category=UserWarning,
            )
            media_type = MediaType.GEOTIFF.value

        media_type_enum = MediaType(media_type) if media_type else None

        collection = stac.create_collection(
            id=collection_id,
            media_type=media_type_enum,
            sample_asset_href=sample_asset_href,
        )
        collection.set_self_href(destination)
        collection.save_object()

    @gladglclu2020.command(
        "create-item",
        help=stac.CREATE_ITEM_DESCRIPTION,
        short_help="Create a STAC item",
    )
    @click.argument("source")
    @click.argument("destination")
    @click.option(
        "--href-format",
        type=str,
        help=stac.CREATE_ITEM_DESCRIPTION,
        default=DEFAULT_HREF_FORMAT,
    )
    def create_item_command(
        source: str,
        destination: str,
        href_format: str,
    ) -> None:
        """Creates a STAC Item

        Args:
            source: HREF of the Asset associated with the Item
            destination: An HREF for the STAC Item
            href_format: Format for asset HREFs
        """
        item = stac.create_item(
            asset_href=source,
            href_format=href_format,
        )
        item.save_object(dest_href=destination)

    return gladglclu2020
