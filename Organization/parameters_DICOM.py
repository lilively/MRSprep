from os import path, listdir
from pydicom import dcmread
from pathlib import Path
from pandas import DataFrame
from datetime import datetime

"""Get parameters from DICOM files and export to Excel"""


def getSingleParameterDICOM(ds, parameter):
    def search_recursive(dataset):
        for element in dataset:
            if element.name == parameter:
                return element.value
            # If this element is a sequence, search inside it
            if element.VR == 'SQ':
                for item in element.value:
                    result = search_recursive(item)
                    if result is not None:
                        return result
        return None
    
    result = search_recursive(ds)
    return result if result is not None else 'Not found in DICOM'

    


def parameters_dicom_files(cases_folder, output_directory, parameterlist):

    #Echo subfolder

    failed_cases = {} 
    processed_cases = {} 
    file_counter = 0
    data = []

    # Process files in this case
    for file in listdir(cases_folder):
        file_path = path.join(cases_folder, file)
        print(f'>>> Processing {Path(file_path).stem}')

        if path.isfile(file_path):
            try:
                parameter_dict = {}
                ds = dcmread(file_path, force=True)
                for elem in parameterlist:
                    param_value = getSingleParameterDICOM(ds, elem)
                    
                    parameter_dict['Filename'] = file
                    parameter_dict[elem] = param_value
                    print(f'    {elem}: {param_value}')
                data.append(parameter_dict)
                file_counter += 1
            except (errors.InvalidDicomError, FileNotFoundError, PermissionError) as e:
                print(f"*** Skipping non-DICOM or unreadable file: {Path(file_path).stem} - {e}")
                if file not in failed_cases:
                    failed_cases[file] = []
                failed_cases[file].append({
                    'filename': file,
                    'error': str(e)
                })
                continue                
            except Exception as e:
                print(f"*** Error processing {file_path}: {e}")
                if file not in failed_cases:
                    failed_cases[file] = []
                failed_cases[file].append({
                    'filename': file,
                    'error': str(e)
                })
            df =DataFrame(data)
            df.to_excel(path.join(output_directory, 'DICOM_Parameters_Export.xlsx'), index=False)
    print(f'>>> Processed {file_counter} files. Writing export logs...')
    print(f'>>> Results saved to {path.join(output_directory, "DICOM_Parameters_Export.xlsx")}')

    if failed_cases:
        failed_cases_file = path.join(output_directory, "failed_DICOM_parameters.txt")
        with open(failed_cases_file, 'w', encoding='utf-8') as f:
            f.write(f"Failed DICOM Cases Log - {datetime.now()}\n\n")
            for case, errors in failed_cases.items():
                f.write(f"Case: {case}\n")
                for error_info in errors:
                    f.write(f"    File: {error_info['filename']} - Error: {error_info['error']}\n")
                f.write("\n")
        print(f">>> Failed cases logged to {failed_cases_file}")

    print('>>> Processing complete.')

# Command line usage example
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Retrieve DICOM parameters and export to Excel')
    parser.add_argument('--input', required=True, help='Path to the folder containing the organized DICOM files')
    parser.add_argument('--parameterList', nargs='+', required=True, help='List of DICOM parameters to extract')
    parser.add_argument('--output', required=True, help='Path to the output directory')
    
    args = parser.parse_args()
    parameters_dicom_files(args.input, args.output, args.parameterList)

# ### Non-command line usage example
# cases_folder= r"C:\Users\lilif\OneDrive\Desktop\Dropbox\Phd\Pipeline testing\Organized DICOMs MV\Spectroscopy\SE"
# output_directory = r"C:\Users\lilif\OneDrive\Desktop\Dropbox\Phd\Pipeline testing"

# parameterList = ['Manufacturer', '''Manufacturer's Model Name''','Study Date','Effective Echo Time',
#                  'Magnetic Field Strength', 'Transmitter Frequency', 'Repetition Time', 
#                  'Spectral Width', '''Patient's Age''', '''Patient's Sex''',  'Protocol Name']
#parameters_dicom_files(cases_folder, output_directory, parameterList)
