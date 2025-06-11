import os
import re
import pandas as pd
from typing import Any, Dict, List, Tuple

from models import db
from models.rps import RPS
from models.gui import GUI
from models.rpGUI import RpGUI
from models.rpMemory import RpMemory
from models.gpu import GPU
from models.rpGPU import RpGPU
from models.researchField import ResearchFields
from models.rpResearchField import RpResearchField
from models.software import Software
from models.rpSoftware import RpSoftware
from models.rpInfo import RpInfo

# Confluence modules
from confluence.confluenceAPI import ConfluenceAPI
from confluence.APIValidation import (
    validate_storage_table,
    validate_suitability,
    validate_memory_table,
    validate_gpu_table
)

# ARA DB API module
from AraDB.araDBapi import ARADBAPI

# If there are known synonyms that should collapse to the same “cleaned” name:
RP_NAME_SYNONYMS: Dict[str, str] = {}

def get_rp_storage_data(storageTable: pd.DataFrame) -> Dict[str, Any]:
    """
    Extract RP storage data from a Confluence storage table.
    Expects the first table to have two columns: Temp Storage and Long-Term Storage.

    This function assumes that the storageTable is valid (validate using validate_storage_table before calling this)
    This function is used to get the storage information from the storage table and
    return it in a dictionary format that can be used to update the database
    The index of the storageTable is directly related to the columns as seen on the confluence page

    Args:
        storageTable: A pandas DataFrame containing the storage table data from Confluence.

    Returns:
        A dictionary with keys 'scratch_tb' and 'longterm_tb' containing the extracted storage values.
    """
    scratch_tb = storageTable.iloc[0, 0]
    longterm_tb = storageTable.iloc[0, 1]
    return {
        'scratch_tb': scratch_tb,
        'longterm_tb': longterm_tb,
    }


def get_rp_memory_data(memoryTable: pd.DataFrame, rp: Any = None) -> List[Dict[str, Any]]:
    """
    Parse memory data from a Confluence memory table.
    Expects the first column to be Node Type and the second column to be Memory (GB).

    This function assumes that the memoryTable is valid (validate using validate_memory_table before calling this)
    This function is used to get the memory information from the memory table and
    return it in a dictionary format that can be used to update the database
    The index of the storageTable is directly related to the columns as seen on the confluence page

    Args:
        memoryTable: A pandas DataFrame containing the memory information for the RP.
        rp: Optional; an RPS object. If provided, each returned dictionary will include the key 'rp'.

    Returns:
        A list of dictionaries containing the memory information.
    """
    node_type_col = memoryTable.columns[0]
    per_node_memory_gb_col = memoryTable.columns[1]

    memoryData: List[Dict[str, Any]] = []
    for i in range(len(memoryTable.index)):
        row = memoryTable.iloc[i]
        try:
            memory_val = float(row[per_node_memory_gb_col])
        except Exception:
            memory_val = 0.0

        entry = {
            'node_type': str(row[node_type_col]).strip(),
            'per_node_memory_gb': memory_val
        }
        if rp is not None:
            entry['rp'] = rp

        memoryData.append(entry)
    return memoryData


def get_rp_functionality_data(funcTable: pd.DataFrame) -> Dict[str, Any]:
    """
    Extract functionality data from a Confluence functionality table.
    Expects the table to contain values for graphical, GPU, and virtual machine features.

    This function assumes that the funcTable is valid (validate using validate_suitability before calling this)
    This function is used to get the functionality information from the functionality table and
    return it in a dictionary format that can be used to update the database
    The index of the funcTable is directly related to the columns as seen on the confluence page

    Args:
        funcTable: A pandas DataFrame representing the functionality table from Confluence.

    Returns:
        A dictionary with keys 'graphical', 'gpu', and 'virtual_machine' containing the corresponding feature values.
    """
    graphical = funcTable.iloc[0, 1]
    gpu = funcTable.iloc[1, 1]
    virtual_machine = funcTable.iloc[2, 1]
    return {
        'graphical': graphical,
        'gpu': gpu,
        'virtual_machine': virtual_machine
    }


