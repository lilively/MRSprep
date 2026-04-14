from os import path, listdir
from pathlib import Path
from pandas import DataFrame
from datetime import datetime


"""Get parameters from SPAR files and export to Excel"""

def getParametersSPAR(sparFile, parameter):
    with open(sparFile, 'r') as f:
        for line in f.readlines():
            if line.startswith(parameter):
                val = line.split(' : ')[1].strip()
                return val
        return 'Not found' 
    

def parameters_spar_files(cases_folder, output_directory, parameterlist):

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
                for elem in parameterlist:
                    param_value = getParametersSPAR(file_path, elem)
                    parameter_dict['Filename'] = file
                    parameter_dict[elem] = param_value
                    print(f'    {elem}: {param_value}')
                file_counter += 1
                data.append(parameter_dict)
            except Exception as e:
                print(f"*** Skipping non-SPAR or unreadable file: {(file_path)} - {e}")
                if file not in failed_cases:
                    failed_cases[file] = []
                failed_cases[file].append({'filename': file, 'error': str(e)})
    df = DataFrame(data)
    df.to_excel(path.join(output_directory, 'SPAR_Parameters_Export.xlsx'), index=False)
    
    print(f'>>> Processed {file_counter} files. Writing export logs...')
    print(f'>>> Results saved to {path.join(output_directory, "SPAR_Parameters_Export.xlsx")}')

    if failed_cases:
        failed_cases_file = path.join(output_directory, "failed_SPAR_parameters.txt")
        with open(failed_cases_file, 'w', encoding='utf-8') as f:
            f.write(f"Failed SPAR/SDAT Cases Log - {datetime.now()}\n\n")
            for case, errors in failed_cases.items():
                f.write(f"Case: {case}\n")
                for error_info in errors:
                    f.write(f"    File: {error_info['filename']} - Error: {error_info['error']}\n")
                f.write("\n")
        print(f">>> Failed cases logged to {failed_cases_file}")

    print('>>> Processing complete.')

# Command line usage
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Retrieve SPAR parameters and export to Excel')
    parser.add_argument('--input', required=True, help='Path to the folder containing organized SPAR files')
    parser.add_argument('--parameterList', nargs='+', required=True, help='List of SPAR parameters to extract')
    parser.add_argument('--output', required=True, help='Path to the output directory')
    
    args = parser.parse_args()
    parameters_spar_files(args.input, args.output, args.parameterList)

# ### Non-command line usage example
# cases_folder= r"C:\Users\lilif\OneDrive\Desktop\Dropbox\Phd\Pipeline testing\Output SPAR\Spectroscopy\SE"
# output_directory = r"C:\Users\lilif\OneDrive\Desktop\Dropbox\Phd\Pipeline testing"

# parameterList = ['echo_time', 'scan_id', 'samples', 'synthesizer_frequency', 
#                 'repetition_time', 'nucleus', 'averages', 'ap_size', 'lr_size', 
#                 'cc_size', 'sample_frequency', 'ps_slice_orientation', 'scan_date']



# parameters_spar_files(cases_folder, output_directory, parameterList)
