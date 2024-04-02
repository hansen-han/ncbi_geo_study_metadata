# NCBI GEO Study Metadata Repository
This repository is designed to facilitate the easy download and processing of metadata from NCBI's Gene Expression Omnibus (GEO) database. By downloading and storing this metadata in a SQL database, users can perform more powerful searches and analyses, bypassing the limitations of the web interface.

### Files  
```utils.py```: A collection of helper scripts that aid in downloading and processing the metadata from NCBI GEO.

```get_geo_metadata_worker.py```: This script is responsible for downloading all the metadata into a SQL database using multithreading, to allow the process to run quickly.

```ncbi_geo_exploration.ipynb``` An interactive Jupyter Notebook (ipynb) for exploring the downloaded metadata over time. This notebook allows users to visualize trends, patterns, and insights within the GEO data.

### How to Use  
Clone the Repository: Start by cloning this repository to your local machine using ```git clone https://github.com/hansenrhan/ncbi_geo_study_metadata.git```

### Install Dependencies:   
Make sure you have all the necessary dependencies installed. You can do this by running pip install -r requirements.txt.

### Download Metadata:   
Run the get_geo_metadata_worker.py script to download and store the metadata in your SQL database. You may need to configure the script to connect to your database and adjust any settings according to your preferences.

### Explore the Data:   
Utilize the ```ncbi_geo_exploration.ipynb``` Jupyter Notebook to explore the downloaded metadata. This notebook provides an interactive environment for visualizing and analyzing the data.
