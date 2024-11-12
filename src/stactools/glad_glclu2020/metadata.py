import csv
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Annotated, Any, Dict, List, Optional, Union

import pystac.extensions.version as version_ext
import rio_stac
from parse import Parser, Result, parse
from pystac import (
    Asset,
    Collection,
    Extent,
    Item,
    Link,
    MediaType,
    RelType,
    SpatialExtent,
    TemporalExtent,
)
from pystac.extensions.classification import (
    AssetClassificationExtension,
    Classification,
    ItemAssetsClassificationExtension,
)
from pystac.extensions.item_assets import AssetDefinition, ItemAssetsExtension
from pystac.extensions.scientific import (
    CollectionScientificExtension,
    ScientificRelType,
)
from rio_cogeo.cogeo import cog_validate
from rio_stac.stac import get_media_type, rasterio
from slugify import slugify

DATA_DIR = Path(__file__).parent / "data"

COLLECTION_START_DATETIME = datetime(2000, 1, 1, tzinfo=timezone.utc)
COLLECTION_END_DATETIME = datetime(2020, 12, 31, 23, 59, 59, tzinfo=timezone.utc)

DEFAULT_HREF_FORMAT = "https://storage.googleapis.com/earthenginepartners-hansen/GLCLU2000-2020/{version}/{year}/{loc}.tif"

COLLECTION_HOMEPAGE = "https://storage.googleapis.com/earthenginepartners-hansen/GLCLU2000-2020/v2/download.html"

COLLECTION_CITATION = (
    "P.V. Potapov, M.C. Hansen, A.H. Pickens, A. Hernandez-Serna, "
    "A. Tyukavina, S. Turubanova, V. Zalles, X. Li, A. Khan, "
    "F. Stolle, N. Harris, X.-P. Song, A. Baggett, I. Kommareddy, "
    "A. Komareddy (2022)."
)
COLLECTION_DOI = "frsen.2022.856903"
COLLECTION_DESCRIPTION = (
    "The GLAD Global Land Cover and Land Use Change dataset quantifies "
    "changes in forest extent and height, cropland, built-up lands, "
    "surface water, and perennial snow and ice extent from the year 2000 "
    "to 2020 at 30-m spatial resolution. The global dataset derived from "
    "the GLAD Landsat Analysis Ready Data. Each thematic product was "
    "independently derived using state-of-the-art, locally and regionally "
    "calibrated machine learning tools. Each thematic layer was validated "
    "independently using a statistical sampling. The global dataset is "
    "available online, with no charges for access and no restrictions on "
    "subsequent redistribution or use, as long as the proper citation is "
    "provided as specified by the Creative Commons Attribution License "
    "(CC BY). For all questions and comment contact Peter Potapov "
    "(potapov@umd.edu).\n\n" + COLLECTION_CITATION
)
COLLECTION_KEYWORDS = [
    "land cover",
    "land use",
    "land use change",
    "vegetation",
    "surface water",
]


class CollectionIDs(str, Enum):
    GLAD_GLCLU2020 = "glad-glclu2020"
    GLAD_GLCLU2020_CHANGE = "glad-glclu2020-change"


BaseURL = Annotated[str, "Base URL for data assets"]
HrefFormat = Annotated[str, "String format for the asset hrefs"]


YEAR_FORMAT = "{year:4d}"
CHANGE_YEAR_FORMAT = "{start_year:4d}-{end_year:4d}change"
ASSET_NAME = "data"
ASSET_ROLES = ["data"]


def _get_media_type(sample_asset_href: str) -> MediaType:
    """Get media type for an asset href"""
    valid_cog, _, _ = cog_validate(sample_asset_href, quiet=True)
    if valid_cog:
        return MediaType.COG if valid_cog else MediaType.GEOTIFF

    with rasterio.open(sample_asset_href) as src:
        media_type: MediaType | None = get_media_type(src)

        if not media_type:
            raise ValueError(f"could not identify media type for {sample_asset_href}")

        return media_type


