from rasterio.crs import CRS
from pathlib import Path
from typing import Dict, List
import pytest
from tensorlakehouse_openeo_driver.local_app import create_app
from openeo_driver.testing import ApiTester
from openeo_driver.users.auth import HttpAuthHandler
from openeo_driver.views import OpenEoApiApp, _normalize_collection_metadata
from tensorlakehouse_openeo_driver.constants import (
    DEFAULT_BANDS_DIMENSION,
    STAC_URL,
    TEST_DATA_ROOT,
    DEFAULT_TIME_DIMENSION,
    DEFAULT_X_DIMENSION,
    DEFAULT_Y_DIMENSION,
)
from tensorlakehouse_openeo_driver.geodn_backend import (
    GeoDNCollectionCatalog,
)
from openeo.capabilities import ComparableVersion
from tensorlakehouse_openeo_driver.stac import STAC
from tensorlakehouse_openeo_driver.tests.unit.unit_test_util import (
    save_openeo_response,
    validate_downloaded_file,
    validate_stac_object_against_schema,
)
from tensorlakehouse_openeo_driver.tests.constants import ITEM_SCHEMA_PATH


TEST_USER = "Mr.Test"
TEST_USER_BEARER_TOKEN = "basic//" + HttpAuthHandler.build_basic_access_token(user_id=TEST_USER)
TEST_USER_AUTH_HEADER = {"Authorization": "Bearer " + TEST_USER_BEARER_TOKEN}

COLLECTION_ID_HISTORICAL_CROP_PLANTING_MAP = "Historical crop planting map (USA)"
BAND_CROP_30M = "111"

COLLECTION_ID_ERA5_ZARR = "Global weather (ERA5) (ZARR)"
BAND_49459 = "49459"

COLLECTION_ID_ERA5 = "Global weather (ERA5)"

BAND_TOTAL_PRECIPITATION = "Total precipitation"

COLLECTION_ID_CROPSCAPE = "Historical crop planting map (USA)"
BAND_CROPSCAPE = "111"

COLLECTION_ID_TWC_SEASONAL_WEATHER_FORECAST = "TWC Seasonal Weather Forecast"
BAND_TWC_MIN_TEMP = "Minimum temperature"

COLLECTION_ID_SENTINEL_2_LAND_USE = "sentinel2-10m-lulc"
BAND_SENTINEL_2_LAND_USE_LULC = "lulc"

HIGH_RES_SENTINEL_2 = "High res  imagery (ESA Sentinel 2)"
COLLECTION_ID = "Daily US weather (PRISM)"
BAND_DAILY_MEAN_TEMP = "Daily mean temperature"
COLLECTION_ID_ERA5_ZARR = "Global weather (ERA5) (ZARR)"
BAND_TOTAL_PRECIPITATION = "49459"


@pytest.fixture(scope="module")
def flask_app() -> OpenEoApiApp:
    app = create_app("dev")
    app.config.from_mapping({"TESTING": True})
    return app


@pytest.fixture
def geodn_client(flask_app: OpenEoApiApp):
    return flask_app.test_client()


@pytest.fixture
def api110(geodn_client) -> ApiTester:
    return ApiTester(api_version="1.1.0", client=geodn_client, data_root=TEST_DATA_ROOT)


def collections(catalog: GeoDNCollectionCatalog, api_version: ComparableVersion) -> Dict[str, List]:
    """this is adapted from views.py module in order to mimic the way the response is built

    Args:
        catalog (GeoDNCollectionCatalog): _description_
        api_version (ComparableVersion): _description_

    Returns:
        _type_: _description_
    """
    metadata = [
        _normalize_collection_metadata(metadata=m, api_version=api_version, full=False)
        for m in catalog.get_all_metadata()
    ]
    return {"collections": metadata, "links": []}


