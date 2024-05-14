from openeo_driver.jobregistry import JOB_STATUS
import time
import xarray as xr
from typing import Any, Dict, List, Tuple
import pytest
from rasterio.crs import CRS
import requests
from openeo_driver.users.auth import HttpAuthHandler
from tensorlakehouse_openeo_driver.constants import (
    DEFAULT_BANDS_DIMENSION,
    TEST_DATA_ROOT,
    DEFAULT_TIME_DIMENSION,
    DEFAULT_Y_DIMENSION,
    DEFAULT_X_DIMENSION,
)
from tensorlakehouse_openeo_driver.tests.unit.unit_test_util import (
    open_array,
    open_raster,
    # plot_array,
    save_openeo_response,
    validate_raster_datacube,
)
from tensorlakehouse_openeo_driver.constants import OPENEO_URL
from tensorlakehouse_openeo_driver.constants import logger

TEST_USER = "Mr.Test"
TEST_USER_BEARER_TOKEN = "basic//" + HttpAuthHandler.build_basic_access_token(
    user_id=TEST_USER
)
TEST_USER_AUTH_HEADER = {"Authorization": "Bearer " + TEST_USER_BEARER_TOKEN}
HIGH_RES_SENTINEL_2 = "High res  imagery (ESA Sentinel 2)"

COLLECTION_ID_ERA5_ZARR = "Global weather (ERA5) (ZARR)"
BAND_TOTAL_PRECIPITATION = "49459"

COLLECTION_ID_PRISM = "Daily US weather (PRISM)"
BAND_DAILY_MEAN_TEMP = "Daily mean temperature"

COLLECTION_ID_SENTINEL_2_LAND_USE = "sentinel2-10m-lulc"
BAND_SENTINEL_2_LAND_USE_LULC = "lulc"


def submit_post_request_load_data(payload: Dict) -> xr.DataArray:
    collection_id = payload["process"]["process_graph"]["loadcollection1"]["arguments"][
        "id"
    ]

    # make sure that the collection exists
    resp = requests.get(
        f"{OPENEO_URL}collections/{collection_id}",
        headers=TEST_USER_AUTH_HEADER,
        verify=False,
    )
    resp.raise_for_status()
    logger.debug(f"POST /result {payload}")
    resp = requests.post(
        f"{OPENEO_URL}result",
        headers=TEST_USER_AUTH_HEADER,
        json=payload,
        verify=False,
        timeout=180,
    )
    logger.debug(f"response POST /result {resp.status_code}")

    resp.raise_for_status()
    # save file locally
    file_format, path = save_openeo_response(
        data=resp.content,
        content_type=resp.headers["Content-type"],
        prefix="test_openeo_",
    )
    # open file
    da = open_raster(path=path, file_format=file_format)
    return da


