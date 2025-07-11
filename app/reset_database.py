from models import db
from models.rps import RPS
from models.researchField import ResearchFields
from models.rpResearchField import RpResearchField
from models.software import Software
from models.rpSoftware import RpSoftware
from models.gui import GUI
from models.rpGUI import RpGUI
from models.gpu import GPU
from models.rpGPU import RpGPU
from models.rpMemory import RpMemory
from models.rpInfo import RpInfo
import csv
from updateDBFromAraDBAPI import update_rps_from_confluence_and_araDBapi,update_software_from_araDBapi
import shutil #to create backup of the DB
import sys
import os
from peewee import *

def recreate_tables():

    """
    delete and recreate all of the tables in the database
    """
    db.connect(reuse_if_open=True)

    with db.atomic() as transaction:
        try:
            tables = db.get_tables()
            print(f"Dropping tables: {tables}")
            tables = [RPS,ResearchFields,RpResearchField,Software,RpSoftware,GUI,RpGUI,RpMemory,RpInfo,GPU,RpGPU]
            db.drop_tables(tables)

            db.create_tables(tables)
            tables = db.get_tables()
            print(f"Recreated tables: {tables}")
        except Exception as e:
            transaction.rollback()
            print(e)

    db.close()

def reset_with_test_data():

    """
    Add test data to the database. This data is used for testing our application
    and is not meant to be used for the actual application.
    """
    db.connect(reuse_if_open=True)
    rps = [
    {"name":"ACES", "scratch_tb":1, "longterm_tb":5, "gpu":2, "graphical":2},
    {"name":"Anvil", "scratch_tb":100, "longterm_tb":50, "gpu":2},
    {"name":"Bridges-2", "scratch_tb":0, "longterm_tb":0, "gpu": 2, "graphical":2},
    {"name":"DARWIN", "scratch_tb":2, "longterm_tb":10, "gpu": 2, "graphical":2},
    {"name":"Delta", "scratch_tb":1.5, "longterm_tb":0.5, "gpu": 2, "graphical":2},
    {"name":"Expanse", "scratch_tb":7000, "longterm_tb":12000, "gpu": 2, "graphical":2},
    {"name":"FASTER", "scratch_tb":1, "longterm_tb":50, "gpu":2, "graphical":2},
    {"name":"Jetstream2", "scratch_tb":0, "longterm_tb":0, "gpu":2, "virtual_machine":2,},
    {"name":"OOKAMI", "scratch_tb":30, "longterm_tb":80, "gpu":2},
    {"name":"KyRIC", "scratch_tb":10, "longterm_tb":0.5, "graphical":2},
    {"name":"Rockfish", "scratch_tb":10, "longterm_tb":100, "gpu":2},
    {"name":"Stampede-2", "scratch_tb":0, "longterm_tb":1, "graphical":2},
    {"name":"Stampede-3", "scratch_tb":0, "longterm_tb":1, "graphical":2},
    {"name":"RANCH", "scratch_tb":0, "longterm_tb":20},
    {"name":"Open Science Grid", "scratch_tb":0, "longterm_tb":0.5, "gpu":2},
    {"name":"Open Storage Network", "scratch_tb":0, "longterm_tb":0},
    ]
    fields = [
        {"field_name":"Biology"},
        {"field_name":"Chemistry"},
        {"field_name":"Physics"},
        {"field_name":"Computer Science"},
        {"field_name":"Civil Engineering"},
        {"field_name":"Economics"},
        {"field_name":"Linguistics"},
        {"field_name":"History"},
        {"field_name":"Agriculture"},
        {"field_name":"Medicine"},
    ]

    #Types of GUI's
    Gui = [
    {"gui_name":"Open OnDemand"},
    {"gui_name":"RStudio"},
    {"gui_name":"JupyterLab"},
    {"gui_name":"Exosphere"},
    {"gui_name":"Horizon"},
    {"gui_name":"CACAO"},
    ]

    # which GUIs belong to which RPs
    rpGUI_together = {
        "Open OnDemand":['bridges-2', 'expanse', 'anvil', 'aces', 'faster'],
        "RStudio":['aces'],
        "JupyterLab":['aces'],
        "Exosphere":['jetstream2'],
        "Horizon":['jetstream2'],
        "CACAO":['jetstream2']}


    with db.atomic() as transaction:
        #try adding the data to the database. If there is an error, rollback the transaction
        try:
            print("Adding RPS data")
            RPS.insert_many(rps).on_conflict_replace().execute()

            #per node memory
            per_node_memory_gb = [{'rp':RPS.get(RPS.name == 'aces'),
                                'node_type':'Standard','per_node_memory_gb':512},
                            {'rp':RPS.get(RPS.name == 'anvil'),
                                'node_type':'Standard','per_node_memory_gb':256},
                            {'rp':RPS.get(RPS.name == 'anvil'),
                                'node_type':'Large Memory', 'per_node_memory_gb':1000},
                            {'rp':RPS.get(RPS.name == 'bridges-2'),
                                'node_type':'Standard','per_node_memory_gb':256},
                            {'rp':RPS.get(RPS.name == 'bridges-2'),
                                'node_type':'Large Memory','per_node_memory_gb':512},
                            {'rp':RPS.get(RPS.name == 'darwin'),
                                'node_type':'Standard','per_node_memory_gb':512},
                            {'rp':RPS.get(RPS.name == 'darwin'),
                                'node_type':'Large Memory','per_node_memory_gb':1024},
                            {'rp':RPS.get(RPS.name == 'darwin'),
                                'node_type':'Extra-Large Memory','per_node_memory_gb':2048},
                            {'rp':RPS.get(RPS.name == 'delta'),
                                'node_type':'Standard','per_node_memory_gb':256},
                            {'rp':RPS.get(RPS.name == 'delta'),
                                'node_type':'Large Memory','per_node_memory_gb':2000},
                            {'rp':RPS.get(RPS.name == 'expanse'),
                                'node_type':'Standard','per_node_memory_gb':256},
                            {'rp':RPS.get(RPS.name == 'expanse'),
                                'node_type':'Large Memory','per_node_memory_gb':2000},
                            {'rp':RPS.get(RPS.name == 'faster'),
                                'node_type':'Standard','per_node_memory_gb':256},
                            {'rp':RPS.get(RPS.name == 'jetstream2'),
                                'node_type':'Standard','per_node_memory_gb':512},
                            {'rp':RPS.get(RPS.name == 'jetstream2'),
                                'node_type':'Large Memory','per_node_memory_gb':1024},
                            {'rp':RPS.get(RPS.name == 'ookami'),
                                'node_type':'Standard','per_node_memory_gb':32},
                            {'rp':RPS.get(RPS.name == 'kyric'),
                                'node_type':'Large Memory','per_node_memory_gb':3000},
                            {'rp':RPS.get(RPS.name == 'rockfish'),
                                'node_type':'Standard','per_node_memory_gb':192},
                            {'rp':RPS.get(RPS.name == 'rockfish'),
                                'node_type':'Large Memory','per_node_memory_gb':1500},
                            {'rp':RPS.get(RPS.name == 'stampede-2'),
                                'node_type':'Standard','per_node_memory_gb':96}]

            print("Adding ResearchFields data")
            ResearchFields.insert_many(fields).on_conflict_replace().execute()

            rpResearch = [
                {"rp": RPS.get(RPS.name == "Bridges-2"),
                "research_field": ResearchFields.get(ResearchFields.field_name == "Biology"),
                "suitability":1,
                },
                {"rp": RPS.get(RPS.name == "stampede-2"),
                "research_field": ResearchFields.get(ResearchFields.field_name == "Biology"),
                "suitability":1,
                },
                {"rp": RPS.get(RPS.name == "expanse"),
                "research_field": ResearchFields.get(ResearchFields.field_name == "Biology"),
                "suitability":1,
                },
                {"rp": RPS.get(RPS.name == "bridges-2"),
                "research_field": ResearchFields.get(ResearchFields.field_name == "Chemistry"),
                "suitability":1,
                },
                {"rp": RPS.get(RPS.name == "stampede-2"),
                "research_field": ResearchFields.get(ResearchFields.field_name == "Chemistry"),
                "suitability":1,
                },
                {"rp": RPS.get(RPS.name == "bridges-2"),
                "research_field": ResearchFields.get(ResearchFields.field_name == "Physics"),
                "suitability":1,
                },
                {"rp": RPS.get(RPS.name == "stampede-2"),
                "research_field": ResearchFields.get(ResearchFields.field_name == "Physics"),
                "suitability":1,
                },
                {"rp": RPS.get(RPS.name == "expanse"),
                "research_field": ResearchFields.get(ResearchFields.field_name == "Physics"),
                "suitability":1,
                },
                {"rp": RPS.get(RPS.name == "bridges-2"),
                "research_field": ResearchFields.get(ResearchFields.field_name == "Computer Science"),
                "suitability":1,
                },
                {"rp": RPS.get(RPS.name == "stampede-2"),
                "research_field": ResearchFields.get(ResearchFields.field_name == "Computer Science"),
                "suitability":1,
                },
                {"rp": RPS.get(RPS.name == "expanse"),
                "research_field": ResearchFields.get(ResearchFields.field_name == "Computer Science"),
                "suitability":1,
                },
                {"rp": RPS.get(RPS.name == "jetstream2"),
                "research_field": ResearchFields.get(ResearchFields.field_name == "Civil Engineering"),
                "suitability":1,
                },
                {"rp": RPS.get(RPS.name == "bridges-2"),
                "research_field": ResearchFields.get(ResearchFields.field_name == "Civil Engineering"),
                "suitability":1,
                },
                {"rp": RPS.get(RPS.name == "jetstream2"),
                "research_field": ResearchFields.get(ResearchFields.field_name == "Economics"),
                "suitability":1,
                },
                {"rp": RPS.get(RPS.name == "expanse"),
                "research_field": ResearchFields.get(ResearchFields.field_name == "Economics"),
                "suitability":1,
                },
                {"rp": RPS.get(RPS.name == "open science grid"),
                "research_field": ResearchFields.get(ResearchFields.field_name == "Linguistics"),
                "suitability":1,
                },
                {"rp": RPS.get(RPS.name == "open science grid"),
                "research_field": ResearchFields.get(ResearchFields.field_name == "History"),
                "suitability":1,
                },
                {"rp": RPS.get(RPS.name == "kyric"),
                "research_field": ResearchFields.get(ResearchFields.field_name == "Agriculture"),
                "suitability":1,
                },
                {"rp": RPS.get(RPS.name == "anvil"),
                "research_field": ResearchFields.get(ResearchFields.field_name == "Agriculture"),
                "suitability":1,
                },
                {"rp": RPS.get(RPS.name == "ookami"),
                "research_field": ResearchFields.get(ResearchFields.field_name == "Medicine"),
                "suitability":1,
                },
                {"rp": RPS.get(RPS.name == "rockfish"),
                "research_field": ResearchFields.get(ResearchFields.field_name == "Medicine"),
                "suitability":1,
                },
                {"rp": RPS.get(RPS.name == "bridges-2"),
                "research_field": ResearchFields.get(ResearchFields.field_name == "Medicine"),
                "suitability":1,
                },
            ]

            print("Adding RpResearchField data")
            RpResearchField.insert_many(rpResearch).on_conflict_replace().execute()

            print("Adding JobClass data")

            print("Adding GUI data")
            GUI.insert_many(Gui).on_conflict_replace().execute()

            rpGui = []
            for gui in list(rpGUI_together.keys()):
                for rp in rpGUI_together[gui]:
                    rpGui.append({"rp": RPS.get(RPS.name == rp),
                    "gui": GUI.get(GUI.gui_name == gui),
                    "suitability":1})

            print("Adding the GUI to the RP list")
            RpGUI.insert_many(rpGui).on_conflict_replace().execute()

            print('Adding data to RpMemory')
            RpMemory.insert_many(per_node_memory_gb).on_conflict_replace().execute()

        except Exception as e:
            transaction.rollback()
            print(e)
    db.close()