def collection_by_id(
    catalog: GeoDNCollectionCatalog, api_version: ComparableVersion, collection_id: str
):
    metadata = catalog.get_collection_metadata(collection_id=collection_id)
    metadata = _normalize_collection_metadata(metadata=metadata, api_version=api_version, full=True)
    return metadata


def collection_items(
    catalog: GeoDNCollectionCatalog, api_version: ComparableVersion, collection_id: str
) -> Dict:
    """this method mimics the implementation of views.py::collection_items

    Args:
        catalog (GeoDNCollectionCatalog): _description_
        api_version (ComparableVersion): _description_
        collection_id (str): _description_

    Returns:
        _type_: _description_
    """

    response = catalog.get_collection_items(collection_id=collection_id, parameters=dict())
    assert response is not None
    assert isinstance(response, dict)
    return response


@pytest.mark.parametrize(
    "collection_id, expected_bands",
    [
        (
            "Global weather (ERA5)",
            ["Total precipitation"],
        ),
        ("Historical crop planting map (USA)", ["111"]),
        (
            "HLSS30",
            ["B02", "B03", "B04", "B8A", "B11", "B12", "Fmask"],
        ),
        (
            "hls-agb-preprocessed",
            ["B01"],
        ),
        (
            "ibm-eis-ga-1-esa-sentinel-2-l2a",
            ["B04"],
        ),
        (
            "sentinel2-10m-lulc",
            ["lulc"],
        ),
        (
            "HSI - Historical crop planting map (USA)",
            [
                "top",
                "freq",
                "count",
                "first",
                "unique",
                "count_1",
                "count_2",
                "count_3",
                "count_4",
                "count_5",
                "count_6",
                "count_10",
                "count_12",
                "count_21",
                "count_22",
                "count_23",
                "count_24",
                "count_26",
                "count_27",
                "count_28",
                "count_29",
                "count_36",
                "count_37",
                "count_41",
                "count_42",
                "count_45",
                "count_47",
                "count_48",
                "count_49",
                "count_50",
                "count_53",
                "count_57",
                "count_58",
                "count_59",
                "count_60",
                "count_61",
                "count_67",
                "count_69",
                "count_72",
                "count_74",
                "count_92",
                "count_111",
                "count_121",
                "count_122",
                "count_123",
                "count_124",
                "count_131",
                "count_141",
                "count_142",
                "count_143",
                "count_152",
                "count_176",
                "count_190",
                "count_195",
                "count_205",
                "count_211",
                "count_212",
                "count_222",
                "count_225",
                "count_226",
                "count_228",
                "count_236",
                "count_238",
                "count_242",
                "count_243",
            ],
        ),
    ],
)
def test_get_collections_by_id(collection_id, expected_bands):
    """this method

    Args:
        collection_id (_type_): _description_
    """
    stac = STAC(STAC_URL)
    if stac.is_collection_available(collection_id=collection_id):
        cat = GeoDNCollectionCatalog()
        collection = collection_by_id(
            catalog=cat,
            api_version=ComparableVersion("1.1.0"),
            collection_id=collection_id,
        )
        cube_dimensions = collection["cube:dimensions"]

        if expected_bands is not None:
            available_bands = cube_dimensions["bands"]["values"]
            for exp_band in expected_bands:
                assert (
                    exp_band in available_bands
                ), f"Error! expected band {exp_band} is not in {available_bands}"
    else:
        pytest.skip(f"Warning! {collection_id} is not available in STAC {STAC_URL}")


@pytest.mark.parametrize(
    "collection_id",
    [
        "Historical crop planting map (USA)",
        "sentinel2-10m-lulc",
        "ibm-eis-ga-1-esa-sentinel-2-l2a",
    ],
)
def test_get_collections_items(collection_id):
    cat = GeoDNCollectionCatalog()
    stac = STAC(STAC_URL)
    if stac.is_collection_available(collection_id=collection_id):
        items = collection_items(
            catalog=cat,
            api_version=ComparableVersion("1.1.0"),
            collection_id=collection_id,
        )
        for item in items.get("features"):
            validate_stac_object_against_schema(stac_object=item, schema_path=ITEM_SCHEMA_PATH)
    else:
        pytest.skip(f"Warning! {collection_id} is not available in STAC {STAC_URL}")


