# The goal of this worker is to build the database that contains all GEO studies and their metadata
from utils import study_metadata_handler, get_study_ids_from_platform_id
from multiprocessing import Pool, set_start_method

# Function to generate the list of strings
def generate_strings(prefix, start_index, end_index):
    strings = []
    for i in range(start_index, end_index + 1):
        strings.append(prefix + str(i))
    return strings


if __name__ == '__main__':

    # Generate the list of strings
    prefix = "GSE"
    start_index = 1
    end_index = 259285 # highest GEO study number as of 2/26/24
    study_ids = generate_strings(prefix, start_index, end_index)
    
    set_start_method('spawn')  # 'forkserver' can also be used as an alternative


    # Create a Pool for multiprocessing
    # Note: It's better to use 'with' to handle the pool's context management.
    with Pool(processes=5) as pool:  # You can adjust the number of processes as needed
        # Calculate statistics for each word in parallel
        results = pool.map(study_metadata_handler, study_ids)
