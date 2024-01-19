"""
Run Simulation
Ben Smith
30/12/2023

This script will run SHETRAN simulations as per the OpenCLIM Framework. Many of these processes are not standard
SHETRAN procedures and so additional exe's are used to adapt the inputs into the required formats.

For SHETRAN information, documentation and the latest release, please see the following Git repository:
https://github.com/nclwater/Shetran-public

The section 'ADAPT SIMULATIONS IF DESIRED' is optional but may increase reliability and decrease unnecessary outputs.

All exe's can be run directly from the command prompt, but you may benefit from some of the variables in this file.
The script is perhaps therefore best edited and then run in a conda prompt or similar.
"""


# --- IMPORTS ---

import os
import shutil
import subprocess
import pandas as pd
from zipfile import ZipFile, ZIP_DEFLATED


# --- USER INPUTS ---
catchment = '1001'  # String

root = "I:/SHETRAN_GB_2021/10_Deliverables/05_SHETRAN_Simulation_Inputs/"

simulation_folder = root + "/04_Example_Simulations/1001_NoNFM_UDM_2017/"

# Load in our list of catchments that states which setup exe to use:
exe_setup_csv_path = root + "01_Software/SHETRAN_exe_list.csv"

# Set path to SHETRAN exe's:
SHETRAN_exe_folder = root + "01_Software/SHETRAN/"

# Set the path to the master climate data folder:
climate_master_folder = root + "03_Climate_Data/"

climate_scenario = "Historical"  # "Historical" Historical or bcm_01/04/05/06/07/08/09/10/11/12/13/15


# --- PREAMBLE ---

exe_setup_csv = pd.read_csv(exe_setup_csv_path, index_col=0)

# Set a list of less stable simulations that will benefit from a decreased timesteps:
unstable_simulations = ["13008", "15021", "33007", "54005", "78003", "84005", "84013",
                        "43021", "53022", "27041", "53018", "71001", "64001", "84017",
                        "54005", "71001", "78003", "84005", "85001", "201006", "201007", "201009", "202001", "203012"]

# Set whether the catchment is in Northern Ireland:
NI = True if int(catchment) >= 200000 else False

# Set whether the catchment is run at 5km resolution:
low_res = exe_setup_csv.loc[int(catchment)]["run_at_5km"]

nfm_present = len([x for x in os.listdir(simulation_folder) if "NFM_storage" in x or "NFM_woodland" in x]) > 0

print(simulation_folder)

# --- FUNCTIONS ---

def visualisation_plan_remove_item(item_number, vis_file_in=str, vis_file_out=None):
    """
    Don't forget that if you use this is combination with the number altering that you need to match the altered number.
    If you are removing multiple items, remove the higher numbers first.
    item_number can be a string or integer.
    Do not specify file_out if you want to overwrite.
    """

    if vis_file_out == None:
        vis_file_out = vis_file_in

    with open(vis_file_in, 'r') as vis:
        updated_text = ""
        number_corrector = 0

        for line in vis:
            line = line.strip().split(" : ")

            # IF the line starts with item then skip ('item' will be written later)
            if line[0] == "item":
                continue

            # IF the line starts with NUMBER, decide whether to read or write:
            if line[0][0:len(line[0]) - 2] == "NUMBER":

                # IF it is the number of interest read the next line too, not writing either
                # and add one to the index corrector:
                if line[0][-1] == str(item_number):
                    next(vis)
                    number_corrector += 1

                # IF a different number:
                if line[0][-1] != str(item_number):
                    new_number = int(line[0][-1]) - number_corrector
                    line[0] = str(line[0][0:len(line[0]) - 1] + str(new_number))
                    updated_text = updated_text + 'item \n' + " : ".join(line) + "\n" + next(vis)

            # If neither, just copy the line:
            else:
                updated_text = updated_text + " : ".join(line) + "\n"

    with open(vis_file_out, "w") as new_vis:
        new_vis.write(updated_text)

    if new_number == 0:
        return "WARNING: No lines were edited"


def change_library_initial_conditions(library_filepath):
    # Note that could also be done using edit_xml_value() if desired.

    # Read file in read mode 'r'
    with open(library_filepath, 'r') as file:
        content = file.read()
    # Replace string
    content = content.replace("<InitialConditions>0</InitialConditions>",
                              "<InitialConditions>20</InitialConditions>")
    # Write new content in write mode 'w'
    with open(library_filepath, 'w') as file:
        file.write(content)

def edit_xml_value(filepath, variable, value):
    # Read file in read mode 'r'
    with open(filepath, 'r') as file:
        lines = file.readlines()

    # Run through the contents and overwrite the relevant line with the new content, else write the existing line:
    with open(filepath, 'w') as file:
        for line in lines:
            if line.startswith(f"<{variable}>"):
                file.writelines(f"<{variable}>{value}</{variable}>\n")
            else:
                file.writelines(line)


