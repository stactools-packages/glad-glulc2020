from pathlib import Path

import pytest
from click import Group
from click.testing import CliRunner
from pystac import Collection, Item, MediaType

from stactools.glad_glclu2020.commands import create_gladglclu2020_command
from stactools.glad_glclu2020.metadata import ASSET_NAME

from . import test_data

command = create_gladglclu2020_command(Group())


@pytest.mark.parametrize(
    ["collection_type", "media_type"],
    [
        (collection_type, media_type)
        for collection_type in ["annual", "change"]
        for media_type in [MediaType.COG, MediaType.GEOTIFF]
    ],
)  # type: ignore
def test_create_collection_from_media_type(
    tmp_path: Path, collection_type: str, media_type: MediaType
) -> None:
    path = str(tmp_path / "collection.json")
    runner = CliRunner()
    result = runner.invoke(
        command,
        [
            "create-collection",
            "--type",
            collection_type,
            "--media-type",
            media_type,
            path,
        ],
    )
    assert result.exit_code == 0, "\n{}".format(result.output)
    collection = Collection.from_file(path)
    collection.validate()


@pytest.mark.parametrize(
    [
        "collection_type",
        "sample_asset_href",
        "media_type",
    ],
    [
        (
            collection_type,
            test_data.get_path(f"data/{format}/v2/{year}/40N_080W.tif"),
            media_type,
        )
        for collection_type in ["annual", "change"]
        for format, media_type in [
            ("geotiff", MediaType.GEOTIFF),
            ("cog", MediaType.COG),
        ]
        for year in ["2000", "2000-2020change"]
    ],
)  # type: ignore
def test_create_collection_from_sample_asset_href(
    tmp_path: Path, collection_type: str, sample_asset_href: str, media_type: MediaType
) -> None:
    path = str(tmp_path / "collection.json")
    runner = CliRunner()
    result = runner.invoke(
        command,
        [
            "create-collection",
            "--type",
            collection_type,
            "--sample-asset-href",
            sample_asset_href,
            path,
        ],
    )
    assert result.exit_code == 0, "\n{}".format(result.output)
    collection = Collection.from_file(path)
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
def test_create_item(
    tmp_path: Path, asset_href: str, year: str, media_type: MediaType
) -> None:
    version, loc = "v2", "40N_080W"
    test_href_format = (
        asset_href.replace(version, "{version}")
        .replace(year, "{year}")
        .replace(loc, "{loc}")
    )
    path = str(tmp_path / "item.json")
    runner = CliRunner()
    result = runner.invoke(
        command, ["create-item", "--href-format", test_href_format, asset_href, path]
    )
    assert result.exit_code == 0, "\n{}".format(result.output)
    item = Item.from_file(path)
    assert item.assets[ASSET_NAME].media_type == media_type
    item.validate()


def test_create_collection_no_media_type_or_sample(tmp_path: Path) -> None:
    """Test warning if no media_type or sample_asset_href provided"""
    path = str(tmp_path / "collection.json")
    runner = CliRunner()
    with pytest.warns(UserWarning, match="No sample_asset_href or media_type provided"):
        result = runner.invoke(
            command,
            [
                "create-collection",
                "--type",
                "annual",
                path,
            ],
        )
    assert result.exit_code == 0, "\n{}".format(result.output)
