"""
Auxiliary files fro upload and download documents
"""

import logging
import os
import requests
from tqdm import tqdm


def create_logger(logger_name: str):
    """Create a logger with the specified name. The format of the logger is as follows:

    .. code-block:: shell

        [%(asctime)s] - [%(name)s] - [%(levelname)s] - %(message)s

    Args:
        logger_name (str): The name of the logger.
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "[%(asctime)s] - [%(name)s] - [%(levelname)s] - %(message)s"
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def extract_article_metadata(metadata: dict[str, any]) -> dict[str, any]:
    """Extract the metadata of the article from the response of the Figshare API. If some metadata is not available and it is not mandatory, it uses defaults values.

    The article metadata should contain the following keys:

    - `title`: The title of the article.
    - `description`: The description of the article.
    - `authors`: The authors of the article, as a list of ids.

    The resulting metadata contains the following keys:

    - `title`: The title of the article.
    - `description`: The description of the article.
    - `keywords`: The keywords of the article. Defaults to ``["scan data"]``
    - `categories`: The categories of the article. Defaults to ``[30103, 30091, 30262]`` (corresponding to ``["High energy astrophysics and galactic cosmic rays", "Astronomical instrumentation", "Space instrumentation"]``)
    - `authors`: The authors of the article.
    - `license`: The license of the article. Defaults to ``1`` (corresponding to ``"CC BY 4.0"``)
    - `defined_type`: The defined type of the article. Defaults to ``"dataset"``

    .. warning::

        The original dictionary is modified in place. If you want to keep the original metadata, make a copy of it before calling this function.

    Args:
        metadata (dict[str, any]): The metadata of the article, as described above.

    Returns:
        dict[str, any]: The extracted metadata of the article.
    """
    defaults = {
        "keywords": ["scan data"],
        "categories": [30103, 30091, 30262],
        "license": 1,
        "defined_type": "dataset",
    }

    article_metadata = {
        "title": metadata.pop("title"),
        "description": metadata.pop("description"),
        "keywords": metadata.pop("keywords", defaults["keywords"]),
        "categories": metadata.pop("categories", defaults["categories"]),
        "authors": [{"id": author_id} for author_id in metadata.pop("authors")],
        "license": metadata.pop("license", defaults["license"]),
        "defined_type": metadata.pop("type", defaults["defined_type"]),
    }

    return article_metadata


def validate_experiment_metadata(metadata: dict[str, any]) -> None:
    """Validate that the experiment has the required metadata. The required metadata are:

    - `detector_id`: The ID of the detector used in the experiment.
    - `source_id`: The ID of the radioactive source used in the experiment.
    - `experiment_type`: The method the data was obtained (e.g., x-scan, z-scan, full-illumination...).
    - `sample_time`: The time the sample was exposed to the source.

    .. warning::

        This list of required metadata is not fixed. It will mutate as we change the requirements of the project.

    Args:
        metadata (dict[str, any]): The metadata of the experiment.

    Raises:
        ValueError: If any of the required metadata is missing.
    """
    required_metadata = ["detector_id", "source_id", "experiment_type", "sample_time"]

    print(metadata.get("type"))

    missing_metadata = [key for key in required_metadata if key not in metadata]

    if missing_metadata:
        raise ValueError(f"Missing metadata: {missing_metadata}")


def download_file(
    file_data: dict[str, any],
    save_path: os.PathLike,
    auth_token: str = "",
    verbose=False,
):
    """Download a file obtained from an API request.

    Args:
        file_data (dict[str, any]): File data. Expected to follow the format of the response from the Figshare API.
        save_path (os.PathLike): The path to save the downloaded file. Expected to be a directory.
        auth_token (str): The authentication token for accessing private data.
    """
    logger = create_logger(f"download_file_{file_data['name']}")

    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    logger.debug(f"Downloading data from {file_data['download_url']}")

    if not os.path.exists(save_path):
        logger.debug(f"{save_path} does not exist. Creating directory.")
        os.makedirs(save_path)

    if not os.path.isdir(save_path):
        raise ValueError(f"Invalid save path: {save_path}")

    url = file_data["download_url"]
    headers = {"Authorization": f"token {auth_token}"}
    response = requests.get(url, headers=headers, stream=True)

    if response.status_code != 200:
        data = response.json()
        raise RuntimeError(
            f"Failed to download data from {file_data['download_url']}: {data}"
        )

    file_name = file_data["name"]
    file_size = int(response.headers.get("Content-Length", 0))

    logger.debug(
        f"Downloading {file_name} ({file_size/1024/1024/1024:.2f} GB) to {save_path}"
    )

    with open(os.path.join(save_path, file_name), "wb") as f:
        for chunk in tqdm(
            response.iter_content(chunk_size=1024 * 1024),
            total=file_size / 1024 / 1024,
            unit="MB",
            desc=f"Downloading {file_name}",
            disable=not verbose,
        ):
            f.write(chunk)

    logger.debug(f"Finished downloading {file_name}")


def upload_file(
    file_path: os.PathLike,
    auth_token: str,
    article_id: int,
    verbose: bool = False,
):
    """Upload a file to an article on the Figshare platform. It is not a direct upload, as the file must be registered first before uploading the content. The process is as follows:

    1. Register the file with the Figshare API.
    2. Upload the content of the file to the registered file, divided into chunks.
    3. Update the file with the Figshare API to mark it as complete.

    Args:
        file_path (os.PathLike): The path to the file to upload.
        auth_token (str): The authentication token for accessing the platform.
        article_id (int): The ID of the article to upload the file to.
        verbose (bool, optional): Whether to display verbose output. Defaults to False.

    Raises:
        RuntimeError: If the upload of the file fails.
    """

    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)

    logger = create_logger(f"upload_file_{file_name}")

    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    logger.debug(f"Uploading {file_name} to article {article_id}")

    headers = {"Authorization": f"token {auth_token}"}

    upload_file_url = f"https://api.figshare.com/v2/account/articles/{article_id}/files"
    response = requests.post(
        upload_file_url,
        headers=headers,
        json={"name": file_name, "size": file_size},
    )

    if response.status_code != 201:
        data = response.json()
        raise RuntimeError(
            f"Failed to upload file {file_name} to article {article_id}: {data}"
        )

    file_location_url = response.json()["location"]
    response = requests.get(file_location_url, headers=headers)

    logger.debug(f"File registered successfully with Figshare API")

    if response.status_code != 200:
        data = response.json()
        raise RuntimeError(
            f"Failed to get upload location for file {file_name}: {data}"
        )

    upload_url = response.json()["upload_url"]
    file_id = response.json()["id"]

    response = requests.get(upload_url, headers=headers)

    if response.status_code != 200:
        data = response.json()
        raise RuntimeError(
            f"Failed to get upload location for file {file_name}: {data}"
        )

    logger.debug(f"Uploading content of {file_name} to {upload_url}")

    with open(file_path, "rb") as f:
        parts = response.json()["parts"]
        for part in tqdm(parts, desc=f"Uploading {file_name}", disable=not verbose):
            url = f"{upload_url}/{part['partNo']}"
            f.seek(part["startOffset"])
            data = f.read(part["endOffset"] - part["startOffset"] + 1)
            response = requests.put(url, headers=headers, data=data)

            if response.status_code != 200:
                data = response.json()
                raise RuntimeError(
                    f"Failed to upload part {part['partNo']} of {file_name}: {data}"
                )

    logger.debug(f"Content of {file_name} uploaded successfully")

    close_file_url = (
        f"https://api.figshare.com/v2/account/articles/{article_id}/files/{file_id}"
    )
    response = requests.post(close_file_url, headers=headers)

    if response.status_code != 202:
        data = response.json()
        raise RuntimeError(
            f"Failed to close file {file_name} on article {article_id}: {data}"
        )

    logger.debug(f"File {file_name} uploaded successfully to article {article_id}")
