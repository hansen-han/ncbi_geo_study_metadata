from bs4 import BeautifulSoup, Tag
import requests
import pandas as pd
from tqdm import tqdm
import json
import sqlite3
import traceback
import random


# helper functions



def get_study_ids_from_platform_id(platform_id):
    # given a platform, download the platform file and get all the GEO samples
    
    url = "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={platform_id}&targ=self&view=brief&form=text".format(platform_id = platform_id)

    response = requests.get(url)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Get the content of the response
        file_content = response.content

    # Decode the binary content to string assuming utf-8 encoding
    file_content_str = file_content.decode('utf-8')

    # Now, you can manipulate and parse the text as needed
    lines = file_content_str.split('\n')

    study_ids = []
    for line in lines:
        # Process each line as needed
        if "GSE" in line:
            study_ids.append(line.split("= ")[1].split("\r")[0])

    return study_ids
    


def get_gse_metadata(study_id):
    # Define the URL and payload
    url = "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi"
    payload = {"acc": study_id}

    # Make the POST request
    response = requests.post(url, data=payload)

    # Check the response
    if response.status_code == 200:
        # The request was successful
        pass
    else:
        # There was an error
        raise Exception("Could not get data from NCBI.")

    # The HTML data
    html_data = response.text

    # Parse the HTML
    soup = BeautifulSoup(html_data, 'html.parser')

    # Find the main table
    main_table = soup.find('table')

    # Initialize table headers and data
    table_headers = []
    table_data = []

    # Loop through rows in the main table
    for row in main_table.find_all('tr'):
        columns = row.find_all('td')
        if len(columns) == 2:
            header = columns[0].get_text(strip=True)
            value = columns[1].get_text(strip=True)
            table_headers.append(header)
            table_data.append(value)

    # Create a Pandas DataFrame
    df = pd.DataFrame({'Attribute': table_headers, 'Value': table_data})

    # Extract Relevant Data 
    result_dict = {}
    platforms = []
    samples = []
    sample_count = 0
    for x in range(0, len(df['Attribute'])):
        attribute = df.iloc[x]['Attribute']
        value = df.iloc[x]['Value']
        if attribute in [
            "Title", 
            "Status", 
            "Organism", 
            "Experiment type", 
            "Summary",
            "Overall design",
            "Citation(s)",
            "BioProject"
            ]:
            result_dict[attribute] = value 
        elif "GPL" in attribute:
            platforms.append(attribute)
        elif "GSM" in attribute:
            sample_count = sample_count + 1
            samples.append(attribute)

    result_dict["Platform(s)"] = platforms
    result_dict["Number of Samples"] = sample_count
    result_dict["Samples"] = samples
    return result_dict

def tag_to_dict(tag):
    # Make sure the input is a bs4.element.Tag
    if not isinstance(tag, Tag):
        raise TypeError("Input must be a bs4.element.Tag")
    # Create a dictionary from the tag's text, splitting by line and then by key-value delimiter
    return dict(line.split(': ') for line in tag.stripped_strings)