def clean_rp_name(name: str) -> str:
    """
    Clean the RP name by removing non-alphanumeric characters and converting to lowercase.

    Args:
        name: The raw RP name.

    Returns:
        A cleaned version of the RP name.
    """
    cleaned: str = re.sub(r'[^A-Za-z0-9]', '', name).lower()
    if cleaned in RP_NAME_SYNONYMS:
        return RP_NAME_SYNONYMS[cleaned]
    return cleaned

def get_rp_research_field_data(researchFieldTable: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Parse the Research Field table from Confluence (table index 4).
    It should have at least two columns:
       1) Research Field name
       2) Suitability (an integer or something convertible to integer)

    Returns a list of dicts, each containing:
       { 'field_name': <str>, 'suitability': <int> }

    This function assumes that the funcTable is valid. There is no validation function for this yet.

    Args:
        researchFieldTable: A pandas DataFrame containing the research field information.

    Returns:
        A list of dictionaries, where each dictionary has keys 'field_name' (str) and 'suitability' (int).
    """
    if researchFieldTable.shape[1] < 2:
        return []

    research_data = []
    for row in researchFieldTable.itertuples(index=False):
        field_name_raw = str(row[0]).strip()
        try:
            suitability_val = int(str(row[1]).strip())
        except ValueError:
            suitability_val = 0  # fallback if not convertible

        if field_name_raw:
            research_data.append({
                "field_name": field_name_raw,
                "suitability": suitability_val
            })
    return research_data


def validate_info_table(infoTable: pd.DataFrame) -> Tuple[bool, str]:
    """
    Validate the Info Table structure.
    Expects at least 1 row and 3 columns: Blurb, Brief Summary Link, and Documentation Link.

    Args:
        infoTable: A pandas DataFrame representing the Info Table from Confluence.

    Returns:
        A tuple where the first element is a boolean indicating if the table structure is valid,
        and the second element is an error message if the table is invalid.
    """
    if infoTable.shape[0] < 1 or infoTable.shape[1] < 3:
        return False, (
            "Invalid Info Table structure. Expected at least 1 row and 3 columns for Blurb, "
            "Summary Link, and Documentation Link."
        )
    return True, ""



def get_rp_info_data(infoTable: pd.DataFrame) -> Dict[str, str]:
    """
    Extract the 'Blurb', 'Brief Summary Link', and 'Documentation Link' from the first row
    of the Info Table.
    Safely converts cell values so that if a cell is NaN, an empty string is returned.

    This function assumes that the funcTable is valid (validate using validate_info_table before calling this)

    Args:
        infoTable: A pandas DataFrame representing the Info Table from Confluence.

    Returns:
        A dictionary with keys 'blurb', 'link', and 'documentation' corresponding to the extracted values.
    """
    def safe_str(cell):
        return "" if pd.isnull(cell) else str(cell).strip()

    blurb = safe_str(infoTable.iloc[0, 0])
    summary_link = safe_str(infoTable.iloc[0, 1])
    documentation_link = safe_str(infoTable.iloc[0, 2])
    return {
        'blurb': blurb,
        'link': summary_link,
        'documentation': documentation_link
    }

def get_rp_gpu_data(gpuTable: pd.DataFrame) -> Dict[str, Any]:
    """
    Extract Rp gpu data from Confluence page.
    Expects the table to have two columns: GPU and Vram/GPU memory

    This function assumes gpuTable is valid (validate using validate_gpu_table)

    Args:
        gpuTabe (pd.Dataframe): A pandas DataFrame containg gpu data

    Returns:
        (dict): A dict with keys 'gpu' and 'gpu_memory'
    """

    gpu_col = gpuTable.columns[0]
    gpu_mem_col = gpuTable.columns[1]
    gpu_data = []
    for i in range(len(gpuTable.index)):
        row = gpuTable.iloc[i]
        try:
            mem_val = int(row[gpu_mem_col])
        except Exception:
            mem_val = 0
        entry = {
            'gpu': str(row[gpu_col]).strip(),
            'gpu_memory': mem_val
        }
        gpu_data.append(entry)
    return gpu_data


def build_rp_dict_from_all_software_data(all_software_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Build a dictionary of RPs from the ARA DB software data for matching.
    We use a cleaned key (e.g. "stampede3" from "Stampede-3") but store the original
    name under 'original_rp_name' (which is used when updating the local DB).

    Args:
        all_software_data: A list of dictionaries, each representing software data from the ARA DB.

    Returns:
        A dictionary mapping cleaned RP names to dictionaries containing 'original_rp_name',
        'software' (a set), and 'research_fields' (a set).
    """
    rp_dict: Dict[str, Dict[str, Any]] = {}

    for sw_item in all_software_data:
        sw_name = sw_item.get('software_name', '')
        rf_field = sw_item.get('ai_research_field', '')

        for raw_rp_name in sw_item.get('rp_name', []):
            rp_name = clean_rp_name(raw_rp_name)

            if rp_name not in rp_dict:
                rp_dict[rp_name] = {
                    'original_rp_name': raw_rp_name,
                    'software': set(),
                    'research_fields': set()
                }
            else:
                existing_orig = rp_dict[rp_name]['original_rp_name']
                if existing_orig != raw_rp_name:
                    print(
                        f"[Info] Found duplicate RP name '{rp_name}' for "
                        f"'{raw_rp_name}' and '{existing_orig}'. Keeping '{existing_orig}' as canonical."
                    )

            if sw_name:
                rp_dict[rp_name]['software'].add(sw_name)
            if rf_field:
                rp_dict[rp_name]['research_fields'].add(rf_field)

    return rp_dict