def test_get_collections():
    cat = GeoDNCollectionCatalog()
    collection_metadata = collections(catalog=cat, api_version=ComparableVersion("1.1.0"))
    for collection in collection_metadata["collections"]:
        basic_keys = [
            "stac_version",
            "stac_extensions",
            "id",
            "title",
            "description",
            "keywords",
            "version",
            "deprecated",
            "license",
            "providers",
            "extent",
            "links",
        ]
        assert all(k in basic_keys for k in collection.keys())


POST_RESULT_PAYLOADS = [
    (
        # processes: load_collection, save_result  - data: zarr
        "api110",
        {
            "process": {
                "process_graph": {
                    "loadcollection1": {
                        "process_id": "load_collection",
                        "arguments": {
                            "bands": [BAND_CROP_30M],
                            "id": COLLECTION_ID_HISTORICAL_CROP_PLANTING_MAP,
                            "spatial_extent": {
                                "west": -90.0,
                                "south": 40.0,
                                "east": -89.0,
                                "north": 41.0,
                            },
                            "temporal_extent": [
                                "2021-01-01T00:00:00Z",
                                "2021-01-01T00:00:00Z",
                            ],
                        },
                    },
                    "saveresult1": {
                        "process_id": "save_result",
                        "arguments": {
                            "data": {"from_node": "loadcollection1"},
                            "format": "netCDF",
                            "options": {},
                        },
                        "result": True,
                    },
                }
            }
        },
        {"lat": 3907, "lon": 3907, "time": 1, DEFAULT_BANDS_DIMENSION: 1},
        [BAND_CROP_30M],
        4326,
    ),
    (
        "api110",
        {
            "process": {
                "process_graph": {
                    "loadcollection1": {
                        "process_id": "load_collection",
                        "arguments": {
                            "bands": ["B02"],
                            "id": "HLSS30",
                            "spatial_extent": {
                                "west": -121.5,
                                "south": 44.0,
                                "east": -121.25,
                                "north": 44.25,
                            },
                            "temporal_extent": [
                                "2022-01-02T00:00:00Z",
                                "2022-01-02T23:59:59Z",
                            ],
                        },
                    },
                    "reducedimension1": {
                        "process_id": "reduce_dimension",
                        "arguments": {
                            "data": {"from_node": "loadcollection1"},
                            "dimension": "time",
                            "reducer": {
                                "process_graph": {
                                    "min1": {
                                        "process_id": "min",
                                        "arguments": {"data": {"from_parameter": "data"}},
                                        "result": True,
                                    }
                                }
                            },
                        },
                    },
                    "saveresult1": {
                        "process_id": "save_result",
                        "arguments": {
                            "data": {"from_node": "reducedimension1"},
                            "format": "netCDF",
                            "options": {},
                        },
                        "result": True,
                    },
                }
            }
        },
        {
            DEFAULT_Y_DIMENSION: 1284,
            DEFAULT_X_DIMENSION: 1182,
            DEFAULT_BANDS_DIMENSION: 1,
        },
        ["B02"],
        32617,
    ),
    (
        "api110",
        {
            "process": {
                "process_graph": {
                    "loadcollection1": {
                        "process_id": "load_collection",
                        "arguments": {
                            "bands": ["B02", "B03"],
                            "id": "HLSS30",
                            "spatial_extent": {
                                "west": -121.5,
                                "south": 44.0,
                                "east": -121.25,
                                "north": 44.25,
                            },
                            "temporal_extent": [
                                "2022-01-02T00:00:00Z",
                                "2022-01-02T23:59:59Z",
                            ],
                        },
                    },
                    "reducedimension1": {
                        "process_id": "reduce_dimension",
                        "arguments": {
                            "data": {"from_node": "loadcollection1"},
                            "dimension": "time",
                            "reducer": {
                                "process_graph": {
                                    "min1": {
                                        "process_id": "min",
                                        "arguments": {"data": {"from_parameter": "data"}},
                                        "result": True,
                                    }
                                }
                            },
                        },
                    },
                    "saveresult1": {
                        "process_id": "save_result",
                        "arguments": {
                            "data": {"from_node": "reducedimension1"},
                            "format": "netCDF",
                            "options": {},
                        },
                        "result": True,
                    },
                }
            }
        },
        {
            DEFAULT_Y_DIMENSION: 1284,
            DEFAULT_X_DIMENSION: 1182,
            DEFAULT_BANDS_DIMENSION: 2,
        },
        ["B02", "B03"],
        32617,
    ),
    (
        "api110",
        {
            "process": {
                "process_graph": {
                    "loadcollection1": {
                        "process_id": "load_collection",
                        "arguments": {
                            "bands": ["B02", "B03"],
                            "id": "HLSS30",
                            "spatial_extent": {
                                "west": -121.5,
                                "south": 44.0,
                                "east": -121.25,
                                "north": 44.25,
                            },
                            "temporal_extent": [
                                "2022-01-02T00:00:00Z",
                                "2022-01-07T23:59:59Z",
                            ],
                        },
                    },
                    "apply1": {
                        "process_id": "apply",
                        "arguments": {
                            "data": {"from_node": "loadcollection1"},
                            "process": {
                                "process_graph": {
                                    "divide1": {
                                        "process_id": "divide",
                                        "arguments": {
                                            "x": {"from_parameter": "x"},
                                            "y": 10000,
                                        },
                                        "result": True,
                                    }
                                }
                            },
                        },
                    },
                    "resamplespatial1": {
                        "process_id": "resample_spatial",
                        "arguments": {
                            "align": "upper-left",
                            "data": {"from_node": "apply1"},
                            "method": "near",
                            "projection": 4326,
                            "resolution": 0.01,
                        },
                    },
                    "saveresult1": {
                        "process_id": "save_result",
                        "arguments": {
                            "data": {"from_node": "resamplespatial1"},
                            "format": "Gtiff",
                            "options": {},
                        },
                        "result": True,
                    },
                }
            }
        },
        {
            DEFAULT_Y_DIMENSION: 41,
            DEFAULT_X_DIMENSION: 56,
            DEFAULT_BANDS_DIMENSION: 2,
            DEFAULT_TIME_DIMENSION: 4,
        },
        ["B02", "B03"],
        4326,
    ),
    (
        # goal: test aggregate_temporal_period, merge_cubes
        "api110",
        {
            "process": {
                "process_graph": {
                    "loadcollection1": {
                        "process_id": "load_collection",
                        "arguments": {
                            "bands": ["B02", "B03"],
                            "id": "HLSS30",
                            "spatial_extent": {
                                "west": -121.4,
                                "south": 44.15,
                                "east": -121.3,
                                "north": 44.25,
                            },
                            "temporal_extent": [
                                "2022-01-02T00:00:00Z",
                                "2022-01-07T23:59:59Z",
                            ],
                        },
                    },
                    "apply1": {
                        "process_id": "apply",
                        "arguments": {
                            "data": {"from_node": "loadcollection1"},
                            "process": {
                                "process_graph": {
                                    "divide1": {
                                        "process_id": "divide",
                                        "arguments": {
                                            "x": {"from_parameter": "x"},
                                            "y": 10000,
                                        },
                                        "result": True,
                                    }
                                }
                            },
                        },
                    },
                    "loadcollection2": {
                        "process_id": "load_collection",
                        "arguments": {
                            "bands": ["Fmask"],
                            "id": "HLSS30",
                            "spatial_extent": {
                                "west": -121.4,
                                "south": 44.15,
                                "east": -121.3,
                                "north": 44.25,
                            },
                            "temporal_extent": [
                                "2022-01-02T00:00:00Z",
                                "2022-01-07T23:59:59Z",
                            ],
                        },
                    },
                    "mergecubes1": {
                        "process_id": "merge_cubes",
                        "arguments": {
                            "cube1": {"from_node": "apply1"},
                            "cube2": {"from_node": "loadcollection2"},
                        },
                    },
                    "resamplespatial1": {
                        "process_id": "resample_spatial",
                        "arguments": {
                            "align": "upper-left",
                            "data": {"from_node": "mergecubes1"},
                            "method": "near",
                            "projection": 4326,
                            "resolution": 0,
                        },
                    },
                    "aggregatetemporalperiod1": {
                        "process_id": "aggregate_temporal_period",
                        "arguments": {
                            "data": {"from_node": "resamplespatial1"},
                            "period": "day",
                            "reducer": {
                                "process_graph": {
                                    "min1": {
                                        "process_id": "min",
                                        "arguments": {"data": {"from_parameter": "data"}},
                                        "result": True,
                                    }
                                }
                            },
                        },
                    },
                    "saveresult1": {
                        "process_id": "save_result",
                        "arguments": {
                            "data": {"from_node": "aggregatetemporalperiod1"},
                            "format": "Gtiff",
                            "options": {},
                        },
                        "result": True,
                    },
                }
            }
        },
        {
            DEFAULT_Y_DIMENSION: 502,
            DEFAULT_X_DIMENSION: 683,
            DEFAULT_BANDS_DIMENSION: 3,
            DEFAULT_TIME_DIMENSION: 2,
        },
        ["B02", "B03", "Fmask"],
        4326,
    ),
    (
        # processes: load_collection -> load_collection_from_hbase
        "api110",
        {
            "process": {
                "process_graph": {
                    "loadcollection1": {
                        "process_id": "load_collection",
                        "arguments": {
                            "bands": ["Total precipitation"],
                            "id": "Global weather (ERA5)",
                            "spatial_extent": {
                                "west": -70,
                                "south": -10,
                                "east": -60,
                                "north": 0,
                            },
                            "temporal_extent": [
                                "2023-07-24T11:00:00Z",
                                "2023-08-03T11:00:00Z",
                            ],
                        },
                    },
                    "reducedimension1": {
                        "process_id": "reduce_dimension",
                        "arguments": {
                            "data": {"from_node": "loadcollection1"},
                            "dimension": "time",
                            "reducer": {
                                "process_graph": {
                                    "max1": {
                                        "process_id": "max",
                                        "arguments": {"data": {"from_parameter": "data"}},
                                        "result": True,
                                    }
                                }
                            },
                        },
                    },
                    "saveresult1": {
                        "process_id": "save_result",
                        "arguments": {
                            "data": {"from_node": "reducedimension1"},
                            "format": "netCDF",
                            "options": {},
                        },
                        "result": True,
                    },
                }
            }
        },
        {DEFAULT_Y_DIMENSION: 96, DEFAULT_X_DIMENSION: 96, DEFAULT_BANDS_DIMENSION: 1},
        ["Total precipitation"],
        4326,
    ),
    (
        "api110",
        {
            "process": {
                "process_graph": {
                    "loadcollection1": {
                        "process_id": "load_collection",
                        "arguments": {
                            "bands": ["B02"],
                            "id": "HLSS30",
                            "spatial_extent": {
                                "west": -121.5,
                                "south": 44.0,
                                "east": -121.25,
                                "north": 44.25,
                            },
                            "temporal_extent": [
                                "2022-01-02T00:00:00Z",
                                "2022-01-02T23:59:59Z",
                            ],
                        },
                    },
                    "saveresult1": {
                        "process_id": "save_result",
                        "arguments": {
                            "data": {"from_node": "loadcollection1"},
                            "format": "netCDF",
                            "options": {},
                        },
                        "result": True,
                    },
                }
            }
        },
        {
            DEFAULT_Y_DIMENSION: 1284,
            DEFAULT_X_DIMENSION: 1182,
            DEFAULT_BANDS_DIMENSION: 1,
        },
        ["B02"],
        32617,
    ),
]