def get_sample_metadata(sample_id):

    # Define the URL and payload
    url = "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi"
    payload = {"acc": sample_id}

    # Make the POST request
    response = requests.post(url, data=payload)

    # Check the response
    if response.status_code == 200:
        # The request was successful
        pass
    else:
        # There was an error
        raise Exception("Could not get data from NCBI.")

    # The HTML data
    html_data = response.text

    # Parse the HTML
    soup = BeautifulSoup(html_data, 'html.parser')
    # Find the main table
    main_table = soup.find('table')

    # Initialize table headers and data
    table_headers = []
    table_data = []

    # Loop through rows in the main table
    for row in main_table.find_all('tr'):
        columns = row.find_all('td')
        if len(columns) == 2:
            header = columns[0].get_text(strip=False)
            value = columns[1]#.get_text(strip=False)
            table_headers.append(header)
            table_data.append(value)

    # Create a Pandas DataFrame
    df = pd.DataFrame({'Attribute': table_headers, 'Value': table_data})

    attribute_dict = {}
    raw_strings = []

    for field_of_interest in ["Characteristics", "Description"]:

        # check if characteristics are in the dataframe
        if field_of_interest in df['Attribute'].values:

            # get the characteristics
            tag = df[df.Attribute == field_of_interest]['Value'].values[0]
            # record the raw text from the tag'
            if tag:
                raw_strings.append(tag.get_text(strip=False))

            # Convert the tag to a dictionary
            try:
                characteristics_dict = tag_to_dict(tag)
            # TODO - there may be formats here that I haven't written logic to handle
            except:
                try:
                    characteristics_dict = {}
                    # check if it is split/formatted a different way
                    for substr in tag.get_text(strip=False).split("_"):
                        key_value_pair = substr.split(":")
                        if len(key_value_pair) != 2:
                            raise ValueError("Not valid format, cannot parse.")
                        
                        characteristics_dict[key_value_pair[0]] = key_value_pair[1]
                except:
                    pass
        else:
            characteristics_dict = {}
        
        # add it to the attribute dict
        for key, value in characteristics_dict.items():
            # dont overwrite anything
            if key not in list(attribute_dict.keys()):
                attribute_dict[key] = value
                    

    # Initialize table headers and data
    table_headers = []
    table_data = []

    # Loop through rows in the main table again....with different formatting
    for row in main_table.find_all('tr'):
        columns = row.find_all('td')
        if len(columns) == 2:
            header = columns[0].get_text(strip=False)
            value = columns[1].get_text(strip=False)
            table_headers.append(header)
            table_data.append(value)
    
    # Create a Pandas DataFrame
    df = pd.DataFrame({'Attribute': table_headers, 'Value': table_data})
    
    try:
        attribute_dict['source_name'] = str(df[df.Attribute == "Source name"]['Value'].values[0])
    except:
        attribute_dict['source_name'] = None
    
    attribute_dict["raw_strings"] = raw_strings

    
    return(attribute_dict)

def get_all_study_metadata(study_id):
    # takes a GEO study ID and returns a dict that contains the study metadata with sample information
    # get study metadata
        study_metadata = get_gse_metadata(study_id)

        # get metadata for all samples
        all_sample_metadata = []
        for sample_id in study_metadata['Samples']:
            all_sample_metadata.append(get_sample_metadata(sample_id))

        # get all unique values for all sample metadata
        sample_metadata_unique_values = {}
        for sample_metadata in all_sample_metadata:
            for key in list(sample_metadata.keys()):
                if key != "raw_strings":
                    if key in sample_metadata_unique_values.keys():
                        sample_metadata_unique_values[key].append(sample_metadata[key])
                    else:
                        sample_metadata_unique_values[key] = [sample_metadata[key]]

        # get unique values for all options
        for key in list(sample_metadata_unique_values.keys()):
            sample_metadata_unique_values[key] = list(set(sample_metadata_unique_values[key]))

        

        # OR...if a field is over a certain length, just take the first 20 values when you send it to GPT (this makes more sense)
        filtered_dict = {key: value for key, value in sample_metadata_unique_values.items()}
        filtered_dict['all_metadata_fields'] = list(sample_metadata_unique_values.keys())

        # randomly sample some raw strings for use by annotator later on....
        # get all raw strings
        raw_strings = []
        for sample_metadata in all_sample_metadata:
            for raw_string in sample_metadata['raw_strings']:
                raw_strings.append(raw_string)

        if len(raw_strings) < 10:
            filtered_dict["raw_strings"] = raw_strings
        else:
            filtered_dict["raw_strings"] =  random.sample(raw_strings, 10)

        study_metadata['sample_metadata'] = filtered_dict
        return study_metadata

def dict_formatter_utility(input_dict, output_dict, input_key, output_key, output_type):
    try:
        if input_key in list(input_dict.keys()):
            output_dict[output_key] = output_type(input_dict[input_key])
        else:
            output_dict[output_key] = None
    except:
        output_dict[output_key] = None