def add_software():
    """
    Add software data to the database from a CSV file and associate each software with the correct RP names.
    """

    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, 'software', 'combined_data.csv')

    rp_name_mapping = {
        "aces": "ACES",
        "anvil": "Anvil",
        "bridges": "Bridges-2",
        "darwin": "DARWIN",
        "delta": "Delta",
        "expanse": "Expanse",
        "faster": "FASTER",
        "jetstream": "Jetstream2",
        "ookami": "OOKAMI",
        "kyric": "KyRIC",
        "stampede3": "Stampede-3",
    }

    db.connect(reuse_if_open=True)
    with open(file_path, 'r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            software_name = row['software name']
            rp_names = row['RP Name'].split(',')  # Split RP names by comma

            # Check if software already exists, if not create it
            software, created = Software.get_or_create(software_name=software_name)

            for rp_name in rp_names:
                    rp_name = rp_name.strip()  # Remove any leading/trailing whitespace

                    # Use the mapping to get the correct RP name
                    if rp_name in rp_name_mapping:
                        rp_name = rp_name_mapping[rp_name]
                    else:
                        print(f"RP name '{rp_name}' not found in mapping. Skipping this RP for software '{software_name}'.")
                        continue

                    # Get the RP instance
                    try:
                        rp = RPS.get(RPS.name == rp_name)
                    except RPS.DoesNotExist:
                        print(f"RP '{rp_name}' does not exist in the database. Skipping this RP for software '{software_name}'.")
                        continue

                    # Associate the software with the RP
                    RpSoftware.get_or_create(software=software, rp=rp)

    db.close()


#Adds "info" to the database. This incudes a blurb about them, a link to the ACCESS resources website, and the individual documentation link
def add_info():
    db.connect(reuse_if_open=True)
    with db.atomic() as transaction:
        try:
            #info about the RP's as well as links to their websites
            rpInfo = [{'rp':RPS.get(RPS.name == 'aces'),
                       'blurb': r"ACES (Accelerating Computing for Emerging Sciences) is funded by NSF ACSS program (Award #2112356) and provides an innovative advanced computational prototype system. ACES is especially recommended for users who need workflows that can utilize novel accelerators and/or multiple GPUs.",
                       'link': r"https://operations.access-ci.org/node/597",
                       'documentation': r"https://xsedetoaccess.ccs.uky.edu/confluence/redirect/ACES+-+TAMU.html"},
                    {'rp':RPS.get(RPS.name == 'anvil'),
                     'blurb': r"Purdue Anvil's advanced computing capabilities are well suited to support a wide range of computational and data-intensive research spanning from traditional high-performance computing to modern artificial intelligence applications. It’s general purpose CPUs and 128 cores per node make it suitable for many types of CPU-based workloads.",
                     'link': r"https://operations.access-ci.org/node/577",
                     'documentation': r"https://xsedetoaccess.ccs.uky.edu/confluence/redirect/Anvil+-+Purdue.html"},
                    {'rp':RPS.get(RPS.name == 'bridges-2'),
                     'blurb': r"Bridges-2 Regular Memory (RM) nodes provide extremely powerful general-purpose computing, machine learning and data analytics, AI inferencing, and pre- and post-processing. Their x86 CPUs support an extremely broad range of applications, and jobs can request anywhere from 1 core to all 64,512 cores of the Bridges-2 RM resource.",
                     'link': r"https://operations.access-ci.org/node/578",
                     'documentation': r"https://xsedetoaccess.ccs.uky.edu/confluence/redirect/Bridges-2+-+PSC.html"},
                    {'rp':RPS.get(RPS.name == 'darwin'),
                     'blurb': r"The Delaware Advanced Research Workforce and Innovation Network’s (DARWIN’s) standard memory nodes provide powerful general-purpose computing, data analytics, and pre- and post-processing capabilities. The large and xlarge memory nodes enable memory-intensive applications and workflows that do not have distributed-memory implementations.",
                     'link': r"https://operations.access-ci.org/node/595",
                     'documentation': r"https://xsedetoaccess.ccs.uky.edu/confluence/redirect/DARWIN+-+Delaware.html"},
                    {'rp':RPS.get(RPS.name == 'delta'),
                     'blurb': r"The Delta CPU resource is designed for general purpose computation across a broad range of domains able to benefit from the scalar and multi-core performance provided by the CPUs such as appropriately scaled weather and climate, hydrodynamics, astrophysics, and engineering modeling and simulation, and other domains that have algorithms that have not yet moved to the GPU.",
                     'link': r"https://operations.access-ci.org/node/575",
                     'documentation': r"https://xsedetoaccess.ccs.uky.edu/confluence/redirect/Delta+-+NCSA.html"},
                    {'rp':RPS.get(RPS.name == 'expanse'),
                    'blurb': r"Expanse is designed to provide cyberfrastructure for the long tail of science, covering a diverse application base with complex workflows. The system is geared towards supporting capacity computing, optimized for quick turnaround on small/modest scale jobs. Expanse supports composable systems computing with dynamic capabilities enabled using tools such as Kubernetes and workflow software.",
                    'link': r"https://operations.access-ci.org/node/566",
                    'documentation': r"https://xsedetoaccess.ccs.uky.edu/confluence/redirect/Expanse+-+SDSC.html"},
                    {'rp':RPS.get(RPS.name == 'faster'),
                    'blurb': r"FASTER (Fostering Accelerated Scientific Transformations, Education and Research) is funded by the NSF MRI program (Award #2019129) and provides a composable high-performance data-analysis and computing instrument. The 180 compute nodes, including 260 NVIDIA GPUs, lend themselves to workflows that can utilize multiple GPUs.",
                    'link': r"https://operations.access-ci.org/node/565",
                    'documentation': r"https://xsedetoaccess.ccs.uky.edu/confluence/redirect/FASTER+-+TAMU.html"},
                    {'rp':RPS.get(RPS.name == 'jetstream2'),
                    'blurb': r"Jetstream 2 is for researchers needing virtual machine services on demand as well as for software creators and researchers needing to create their own customized virtual machine environments. Additional use cases are for research-supporting infrastructure services that need to be 'always on' as well as science gateway services and for education support, providing virtual machines for students.",
                    'link': r"https://operations.access-ci.org/node/564",
                    'documentation': r"https://xsedetoaccess.ccs.uky.edu/confluence/redirect/Jetstream2+-+IU.html"},
                    {'rp':RPS.get(RPS.name == 'ookami'),
                    'blurb': r"Ookami provides researchers with access to the A64FX processor developed by Riken and Fujitsu for the Japanese path to exascale computing and is deployed in the, until June 2022, fastest computer in the world, Fugaku. It is the first such computer outside of Japan. Applications that are fitting within the memory requirements (27GB per node) and are well vectorized, or well auto-vectorized by the compiler. Note a node is allocated exclusively to one user. Node-sharing is not available.",
                    'link': r"https://operations.access-ci.org/node/585",
                    'documentation': r"https://xsedetoaccess.ccs.uky.edu/confluence/redirect/OOKAMI+-+Stonybrook.html"},
                    {'rp':RPS.get(RPS.name == 'kyric'),
                    'blurb': r"The Kentucky Research informatics Cloud (KyRIC) Large Memory nodes are increasingly needed by a wide range of ACCESS researchers, particularly researchers working with big data such as massive NLP data sets used in many research domains or the massive genomes required by computational biology and bioinformatics.",
                    'link': r"https://operations.access-ci.org/node/568",
                    'documentation': r"https://xsedetoaccess.ccs.uky.edu/confluence/redirect/KyRIC+-+Kentucky.html"},
                    {'rp':RPS.get(RPS.name == 'rockfish'),
                    'blurb': r"Johns Hopkins University’s flagship cluster, Rockfish, integrates high-performance and data-intensive computing while developing tools for generating, analyzing and disseminating data sets of ever-increasing size. The cluster contains compute nodes optimized for different research projects and complex, optimized workflows.",
                    'link': r"https://operations.access-ci.org/node/569",
                    'documentation': r"https://xsedetoaccess.ccs.uky.edu/confluence/redirect/Rockfish+-+JHU.html"},
                    # {'rp':RPS.get(RPS.name == 'stampede-2'),
                    # 'blurb': r"Stampede2 is intended primarily for parallel applications scalable to tens of thousands of cores, as well as general purpose and throughput computing. Normal batch queues will enable users to run simulations up to 48 hours. Jobs requiring run times and more cores than allowed by the normal queues will be run in a special queue after approval of TACC staff. normal, serial and development queues are configured as well as special purpose queues.",
                    # 'link': r"https://operations.access-ci.org/node/596",
                    # 'documentation': r"https://xsedetoaccess.ccs.uky.edu/confluence/redirect/Stampede-2+-+TACC.html"},
                    {'rp':RPS.get(RPS.name == 'stampede-3'),
                    'blurb': r"Stampede3 is intended primarily for parallel applications scalable to tens of thousands of cores, as well as general purpose and throughput computing. Normal batch queues will enable users to run simulations up to 48 hours.",
                    'link': r"https://operations.access-ci.org/node/592",
                    'documentation': r"https://access-ci.atlassian.net/wiki/spaces/ACCESSdocumentation/pages/467111711/Stampede-3+-+TACC"},
                    {'rp':RPS.get(RPS.name == 'ranch'),
                    'blurb': r"TACC's High Performance Computing systems are used primarily for scientific computing with users having access to WORK, SCRATCH, and HOME file systems that are limited in size.The Ranch system serves the HPC and Vis community systems by providing a massive, high-performance file system for archival purposes.",
                    'link': r"https://operations.access-ci.org/node/572",
                    'documentation': r"https://xsedetoaccess.ccs.uky.edu/confluence/redirect/RANCH+-+TACC.html"},
                    {'rp':RPS.get(RPS.name == 'open science grid'),
                    'blurb': r"A virtual HTCondor pool made up of resources from the Open Science Grid (OSG). Recommended for high throughput jobs using a single core, or a small number of threads which can fit on a single compute node.",
                    'link': r"https://operations.access-ci.org/node/583",
                    'documentation': r"https://xsedetoaccess.ccs.uky.edu/confluence/redirect/Open+Science+Grid+-+OSG.html"},
                    {'rp':RPS.get(RPS.name == 'open storage network'),
                    'blurb': r"The Open Storage Network (OSN) is an NSF-funded cloud storage resource, geographically distributed among several pods. Cloud-style storage of project datasets for access using AWS S3-compatible tools. The minimum allocation is 10TB. Storage allocations up to 300TB may be requested via the ACCESS resource allocation process.",
                    'link': r"https://operations.access-ci.org/node/582",
                    'documentation': r"https://access-ci.atlassian.net/wiki/spaces/ACCESSdocumentation/pages/283775144/Open+Storage+Network+OSN"}]
            print('Adding data to RpInfo')
            RpInfo.insert_many(rpInfo,fields=[RpInfo.rp,RpInfo.blurb,RpInfo.link,RpInfo.documentation]).on_conflict_replace().execute()
            #close the database
        except Exception as e:
            transaction.rollback()
            print(e)
    db.close()

def backup_database(db_path: str, backup_path: str) -> None:
    """Create a backup of the existing database.

    Creates a backup of the database file at `db_path` and stores it at `backup_path`.
    Overwrites the backup file if it already exists.

    Args:
        db_path: The file path of the current database.
        backup_path: The file path where the backup should be saved.
    """
    if os.path.exists(db_path):
        print(f"Backing up existing database from '{db_path}' to '{backup_path}'.")
        shutil.copy2(db_path, backup_path)
    else:
        print(f"No existing database found at '{db_path}'. No backup created.")


def revert_database(db_path: str, backup_path: str) -> None:
    """Revert the database from a backup.

    Reverts the database by copying the backup from `backup_path` to `db_path`,
    overwriting the current database file.

    Args:
        db_path: The file path of the current database.
        backup_path: The file path of the backup database.
    """
    if os.path.exists(backup_path):
        if os.path.exists(db_path):
            os.remove(db_path)
        shutil.copy2(backup_path, db_path)
        print("Database was successfully reverted from backup.")
    else:
        print(f"No backup file found at '{backup_path}'. Unable to revert.")

if __name__ == "__main__":

    # Check command-line arg
    if len(sys.argv) < 2:
        print("Usage: python reset_database.py <test|conf|araDB>")
        sys.exit(1)

    data_source = sys.argv[1]

    # Gets directory info for backup
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, "models", "sqlite_db.db")
    backup_path = os.path.join(base_dir, "models", "sqlite_db_backup.db")

    print("Attempting create backup of DB at:", db_path)
    backup_database(db_path, backup_path)

    try:
        if data_source == 'test':
            recreate_tables()
            print("Resetting database from test data")
            reset_with_test_data()
            add_software()
            add_info()
            print("Database reset (test) completed successfully.")

        elif data_source == 'conf':
            print("Confluence-only retrieval has been removed. Please use 'araDB' instead. No changes to the database were made.")

        elif data_source == 'araDB':
            recreate_tables()
            print("Resetting database from ara Database API and conf")
            update_rps_from_confluence_and_araDBapi()
            print("Updating softwares from ara Database API and conf")
            update_software_from_araDBapi()
            print("Database reset (araDB) completed successfully.")
        else:
            print("Invalid argument for reset_database.\nPass in 'test', 'conf', or 'araDB'.")

    except Exception as e:
        print(f"ERROR during update: {e}")
        print("Reverting to previous database backup.")
        revert_database(db_path, backup_path)