def update_rps_from_confluence_and_araDBapi() -> None:
    """
    Update RPs in the local DB using data from Confluence and the ARA DB. We take the unity of the RPs from the two sources.
    We get Storage, Memory, Functionality, GUI, General Info (Blurbs etc) and some RPs from Confluence, and we get most RPs, Research Fields, and Software info from the API.
    Whenever Confluence and araDB RP names match, we join their info.

    The Confluence page is expected to have the following tables (in order):
      0) Storage Table (Temp and Long-Term Storage)
      1) Memory Table (Node Type and Memory (GB))
      2) Functionality Table (Graphical, GPU, Virtual Machine)
      3) GUI Table
      4) Research Field Table (We don't care about this one -- We get this info from the ara DB API)
      5) Info Table

    If a page has only 5 tables, the Info data is assumed to be missing.

    Args:
        None.

    Returns:
        None.
    """
    conf_api = ConfluenceAPI()
    db_api = ARADBAPI()

    all_software_data = db_api.query_all_software()
    if not all_software_data:
        print("[araDBapi] No software data returned. Cannot proceed with RP updates.")
        return

    # Build dictionary keyed by cleaned RP names for matching with ARA DB data
    rp_dict = build_rp_dict_from_all_software_data(all_software_data)
    matched_rps: set = set()

    parent_id = os.getenv("parent_page_id")
    pageIds = conf_api.get_page_children_ids(parent_id)

    for pid in pageIds:
        rp = None  # Ensure 'rp' is always defined in this scope
        tables, pageName = conf_api.get_tabulated_page_data(page_id=pid)
        # Process only pages ending with " Data"
        if not pageName.endswith(" Data"):
            continue

        raw_rp_name = pageName[:-len(" Data")].strip()
        cleaned_confluence_name = clean_rp_name(raw_rp_name)
        is_new = False
        if cleaned_confluence_name in rp_dict:
            matched_rps.add(cleaned_confluence_name)
            # Use the Confluence name as default
            final_rpName = raw_rp_name
            research_fields = rp_dict[cleaned_confluence_name]['research_fields']
            print(f"[Match] Confluence page '{pageName}' => DB RP '{final_rpName}'")
        else:
            is_new = True
            print(f"[New] Confluence page '{pageName}' does not match any AraDB API RP. Creating new record.")
            final_rpName = raw_rp_name
            research_fields = set()

        messages: List[str] = []
        # Require a minimum of 5 tables: Storage, Memory, Functionality, GUI, and Research Field
        if len(tables) < 5:
            msg = (
                f"[Warn] Page '{pageName}' does not have the minimum required 5 tables. "
                f"Found only {len(tables)}."
            )
            print(msg)
            messages.append(msg)
            continue

        # === 1) Storage Table (index 0) ===
        storageTable = tables[0]
        storageTableIsValid, msg = validate_storage_table(storageTable)
        if storageTableIsValid:
            storageData = get_rp_storage_data(storageTable)
        else:
            storageData = {}
            messages.append(msg + ". Storage data was not updated.")
            print(msg + ". Storage data was not updated.")

        # === 2) Memory Table (index 1) ===
        memoryTable = tables[1]
        memoryDataIsValid, msg = validate_memory_table(memoryTable)
        if memoryDataIsValid:
            memoryData = get_rp_memory_data(memoryTable)
        else:
            memoryData = []
            messages.append(msg + " Memory data was not updated.")
            print(msg + " Memory data was not updated.")

        # === 3) Functionality Table (index 2) ===
        funcTable = tables[2]
        funcTableIsValid, msg = validate_suitability(funcTable)
        if funcTableIsValid:
            funcData = get_rp_functionality_data(funcTable)
        else:
            funcData = {}
            messages.append(msg + ". Functionality data was not updated.")
            print(msg + ". Functionality data was not updated.")

        # === 4) GUI Table (index 3) ===
        guiTable = tables[3]
        guiTableIsValid, _ = validate_suitability(guiTable)

        #Please note that the following information will soon be outdated. The fifth table from Confluence will be deleted, and this will mess with the table indices during retrieval.
        # === 5) Research Field Table (index 4) === // We skip Research Field info from Confluence
        #researchFieldTable = tables[4]
        #confluence_research_fields = get_rp_research_field_data(researchFieldTable)

        # === 6) Info Table (index 5) ===
        if len(tables) >= 6:
            infoTable = tables[5]
            infoTableIsValid, msg = validate_info_table(infoTable)
            if infoTableIsValid:
                infoData = get_rp_info_data(infoTable)
            else:
                infoData = {}
                messages.append(msg + ". Info data was not updated.")
                print(msg + ". Info data was not updated.")
        else:
            infoData = {}

        # === 7) GPU Table (index 6) ===
        rp_gpus = []
        if len(tables) >= 7:
            gpu_info = tables[6]
            gpuTableIsValid, msg = validate_gpu_table(gpu_info)
            if gpuTableIsValid:
                rp_gpus = get_rp_gpu_data(gpu_info)
            else:
                rp_gpus = []
                messages.append(msg + ". GPU data was not updated.")
                print(msg + ". Gpu data was not updated.")

        # --- Create or update the RPS record ---
        rp = RPS.get_or_none(RPS.name == final_rpName)
        if not rp:
            # Only create if the fundamental tables (storage, func) are valid
            if not (storageTableIsValid and funcTableIsValid):
                msg = f"Unable to create new RP '{final_rpName}' due to invalid tables."
                print(msg)
                messages.append(msg)
                continue

            try:
                with db.atomic():
                    rpTableData = {
                        'name': final_rpName,
                        **storageData,
                        **funcData
                    }
                    rp = RPS.create(**rpTableData)
                    if is_new:
                        print(f"RP '{final_rpName}' created (new Confluence-only record).")
                    else:
                        print(f"RP '{final_rpName}' created.")
            except Exception as e:
                msg = f"Error while trying to create RP '{final_rpName}': {e}"
                print(msg)
                messages.append(msg)
                continue
        else:
            try:
                with db.atomic():
                    rpTableData: Dict[str, Any] = {}
                    if storageTableIsValid:
                        rpTableData.update(storageData)
                    if funcTableIsValid:
                        rpTableData.update(funcData)
                    rpTableData['name'] = final_rpName
                    RPS.update(**rpTableData).where(RPS.id == rp.id).execute()
                    print(f"RP '{final_rpName}' updated.")
            except Exception as e:
                msg = f"Error while trying to update RP '{final_rpName}': {e}"
                print(msg)
                messages.append(msg)

        # === Update Memory ===
        if rp and memoryData:
            try:
                for row in memoryData:
                    row['rp_id'] = rp.id
                with db.atomic():
                    RpMemory.insert_many(memoryData).on_conflict_replace().execute()
                print(f"Memory info updated for '{final_rpName}'")
            except Exception as e:
                msg = f"Error updating memory for '{final_rpName}': {e}"
                print(msg)
                messages.append(msg)

        # === Update GUI ===
        if rp and guiTableIsValid:
            guiTable.fillna(1, inplace=True)
            guiTuple = guiTable.itertuples(index=False)
            try:
                with db.atomic():
                    for item in guiTuple:
                        gui_name = str(item[0]).strip()
                        gui, _ = GUI.get_or_create(gui_name=gui_name)
                        rpGuiData = {'rp': rp, 'gui': gui, 'suitability': item[1]}
                        RpGUI.create(**rpGuiData)
                print(f"GUI info updated for '{final_rpName}'")
            except Exception as e:
                msg = f"Error updating GUI for '{final_rpName}': {e}"
                print(msg)
                messages.append(msg)

        # === Update Research Fields (from ARA DB data) ===
        if rp and research_fields:
            try:
                with db.atomic():
                    for field_name in research_fields:
                        # Split on commas, strip whitespace, ignore empty pieces
                        for single_field in [f.strip() for f in field_name.split(',') if f.strip()]:
                            field_obj, _ = ResearchFields.get_or_create(field_name=single_field)
                            RpResearchField.get_or_create(
                                rp=rp,
                                research_field=field_obj,
                                defaults={'suitability': 1}
                            )
                print(f"RP Research Fields updated for '{final_rpName}'")
            except Exception as e:
                msg = f"Error updating research fields for '{final_rpName}': {e}"
                print(msg)
                messages.append(msg)

        # === Update RpInfo (Info Table Data) ===
        if rp and infoData:
            try:
                rp_info_obj, created = RpInfo.get_or_create(
                    rp=rp,
                    defaults={
                        "blurb": infoData["blurb"],
                        "link": infoData["link"],
                        "documentation": infoData["documentation"]
                    }
                )
                if not created:
                    rp_info_obj.blurb = infoData["blurb"]
                    rp_info_obj.link = infoData["link"]
                    rp_info_obj.documentation = infoData["documentation"]
                    rp_info_obj.save()
                print(f"Info data updated for '{final_rpName}'")
            except Exception as e:
                msg = f"Error updating RpInfo for '{final_rpName}': {e}"
                print(msg)
                messages.append(msg)

        # === Update GPU info ===
        if rp and rp_gpus:
            # try:

            with db.atomic():
                for gpu in rp_gpus:
                    gpu_obj, _ = GPU.get_or_create(gpu_name=gpu['gpu'])
                    rp_gpu = RpGPU.get_or_create(rp=rp, gpu=gpu_obj, gpu_memory=gpu['gpu_memory'])
                # rp_gpu_obj, created =
            # except:
            #     msg = f"Error updating GPU data for '{final_rpName}'"
            #     print(msg)
            #     messages.append(msg)

        if messages:
            print("Errors for RP", final_rpName, ":", messages)

    # Handle RPs that exist in ARA DB but have no Confluence page:
    for cleaned_rp_name, rp_info in rp_dict.items():
        if cleaned_rp_name in matched_rps:
            continue

        final_rpName = rp_info['original_rp_name']
        rp = RPS.get_or_none(RPS.name == final_rpName)
        if rp:
            print(f"[Warn] RP '{final_rpName}' has no Confluence page, but already exists locally. Updating fields.")
        else:
            print(f"[Warn] RP '{final_rpName}' has no Confluence page. Creating minimal record in local DB.")
            try:
                with db.atomic():
                    rp = RPS.create(
                        name=final_rpName,
                        scratch_tb=0.0,
                        longterm_tb=0.0,
                        graphical=0,
                        gpu=0,
                        virtual_machine=0
                    )
            except Exception as e:
                print(f"[Error] Failed to create minimal record for RP '{final_rpName}': {e}")
                continue

        fields_set = rp_info['research_fields']
        if rp and fields_set:
            try:
                with db.atomic():
                    RpResearchField.delete().where(RpResearchField.rp == rp).execute()
                    for field_name in fields_set:
                        # If multiple fields come in one string,  split by commas
                        for single_field in [f.strip() for f in field_name.split(',') if f.strip()]:
                            field_obj, _ = ResearchFields.get_or_create(field_name=single_field)
                            RpResearchField.create(rp=rp, research_field=field_obj, suitability=1)
            except Exception as e:
                print(f"[Error] Failed updating research fields for '{final_rpName}': {e}")

    print("\nDone updating RPs from Confluence + ARA DB.")


