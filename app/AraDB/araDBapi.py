import os
from dotenv import load_dotenv
import requests
from typing import Optional, Any, Dict, List

class ARADBAPI:
    """Client for querying the ARA DB API."""

    def __init__(self) -> None:
        """Initialize the ARADBAPI client by loading environment variables."""
        load_dotenv()
        self.base_url: str = "https://ara-db.ccs.uky.edu/api=API_0"
        self.api_key: Optional[str] = os.getenv("ARA_DB_API_KEY")

    def query_rp(self, rp_name: str) -> Dict[str, Any]:
        """Query RP information from the ARA DB API.

        Args:
            rp_name: The name of the RP to query.

        Returns:
            A dictionary with the RP data if successful; otherwise, None.
        """
        try:
            url = f"{self.base_url}/{self.api_key}/rp={rp_name}"
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error querying RP: {e}")
            return {}

    def query_software(self, software_name: str) -> Dict[str, Any]:
        """Query software information from the ARA DB API.

        Args:
            software_name: The name of the software to query.

        Returns:
            A dictionary with the software data if successful; otherwise, None.
        """
        try:
            url = f"{self.base_url}/{self.api_key}/software={software_name}"
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error querying software: {e}")
            return {}

    def query_all_software(self) -> List[Dict[str, Any]]:
        """Query all software data from the ARA DB API.

        Returns:
            A list of dictionaries containing software data if successful; otherwise, None.
        """
        try:
            url = f"{self.base_url}/{self.api_key}/software=*"
            response = requests.get(url)
            response.raise_for_status()
            return response.json()  # should be a large list of dicts
        except requests.exceptions.RequestException as e:
            print(f"Error querying all software: {e}")
            return []

    def query_software_name_by_rp(self, rp_name: str) -> List[Dict[str, Any]]:
        """Query software Names for a given RP, returning only rp_name and software_name fields.

        Args:
            rp_name: The name of the RP to query.

        Returns:
            A list of dictionaries containing the software data if successful; otherwise, None.
        """
        try:
            # Use the include flag to restrict returned fields to rp_name and software_name.
            url = f"{self.base_url}/{self.api_key}/rp={rp_name},include=rp_name+software_name"
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error querying software for RP '{rp_name}': {e}")
            return []