"""Download and upload calibration files for the i-RASE 3DCZT software"""

import os
import logging
import requests
from tqdm import tqdm
import numpy as np
import irase_data_manager
import h5py


def calibration_download(
    article_id: int,
    auth_token: str = "",
    save_path: os.PathLike = os.getcwd(),
    verbose: bool = False,
) -> None:
    """Download calibration data from the i-RASE 3DCZT software.

    Args:
        article_id (int): The ID of the article to download the data from.
        auth_token (str, optional): The authentication token for accessing the platform. Defaults to "".
        save_path (os.PathLike, optional): The path to save the downloaded file. Defaults to the current working directory.
        verbose (bool, optional): Whether to display verbose output. Defaults to False.
    """
    logger = irase_data_manager.create_logger("download_calibration")

    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    article_url = f"https://api.figshare.com/v2/account/articles/{article_id}/files"
    if auth_token == "":
        logger.debug("No authentication token provided. Assuming public data.")
        article_url = f"https://api.figshare.com/v2/articles/{article_id}/files"

    headers = {"Authorization": f"token {auth_token}"}
    response = requests.get(article_url, headers=headers)

    logger.debug("Downloading calibration data from the i-RASE 3DCZT software")

    if response.status_code != 200:
        data = response.json()
        raise RuntimeError(f"Failed to fetch data from {article_url}: {data}")

    files = response.json()

    logger.debug(f"Found {len(files)} files in the response")

    for file in files:
        irase_data_manager.download_file(
            file, save_path, auth_token=auth_token, verbose=verbose
        )


def calibration_upload(
    calibration_data: list[tuple[np.ndarray]],
    auth_token: str = "",
    save_path: os.PathLike = os.getcwd(),
    verbose: bool = False,
):
    """Upload calibration data to the calibration.hdf5 file.

    The expected input format is a list of tuples of numpy arrays. Each tuple represent a different calibration file. The first member of the tuple is "k1" and the second member is "k2".


    .. note::
        The list of data is expected to be ordered.


    .. warning::

        The metadata is hardcoded in the function. If you want to change the metadata, you need to change the function. If we update the files regularly, we should come back to the function and update the metadata, or allow to be changed via the function arguments.

    Args:
        calibration_data (list[tuple[np.ndarray, np.ndarray]]): List of calibration data.
        auth_token (str, optional): The authentication token for accessing the platform. Defaults to "".
        save_path (os.PathLike, optional): The path to save the calibration file. Defaults to the current working directory.
        verbose (bool, optional): Whether to display verbose output. Defaults to False.

    Raises:
        RuntimeError: If the upload of the calibration data fails.

    """

    logger = irase_data_manager.create_logger("upload_calibration")

    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    # Check that the path exists and create it if it doesn't. Verify that ir is a directory
    if not os.path.isdir(save_path):
        os.makedirs(save_path)

    file_path = os.path.join(save_path, "calibration.hdf5")

    with h5py.File(file_path, "w") as f:
        for i, array in tqdm(
            enumerate(calibration_data),
            desc="Uploading calibration data to calibration.hdf5",
            disable=not verbose,
            total=len(calibration_data),
        ):
            group_name = f"D{i + 1}"
            f.create_group(group_name)
            f[group_name].create_dataset("k1", data=array[0])
            f[group_name].create_dataset("k2", data=array[1])

    logger.debug("Calibration data uploaded successfully")

    headers = {"Authorization": f"token {auth_token}"}
    article_metadata = {
        "title": "Calibration data for the i-RASE 3DCZT software",
        "description": "Calibration data for the i-RASE 3DCZT software.",
        "keywords": ["calibration"],
        "categories": [30103, 30091, 30262],
        "authors": [{"id": 6659987}],
        "license": 1,
        "defined_type": "dataset",
    }

    # Create a new article for the calibration data
    create_article_url = "https://api.figshare.com/v2/account/projects/211264/articles"
    response = requests.post(create_article_url, headers=headers, json=article_metadata)

    if response.status_code != 201:
        data = response.json()
        raise RuntimeError(f"Failed to create article: {data}")

    article_id = response.json()["entity_id"]

    # Upload the calibration file
    irase_data_manager.upload_file(file_path, auth_token, article_id, verbose=verbose)

    logger.debug(f"Calibration data uploaded successfully with article ID {article_id}")