def update_software_from_araDBapi() -> None:
    """
    Update local database software information from the ARA DB API.
    For each RP in the local DB, we try two attempts to query the ARA DB API:
      1) Convert the RP name to lowercase alphanumeric only (like the original clean_rp_name).
      2) Convert the RP name to lowercase, but preserve alphanumeric, dashes, and underscores.

    If neither attempt returns any software, we skip with a message indicating
    it's likely a Confluence-only RP.

    Args:
        None.

    Returns:
        None.
    """
    import re

    db_api = ARADBAPI()
    rp_list = [rp.name for rp in RPS.select()]
    if not rp_list:
        print("No RPs found in local DB. Aborting software updates.")
        return

    for rp_name in rp_list:
        # Since the default name is now from Confluence, that means that we need to clean the name before passing it to the ARA API since there's no unified pattern.
        # Attempt #1: Strictly alphanumeric + lowercase
        rp_first_attempt = re.sub(r'[^A-Za-z0-9]', '', rp_name).lower()
        rp_second_attempt = re.sub(r'[^A-Za-z0-9\-_]', '', rp_name).lower()
        software_data = db_api.query_software_name_by_rp(rp_first_attempt + "+" + rp_second_attempt)

        # If we still have no data, move on
        if not software_data:
            print(f"[Skip] No software data found for RP '{rp_name}'. "
                  "This is likely a Confluence-only RP.")
            continue

        # Otherwise, proceed to link the software data to the existing RP
        for item in software_data:
            sw_name = item.get('software_name')
            if not sw_name:
                continue

            # Create/get software record
            try:
                software_obj, _ = Software.get_or_create(software_name=sw_name)
            except Exception as e:
                print(f"[Error] Could not create/get software '{sw_name}': {e}")
                continue

            # Retrieve local RP record by the *original* name
            rp = RPS.get_or_none(RPS.name == rp_name)
            if not rp:
                print(f"[Skip] RP '{rp_name}' not found in local DB. "
                      f"Skipping link with software '{sw_name}'.")
                continue

            # Link the Software entry to the local RP
            try:
                with db.atomic():
                    RpSoftware.insert(rp=rp, software=software_obj)\
                              .on_conflict_replace()\
                              .execute()
            except Exception as e:
                print(f"Error linking software '{sw_name}' to RP '{rp_name}': {e}")

        print(f"Software updates for RP '{rp_name}' complete.")

    print("Software updates from ARA DB complete.")


if __name__ == '__main__':
    update_rps_from_confluence_and_araDBapi()
    update_software_from_araDBapi()
