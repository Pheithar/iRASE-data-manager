"""
Download and upload data from the i-RASE project on the DTU Data platform 
"""

import irase_data_manager
import os
import requests
from tqdm import tqdm
import logging
import numpy as np


def download_data(
    auth_token: str = "", save_path: os.PathLike = os.getcwd(), verbose: bool = False
) -> None:
    """
    Download the weighting potentials and electric field data from the i-RASE project on the DTU Data platform.

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


def upload_data(
    auth_token: str,
    data_path: os.PathLike,
    size: tuple[float, float, float] = (40, 5, 40),
    step: tuple[float, float, float] = (0.1, 0.1, 0.1),
    num_cathodes: int = 20,
    num_anodes: int = 20,
    num_drifts: int = 25,
    num_electric_fields: int = 3,
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
    electric_fields_data = np.loadtxt(
        os.path.join(data_path, "E_3D.txt"), comments="%", dtype=np.float64
    )

    _check_input_values(size, step, num_electric_fields, electric_fields_data)

    num_x_steps = int(size[0] / step[0]) + 1  # +1 to include the last point
    num_y_steps = int(size[1] / step[1]) + 1
    num_z_steps = int(size[2] / step[2]) + 1

    # Reshape by skipping the first 3 rows, which mean the x, y, z values. These values are already known by input to the function.
    # Fortran order to match the order of the data -> x, y, z, id
    # Transpose to match the order of the data -> id, x, y, z
    electric_fields_data_reshaped = _reshape_data(
        electric_fields_data, num_x_steps, num_y_steps, num_z_steps, num_electric_fields
    )

    # assert that the data is accessed correctly in x, y, z order
    _check_reshaped_data(
        electric_fields_data_reshaped, electric_fields_data, num_x_steps, num_y_steps
    )


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
    return (
        data[:, 3:]
        .reshape(num_x_steps, num_y_steps, num_z_steps, num_values, order="F")
        .transpose(3, 0, 1, 2)
    )


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


from scipy.interpolate import RegularGridInterpolator as rgi


def interpol(xdim, ydim, zdim, matrix, coord):
    data_interpol = rgi(
        (
            np.linspace(0, zdim - 1, zdim),
            np.linspace(0, ydim - 1, ydim),
            np.linspace(0, xdim - 1, xdim),
        ),
        matrix,
    )
    return data_interpol(np.array(coord).T)


def comsolDataInterpolations(e3d2, coord):
    temp_vec = np.zeros(3)
    temp_vec = np.zeros(3)
    for k in range(0, 3):
        temp_vec[k] = interpol(401, 51, 401, e3d2[k, :, :, :], coord)
    # Ex_el, Ey_el, Ez_el = temp_vec
    eField = temp_vec

    print(eField)


def interpolv2(xdim, ydim, zdim, matrix, coords):
    data_interpol = rgi(
        (
            np.linspace(0, xdim - 1, xdim),
            np.linspace(0, ydim - 1, ydim),
            np.linspace(0, zdim - 1, zdim),
        ),
        matrix,
    )
    return data_interpol(np.array(coords))


def comsolDataInterpolationsv2(e3d2, coords):
    temp_vec = np.zeros((len(coords), 3))
    for k in range(3):
        temp_vec[:, k] = interpolv2(401, 51, 401, e3d2[k], coords)
    eField = temp_vec
    return eField
