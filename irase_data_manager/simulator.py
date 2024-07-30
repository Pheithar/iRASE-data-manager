"""
Download and upload data from the i-RASE project on the DTU Data platform 
"""

import irase_data_manager
import os
import requests
import logging
import numpy as np
import time
import h5py


def download_data(
    article_id: int,
    auth_token: str = "",
    save_path: os.PathLike = os.getcwd(),
    verbose: bool = False,
) -> None:
    """
    Download the weighting potentials and electric field data from the i-RASE project on the DTU Data platform.

    .. note::
        To get the article id, visit DTU Data and look at the URL to get the article id. For example, if the URL is `https://data.dtu.dk/account/projects/211264/articles/12345678`, the article id is `12345678`.

    .. warning::
        The URL differs depending on whether the data is public or private. If the token is not provided, the data is assumed to be public.

    The expected file to download is the first file in the list of files in the response, which should be an `.hdf5` file containing the data.

    Args:
        article_id (int): The ID of the article to download the file from.
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

    url = f"https://api.figshare.com/v2/account/articles/{article_id}/files"
    if auth_token == "":
        logger.debug("No authentication token provided. Assuming public data.")
        url = f"https://api.figshare.com/v2/articles/{article_id}/files"

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


def upload_data(
    auth_token: str,
    data_path: os.PathLike,
    size: tuple[float, float, float] = (40, 5, 40),
    step: tuple[float, float, float] = (0.1, 0.1, 0.1),
    verbose: bool = False,
) -> None:
    """
    Upload the weighting potentials and electric field data to the i-RASE project on the DTU Data platform.

    The data_path should be a directory containing the `.txt` files to upload. The expected txt files are `AW_3D.txt`, `CW_3D.txt`, `DW_3D.txt`, and `E_3D.txt`.

    Args:
        auth_token (str): The authentication token for accessing the platform.
        data_path (os.PathLike): The path to the directory containing the data files.
        verbose (bool, optional): Whether to display verbose output. Defaults to False.

    Raises:
        RuntimeError: If the upload of the file fails.
    """
    logger = irase_data_manager.create_logger("upload_weighting_potentials")

    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    num_x_steps = int(size[0] / step[0]) + 1  # +1 to include the last point
    num_y_steps = int(size[1] / step[1]) + 1
    num_z_steps = int(size[2] / step[2]) + 1

    logger.debug("Uploading data to the i-RASE project on the DTU Data platform")

    aw_metadata = _extract_comsol_metadata(os.path.join(data_path, "AW_3D.txt"))

    num_anodes = aw_metadata["expressions"]

    logger.debug(
        f"Extracted metadata from {os.path.join(data_path, 'AW_3D.txt')}: {aw_metadata}"
    )

    logger.debug(f"Reading data from {os.path.join(data_path, 'AW_3D.txt')}")

    # Load the aw data
    anode_weights_data = np.loadtxt(
        os.path.join(data_path, "AW_3D.txt"), comments="%", dtype=np.float64
    )
    _check_input_values(size, step, num_anodes, anode_weights_data)

    anode_weights_data = _reshape_data(
        anode_weights_data, num_x_steps, num_y_steps, num_z_steps, num_anodes
    )

    logger.debug(f"Anode weights data shape: {anode_weights_data.shape}")

    cw_metadata = _extract_comsol_metadata(os.path.join(data_path, "CW_3D.txt"))

    num_cathodes = cw_metadata["expressions"]

    logger.debug(
        f"Extracted metadata from {os.path.join(data_path, 'CW_3D.txt')}: {cw_metadata}"
    )

    cathode_weights_data = np.loadtxt(
        os.path.join(data_path, "CW_3D.txt"), comments="%", dtype=np.float64
    )

    _check_input_values(size, step, num_cathodes, cathode_weights_data)

    cathode_weights_data = _reshape_data(
        cathode_weights_data, num_x_steps, num_y_steps, num_z_steps, num_cathodes
    )

    logger.debug(f"Cathode weights data shape: {cathode_weights_data.shape}")

    dw_metadata = _extract_comsol_metadata(os.path.join(data_path, "DW_3D.txt"))

    num_drifts = dw_metadata["expressions"]

    logger.debug(
        f"Extracted metadata from {os.path.join(data_path, 'DW_3D.txt')}: {dw_metadata}"
    )

    drift_weights_data = np.loadtxt(
        os.path.join(data_path, "DW_3D.txt"), comments="%", dtype=np.float64
    )

    _check_input_values(size, step, num_drifts, drift_weights_data)

    drift_weights_data = _reshape_data(
        drift_weights_data, num_x_steps, num_y_steps, num_z_steps, num_drifts
    )

    logger.debug(f"Drift weights data shape: {drift_weights_data.shape}")

    e_metadata = _extract_comsol_metadata(os.path.join(data_path, "E_3D.txt"))

    logger.debug(
        f"Extracted metadata from {os.path.join(data_path, 'E_3D.txt')}: {e_metadata}"
    )

    num_electric_fields = e_metadata["expressions"]

    electric_fields_data = np.loadtxt(
        os.path.join(data_path, "E_3D.txt"), comments="%", dtype=np.float64
    )

    _check_input_values(size, step, num_electric_fields, electric_fields_data)

    electric_fields_data = _reshape_data(
        electric_fields_data, num_x_steps, num_y_steps, num_z_steps, num_electric_fields
    )

    file_path = os.path.join(data_path, "weightingPotential_electricFields.hdf5")

    with h5py.File(file_path, "w") as f:
        # Create a group for the weighting potentials
        aw_group = f.create_group("anode_weights")
        for key, value in aw_metadata.items():
            aw_group.attrs[key] = value

        aw_group.create_dataset("data", data=anode_weights_data)

        cw_group = f.create_group("cathode_weights")
        for key, value in cw_metadata.items():
            cw_group.attrs[key] = value

        cw_group.create_dataset("data", data=cathode_weights_data)

        dw_group = f.create_group("drift_weights")
        for key, value in dw_metadata.items():
            dw_group.attrs[key] = value

        dw_group.create_dataset("data", data=drift_weights_data)

        e_group = f.create_group("electric_fields")
        for key, value in e_metadata.items():
            e_group.attrs[key] = value

        e_group.create_dataset("data", data=electric_fields_data)

        # Add the metadata for size and steps
        f.attrs["x_size"] = size[0]
        f.attrs["y_size"] = size[1]
        f.attrs["z_size"] = size[2]

        f.attrs["x_step"] = step[0]
        f.attrs["y_step"] = step[1]
        f.attrs["z_step"] = step[2]

    logger.debug(
        f"File saved to {file_path}. Uploading data to the i-RASE project on the DTU Data platform"
    )

    headers = {"Authorization": f"token {auth_token}"}
    article_metadata = {
        "title": "Weighting potentials and electric field data for the i-RASE ATDM",
        "description": "Weighting potentials and electric field data for the i-RASE 3DCZT Advanced Theoretical Data Model (ATDM), in a single .hdf5 file containing the data and metadata.",
        "keywords": ["weighting potentials", "electric field", "i-RASE 3DCZT"],
        "categories": [30103, 30091, 30262],
        "authors": [{"id": 6659987}],
        "license": 1,
        "defined_type": "dataset",
    }

    create_article_url = "https://api.figshare.com/v2/account/projects/211264/articles"
    response = requests.post(create_article_url, headers=headers, json=article_metadata)

    if response.status_code != 201:
        data = response.json()
        raise RuntimeError(f"Failed to create article: {data}")

    article_id = response.json()["entity_id"]

    logger.debug(f"Created article with ID {article_id}")

    irase_data_manager.upload_file(file_path, auth_token, article_id, verbose=verbose)

    logger.debug(f"Data uploaded successfully with article ID {article_id}")


def _reshape_data(
    data: np.ndarray,
    num_x_steps: int,
    num_y_steps: int,
    num_z_steps: int,
    num_values: int,
) -> np.ndarray:
    """Reshape the data to the correct shape. The data is expected to be in the format:

    x, y, z, value1, value2, ..., valueN
    0, 0, 0, value1, value2, ..., valueN
    1, 0, 0, value1, value2, ..., valueN
    2, 0, 0, value1, value2, ..., valueN
    ...

    The data will be reshaped to be an array of shape (num_values, num_x_steps, num_y_steps, num_z_steps) where the data can be accessed by:

    id, x, y, z

    For that, the fortran order is used to match the order of the data, and then the data is transposed to match the order of the data.

    It has to end up being a 4d array with the shape (num_values, num_x_steps, num_y_steps, num_z_steps).

    Args:
        data (np.ndarray): The data to reshape.
        num_x_steps (int): The number of x steps.
        num_y_steps (int): The number of y steps.
        num_z_steps (int): The number of z steps.
        num_values (int): The number of values. Can be anodes, cathodes, drifts, etc.

    Returns:
        np.ndarray: The reshaped data.
    """
    reshaped_data = (
        data[:, 3:]
        .reshape(num_x_steps, num_y_steps, num_z_steps, num_values, order="F")
        .transpose(3, 0, 1, 2)
    )

    _check_reshaped_data(reshaped_data, data, num_x_steps, num_y_steps)

    return reshaped_data


def _check_input_values(
    size: tuple[float, float, float],
    step: tuple[float, float, float],
    num_values: int,
    data: np.ndarray,
) -> None:
    """Check that the input values are correct. That means, the size, step, and number of values are correct.

    These checks that the number of steps and the number of values are the same, and that the number of columns is equal to the number of values.

    Also, check that the step is correct and that the size is correct.

    These are not exhaustive checks, but they are a good start.

    Args:
        size (tuple[float, float, float]): The size of the data.
        step (tuple[float, float, float]): The step of the data.
        num_values (int): The number of values. Can be anodes, cathodes, drifts, etc.
        data (np.ndarray): The data to check.

    Raises:
        AssertionError: If the input values are not correct.
    """
    num_x_steps = int(size[0] / step[0]) + 1  # +1 to include the last point
    num_y_steps = int(size[1] / step[1]) + 1
    num_z_steps = int(size[2] / step[2]) + 1

    assert num_x_steps * num_y_steps * num_z_steps == len(
        data
    ), f"The number of steps and the number of values are not the same. Expected {num_x_steps * num_y_steps * num_z_steps}, got {len(data)}"

    assert (
        data.shape[1] == num_values + 3
    ), f"The number of columns is not equal to the data. Expected {data.shape[1]}, got {num_values + 3}"

    # Check that the step is correct
    assert np.allclose(
        np.diff(data[:, 0]).max(), step[0]
    ), f"Expected x step {np.diff(data[:, 0]).max()}, got {step[0]}"
    assert np.allclose(
        np.diff(data[:, 1]).max(), step[1]
    ), f"Expected y step {np.diff(data[:, 1]).max()}, got {step[1]}"
    assert np.allclose(
        np.diff(data[:, 2]).max(), step[2]
    ), f"Expected z step {np.diff(data[:, 2]).max()}, got {step[2]}"

    # Check that the size is correct
    assert np.allclose(
        data[:, 0].max(), size[0]
    ), f"Expected x size {data[:, 0].max()}, got {size[0]}"
    assert np.allclose(
        data[:, 1].max(), size[1]
    ), f"Expected y size {data[:, 1].max()}, got {size[1]}"
    assert np.allclose(
        data[:, 2].max(), size[2]
    ), f"Expected z size {data[:, 2].max()}, got {size[2]}"


def _check_reshaped_data(
    reshaped_data: np.ndarray,
    original_data: np.ndarray,
    num_x_steps: int,
    num_y_steps: int,
) -> None:
    """Check that the reshaped data is correct. That means, it can be accessed by: `id`, `x`, `y`, `z`.

    These are not exhaustive checks, but they are a good start.

    Args:
        reshaped_data (np.ndarray): The reshaped data.
        original_data (np.ndarray): The original data.
        num_x_steps (int): The number of x steps.
        num_y_steps (int): The number of y steps.

    Raises:
        AssertionError: If the reshaped data is not correct.
    """
    assert np.all(
        reshaped_data[:, 0, 0, 0] == original_data[0, 3:]
    ), f"Expected {original_data[0, 3]}, got {reshaped_data[:, 0, 0, 0]}"
    assert np.all(
        reshaped_data[:, 1, 0, 0] == original_data[1, 3:]
    ), f"Expected {original_data[1, 3]}, got {reshaped_data[:, 1, 0, 0]}"
    assert np.all(
        reshaped_data[:, 0, 1, 0] == original_data[num_x_steps, 3:]
    ), f"Expected {original_data[num_x_steps, 3]}, got {reshaped_data[:, 0, 1, 0]}"
    assert np.all(
        reshaped_data[:, 0, 0, 1] == original_data[num_x_steps * num_y_steps, 3:]
    ), f"Expected {original_data[num_x_steps * num_y_steps, 3]}, got {reshaped_data[:, 0, 0, 1]}"


def _extract_comsol_metadata(file_path: os.PathLike) -> dict[str, any]:
    """Extract the relevant metadata from the top of the COMSOL file.
    The COMSOL file have ,metadata starting with `%`.

    The metadata we are interested in is COMSOL Version, Date, Nodes, Expressions, Dimensions and Length units.

    Args:
        file_path (os.PathLike): The path to the COMSOL file.

    Returns:
        dict[str, any]: The extracted metadata.
    """

    metadata = {}

    with open(file_path, "r") as f:
        # Read only until the line does not start with `%`
        stop_reading = False
        while not stop_reading:
            line = f.readline().strip()
            if line.startswith("%"):
                # The loine structure is `% key: value`
                key, *value = line[1:].split(":")
                # Some lines, like time, have a colon in the value, so we join the value
                value = ":".join(value).strip()
                # Strip also the key to remove any extra spaces
                key = key.strip()
                if key == "Version":
                    metadata["COMSOL_version"] = value
                elif key == "Date":
                    # Save the date in ISO format
                    parsed_time = time.strptime(value, "%b %d %Y, %H:%M")
                    iso_date = time.strftime("%Y-%m-%dT%H:%M:%SZ", parsed_time)
                    metadata["date"] = iso_date
                elif key == "Nodes":
                    metadata["nodes"] = int(value)
                elif key == "Expressions":
                    metadata["expressions"] = int(value)
                elif key == "Dimensions":
                    metadata["dimensions"] = int(value)
                elif key == "Length unit":
                    metadata["length_unit"] = value

            else:
                stop_reading = True

        return metadata
