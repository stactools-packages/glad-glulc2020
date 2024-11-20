from typing import Optional

from pystac import (
    Collection,
    Item,
    MediaType,
)

from stactools.glad_glclu2020.metadata import (
    DEFAULT_HREF_FORMAT,
    CollectionIDs,
    CollectionRegistry,
    HrefFormat,
)

CREATE_COLLECTION_DESCRIPTION = f"""Generate collection metadata for either the annual
({CollectionIDs.GLAD_GLCLU2020.value}) or change 
({CollectionIDs.GLAD_GLCLU2020_CHANGE.value}) collection types.

Either the media_type or sample_asset_href arguments must be supplied in order to
populate the media type in the item-assets metadata.
"""

CREATE_ITEM_DESCRIPTION = """Generate item metadata given an asset href and an 
href_format. Users can simply provide an href from the lists published on the
dataset homepage (e.g. https://storage.googleapis.com/earthenginepartners-hansen/GLCLU2000-2020/v2/2020.txt)
to generate item metadata for the original assets. In this case the default href_format
is used (https://storage.googleapis.com/earthenginepartners-hansen/GLCLU2000-2020/{version}/{year}/{loc}.tif).

To generate item metadata for a set of assets in a different storage location, e.g. 
COGs in S3, those hrefs can be provided with an accompanying href_format (e.g. 
s3://bucket/GLCLU2000-2020/{version}/{year}/{loc}.tif) that can be used to parse the 
item ID information from the href.
"""


def create_collection(
    id: CollectionIDs,
    media_type: Optional[MediaType] = None,
    sample_asset_href: Optional[str] = None,
) -> Collection:
    f"""Creates a STAC Collection.

    {CREATE_COLLECTION_DESCRIPTION}

    Args:
        id: Either CollectionIDs.GLAD_GLCLU2020 or CollectionIDs.GLAD_GLCLU2020_CHANGE
        media_type: The media type of the assets (usually MediaType.COG or
            Mediatype.GEOTIFF)
        sample_asset_href: A sample asset href to use for identifying the media type
    Returns:
        Collection: STAC Collection object
    """
    collections = CollectionRegistry()
    config = collections.get_config(id)

    return config.build_collection(media_type, sample_asset_href)


def create_item(asset_href: str, href_format: HrefFormat = DEFAULT_HREF_FORMAT) -> Item:
    f"""Creates a STAC item from an asset href.
    
    {CREATE_ITEM_DESCRIPTION}

    Args:
        asset_href (str): The asset href from which to create the item
        href_format (str): The string format that can be used to parse the asset_href

    Details:
        The href_format parameter is used to extract the year from the
        asset_href. href_format must include the parameter 'year'.
        Any other parameters that are included will be parsed and added to the item ID.

    Returns:
        Item: STAC Item object
    """
    registry = CollectionRegistry(href_format=href_format)
    for config in registry.configs.values():
        if config.parse_href(asset_href):
            return config.create_item(asset_href)

    raise ValueError(f"No matching collection found for href: {asset_href}")
