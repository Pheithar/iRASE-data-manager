"""
Download and upload data from the i-RASE project on the DTU Data platform 
"""

import irase_data_manager
import os
import requests
from tqdm import tqdm
import logging


def download_data(
    auth_token: str = "", save_path: os.PathLike = os.getcwd(), verbose: bool = False
) -> None:
    """
    Download data from the i-RASE project on the DTU Data platform.

    .. warning::
        The URL differs depending on whether the data is public or private. If the token is not provided, the data is assumed to be public.

    The expected file to download is the first file in the list of files in the response, which should be an `.hdf5` file containing the data.

    Args:
        auth_token (str): The authentication token for accessing private data. Defaults to an empty string.
        save_path (os.PathLike, optional): The path to save the downloaded file. Defaults to the current working directory.
        verbose (bool, optional): Whether to display verbose output. Defaults to False.

    Raises:
        RuntimeError: If the request to the API fails.
        RuntimeError: If the download of the file fails.
    """

    logger = irase_data_manager.create_logger("download_weighting_potentials")
    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    url = "https://api.figshare.com/v2/account/articles/26117449/files"
    if auth_token == "":
        logger.debug("No authentication token provided. Assuming public data.")
        url = "https://api.figshare.com/v2/articles/26117449/files"

    headers = {"Authorization": f"token {auth_token}"}
    response = requests.get(url, headers=headers)

    logger.debug("Downloading data from the i-RASE project on the DTU Data platform")

    if response.status_code != 200:
        data = response.json()
        raise RuntimeError(f"Failed to fetch data from {url}: {data}")

    files = response.json()

    logger.debug(f"Found {len(files)} files in the response")

    for file in files:
        irase_data_manager.download_file(
            file, save_path, auth_token=auth_token, verbose=verbose
        )


def upload_data() -> None:
    """TODO: Docstring for upload_data.

    Raises:
        NotImplementedError: This function is not implemented yet.
    """
    raise NotImplementedError("This function is not implemented yet.")
