from dotenv import load_dotenv
import pandas as pd
from xdmod_data.warehouse import DataWarehouse

load_dotenv()

XDMOD_API_URL = "https://xdmod.access-ci.org"
dw = DataWarehouse(XDMOD_API_URL)

def fetch_job_data(duration, metric, dimension=None, dataset_type=None,  filters={}):
    """
    Generic function to fetch job data from the 'Jobs' realm.
    If a dimension is provided, the data will be grouped by that dimension.
    """
    with dw:
        kwargs = dict(
            duration=duration,
            realm="Jobs",
            metric=metric,
            filters=filters,
            dataset_type= dataset_type
        )
        if dimension is not None:
            kwargs["dimension"] = dimension
        data = dw.get_data(**kwargs)
        if dataset_type is not None:
            kwargs["dataset_type"] = dataset_type
        data = dw.get_data(**kwargs)

    return data

def process_data_for_display(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process the DataFrame for display.
    For example, reset the index and apply any formatting you may need.
    """
    processed_df = df.reset_index()


    return processed_df

def fetch_wait_time_by_resource(duration = "7 day"):
    """
    Fetch the average wait time (in hours) per job grouped by resource.
    """
    data = fetch_job_data(duration, metric="avg_waitduration_hours", dimension="resource", dataset_type = "aggregate")
    data = data.reset_index()
    resource_names = {
        "Purdue Anvil GPU": "Anvil_GPU",
        "Purdue Anvil CPU": "Anvil_CPU",
        "Bridges 2 GPU": "Bridges-2",
        "Bridges 2 RM": "Bridges-2",
        "Bridges 2 EM": "Bridges-2",
        "Bridges2 GPU AI": "Bridges-2",
        "NCSA DELTA CPU": "Delta",
        "NCSA DELTA GPU": "Delta",
        "NCSA DeltaAI": "DeltaAI",
        "UD DARWIN": "DARWIN",
        "UD DARWIN GPU": "DARWIN",
        "TACC STAMPEDE3": "Stampede-3",
        "IACS Ookami": "OOKAMI",
        "Expanse": "Expanse",
        "Expanse GPU": "Expanse",
        "Texas A&M U FASTER": "FASTER",
        "Texas A&M U ACES": "ACES",
        "PSC Neocortex": "Neocortex",
        "PSC Neocortex SDFlex": "Neocortex",
    }

    # Create a new column with the simplified resource names
    data['Simplified Resource'] = data['Resource'].map(resource_names)
    # Group by the simplified resource name and find the max wait time
    max_wait_times = data.groupby('Simplified Resource')['Wait Hours: Per Job'].max().reset_index()
    return max_wait_times
