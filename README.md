# MRS data processing pipeline

A collection of Python scripts for processing magnetic resonance spectroscopy (MRS) data.
 
## Citation
If you use this software in your research, please cite:







# Requirements
The pipeline is built using Python 3.8 and the necessary imports can be found at requirements.txt which can be installed by the following command
```bash
 pip install -r requirements.txt
```

# Supported data formats

The pipeline is built to handle both single voxel (SV) and multi voxel (MV) files and prompts the user to specify which type when required. Unprocessed raw data is stored in SPAR/SDAT, DICOM and MRUI format and processed data in xml format. 


**Raw data:**
- DICOM
- SPAR/SDAT
- MRUI
- JMRUI text file

**Processed data:**
- JMRUI text file
- JMRUIXML-SV
- JMRUIXML-MV
- Spectra Classifier matrix
 

# Preprocessing and organization

Both for DICOM and SPAR/SDAT data acquisition are stored in folders named according to the case IDs. The files within these folders may contain additional information in their filenames, where “Case_X” represents the unique identifier, “C” stand for short echo and “L” for long echo and “M” for water suppressed metabolite files and “W” water unsuppressed acquisitions.
This naming is not consistent for all files, and for many instances the echo time and the acquisition type can only be determined by opening the file in JMRUI and visually assessing the spectra or by checking the header parameters in the SPAR file.
## Original DICOM file structure
**Note:** Any deviation from this structure may require modifying the pipeline to ensure combability.
```
Data DICOM
 ┣ Case_1
 ┃ ┣ DICOM
 ┃ ┃ ┣ IM_0001
 ┃ ┃ ┣ PS_0002
 ┃ ┃ ┣ XX_0003
 ┃ ┃ ┗ XX_0004
 ┃ ┗ DICOMDIR
 ┗ Case_2
   ┣ DICOM
   ┃ ┣ IM_0001
   ┃ ┣ IM_0006
   ┃ ┣ PS_0002
   ┃ ┣ XX_0003
   ┃ ┗ XX_0004
   ┗ DICOMDIR 

```
## Organizing DICOM file structure
`org_dicom.py` 
This script identifies T1 weighted images and spectroscopy files and determines the type of spectroscopy files using the pydicom python package.
**Parameters:**
| Parameter | Description | Default |
|-----------|-------------|---------|
| `--input`  | Path to the folder containing DICOM cases | required |
| `--output` | Path to the directory for organized files | required |
| `--help` | Show help message |  | 

**Usage:**
```
python org_dicom.py --input [path] --output [path]
```
## Generated file structure
Detailed logs for processed and failed cases are generated as simple text files are generated for each run.
```
Organized DICOM
 ┣ Images
 ┃ ┣ Case_1-T1
 ┃ ┗ Case_2-T1
 ┣ Spectroscopy
 ┃ ┗ SE
 ┃   ┣ Case_1-SE
 ┃   ┗ Case_2-SE
 ┣ failed_DICOM_cases.txt
 ┗ processed_DICOM_cases.txt
```
## Converting DICOM files to mrui
DICOM spectroscopy files contain the unsuppressed water and suppressed acquisitions in the same file. Files need to be opened with JMRUI and saved as separate files. For SV files the first file is always the M and the second is the W.
## Original MRUI file structure
```
DATA SV MRUI
 ┣ Case_1-LE_0.mrui
 ┣ Case_1-LE_1.mrui
 ┣ Case_1-SE_0.mrui
 ┗ Case_1-SE_1.mrui
```
## Organizing MRUI files
`org_mrui.py`
Determine if mrui file is water or metabolite file from signal order and copies them to folders. 
**Parameters:**
| Parameter | Description | Default |
|-----------|-------------|---------|
| `--input`  | Path to the folder containing MRUI files | required |
| `--output` | Path to the directory for renamed files | required |
| `--help` | Show help message |  |

