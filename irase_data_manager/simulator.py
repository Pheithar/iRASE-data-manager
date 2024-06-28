"""
Download and upload data from the i-RASE project on the DTU Data platform 
"""

import os
import requests
from tqdm import tqdm


def download_data(auth_token: str, save_path: str = os.getcwd()) -> None:
    """
    Download data from the i-RASE project on the DTU Data platform.

    The URL differs depending on whether the data is public or private:

    - **Private data URL**: `https://api.figshare.com/v2/account/articles/26117449`
    - **Public data URL**: `https://api.figshare.com/v2/articles/26117449`

    Currently, the project is private, so the private URL is used. However, the project will be made public in the future, necessitating a change in the URL path. Additionally, public URLs do not require authentication, whereas private URLs require an authentication token in the headers.

    At present, the authentication token is required as the project is private. This requirement will be removed once the project becomes public.

    The expected file to download is the first file in the list of files in the response, which should be an `.hdf5` file containing the data.

    Args:
        auth_token (str): The authentication token for accessing private data.
        save_path (str, optional): The path to save the downloaded file. Defaults to the current working directory.

    Raises:
        RuntimeError: If the request to the API fails.
        RuntimeError: If the download of the file fails.
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
