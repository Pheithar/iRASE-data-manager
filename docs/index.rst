.. i-Rase Data Management documentation master file, created by
   sphinx-quickstart on Fri Jun 28 10:22:24 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to i-Rase Data Management's Documentation!
==================================================

**iRASE-data-manager** is a Python library designed for managing data uploads and downloads on the DTU Data platform. This library offers a streamlined interface for interacting with the Figshare-based DTU Data system, tailored specifically for the i-RASE project.

Features
--------

- **Simple Interface**: Intuitive methods for uploading and downloading data.
- **Integration**: Seamless interaction with the DTU Data platform.
- **Project Specific**: Customized for the i-RASE project requirements.

.. toctree::
   :maxdepth: 2

   installation
   modules

Installation
============

To install the **iRASE-data-manager** library, use pip with the following command:

.. code-block:: bash

    pip install git+https://github.com/Pheithar/iRASE-data-manager.git

Getting Started
===============

To get started with the library, ensure you have the appropriate access to the i-RASE project. Access permissions are required for uploading data, whereas downloading public data is available to all users once published.

Access Requirements
-------------------

If you are part of the i-RASE project team, you need access permissions to upload data. Contact the project manager to obtain these permissions.

Authorization Token
-------------------

To use the library's private functionalities, an authorization token from Figshare through DTU Data is required. Follow the instructions in the official documentation to get a personal token: `How to get a personal token <https://help.figshare.com/article/how-to-get-a-personal-token>`_.

Store your token securely using a ``.env`` file in the root directory of your project:

.. code-block:: bash

    FIGSHARE_TOKEN=your_token_here

Using the Library
=================

After installation, import and configure the library in your Python script. Use the ``os`` and ``dotenv`` libraries to handle your Figshare token securely.

Example Code
------------

Here is a basic example of how to load and use your Figshare token within a Python script:

.. code-block:: python

    import os
    from dotenv import load_dotenv

    load_dotenv()

    token = os.getenv('FIGSHARE_TOKEN')

    print(token)  # Ensure the token is loaded correctly

Uploading Data
--------------

To upload data, use the following method after setting up your token:

.. code-block:: python

    from irase_data_manager import experiments_upload_data

    ...

    # Replace 'data_list' and 'metadata' with actual data and metadata
    local_saved_path = experiments_upload_data(data_list, token, metadata)
    print(local_saved_path) # Print the local path where the data is saved

Downloading Data
----------------

To download data, utilize the download method:

.. code-block:: python

    from irase_data_manager import experiments_download_data

    ...

    # Replace 'article_id' with the actual ID of the dataset you want to download
    experiments_download_data(article_id, token, save_path="path/to/save/data/local")

Support
=======

For further assistance or to report issues, please visit the project's GitHub repository: `iRASE-data-manager GitHub <https://github.com/Pheithar/iRASE-data-manager>`_.

FAQs
====

**Q: How do I obtain access to the i-RASE project?**

A: Contact the project manager to get access permissions.

**Q: What if I encounter issues with my token?**

A: Ensure your token is correctly stored in the ``.env`` file and follow the guidelines provided by Figshare for generating and managing tokens.

Additional Resources
=====================

For more information on the DTU Data platform and Figshare integration, refer to the following resources:

- `DTU Data <https://www.data.dtu.dk>`_
- `Figshare <https://figshare.com>`_
- `dotenv Python library <https://pypi.org/project/python-dotenv/>`_
