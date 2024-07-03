"""
Download and upload data from the experimental setup of the i-RASE project
"""

import os
import h5py
import numpy as np
import requests
import irase_data_manager
import logging
from tqdm import tqdm


def download_data(
    article_id: int,
    auth_token: str = "",
    save_path: os.PathLike = os.getcwd(),
    verbose: bool = False,
) -> None:
    """Download data from the experimental setup of the i-RASE project. For now, we require the article id to download the data.

    .. note::

        If you are not sure which article id to use, you can look for the article in the DTU Data platform and use the corresponding id, which can be seen from the url.

    .. warning::

        If the data is private, an authentication token is required to access the data.

    Args:
        article_id (int): The ID of the article to download the data from.
        auth_token (str): The authentication token for accessing the platform. Defaults to an empty string.
        save_path (os.PathLike, optional): The path to save the downloaded file. Defaults to the current working directory.
        verbose (bool, optional): Whether to display verbose output. Defaults to False.

    Raises:
        RuntimeError: If the request to the API fails.
        RuntimeError: If the download of the file fails.
    """

    logger = irase_data_manager.create_logger(f"download_data_{article_id}")

    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    article_url = f"https://api.figshare.com/v2/account/articles/{article_id}/files"  # Private data URL
    if auth_token == "":
        # We assume that if no auth_token is provided, the data is public
        logger.debug("No authentication token provided. Assuming public data.")
        article_url = f"https://api.figshare.com/v2/articles/{article_id}/files"  # Public data URL

    headers = {"Authorization": f"token {auth_token}"}
    response = requests.get(article_url, headers=headers)

    if response.status_code != 200:
        data = response.json()
        raise RuntimeError(f"Failed to fetch data from {article_url}: {data}")

    files = response.json()
    logger.debug(f"Found {len(files)} files in the response")

    for file in files:
        irase_data_manager.download_file(
            file, save_path, auth_token=auth_token, verbose=verbose
        )


def upload_data(
    data: list[np.ndarray],
    auth_token: str,
    metadata: dict[str, any],
    save_path: str = os.getcwd(),
    verbose: bool = False,
) -> os.PathLike:
    """Upload data from the experimental setup of the i-RASE project to the DTU Data platform.

    It requires an authentication token to access the platform. The data is uploaded as an HDF5 file containing the experimental data.

    The metadata is expected to be a dictionary with, at least, the following keys:

    1. `title`: The title of the article.
    2. `description`: A description of the article.
    3. `authors`: A list of authors.
    4. `detector_id`: The ID of the detector used in the experiment.
    5. `source_id`: The ID of the radioactive source used in the experiment.
    6. `experiment_type`: The method the data was obtained (e.g., x-scan, z-scan, full-illumination...).
    7. `sample_time`: The time the sample was exposed to the source.

    Additionally, if the following keys are present in the metadata, they will be used in the article creation. If not, default values will be used

    1. `categories`: A list of categories for the article.
    2. `keywords`: A list of keywords for the article.
    3. `license`: The license of the article.
    4. `type`: The type of the article.

    .. note::

        The authors should be given as a list of ids. If you are not sure which ids to use, look the author name in the DTU Data platform and use the corresponding id, which can be seen from the url. Other user searching tool is the apidocs at https://docs.figshare.com/#private_authors_search, but an oauth token is needed.

        Some ids that can be useful from the project authors are:
            - Selina Howalt Owe: 6659987
            - Irfan Kuvvetli: 6213518
            - Alejandro Valverde Mahou: 18722368

    If any other metadata is added, it will be stored in the ``.hdf5`` file as attributes.


    Args:
        data (list[np.ndarray]): A list of numpy arrays containing the experimental data, ordered as they were obtained.
        auth_token (str): The authentication token for accessing the platform.
        metadata (dict[str, any]): The metadata of the article, as described above.
        save_path (str, optional): The path to save the uploaded file. Defaults to the current working directory.
        verbose (bool, optional): Whether to display verbose output. Defaults to False.

    Returns:
        os.PathLike: The path to the file uploaded locally saved.

    Raises:
        RuntimeError: If the request to the API fails.
        RuntimeError: If the upload of the file fails.
        RuntimeError: If the creation of the article fails.
    """

    logger = irase_data_manager.create_logger("upload_experimental_data")

    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    print(metadata)

    article_metadata = irase_data_manager.extract_article_metadata(metadata)
    irase_data_manager.validate_experiment_metadata(metadata)

    print(metadata)
    print(article_metadata)

    logger.debug("Transforming data into a single HDF5 file")

    file_name = "test_data.hdf5"  # NOTE: Update when naming convention is decided
    file_path = os.path.join(save_path, file_name)

    with h5py.File(file_path, "w") as f:
        for i, array in tqdm(
            enumerate(data),
            desc=f"Uploading data to {file_name}",
            disable=not verbose,
            total=len(data),
        ):
            f.create_dataset(
                f"array_{i}", data=array
            )  # NOTE: Update when naming convention is decided

        for key, value in metadata.items():
            f.attrs[key] = value

    logger.debug("Data transformed successfully")

    headers = {"Authorization": f"token {auth_token}"}

    create_article_url = "https://api.figshare.com/v2/account/projects/211264/articles"
    response = requests.post(create_article_url, headers=headers, json=article_metadata)

    if response.status_code != 201:
        data = response.json()
        raise RuntimeError(f"Failed to create article: {data}")

    article_id = response.json()["entity_id"]

    logger.debug(f"Article created successfully with id {article_id}")

    irase_data_manager.upload_file(file_path, auth_token, article_id, verbose=verbose)

    return file_path