@dataclass
class CollectionDefinition:
    """Collection configuration"""

    id: CollectionIDs
    title: str
    description: str
    classifications_file: Path
    asset_title: str
    asset_description: str

    # Asset configuration
    href_format: Annotated[str, "String format for the asset hrefs"] = (
        DEFAULT_HREF_FORMAT
    )

    # Cached properties
    _classifications: Optional[List[Classification]] = field(init=False, default=None)

    @property
    def classifications(self) -> List[Classification]:
        """Lazy load classifications from CSV."""
        if self._classifications is None:
            self._classifications = self._load_classifications()
        return self._classifications

    def _load_classifications(self) -> List[Classification]:
        classifications = []
        with open(self.classifications_file, "r", newline="") as csvfile:
            reader = csv.DictReader(csvfile, delimiter=",")
            for row in reader:
                entry = Classification.create(
                    value=int(row["value"]),
                    name=slugify(
                        "__".join(
                            [row["general_class"], row["class"], row["sub_class"]]
                        )
                    ),
                    description=(
                        f"{row['class']} - {row['sub_class']}"
                        if row["sub_class"].strip()
                        else row["class"]
                    ),
                    nodata=True if int(row["value"]) == 255 else False,
                    color_hint=row["color_hint"].strip() if row["color_hint"] else None,
                )
                classifications.append(entry)

        return classifications

    @property
    def item_assets(self) -> Dict[str, AssetDefinition]:
        asset_definition = AssetDefinition.create(
            roles=ASSET_ROLES,
            title=self.asset_title,
            description=self.asset_description,
            media_type=None,
        )
        classification_extension = ItemAssetsClassificationExtension(asset_definition)
        classification_extension.classes = self.classifications

        return {ASSET_NAME: asset_definition}

    @property
    def renders(self) -> Dict[str, Any]:
        """Set up render keys for each unique datetime in the collection"""
        datetimes = (
            [
                (year, f"{year}-01-01T00:00:00Z/{year}-12-31T23:59:59Z")
                for year in ["2000", "2005", "2010", "2015", "2020"]
            ]
            if self.id == CollectionIDs.GLAD_GLCLU2020
            else [("2000-2020 change", "2000-01-01T00:00:00Z/2020-12-31T23:59:59Z")]
        )
        return {
            year: {
                "assets": [ASSET_NAME],
                "datetime": datetime_str,
                "colormap": {
                    # convert hex to rgb
                    classification.value: tuple(
                        int(classification.color_hint[i : i + 2], 16) for i in (0, 2, 4)
                    )
                    for classification in self.classifications
                    if classification.color_hint
                },
            }
            for year, datetime_str in datetimes
        }

    def build_collection(
        self,
        media_type: Optional[MediaType] = None,
        sample_asset_href: Optional[str] = None,
    ) -> Collection:
        """Build Collection object"""
        if not (sample_asset_href or media_type):
            raise ValueError(
                "either provide a media_type or sample_asset_href in order to "
                "determine the media type"
            )

        if not media_type and sample_asset_href:
            media_type = _get_media_type(sample_asset_href)

        assets = self.item_assets
        assets[ASSET_NAME].media_type = media_type

        collection = Collection(
            id=self.id.value,
            title=self.title,
            description=self.description,
            extent=Extent(
                SpatialExtent([[-180.0, 80.0, 180.0, -80.0]]),
                TemporalExtent(
                    [
                        [
                            COLLECTION_START_DATETIME,
                            COLLECTION_END_DATETIME,
                        ]
                    ]
                ),
            ),
            extra_fields={"renders": self.renders},
            keywords=COLLECTION_KEYWORDS,
            license="CC-BY-4.0",
            assets={
                "thumbnail": Asset(
                    href=(
                        "https://glad.umd.edu/sites/default/files/styles/projects/public/datasets_glulc.jpg?itok=bxS-HPMi"
                    ),
                    media_type=MediaType.PNG,
                    title=self.title,
                    roles=["thumbnail"],
                )
            },
        )

        # add scientific citation extension
        scientific_extension = CollectionScientificExtension.ext(
            collection, add_if_missing=True
        )
        scientific_extension.citation = COLLECTION_CITATION

        # add item_assets extension
        item_assets_ext = ItemAssetsExtension.ext(collection, add_if_missing=True)
        item_assets_ext.item_assets = assets

        # add links
        links = [
            Link(
                rel=RelType.LICENSE,
                target="https://creativecommons.org/licenses/by/4.0/",
                media_type="text/html",
                title="CC-BY-4.0 license",
            ),
            Link(
                rel="documentation",
                target=COLLECTION_HOMEPAGE,
                media_type="text/html",
                title="GLAD GLCLU Access Page",
            ),
            Link(
                rel=ScientificRelType.CITE_AS,
                target="https://doi.org/10.3389/frsen.2022.856903",
            ),
        ]
        collection.add_links(links)

        return collection

    def parse_href(self, href: str) -> Union[None, Dict[str, Any]]:
        parsed = parse(self.href_format, href)
        if not isinstance(parsed, Result):
            raise ValueError(
                f"could not parse the provided href ({href}) using the provided "
                f"href_format: {self.href_format}"
            )

        if year_parsed := parse(CHANGE_YEAR_FORMAT, parsed.named["year"]):
            if not isinstance(year_parsed, Result):
                return None

            collection_id = CollectionIDs.GLAD_GLCLU2020_CHANGE
            datetime_properties = {
                "start_datetime": datetime(
                    year=int(year_parsed.named["start_year"]),
                    month=1,
                    day=1,
                    tzinfo=timezone.utc,
                ).isoformat(),
                "end_datetime": datetime(
                    year=int(year_parsed.named["end_year"]),
                    month=12,
                    day=31,
                    hour=23,
                    minute=59,
                    second=59,
                    tzinfo=timezone.utc,
                ).isoformat(),
                "datetime": datetime(
                    year=int(
                        year_parsed.named["end_year"],
                    ),
                    month=1,
                    day=1,
                    tzinfo=timezone.utc,
                ),
            }
        elif year_parsed := parse(YEAR_FORMAT, parsed.named["year"]):
            if not isinstance(year_parsed, Result):
                return None

            collection_id = CollectionIDs.GLAD_GLCLU2020
            datetime_properties = {
                "datetime": datetime(
                    year=int(year_parsed.named["year"]),
                    month=1,
                    day=1,
                    tzinfo=timezone.utc,
                ),
            }
        else:
            raise ValueError(
                "The year parameter cannot be parsed into either the annual or change "
                f"formats: {parsed.named['year']}\n"
                "Make sure the year parameter matches either of these formats:\n"
                + ", ".join([YEAR_FORMAT, CHANGE_YEAR_FORMAT])
            )

        return {
            "id": "_".join(parsed.named.values()),
            "version": parsed.named["version"],
            "collection": collection_id,
            **datetime_properties,
        }

    def create_item(self, asset_href: str) -> Item:
        """Creates a STAC item from a raster asset."""
        href_parsed = self.parse_href(asset_href)
        if not href_parsed:
            raise ValueError(f"Unable to parse href: {asset_href}")

        id = href_parsed.pop("id")
        item_datetime = href_parsed.pop("datetime")
        collection = href_parsed.pop("collection")

        item: Item = rio_stac.create_stac_item(
            source=asset_href,
            id=id,
            collection=collection,
            input_datetime=item_datetime,
            properties=href_parsed,
            asset_name=ASSET_NAME,
            asset_roles=ASSET_ROLES,
            asset_media_type=_get_media_type(asset_href),
            extensions=[version_ext.SCHEMA_URI],
            with_raster=False,
            with_proj=True,
        )

        classification_extension = AssetClassificationExtension(item.assets[ASSET_NAME])
        classification_extension.classes = self.classifications

        return item