**Usage:**
```
python org_mrui.py --input [path] --output [path]
```
##  Organized MRUI file structure
```
Organized MRUI
 ┣ M
 ┃ ┣ Case_1-LE-M.mrui
 ┃ ┗ Case_1-SE-M.mrui
 ┣ W
 ┃ ┣ Case_1-LE-W.mrui
 ┃ ┗ Case_1-SE-W.mrui
 ┣ processed_cases.txt
 ┗failed_cases.txt
```
## Original SDAT/SPAR file structure
```
DATA SV SPAR
 ┣ Case_1
 ┃ ┣ Case_1-LE-M.SDAT
 ┃ ┣ Case_1-LE-M.SPAR
 ┃ ┣ Case_1-LE-W.SDAT
 ┃ ┣ Case_1-LE-W.SPAR
 ┃ ┣ Case_1-SE-M.SDAT
 ┃ ┣ Case_1-SE-M.SPAR
 ┃ ┣ Case_1-SE-W.SDAT
 ┃ ┗ Case_1-SE-W.SPAR
 ┗ Case_2
   ┣ Case_1-SE-M.SDAT
   ┣ Case_1-SE-M.SPAR
   ┣ Case_1-SE-W.SDAT
   ┣ Case_1-SE-W.SPAR
   ┣ Case_1-LE-M.SDAT
   ┣ Case_1-LE-M.SPAR
   ┣ Case_1-LE-W.SDAT
   ┗ Case_1-LE-W.SPAR
 ```
 ## Organizing SDAT/SPAR file structure
 `org_spar.py`  
This script determinates the type identifies spectroscopy files using the SPAR header information.
**Parameters:**
| Parameter | Description | Default |
|-----------|-------------|---------|
| `--input`  |Path to the folder containing SPAR/SDAT cases | required |
| `--output` | Path to the directory for organized files | required |
| `--help` | Show help message |  |

**Usage:**
```
python org_spar.py --input [path] --output [path]
```
 ### Organized SDAT/SPAR file structure
 ```
Organized SPAR
 ┣ Spectroscopy
 ┃ ┣ LE
 ┃ ┃ ┣ Case_1-LE-M.SDAT
 ┃ ┃ ┣ Case_1-LE-M.SPAR
 ┃ ┃ ┣ Case_1-LE-W.SDAT
 ┃ ┃ ┣ Case_1-LE-W.SPAR
 ┃ ┃ ┣ Case_2-LE-M.SDAT
 ┃ ┃ ┣ Case_2-LE-M.SPAR
 ┃ ┃ ┣ Case_2-LE-W.SDAT
 ┃ ┃ ┗ Case_2-LE-W.SPAR
 ┃ ┗ SE
 ┃   ┣ Case_1-SE-M.SDAT
 ┃   ┣ Case_1-SE-M.SPAR
 ┃   ┣ Case_1-SE-W.SDAT
 ┃   ┣ Case_1-SE-W.SPAR
 ┃   ┣ Case_2-SE-M.SDAT
 ┃   ┣ Case_2-SE-M.SPAR
 ┃   ┣ Case_2-SE-W.SDAT
 ┃   ┗ Case_2-SE-W.SPAR
 ┣ processed_SPAR_cases.txt
 ┗ failed_cases.txt
 ```
# Automated parameter retrieval
Acquisition parameters like echo time, magnetic field strength or repetition time can be retrieved from both the DICOM files and SPAR/SDAT files.
## Parameter retrieval from DICOM files
`parameters_dicom.py`
**Parameters**
| Parameter | Description | Default |
|-----------|-------------|---------|
| `--input` | Path to the folder containing the organized DICOM files | required |
| `--parameterList` | List of DICOM parameters to extract | required |
| `--output` | Path to the output directory | required |
| `--help` | Show help message | |

**Usage:**
```
python parameters_dicom.py --input [path] --parameterList [param1] [param2] ... [paramX] --output [path]
```
## Parameter retrieval from SPAR/SDAT files
`parameters_spar.py` 
**Parameters**
| Parameter | Description | Default |
|-----------|-------------|---------|
| `--input` | Path to the folder of the organized SPAR/SDAT files | required |
| `--parameterList` | List of DICOM parameters to extract | required |
| `--output` | Path to the output directory | required |
| `--help` | Show help message | |

**Usage:**
```
python parameters_spar.py --input [path] --parameterList [param1] [param2] ... [paramN] --output [path]
```
## Validate files
`validate_files.py` 
Compare the existence of various file types based on potential cases from excel.
**Parameters**
| Parameter | Description | Default |
|-----------|-------------|---------|
| `--cases` | Path to Excel file with potential cases | required |
| `--id-col` | Name of the ID column | required |
| `--echo` | Echo filter ('SE' or 'LE') | required |
| `--output` | Directory to save merged output | required |
| `--mrui` | Path to MRUI files folder | optional* |
| `--xml` | Path to XML files folder | optional* |
| `--dicom` | Path to DICOM files folder | optional* |
| `--spar` | Path to SPAR files folder | optional* |
| `--sheet` | Excel sheet name | Cases |
| `--help` | Show help message | |

