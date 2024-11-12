from typing import Literal

import pytest
from pystac import MediaType

from stactools.glad_glclu2020 import stac
from stactools.glad_glclu2020.metadata import ASSET_NAME, CollectionIDs

from . import test_data


@pytest.mark.parametrize(
    ["id", "media_type"],
    [
        (CollectionIDs.GLAD_GLCLU2020, MediaType.GEOTIFF),
        (CollectionIDs.GLAD_GLCLU2020, MediaType.COG),
        (CollectionIDs.GLAD_GLCLU2020_CHANGE, MediaType.GEOTIFF),
        (CollectionIDs.GLAD_GLCLU2020_CHANGE, MediaType.COG),
    ],
)  # type: ignore
def test_create_collection_from_media_type(
    id: Literal[CollectionIDs.GLAD_GLCLU2020, CollectionIDs.GLAD_GLCLU2020_CHANGE],
    media_type: MediaType,
) -> None:
    # This function should be updated to exercise the attributes of interest on
    # the collection

    collection = stac.create_collection(id, media_type=media_type)
    collection.set_self_href(None)  # required for validation to pass
    assert collection.id == id
    assert collection.ext.item_assets[ASSET_NAME].media_type == media_type
    collection.validate()


@pytest.mark.parametrize(
    ["id", "sample_asset_href", "media_type"],
    [
        (
            collection_id,
            test_data.get_path(f"data/{format}/v2/{year}/40N_080W.tif"),
            media_type,
        )
        for collection_id in CollectionIDs
        for format, media_type in [
            ("geotiff", MediaType.GEOTIFF),
            ("cog", MediaType.COG),
        ]
        for year in ["2000", "2000-2020change"]
    ],
)  # type: ignore
def test_create_collection_from_sample_asset_href(
    id: Literal[CollectionIDs.GLAD_GLCLU2020, CollectionIDs.GLAD_GLCLU2020_CHANGE],
    sample_asset_href: str,
    media_type: MediaType,
) -> None:
    # This function should be updated to exercise the attributes of interest on
    # the collection

    collection = stac.create_collection(id, sample_asset_href=sample_asset_href)
    collection.set_self_href(None)  # required for validation to pass
    assert collection.id == id
    print("asset media_type:", collection.ext.item_assets[ASSET_NAME].media_type)
    print("expected media_type:", media_type)
    assert collection.ext.item_assets[ASSET_NAME].media_type == media_type
    collection.validate()


@pytest.mark.parametrize(
    ["asset_href", "year", "media_type"],
    [
        (
            test_data.get_path(f"data/{format}/v2/{year}/40N_080W.tif"),
            year,
            media_type,
        )
        for format, media_type in [
            ("geotiff", MediaType.GEOTIFF),
            ("cog", MediaType.COG),
        ]
        for year in ["2000", "2000-2020change"]
    ],
)  # type: ignore
def test_create_item(asset_href: str, year: str, media_type: MediaType) -> None:
    version, loc = "v2", "40N_080W"
    test_href_format = (
        asset_href.replace(version, "{version}")
        .replace(year, "{year}")
        .replace(loc, "{loc}")
    )

    item = stac.create_item(
        test_data.get_path(asset_href), href_format=test_href_format
    )
    assert item.id == "_".join([version, year, loc])
    assert item.assets[ASSET_NAME].media_type == media_type
    item.validate()


def test_bad_item_href_formats() -> None:
    """Test bad hrefs and href_formats"""
    with pytest.raises(ValueError, match="missing required parameters: version"):
        stac.create_item("test.tif", href_format="test/{ver}/{year}/{loc}.tif")

    with pytest.raises(ValueError, match="missing required parameters: year"):
        stac.create_item("test.tif", href_format="test/{version}/{yeer}/{loc}.tif")

    with pytest.raises(ValueError, match="The year parameter cannot be parsed"):
        stac.create_item(
            "test/v2/20000/10N_050W.tif", href_format="test/{version}/{year}/{loc}.tif"
        )

    with pytest.raises(ValueError, match="The year parameter cannot be parsed"):
        stac.create_item(
            "test/v2/2000-20200change/10N_050W.tif",
            href_format="test/{version}/{year}/{loc}.tif",
        )

    with pytest.raises(ValueError, match="could not parse the provided href"):
        stac.create_item(
            "10N_050W.tif",
            href_format="test/{version}/{year}/{loc}.tif",
        )