POST_RESULT_PAYLOADS_ISSUE_324_MAX_TIME = [
    (
        # Issue 324 datacube.max_time() fails on era5 as dim 'time' not found in cube dims(t,x,y)
        "api110",
        {
            "process": {
                "process_graph": {
                    "loadcollection1": {
                        "process_id": "load_collection",
                        "arguments": {
                            "bands": ["Total precipitation"],
                            "id": "Global weather (ERA5)",
                            "spatial_extent": {
                                "west": -70,
                                "south": -10,
                                "east": -60,
                                "north": 0,
                            },
                            "temporal_extent": [
                                "2015-01-01T00:00:00Z",
                                "2015-02-03T00:00:00Z",
                            ],
                        },
                    },
                    "reducedimension1": {
                        "process_id": "reduce_dimension",
                        "arguments": {
                            "data": {"from_node": "loadcollection1"},
                            "dimension": "time",
                            "reducer": {
                                "process_graph": {
                                    "max1": {
                                        "process_id": "max",
                                        "arguments": {"data": {"from_parameter": "data"}},
                                        "result": True,
                                    }
                                }
                            },
                        },
                    },
                    "saveresult1": {
                        "process_id": "save_result",
                        "arguments": {
                            "data": {"from_node": "reducedimension1"},
                            "format": "netCDF",
                            "options": {},
                        },
                        "result": True,
                    },
                }
            }
        },
        {DEFAULT_Y_DIMENSION: 96, DEFAULT_X_DIMENSION: 96, DEFAULT_BANDS_DIMENSION: 1},
        ["Total precipitation"],
        4326,
    ),
]