def validate_href_format(href_format: str) -> str:
    """Validate that the href_format string can be used as a parse format string
    and contains all required parameters.

    Args:
        href_format: String format for asset hrefs

    Returns:
        The validated href_format string

    Raises:
        ValueError: If the format string is invalid or missing required parameters
    """
    required_params = {"version", "year"}

    # Try to create a Parser object - this validates the format string syntax
    try:
        parser = Parser(href_format)
    except Exception as e:
        raise ValueError(f"Invalid href_format: {e}")

    found_params = set(parser.named_fields)

    missing = required_params - found_params
    if missing:
        raise ValueError(
            f"Format string missing required parameters: {', '.join(sorted(missing))}. "
            f"Required parameters are: {', '.join(sorted(required_params))}"
        )

    return href_format


@dataclass
class CollectionRegistry:
    """Registry of collection configurations."""

    href_format: HrefFormat = DEFAULT_HREF_FORMAT
    configs: Dict[CollectionIDs, CollectionDefinition] = field(init=False)

    def __post_init__(self) -> None:
        self.href_format = validate_href_format(self.href_format)

        self.configs = {
            CollectionIDs.GLAD_GLCLU2020: CollectionDefinition(
                id=CollectionIDs.GLAD_GLCLU2020,
                title="GLAD: Annual maps of land cover and land use",
                description=COLLECTION_DESCRIPTION,
                asset_title="Annual maps of land cover and land use",
                asset_description=(
                    "Continuous measures of bare ground and tree height inside and "
                    "outside of wetlands, seasonal water percent, and binary labels of "
                    "built-up, permanent snow/ice, and cropland."
                ),
                classifications_file=DATA_DIR / "annual_classes.csv",
                href_format=self.href_format,
            ),
            CollectionIDs.GLAD_GLCLU2020_CHANGE: CollectionDefinition(
                id=CollectionIDs.GLAD_GLCLU2020_CHANGE,
                title="GLAD: Net change of land cover and land use between 2000 and "
                "2020",
                description=COLLECTION_DESCRIPTION,
                asset_title="Net change of land cover and land use between 2000 and "
                "2020",
                asset_description=(
                    "Land cover and land use states of 2020 with transitions "
                    "relative to 2000 labeled."
                ),
                classifications_file=DATA_DIR / "change_classes.csv",
                href_format=self.href_format,
            ),
        }

    def get_config(self, collection_id: CollectionIDs) -> CollectionDefinition:
        if collection_id not in self.configs:
            raise ValueError(f"Unknown collection ID: {collection_id}")

        return self.configs[collection_id]