*At least one data source folder (–mrui, –xml, –dicom, or –spar) should be provided
### Usage
```bash
python validate_files.py --cases [path] --id-col [column_name] --echo [SE/LE] --output [path] --mrui [path] --xml [path] --dicom [path] --spar [path]
```
**Note** *At least one data source folder (--mrui, --xml, --dicom, or --spar) should be provided
## Renaming files based on ID mapping
`rename_id.py`
This script renames files in a folder based on ID mappings provided in an Excel file.
**Parameters:**
| Parameter | Description | Default |
|-----------|-------------|---------|
| `--excel` | Path to Excel file with ID mapping | required |
| `--folder` | Path to the folder containing files to rename | required |
| `--original` | Original ID column name | required |
| `--new` | New ID column name | required |
| `--help` | Show help message | |

**Usage:**
```
python rename_id.py --excel [path] --original [column_name] --new [column_name] --folder [path]
```
## Replace old pattern with new pattern
`replace_pattern.py`
This script renames files in a directory by replacing a specified pattern in filenames.
**Parameters:**
| Parameter | Description | Required |
|-----------|-------------|----------|
| `directory` | Path to the directory containing files to rename | Yes |
| `--old_pattern` | Pattern to replace in filenames | Yes |
| `--new_pattern` | New pattern to use as replacement | Yes |

**Usage:**
```bash
python replace_pattern.py --directory [path] --old_pattern OLD --new_pattern NEW
```

# Postprocessing xml files:
## Label with information
`label_xml.py`
This script changes the TissueType element of the XML files based on IDs provided in an Excel file.
**Parameters:**
| Parameter | Description | Default |
|-----------|-------------|---------|
| `--xml_folder`  | Path to the folder containing the XML files|  required|
| `--label_excel`  | Path to the Excel file containing labels|  required|
| `--output`  | Path to the output directory|  required|
| `--id_col`  | Column name for IDs in XML files|  required|
| `--label_col`  |Column name for the new labels in the Excel file|  required|
| `--type`  | 'MV' for Multi-Voxel, leave empty for Single-Voxel|  optional|
| `--xcol`  | Column name for X coordinate (if type is MV)|  optional|
| `--ycol`  | Column name for Y coordinate (if type is MV)|  optional|

**Usage:**
```bash 
python label_xml.py --xml_folder [path] --label_excel [path] --id_col PatientID --label_col Diagnoses --output [path]
```
## Renormalize in range
`filter_renormalize.py`
This script filters and renormalizes XML files to a new ppm range.
**Parameters:**
| Parameter | Description | Default |
|-----------|-------------|---------|
| `--input`  | Path to the folder containing the XML files|  required|
| `--output`  | Path to the output directory|  required|
| `--ppm_range`  | New ppm range|  required|
| `--help`  | Show help message|  required|

**Usage:**
```bash 
python filter_renormalize.py --input [path] --output [path] --ppm_range [firstPPM lastPPM]
```
# Quality control
## Extract SNR from XML Files
`get_snr.py`
Retrieve SNR values from a directory of XML files and return as an Excel. 
**Parameters:**
| Parameter | Description | Default |
|-----------|-------------|---------|
| `--xml_directory` | Path to the directory containing XML files | required |
| `--output_directory` | Directory to save the output Excel file| required |
| `--output_filename` | Output Excel filename (without extension) | required |

**Usage**
```bash
python get_snr.py --xml_directory [path] --output_directory [path] --output_filename [path]
```
## Extract full width at half maximum (FWHM) from JMRUI files
`get_fwhm.py`
Retrieve FWHM values from HLSVDPRO files and matches them with signal names from raw files.
- <em>Raw file:</em> JMRUI text file containing signal names of the unsuppressed acquisitions.  
- <em>HLSVDPRO file:</em> JMRUI Text file results of quantification with HLSVDPRO for one component.