@pytest.mark.parametrize(
    # "api110, payload, expected_dims, expected_data_variables, expected_epsg",
    # POST_RESULT_PAYLOADS_ISSUE_324_MAX_TIME,
    "api110, payload, expected_dims, expected_data_variables, expected_epsg",
    POST_RESULT_PAYLOADS,
    indirect=["api110"],
)
class TestSynchronousPostResult:
    AUTH_HEADER = TEST_USER_AUTH_HEADER

    def test_post_result(
        self, api110, payload, expected_dims, expected_data_variables, expected_epsg
    ):
        expected_crs = CRS.from_epsg(expected_epsg)
        print(f"api110 type = {type(api110)}")
        collection_id = payload["process"]["process_graph"]["loadcollection1"]["arguments"]["id"]
        assert isinstance(collection_id, str)

        print(f"GET /collections/{collection_id}")

        resp = api110.get(
            f"/collections/{collection_id}",
            headers=self.AUTH_HEADER,
        )

        if resp.status_code != 200:
            print(f"skipping test status={resp.status_code}")
            pytest.skip(f"Collection {collection_id} is not available")
        else:
            resp = api110.post(
                "/result",
                headers=self.AUTH_HEADER,
                json=payload,
            )
            assert resp.status_code in [
                200,
                201,
            ], f"Error! {resp.status_code} {resp.text}"
            file_format, path = save_openeo_response(
                data=resp.data,
                content_type=resp.headers["Content-type"],
                prefix="test_openeo_",
            )
            validate_downloaded_file(
                path=path,
                expected_dimension_size=expected_dims,
                band_names=expected_data_variables,
                file_format=file_format,
                expected_crs=expected_crs,
            )
            # arr = open_array(
            #     file_format=file_format,
            #     path=path,
            #     data_variables=expected_data_variables,
            # )
            # plot_array(arr=arr, time_index={"time": 0}, band_index={BANDS: 0})
            # delete file
            file_path = Path(path)
            if file_path.exists():
                file_path.unlink()
