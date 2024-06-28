"""
Download and upload data from the i-RASE project on the DTU Data platform 
"""

import os
import requests
from tqdm import tqdm


def download_data(auth_token: str, save_path: str = os.getcwd()) -> None:
    """
    Download data from the i-RASE project on the DTU Data platform.


    The url is different if the data is public or private. If it is private, the url is:

    `https://api.figshare.com/v2/account/articles/26117449`

    If it is public, the url is:

    `https://api.figshare.com/v2/articles/26117449`

    Right now, the project is private, so we will use the first url, but we will make it public in the future, so we will have to change the url path.
    Additionally, if the URL is public, no authentication is required, but if it is private, we need to provide an authentication token in the headers.

    Again, for now, as it is private, we request the authentication token from the headers, but in the future, we will remove it.

    The expected file to download is the first file in the list of files in the response, which should be an `.hdf5` file containing the data.

    Args:
        auth_token (str): The authentication token for the private data.
        save_path (str, optional): The path to save the downloaded file. Defaults to os.getcwd().
    """

    authorization = f"token {auth_token}"
    url = "https://api.figshare.com/v2/account/articles/26117449"
    headers = {"Authorization": authorization}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        data = response.json()
        raise RuntimeError(f"Failed to fetch data from {url}: {data}")

    file = response.json()["files"][0]
    download_url = file["download_url"]

    print(f"Downloading data from {download_url}")

    response = requests.get(download_url, headers=headers, stream=True)

    if response.status_code != 200:
        data = response.json()
        raise RuntimeError(f"Failed to download data from {download_url}: {data}")

    file_name = file["name"]
    file_size = int(response.headers.get("Content-Length", 0))

    with open(os.path.join(save_path, file_name), "wb") as f:
        # display tqdm in GB
        for chunk in tqdm(
            response.iter_content(chunk_size=1024 * 1024),
            total=file_size / 1024 / 1024,
            unit="MB",
            desc=f"Downloading {file_name}",
        ):
            f.write(chunk)


def upload_data() -> None:
    """TODO: Docstring for upload_data.

    Raises:
        NotImplementedError: This function is not implemented yet.
    """
    raise NotImplementedError("This function is not implemented yet.")