def study_metadata_handler(study_id):
    # creates sql database, retrieves data, saves it to the database
    # main function for running many queries in parallel

    # create connection, table if it doesn't exist yet
    conn = sqlite3.connect('geo_annotations.db')
    cursor = conn.cursor()

    # Create a table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS geo_studies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            study_id TEXT,
            status TEXT,
            title TEXT,
            organism TEXT,
            experiment_type TEXT,
            summary TEXT,
            overall_design TEXT,
            citations TEXT,
            bioproject TEXT,
            platforms TEXT,
            num_samples INTEGER,
            sample_ids TEXT,
            sample_metadata TEXT,
            ai_annotation TEXT
        );
    ''')

    # Commit the changes to the database
    conn.commit()

    # only run the collection if there is not any data already for the study
    cursor.execute("SELECT * FROM geo_studies WHERE study_id = ?", (study_id,))
    result = cursor.fetchone()
    if result is None:
        # get the metadata
        try:
            study_metadata = get_all_study_metadata(study_id)

            formatted_dict = {
                "study_id": study_id,
                "ai_annotation": None
            }

            # reformat values with graceful error handling
            dict_formatter_utility(study_metadata,formatted_dict,"Study","study",str)
            dict_formatter_utility(study_metadata,formatted_dict,"Status","status",str)
            dict_formatter_utility(study_metadata,formatted_dict,"Title","title",str)
            dict_formatter_utility(study_metadata,formatted_dict,"Organism","organism",str)
            dict_formatter_utility(study_metadata,formatted_dict,"Experiment type","experiment_type",str)
            dict_formatter_utility(study_metadata,formatted_dict,"Summary","summary",str)
            dict_formatter_utility(study_metadata,formatted_dict,"Overall design","overall_design",str)
            dict_formatter_utility(study_metadata,formatted_dict,"Citation(s)","citations",str)
            dict_formatter_utility(study_metadata,formatted_dict,"BioProject","bioproject",str)
            dict_formatter_utility(study_metadata,formatted_dict,"Platform(s)","platforms",str)
            dict_formatter_utility(study_metadata,formatted_dict,"Number of Samples","num_samples",int)
            dict_formatter_utility(study_metadata,formatted_dict,"Samples","sample_ids",str)
            dict_formatter_utility(study_metadata,formatted_dict,"sample_metadata","sample_metadata",str)
                        
            # Construct the INSERT INTO statement
            insert_query = '''
                INSERT INTO geo_studies (
                    study_id, 
                    status, 
                    title, 
                    organism, 
                    experiment_type, 
                    summary, 
                    overall_design,
                    citations,
                    bioproject, 
                    platforms, 
                    num_samples, 
                    sample_ids, 
                    sample_metadata, 
                    ai_annotation
                ) VALUES (
                    :study_id, 
                    :status, 
                    :title, 
                    :organism, 
                    :experiment_type, 
                    :summary, 
                    :overall_design,
                    :citations,
                    :bioproject, 
                    :platforms, 
                    :num_samples, 
                    :sample_ids, 
                    :sample_metadata, 
                    :ai_annotation
                )
            '''

            # Execute the insert query
            cursor.execute(insert_query, formatted_dict)

            # Commit the changes to the database, close connection
            conn.commit()
            conn.close()

        except Exception as e:
            traceback.print_exc()
            print("An error occurred. Details:\n", e)

def get_abstract_from_ncbi_citation_code(citation_code):

    import requests
    from bs4 import BeautifulSoup

    r = requests.get("https://pubmed.ncbi.nlm.nih.gov/{citation_code}/".format(citation_code=citation_code))
    # Parse the HTML using BeautifulSoup
    soup = BeautifulSoup(r.text, 'lxml')

    # Find the div with class "abstract-content" and id "eng-abstract"
    div_element = soup.find('div', {'class': 'abstract-content', 'id': 'eng-abstract'})

    # Extract the text inside the div
    if div_element:
        abstract_text = div_element.get_text(strip=True)
        return abstract_text

    else:
        return "None Available"
    

def add_overall_design_to_db(study_id):
    # Establish a new database connection here for each process
    conn = sqlite3.connect('geo_annotations.db')
    cursor = conn.cursor()

    try:
        new_overall_design = get_all_study_metadata(study_id=study_id)['Overall design']

        cursor.execute('''
            UPDATE geo_studies
            SET overall_design = ?
            WHERE study_id = ?;
        ''', (new_overall_design, study_id))

        conn.commit()
    except:
        pass

    conn.close()