POST_RESULT_PAYLOADS = [
    (
        {
            "process": {
                "process_graph": {
                    "loadcollection1": {
                        "process_id": "load_collection",
                        "arguments": {
                            "bands": ["B04"],
                            "id": "ibm-eis-ga-1-esa-sentinel-2-l2a",
                            "spatial_extent": {
                                "west": -122.99,
                                "south": 38.74,
                                "east": -122.887424,
                                "north": 38.84992,
                            },
                            "temporal_extent": [
                                "2023-03-15T18:51:39Z",
                                "2023-03-15T18:51:39Z",
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
            DEFAULT_Y_DIMENSION: 859,
            DEFAULT_X_DIMENSION: 802,
            "time": 1,
            DEFAULT_BANDS_DIMENSION: 1,
        },
        4326,
        [],
    ),
    (
        {
            "process": {
                "process_graph": {
                    "loadcollection1": {
                        "process_id": "load_collection",
                        "arguments": {
                            "bands": ["B02", "Fmask"],
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
        {DEFAULT_Y_DIMENSION: 1284, DEFAULT_X_DIMENSION: 1182},
        32617,
        [],
    ),
    (
        {
            "process": {
                "process_graph": {
                    "loadcollection1": {
                        "process_id": "load_collection",
                        "arguments": {
                            "bands": [BAND_SENTINEL_2_LAND_USE_LULC],
                            "id": COLLECTION_ID_SENTINEL_2_LAND_USE,
                            "spatial_extent": {
                                "west": -73.57,
                                "south": 45.50,
                                "east": -73.54,
                                "north": 45.53,
                            },
                            "temporal_extent": [
                                "2022-01-01T00:00:00Z",
                                "2022-01-01T00:00:00Z",
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
        {DEFAULT_Y_DIMENSION: 470, DEFAULT_X_DIMENSION: 470},
        4326,
        [],
    ),
    (
        # Test multi-asset STAC entries #233
        {
            "process": {
                "process_graph": {
                    "loadcollection1": {
                        "process_id": "load_collection",
                        "arguments": {
                            "bands": ["B01", "B02"],
                            "id": "HLSS_dev",
                            "spatial_extent": {
                                "west": -106.52490395,
                                "south": 31.1300375,
                                "east": -106.42490395,
                                "north": 31.2300375,
                            },
                            "temporal_extent": ["2020-06-01", "2020-06-03"],
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
            DEFAULT_Y_DIMENSION: 375,
            DEFAULT_X_DIMENSION: 324,
            DEFAULT_BANDS_DIMENSION: 2,
            "time": 1,
        },
        32613,
        [],
    ),
    (
        # aggregate return period returns days with only nan values
        # https://github.ibm.com/GeoDN-Discovery/main/issues/231
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
                                "east": -121.45,
                                "north": 44.05,
                            },
                            "temporal_extent": [
                                "2022-01-02T00:00:00Z",
                                "2022-01-07T23:59:59Z",
                            ],
                        },
                    },
                    "aggregatetemporalperiod1": {
                        "process_id": "aggregate_temporal_period",
                        "arguments": {
                            "data": {"from_node": "loadcollection1"},
                            "period": "day",
                            "reducer": {
                                "process_graph": {
                                    "min1": {
                                        "process_id": "min",
                                        "arguments": {
                                            "data": {"from_parameter": "data"}
                                        },
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
                            "format": "netCDF",
                            "options": {},
                        },
                        "result": True,
                    },
                }
            }
        },
        {
            DEFAULT_Y_DIMENSION: 258,
            DEFAULT_X_DIMENSION: 238,
            DEFAULT_BANDS_DIMENSION: 1,
            "time": 2,
        },
        32617,
        [],
    ),
    (
        # timeout error https://github.ibm.com/GeoDN-Discovery/main/issues/216
        {
            "process": {
                "process_graph": {
                    "loadcollection1": {
                        "process_id": "load_collection",
                        "arguments": {
                            "bands": ["B02", "B03", "B04", "B05", "B06", "B07"],
                            "id": "HLSL30",
                            "spatial_extent": {
                                "west": 35.6948437,
                                "south": -0.9913317,
                                "east": 36.6805874,
                                "north": 0.0,
                            },
                            "temporal_extent": [
                                "2023-05-25T00:00:00Z",
                                "2023-05-30T23:59:59Z",
                            ],
                        },
                    },
                    "saveresult1": {
                        "process_id": "save_result",
                        "arguments": {
                            "data": {"from_node": "loadcollection1"},
                            "format": "GTiff",
                            "options": {},
                        },
                        "result": True,
                    },
                }
            }
        },
        {
            DEFAULT_Y_DIMENSION: 3661,
            DEFAULT_X_DIMENSION: 3665,
            DEFAULT_BANDS_DIMENSION: 6,
            DEFAULT_TIME_DIMENSION: 6,
        },
        32636,
        [],
    ),
    (
        #  Test multi-asset STAC entries #233
        {
            "process": {
                "process_graph": {
                    "loadcollection1": {
                        "process_id": "load_collection",
                        "arguments": {
                            "bands": ["B01", "B02"],
                            "id": "HLSS_dev",
                            "spatial_extent": {
                                "west": -106.52490395,
                                "south": 31.1300375,
                                "east": -106.42490395,
                                "north": 31.2300375,
                            },
                            "temporal_extent": ["2020-06-01", "2020-06-03"],
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
            DEFAULT_Y_DIMENSION: 375,
            DEFAULT_X_DIMENSION: 324,
            DEFAULT_BANDS_DIMENSION: 2,
            "time": 1,
        },
        32613,
        [],
    ),
    (
        #  Test multi-asset STAC entries #233
        {
            "process": {
                "process_graph": {
                    "loadcollection1": {
                        "process_id": "load_collection",
                        "arguments": {
                            "bands": ["Maximum temperature"],
                            "id": "Global weather (ERA5)",
                            "spatial_extent": {
                                "west": -91,
                                "south": 41,
                                "east": -90,
                                "north": 42,
                            },
                            "temporal_extent": ["2023-06-20", "2023-06-21"],
                        },
                    },
                    "renamelabels1": {
                        "process_id": "rename_labels",
                        "arguments": {
                            "data": {"from_node": "loadcollection1"},
                            "dimension": "bands",
                            "source": ["Maximum temperature"],
                            "target": ["max_temp"],
                        },
                    },
                    "saveresult1": {
                        "process_id": "save_result",
                        "arguments": {
                            "data": {"from_node": "renamelabels1"},
                            "format": "netCDF",
                            "options": {},
                        },
                        "result": True,
                    },
                }
            }
        },
        {
            DEFAULT_Y_DIMENSION: 32,
            DEFAULT_X_DIMENSION: 32,
            DEFAULT_BANDS_DIMENSION: 1,
            "time": 25,
        },
        4326,
        ["max_temp"],
    ),
    (
        #  axis limits #183
        {
            "process": {
                "process_graph": {
                    "loadcollection1": {
                        "process_id": "load_collection",
                        "arguments": {
                            "bands": ["B02", "B03", "B04", "B8A", "B11", "B12"],
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
                                    "multiply1": {
                                        "process_id": "multiply",
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
                    "mergecubes1": {
                        "process_id": "merge_cubes",
                        "arguments": {
                            "cube1": {"from_node": "apply1"},
                            "cube2": {"from_node": "loadcollection2"},
                        },
                    },
                    "aggregatetemporalperiod1": {
                        "process_id": "aggregate_temporal_period",
                        "arguments": {
                            "data": {"from_node": "mergecubes1"},
                            "period": "day",
                            "reducer": {
                                "process_graph": {
                                    "mean1": {
                                        "process_id": "mean",
                                        "arguments": {
                                            "data": {"from_parameter": "data"}
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
                            "data": {"from_node": "aggregatetemporalperiod1"},
                            "method": "near",
                            "projection": 4326,
                            "resolution": 0,
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
        {"t": 2, "bands": 7, "y": 1255, "x": 1706},
        4326,
        [],
    ),
]


@pytest.mark.parametrize(
    "payload, expected_dims, expected_epsg, expected_variables",
    POST_RESULT_PAYLOADS,
)
def test_post_result(
    payload, expected_dims, expected_epsg: int, expected_variables: List[str]
):
    collection_id = payload["process"]["process_graph"]["loadcollection1"]["arguments"][
        "id"
    ]
    if len(expected_variables) == 0:
        expected_variables = payload["process"]["process_graph"]["loadcollection1"][
            "arguments"
        ]["bands"]
    resp = requests.get(
        f"{OPENEO_URL}collections/{collection_id}",
        headers=TEST_USER_AUTH_HEADER,
        verify=False,
    )
    if resp.status_code == 200:
        logger.debug(f"POST /result {payload}")
        resp = requests.post(
            f"{OPENEO_URL}result",
            headers=TEST_USER_AUTH_HEADER,
            json=payload,
            verify=False,
        )
        logger.debug(f"response POST /result {resp.status_code}")

        resp.raise_for_status()
        file_format, path = save_openeo_response(
            data=resp.content,
            content_type=resp.headers["Content-type"],
            prefix="test_openeo_",
        )
        expected_crs = CRS.from_epsg(expected_epsg)
        da = open_array(
            file_format=file_format, path=path, band_names=expected_variables
        )
        validate_raster_datacube(
            cube=da,
            expected_dim_size=expected_dims,
            expected_attrs={},
            expected_crs=expected_crs,
        )
        # plot_array(arr=da, time_index={"t": 0}, band_index={"bands": 0})
        path.unlink()
    else:
        pytest.skip(f"Collection {collection_id} is not available")


INPUT_TEST_CREATE_JOBS: List[Tuple[Dict, Dict, Dict, int]] = [
    (
        {
            "process": {
                "process_graph": {
                    "loadcollection1": {
                        "process_id": "load_collection",
                        "arguments": {
                            "bands": ["Temperature"],
                            "id": "Global weather (ERA5)",
                            "spatial_extent": {
                                "west": -70,
                                "south": -10,
                                "east": -60,
                                "north": 0,
                            },
                            "temporal_extent": [
                                "2023-07-24T11:00:00Z",
                                "2023-07-24T11:00:00Z",
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
            },
            "title": "Foo job",
            "description": "Run the `foo` process!",
        },
        {"bands": 1, "x": 96, "y": 96},
        {},
        4326,
    ),
    (
        {
            "process": {
                "process_graph": {
                    "loadcollection1": {
                        "process_id": "load_collection",
                        "arguments": {
                            "bands": ["Temperature"],
                            "id": "Global weather (ERA5)",
                            "spatial_extent": {
                                "west": -70,
                                "south": -10,
                                "east": -60,
                                "north": 0,
                            },
                            "temporal_extent": [
                                "2023-07-24T11:00:00Z",
                                "2023-07-24T11:00:00Z",
                            ],
                        },
                    },
                    "saveresult1": {
                        "process_id": "save_result",
                        "arguments": {
                            "data": {"from_node": "loadcollection1"},
                            "format": "GTiff",
                            "options": {},
                        },
                        "result": True,
                    },
                }
            },
            "title": "Foo job",
            "description": "Run the `foo` process!",
        },
        {"band": 1, "x": 96, "y": 96},
        {},
        4326,
    ),
    (
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
        {DEFAULT_Y_DIMENSION: 1284, DEFAULT_X_DIMENSION: 1182, "bands": 1, "time": 2},
        {},
        32617,
    ),
]


@pytest.mark.parametrize(
    "payload, expected_dim_size, expected_attrs, expected_crs", INPUT_TEST_CREATE_JOBS
)
def test_create_jobs(
    payload: Dict, expected_dim_size: Dict, expected_attrs: Dict, expected_crs: int
):
    resp = requests.post(
        f"{OPENEO_URL}jobs",
        headers=TEST_USER_AUTH_HEADER,
        json=payload,
        verify=False,
    )
    resp.raise_for_status()
    job_id = resp.headers["OpenEO-Identifier"]
    time.sleep(2)
    print(f"Job_id={job_id}")
    resp = requests.get(
        f"{OPENEO_URL}jobs/{job_id}", headers=TEST_USER_AUTH_HEADER, verify=False
    )
    resp.raise_for_status()
    response = resp.json()
    status = response.get("status")
    while status not in [JOB_STATUS.ERROR, JOB_STATUS.FINISHED, JOB_STATUS.CANCELED]:
        time.sleep(2)
        resp = requests.get(
            f"{OPENEO_URL}jobs/{job_id}", headers=TEST_USER_AUTH_HEADER, verify=False
        )
        resp.raise_for_status()
        response = resp.json()
        status = response.get("status")

    url = f"{OPENEO_URL}jobs/{job_id}/results"
    resp = requests.get(url=url, headers=TEST_USER_AUTH_HEADER, verify=False)
    resp.raise_for_status()
    response = resp.json()
    assets = response["assets"]
    assert isinstance(assets, dict)
    assert len(assets) > 0
    for filename, metadata in assets.items():
        assert isinstance(metadata, dict)
        assert "href" in metadata.keys(), f"Error! missing href : {metadata} "
        href = metadata["href"]
        path = TEST_DATA_ROOT / filename
        response = requests.get(href, stream=True)
        with open(path, mode="wb") as f:
            for chunk in response.iter_content(chunk_size=10 * 1024):
                f.write(chunk)

            file_format = payload["process"]["process_graph"]["saveresult1"][
                "arguments"
            ]["format"]
            cube = open_raster(path=path, file_format=file_format)
            validate_raster_datacube(
                cube=cube,
                expected_dim_size=expected_dim_size,
                expected_attrs=expected_attrs,
                expected_crs=expected_crs,
            )


TEST_AGGREGATE_TEMPORAL_PERIOD_INPUT: List[Tuple[Dict, Dict, int, List]] = [
    (
        {
            "process": {
                "process_graph": {
                    "loadcollection1": {
                        "process_id": "load_collection",
                        "arguments": {
                            "bands": ["CEH rainfall for Great Britain"],
                            "id": "CEH gridded hourly rainfall for Great Britain",
                            "spatial_extent": {
                                "west": -3.7,
                                "south": 51.6,
                                "east": -3.5,
                                "north": 51.8,
                            },
                            "temporal_extent": [
                                "2007-01-01T11:00:00Z",
                                "2007-12-31T11:00:00Z",
                            ],
                        },
                    },
                    "aggregatetemporalperiod1": {
                        "process_id": "aggregate_temporal_period",
                        "arguments": {
                            "data": {"from_node": "loadcollection1"},
                            "period": "month",
                            "reducer": {
                                "process_graph": {
                                    "mean1": {
                                        "process_id": "mean",
                                        "arguments": {
                                            "data": {"from_parameter": "data"}
                                        },
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
                            "format": "netCDF",
                            "options": {},
                        },
                        "result": True,
                    },
                }
            }
        },
        {
            DEFAULT_Y_DIMENSION: 32,
            DEFAULT_X_DIMENSION: 64,
            "time": 12,
            DEFAULT_BANDS_DIMENSION: 1,
        },
        4326,
        [],
    ),
    # (
    #     {
    #         "process": {
    #             "process_graph": {
    #                 "loadcollection1": {
    #                     "process_id": "load_collection",
    #                     "arguments": {
    #                         "bands": ["B02"],
    #                         "id": "HLSS30",
    #                         "spatial_extent": {
    #                             "west": -117.0,
    #                             "south": 33.99,
    #                             "east": -116.99,
    #                             "north": 34.0,
    #                         },
    #                         "temporal_extent": [
    #                             "2020-09-01T00:00:00Z",
    #                             "2020-11-01T00:00:00Z",
    #                         ],
    #                     },
    #                 },
    #                 "aggregatetemporalperiod1": {
    #                     "process_id": "aggregate_temporal_period",
    #                     "arguments": {
    #                         "data": {"from_node": "loadcollection1"},
    #                         "period": "day",
    #                         "reducer": {
    #                             "process_graph": {
    #                                 "mean1": {
    #                                     "process_id": "mean",
    #                                     "arguments": {
    #                                         "data": {"from_parameter": "data"}
    #                                     },
    #                                     "result": True,
    #                                 }
    #                             }
    #                         },
    #                     },
    #                 },
    #                 "saveresult1": {
    #                     "process_id": "save_result",
    #                     "arguments": {
    #                         "data": {"from_node": "aggregatetemporalperiod1"},
    #                         "format": "netCDF",
    #                         "options": {},
    #                     },
    #                     "result": True,
    #                 },
    #             }
    #         }
    #     },
    #     {
    #         DEFAULT_Y_DIMENSION: 526,
    #         DEFAULT_X_DIMENSION: 487,
    #         "time": 12,
    #         DEFAULT_BANDS_DIMENSION: 1,
    #     },
    #     32617,
    #     ["B02"],
    # ),
    (
        {
            "process": {
                "process_graph": {
                    "loadcollection1": {
                        "process_id": "load_collection",
                        "arguments": {
                            "bands": ["Total precipitation"],
                            "id": "Global weather (ERA5)",
                            "spatial_extent": {
                                "west": -0.48,
                                "south": 53.709,
                                "east": -0.22,
                                "north": 53.812,
                            },
                            "temporal_extent": [
                                "2007-01-01T11:00:00Z",
                                "2007-12-31T11:00:00Z",
                            ],
                        },
                    },
                    "aggregatetemporalperiod1": {
                        "process_id": "aggregate_temporal_period",
                        "arguments": {
                            "data": {"from_node": "loadcollection1"},
                            "period": "day",
                            "reducer": {
                                "process_graph": {
                                    "mean1": {
                                        "process_id": "mean",
                                        "arguments": {
                                            "data": {"from_parameter": "data"}
                                        },
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
                            "format": "netCDF",
                            "options": {},
                        },
                        "result": True,
                    },
                }
            }
        },
        {
            DEFAULT_Y_DIMENSION: 32,
            DEFAULT_X_DIMENSION: 32,
            "time": 365,
            DEFAULT_BANDS_DIMENSION: 1,
        },
        4326,
        [],
    ),
]


@pytest.mark.parametrize(
    "payload, expected_dims, expected_epsg, expected_variables",
    TEST_AGGREGATE_TEMPORAL_PERIOD_INPUT,
)
def test_aggregate_temporal_period(
    payload: Dict[str, Any],
    expected_dims: Dict[str, int],
    expected_epsg: int,
    expected_variables: List[str],
):
    """test response of a request that includes aggregate_temporal_period process

    Args:
        payload (_type_): _description_
        expected_dims (_type_): _description_
        expected_epsg (int): _description_
        expected_variables (List[str]): _description_
    """

    if len(expected_variables) == 0:
        expected_variables = payload["process"]["process_graph"]["loadcollection1"][
            "arguments"
        ]["bands"]
    # make sure that the collection exists
    da = submit_post_request_load_data(payload=payload)

    expected_crs = CRS.from_epsg(expected_epsg)
    # open file
    # validate datacube dimensions
    validate_raster_datacube(
        cube=da,
        expected_dim_size=expected_dims,
        expected_attrs={},
        expected_crs=expected_crs,
    )
    # assumption: all inputs generate datacubes that have at least two timestamps
    temporal_dims = [
        t for t in expected_dims.keys() if t in ["time", "t", DEFAULT_TIME_DIMENSION]
    ]
    time_dim = temporal_dims[0]
    assert da[time_dim].size > 2
    for time_index in range(da[time_dim].size - 1):
        cur_cube = da.isel({time_dim: time_index})
        next_cube = da.isel({time_dim: time_index + 1})
        assert not bool(cur_cube.isnull().all())
        assert not bool(next_cube.isnull().all())
        max_cur_cube = float(cur_cube.max())
        max_next_cube = float(next_cube.max())
        if not (max_cur_cube == max_next_cube == 0):
            delta = next_cube - cur_cube
            max_v = float(delta.max())
            min_v = float(delta.min())
            assert not (max_v == min_v == 0), f"Error! max_v={max_v} min_v={min_v}"


TEST_AGGREGATE_SPATIAL: List[Tuple[Dict, Dict, int, List]] = [
    (
        {
            "process": {
                "process_graph": {
                    "loadcollection1": {
                        "process_id": "load_collection",
                        "arguments": {
                            "bands": ["Total precipitation"],
                            "id": "Global weather (ERA5)",
                            "spatial_extent": {
                                "west": -97,
                                "south": 28.5,
                                "east": -95,
                                "north": 30.5,
                            },
                            "temporal_extent": [
                                "2015-01-01T00:00:00Z",
                                "2015-02-03T00:00:00Z",
                            ],
                        },
                    },
                    "aggregatespatial1": {
                        "process_id": "aggregate_spatial",
                        "arguments": {
                            "data": {"from_node": "loadcollection1"},
                            "geometries": {
                                "type": "FeatureCollection",
                                "features": [
                                    {
                                        "type": "Feature",
                                        "properties": {},
                                        "geometry": {
                                            "coordinates": [
                                                [
                                                    [-97, 28.5],
                                                    [-97, 30.5],
                                                    [-95, 30.5],
                                                    [-95, 28.5],
                                                    [-97, 28.5],
                                                ]
                                            ],
                                            "type": "Polygon",
                                        },
                                    }
                                ],
                            },
                            "reducer": {
                                "process_graph": {
                                    "mean1": {
                                        "process_id": "mean",
                                        "arguments": {
                                            "data": {"from_parameter": "data"}
                                        },
                                        "result": True,
                                    }
                                }
                            },
                        },
                    },
                    "saveresult1": {
                        "process_id": "save_result",
                        "arguments": {
                            "data": {"from_node": "aggregatespatial1"},
                            "format": "netCDF",
                            "options": {},
                        },
                        "result": True,
                    },
                }
            }
        },
        {"time": 793, DEFAULT_BANDS_DIMENSION: 1},
        4326,
        [],
    ),
]


@pytest.mark.parametrize(
    "payload, expected_dims, expected_epsg, expected_variables",
    TEST_AGGREGATE_SPATIAL,
)
def test_aggregate_spatial(
    payload: Dict[str, Any],
    expected_dims: Dict[str, int],
    expected_epsg: int,
    expected_variables: List[str],
):
    data = submit_post_request_load_data(payload=payload)
    expected_crs = CRS.from_epsg(expected_epsg)
    validate_raster_datacube(
        cube=data,
        expected_dim_size=expected_dims,
        expected_attrs={},
        expected_crs=expected_crs,
    )
