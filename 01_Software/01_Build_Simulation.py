# Collate SHETRAN Inputs for Model Publishing - Model Setup
# 30/10/2023
# Ben Smith

# This script takes the model data and re-formats them into model setups. This essentially just extracts the
# necessary model inputs and copies them to a new location with the correct names.

# --- USER INPUTS ---

# > Choose a catchment to run (listed in Software/SHETRAN_exe_list.csv)
catchment = '1001'  # (String)

# > Choose which NFM scenario and adaptation measures you wish to use: ([0] / [1] / [2])
NFM = ["NoNFM", "balanced", "max"][0]  # No NFM adaptation is available for Northern Ireland.
NFM_woodland = True  # True/False
NFM_storage = True  # True/False

# > Choose which UDM scenario/year you wish to use: ([0] / [1] / [2] / [3] / [4])
UDM_path = ["UDM_2017",  # If a Northern Ireland catchment is chosen, this will automatically use CEH data.
            "UDM_SSP2_2050", "UDM_SSP2_2080",
            "UDM_SSP4_2050", "UDM_SSP4_2080"][0]

# Se the path to the inputs (probably the folder above this one):
input_path = "I:/SHETRAN_GB_2021/10_Deliverables/05_SHETRAN_Simulation_Inputs/02_Catchment_Inputs/"

# Set the path for the folder where you want to run/setup the simulation:
destination_path = f"I:/SHETRAN_GB_2021/10_Deliverables/05_SHETRAN_Simulation_Inputs/04_Example_Simulations/{catchment}_{NFM}_{UDM_path}/"

# --- PREAMBLE ---
import os
import shutil

# Make a directory for the simulation files
if not os.path.exists(destination_path):
    os.mkdir(destination_path)

# Create the specific catchment data source folder:
catchment_inputs = f"{input_path}{catchment}/"

# --- CHECKS ---
print(destination_path)

if NFM == 'NoNFM' and (NFM_woodland or NFM_storage):
    print("NFM is set to 'NoNFM', but 'NFM_storage' or 'NFM_woodland' are set to 'True'. "
          "No NFM adaptation will be applied.")

if int(catchment) >= 200000 and NFM != "NoNFM":
    print("NFM adaptation is not available for Northern Ireland. No NFM adaptation will be applied. Change folder name.")

if int(catchment) >= 200000 and UDM_path != "UDM_2017":
    print("Future UDM scenarios are not available for Northern Ireland. No UDM change will be applied. Change folder name.")

# --- COPY FILES ---

# Base Files:
print("Building base files...")
files_to_copy = ["_DEM.asc", "_Lake.asc", "_MinDEM.asc", "_Mask.asc"]
for file in files_to_copy:
    shutil.copy2(os.path.join(catchment_inputs, catchment + file),
                 os.path.join(destination_path, catchment + file))

# Library Files:
print("Building library files...")
shutil.copy(os.path.join(catchment_inputs, catchment + '_LibraryFile.xml'),
            os.path.join(destination_path, catchment + '_LibraryFile.xml'))

catchment_files = os.listdir(catchment_inputs)
autocalibration_library_file = [f for f in catchment_files if '_autocal_LibraryFile' in f][0]
shutil.copy(os.path.join(catchment_inputs, autocalibration_library_file),
            os.path.join(destination_path, autocalibration_library_file.split("_")[-1]))

shutil.copy(os.path.join(catchment_inputs, catchment + '_results.csv'),
            os.path.join(destination_path, 'results.csv'))

# Land Cover:
print("Building land cover files...")
if int(catchment) >= 200000:
    # Copy Northern Ireland land cover, taken from CEH:
    shutil.copy(os.path.join(catchment_inputs, catchment + '_LandCover_CEH.asc'),
                os.path.join(destination_path, catchment + '_LandCover.asc'))

else:
    # Copy the GB land cover, taken from MasterMap and UDM:
    shutil.copy(os.path.join(catchment_inputs, f'{catchment}_LandCover_{UDM_path}.asc'),
                os.path.join(destination_path, f'{catchment}_landCover_UDM.asc'))

# NFM Adaptations:
print("Building NFM adaptation files...")
if int(catchment) <= 200000 and NFM != 'NoNFM':
    # (Only available for Great Britain)
    if NFM_woodland:
        shutil.copy(os.path.join(catchment_inputs, f'{catchment}_NFM_woodland_{NFM}.asc'),
                    os.path.join(destination_path, catchment + '_NFM_woodland.asc'))
    if NFM_storage:
        shutil.copy(os.path.join(catchment_inputs, f'{catchment}_NFM_storage_{NFM}.asc'),
                    os.path.join(destination_path, catchment + '_NFM_storage.asc'))

# --- NOTES ---
# This script should now have copied the necessary files for you to run a simulation bar climate files.
# The Library Files point the files that will be used, but some of these values (the land covers and dates) will
# be automatically changed by the UDM executables that will be applied later, during the run process.