**Parameters:**
| Parameter | Description | Default |
|-----------|-------------|---------|
| `--hp_file` | Path to the HLSVDPRO file containing FWHM values | required |
| `--raw_file` | Path to the raw file containing signal names | required |
| `--parameter` | Parameter to extract from the HLSVDPRO file | required |
| `--output` | Path to the output folder to save results | required |
| `--outfilename` | Name of the output file (without extension) | required |

**Usage**
```bash
python get_fwhm.py --hp_file [path] --raw_file [path] --parameter [param_name] --output [path] --outfilename [filename]
```
## Create status based on SNR and FWHM values
`add_status.py`
Merge SNR and FWHM data with case files and add quality status based on specified criteria. Cases are “Selected” if FWHM<8Hz and SNR>10. 

**Parameters:**
| Parameter | Description | Default |
|-----------|-------------|---------|
| `--cases` | Path to the Excel file containing case data | required |
| `--data_id` | Column name for case IDs in the case data file | required |
| `--snr_path` | Path to the Excel file containing SNR data | required |
| `--snr_id` | Column name for case IDs in the SNR data file | required |
| `--fwhm_path` | Path to the Excel file containing FWHM data | optional |
| `--fwhm_id` | Column name for case IDs in the FWHM data file (required if fwhm_path is provided) | optional |
| `--output` | Directory to save the output Excel file | required |
| `--filename` |Name of the output Excel file (without extension) | required |

**Usage**

```bash
python add_status.py --cases [path] --data_id [column_name] --snr_path [path] --snr_id [column_name] --output [path] --filename [filename]
```
## Move or Copy Files Based on Status
`move_status.py`
Move or copy files to an output directory based on status labels specified in an Excel file. 
<em>- Copy mode:</em> Creates copies of files in the output directory, leaving originals in place 
<em>- Move mode:</em> Moves files to the output directory, removing them from the working folder

**Parameters:**
| Parameter | Description | Default |
|-----------|-------------|---------|
| `--excel_file` | Path to the Excel file containing file statuses | required |
| `--working_folder` | Path to the folder containing files to be moved or copied | required |
| `--output_directory` | Path to the output directory where files will be organized | required |
| `--id_col` | Column name for IDs in the Excel file | required |
| `--status_label` | The status label indicating which files to move or copy | required |
| `--mode` | Operation mode: 'move' or 'copy' | required|

**Usage**
```bash
python move_status.py --excel_file [path] --working_folder [path] --output_directory [path] --id_col [column_name] --status_label [status] --mode [move/copy]
```

# Visualization

## Combine Images from Multiple Directories
`display_images.py`
Create combined plots from images located in multiple input directories and saves them to an output directory.
**Parameters**
| Parameter | Description | Default |
|-----------|-------------|---------|
| `--output_directory` | Directory to save the combined images | required |
| `--filedir1` | First input directory containing images | required |
| `--filedir2` | Second input directory containing images | required |
| `--filedir3` | Optional third input directory containing images | optional |
| `--filedir4` | Optional fourth input directory containing images | optional |

**Usage**
```bash
python plot_directory.py --output_directory [path] --filedir1 [path] --filedir2 [path] --filedir3 [path] --filedir4 [path]
```
## Create a PowerPoint presentation from images from a directory
`ppt_create.py`
This script creates a PowerPoint presentation from images in a specified directory, adding each image to a new slide with optional titles.
**Parameters:**
| Parameter | Description | Default |
|-----------|-------------|---------|
|--directory	-|Directory containing image files|required
|--output	|Directory to save the PowerPoint presentation|required
|--ppt_name	|Name of the output presentation|required
|--title	|Filename as title for each slide (without extension)|optional
|--help	|Show help message|

**Usage:**
```bash
python ppt_create.py --directory [path] --output [path] --ppt_name [filename]—tilte [True]
```
# Analysis
## Concatenate SpectraClassifier datasets
`concat_data.py`
This script identifies common cases from short and long echo Spectra Classifier files and removes the non-common cases. The new datasets can be concatenated in the analysis step. 
**Parameters:**

| Parameter | Description | Default |
|-----------|-------------|---------|
| --xml1 | Path to the first XML file | required |
| --xml2 | Path to the second XML file | required |
| --output | Output directory for processed XML files | required |
| --help | Show help message | |

**Usage:**
```bash
python concatenate_data.py --xml1 [path] --xml2 [path] --output [path] 
```