def change_frd_timestep(frd_file):

    # Read file in read mode 'r'
    with open(frd_file, 'r') as file:
        content = file.read()

    # Replace string in APM files:
    content = content.replace("0.5000 0.0500 9999.0 1.0000      T",
                              "0.2000 0.0200 99999. 0.5000      T")

    # Replace string in Autocal files:
    content = content.replace("0.5000 0.0500 99999. 1.0000      T",
                              "0.2000 0.0200 99999. 0.5000      T")

    # Write new content in write mode 'w'
    with open(frd_file, 'w') as file:
        file.write(content)


# --- COPY & UNZIP CLIMATE DATA ---
zip_files = os.listdir(os.path.join(climate_master_folder, climate_scenario))
zip_file = [f for f in zip_files if f.startswith(f"{catchment}_")][0]
with ZipFile(os.path.join(climate_master_folder, climate_scenario, zip_file), 'r') as zip_ref:
    print('Copying climate data...(Precip/PET/Temp/Cells)')
    zip_ref.extractall(simulation_folder)
with open(simulation_folder + 'readme.txt', 'w') as f:
    f.write('Climate Scenario: ' + climate_scenario)

# --- RUN PREPARATION EXECUTABLES ---

# - Prepare Land Cover Data -
# (This will convert the land covers & climate data to urban/non-urban)

if NI:  # Use the CEH data:
    print("EXE PATH = " + SHETRAN_exe_folder + "Shetran-setup-CEH2Types.exe")
    print("CATCHMENT PATH = ", simulation_folder + catchment)
    subprocess.call([SHETRAN_exe_folder + "Shetran-setup-CEH2Types.exe", simulation_folder + catchment])
    Library_File_name = "_LibraryFile_CEH-2Types.xml"

else:  # Use the UDM data:
    Library_File_name = "_LibraryFile_UDM.xml"

    if low_res:
        # Convert UDM to 5km and prepare the data:
        subprocess.call([SHETRAN_exe_folder + "1km-to-5km-udm.exe",
                         simulation_folder + catchment])

        subprocess.call([SHETRAN_exe_folder + "Shetran-setup-UDM-5km.exe",
                         simulation_folder + catchment])
    else:
        subprocess.call([SHETRAN_exe_folder + "Shetran-setup-UDM.exe",
                         simulation_folder + catchment])

# If using NFM on a 5km catchment, copy/backup the 1km and then resample to 5km:
if low_res and nfm_present:
    # Copy the 1km NFM data before you re-grid it to 5km:
    shutil.copy2(simulation_folder + catchment + "_NFM_storage.asc",
                 simulation_folder + catchment + "_NFM_storage-1km.asc")
    shutil.copy2(simulation_folder + catchment + "_NFM_woodland.asc",
                 simulation_folder + catchment + "_NFM_woodland-1km.asc")
    subprocess.call([SHETRAN_exe_folder + "1km-to-5km-storage-and-forest.exe",
                     simulation_folder + catchment])


# - Change Initial Conditions -
LibraryFile_path = os.path.join(simulation_folder, catchment + Library_File_name)

# Some simulations needed different initial conditions as they are too full and unstable:
if catchment in ["39016", "44002", "54027"]:
    change_library_initial_conditions(LibraryFile_path)


# - Prepare SHETRAN Inputs -

# Change the dates in the Library File if needed (the exe's above were made for the future climate simulations and
# do this automatically, so these need changing back if running historical simulations):
edit_xml_value(filepath=LibraryFile_path, variable="StartDay", value="1")
edit_xml_value(filepath=LibraryFile_path, variable="StartMonth", value="1")
edit_xml_value(filepath=LibraryFile_path, variable="StartYear", value="1980")
edit_xml_value(filepath=LibraryFile_path, variable="EndDay", value="1")
edit_xml_value(filepath=LibraryFile_path, variable="EndMonth", value="1")
edit_xml_value(filepath=LibraryFile_path, variable="EndYear", value="2011")

# Prepare using one of two exe's that set the strickler coefficient differently depending on which catchment is used.
strickler = exe_setup_csv.loc[int(catchment)]["prepare_exe"][-2:]
subprocess.call([f'{SHETRAN_exe_folder}shetran-prepare-snow-STR-R-{strickler}b.exe', LibraryFile_path])


# --- ADAPT SIMULATIONS IF DESIRED --

# - Less Stable Catchments -
# Some simulations needed shorter timesteps because they are less stable:
if catchment in unstable_simulations:
    change_frd_timestep(simulation_folder + "input_" + catchment + "_frd.txt")


#  - Reduce Output Volume -
#  Edit the Visualisation plan to remove outputs that you do not need to reduce the output file size.
# Item number must be listed in descending order!
for item in ["6", "5", "3", "2", "1"]:
    visualisation_plan_remove_item(item, f'{simulation_folder}input_{catchment}_visualisation_plan.txt')


# --- RUN SHETRAN ---
# Run the SHETRAN simulation:
subprocess.call([SHETRAN_exe_folder + 'Shetran.exe',  '-f ', f'{simulation_folder}rundata_{catchment}.txt'])

