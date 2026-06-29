from os import path, listdir, makedirs
from pathlib import Path
from shutil import copy2
from datetime import datetime

"""Organize SPAR files into structured folders based on metadata."""



def getParametersSPAR(sparFile, parameter):
    """ Extracts the value of a specified parameter from a SPAR file. """

    with open(sparFile, 'r') as f:
        value=[]
        for line in f.readlines():
            if line.startswith(parameter):
                val = (line.split(' : ')[1])
                val = val.split('\n')[0]
                value.append(str(val))
                #print(val)
                break
            else:
                val = 'missing'
                value.append(val)
    return value[-1]

def analyze_se_le_files(folder, se_files, le_files):
    """
    Analyzes SE files with each other and LE files with each other.
    Creates nested dictionaries with file stats for easy comparison.
    """

    def get_file_stats_dict(folder, file_list, file_type):
        """Create a nested dictionary of file statistics indexed by filename."""
        stats = {}

        for idx, (spar_file, sdat_file) in enumerate(file_list, start=1):
            stem = Path(spar_file).stem
            #print(f'      Analyzing {stem}')

            try:
                avg = float(getParametersSPAR(spar_file, 'averages') or 0)
                mix = float(getParametersSPAR(spar_file, 'mix_number') or 0)
                filename = str(stem).upper()
                #print(f'        Filename for acq mode check: {filename}')

                # Determine acquisition mode
                if 'ACT' in filename:
                    acq_mode = 'ACT'
                elif 'REF' in filename:
                    acq_mode = 'REF'
                elif 'M' in filename or '-M' in filename:
                    acq_mode = 'M'
                elif 'W' in filename or '-W' in filename:
                    acq_mode = 'W'
                else:
                    acq_mode = 'UNKNOWN'

                # Create entry with file number as key
                file_key = f'File_{idx}'
                stats[file_key] = {
                    'filename': stem,
                    'averages': avg,
                    'mix_number': mix,
                    'filename_parameter': acq_mode
                }

                # print(f'        Averages: {avg}')
                # print(f'        Mix number: {mix}')
                # print(f'        Acquisition mode: {acq_mode}')

            except ValueError as e:
                print(f'        Error parsing {stem}: {e}')
                stats[file_key] = {'error': 'parsing_error'}
                continue

        return stats

    se_stats = get_file_stats_dict(folder, se_files, 'SE')
    le_stats = get_file_stats_dict(folder, le_files, 'LE')

    analysis = {
        'SE': se_stats,
        'LE': le_stats,
    }

    return analysis


def assign_file_types(file_stats_dict, group_name):
    """
    Assign W and M types to individual files in a group.
    Compares File_1 and File_2 averages:
    - File with smaller averages → W (Water)
    - File with larger averages → M (Metabolite)
    - If averages are equal, use filename_parameter to determine type
    - If only one file exists, assign based on that file's parameter
    
    Returns:
        dict with file information and assigned types
    """
    typed_files = {}
    files_list = list(file_stats_dict.items())
    
    print(f"\n   Assigning types for {group_name} Files:")
    
    # If we have 2 or more files, compare File_1 and File_2 averages
    if len(files_list) >= 2:
        file_1_key, file_1_data = files_list[0]
        file_2_key, file_2_data = files_list[1]
        
        avg_1 = file_1_data['averages']
        avg_2 = file_2_data['averages']
        
        print(f"   Comparing averages: {file_1_key}={avg_1} vs {file_2_key}={avg_2}")
        
        if avg_1 < avg_2:
            # File_1 has smaller averages -> File_1 is W, File_2 is M
            typed_files[file_1_key] = {
                'filename': file_1_data['filename'],
                'averages': file_1_data['averages'],
                'mix_number': file_1_data['mix_number'],
                'filename_parameter': file_1_data['filename_parameter'],
                'type': 'W',
                'reason': f"Smaller averages ({avg_1} < {avg_2}) → Water"
            }
            typed_files[file_2_key] = {
                'filename': file_2_data['filename'],
                'averages': file_2_data['averages'],
                'mix_number': file_2_data['mix_number'],
                'filename_parameter': file_2_data['filename_parameter'],
                'type': 'M',
                'reason': f"Larger averages ({avg_2} > {avg_1}) → Metabolite"
            }
        elif avg_2 < avg_1:
            # File_2 has smaller averages -> File_2 is W, File_1 is M
            typed_files[file_1_key] = {
                'filename': file_1_data['filename'],
                'averages': file_1_data['averages'],
                'mix_number': file_1_data['mix_number'],
                'filename_parameter': file_1_data['filename_parameter'],
                'type': 'M',
                'reason': f"Larger averages ({avg_1} > {avg_2}) → Metabolite"
            }
            typed_files[file_2_key] = {
                'filename': file_2_data['filename'],
                'averages': file_2_data['averages'],
                'mix_number': file_2_data['mix_number'],
                'filename_parameter': file_2_data['filename_parameter'],
                'type': 'W',
                'reason': f"Smaller averages ({avg_2} < {avg_1}) → Water"
            }
        else:
            # Averages are equal, use filename_parameter to determine type
            print(f"   Averages are equal, using filename parameters")
            for file_key, file_data in file_stats_dict.items():
                param = file_data['filename_parameter']
                if param in ['W', 'REF']:
                    file_type = 'W'
                    reason = f"Averages equal, Parameter {param} → Water"
                elif param in ['M', 'ACT']:
                    file_type = 'M'
                    reason = f"Averages equal, Parameter {param} → Metabolite"
                else:
                    file_type = 'UNKNOWN'
                    reason = f"Averages equal, Unknown parameter: {param}"
                
                typed_files[file_key] = {
                    'filename': file_data['filename'],
                    'averages': file_data['averages'],
                    'mix_number': file_data['mix_number'],
                    'filename_parameter': param,
                    'type': file_type,
                    'reason': reason
                }
    else:
        # Only one file, assign based on filename_parameter
        for file_key, file_data in file_stats_dict.items():
            param = file_data['filename_parameter']
            if param in ['W', 'ref']:
                file_type = 'W'
                reason = f"Single file, Parameter {param} → Water"
            elif param in ['M', 'ACT']:
                file_type = 'M'
                reason = f"Single file, Parameter {param} → Metabolite"
            else:
                file_type = 'UNKNOWN'
                reason = f"Single file, Unknown parameter: {param}"
            
            typed_files[file_key] = {
                'filename': file_data['filename'],
                'averages': file_data['averages'],
                'mix_number': file_data['mix_number'],
                'filename_parameter': param,
                'type': file_type,
                'reason': reason
            }
    print(f"   Assigned types: ")
    for file_key, file_info in typed_files.items():
        print(f"   {file_key}: {file_info['filename']} → Type {file_info['type']}")
    return typed_files

def organize_spar_files(cases_folder, output_directory):
    # Create main output folders
    spectroscopy_folder = path.join(output_directory, 'Spectroscopy')
    image_folder = path.join(output_directory, 'Images')
    makedirs(spectroscopy_folder, exist_ok=True)

    #Image subfolder
    image_folder_created = set()

    #Echo subfolder
    echo_folders_created = set()
    failed_cases = {} 
    processed_cases = {} 
    file_counter = 1
    
    # Process each case folder
    for case_id in listdir(cases_folder):
        folder_path = path.join(cases_folder, case_id)
        print(f'Parsing folder: {folder_path}')
        if path.isdir(folder_path):
            spar_files = list(Path(folder_path).rglob("*.SPAR*"))
            sdat_files = list(Path(folder_path).rglob("*.SDAT*"))
            
            if len(spar_files) != len(sdat_files):
                print(f"Warning: {len(spar_files)} SPAR files but {len(sdat_files)} SDAT files")
                if folder_path not in failed_cases:
                    failed_cases[folder_path] = []
                failed_cases[folder_path].append({
                    'filename': 'Mismatch',
                    'error': f"Count mismatch: {len(spar_files)} SPAR vs {len(sdat_files)} SDAT files"
                })
            
            
            se_files = []
            le_files = []

            if not spar_files:
                if folder_path not in failed_cases:
                    failed_cases[folder_path] = []
                failed_cases[folder_path].append({
                    'filename': 'N/A (no files found)',
                    'error': "No .SPAR files found."
                })
                continue

            """ Parsing SPAR files """
            for spar_file, sdat_file in zip(spar_files, sdat_files):
                file_counter += len(spar_files)
                file_name = Path(spar_file).stem
                file_ending = Path(spar_file).suffix

                try:
                    echo_time = float(getParametersSPAR(spar_file, 'echo_time') or 0)
                except ValueError:
                    print(f"Error parsing parameters for {file_name}. Skipping...")
                    if folder_path not in failed_cases:
                        failed_cases[folder_path] = []
                    failed_cases[folder_path].append({
                        'filename': f"{file_name}{file_ending}",
                        'error': "Error parsing echo_time parameter."
                    })
                    continue

                suffix_echo = "SE" if echo_time and echo_time < 50 else "LE" if echo_time else "XX"

                if suffix_echo == "SE":
                    se_files.append((spar_file, sdat_file))
                elif suffix_echo == "LE":
                    le_files.append((spar_file, sdat_file))

            print(f'   Found {len(se_files)} SE files and {len(le_files)} LE files.')
            
            # Create echo-specific subfolder only when needed
            if se_files:
                echo_subfolder_se = path.join(spectroscopy_folder, 'SE')
                if 'SE' not in echo_folders_created:
                    makedirs(echo_subfolder_se, exist_ok=True)
                    echo_folders_created.add('SE')
            
            if le_files:
                echo_subfolder_le = path.join(spectroscopy_folder, 'LE')
                if 'LE' not in echo_folders_created:
                    makedirs(echo_subfolder_le, exist_ok=True)
                    echo_folders_created.add('LE')

            try:
                analysis = analyze_se_le_files(folder_path, se_files, le_files)
                
                # Assign types to SE files
                if analysis['SE']:
                    se_types = assign_file_types(analysis['SE'], 'SE')
                    # Initialize folder entry if it doesn't exist
                    if folder_path not in processed_cases:
                        processed_cases[folder_path] = []
                    
                    for file_key, file_info in se_types.items():
                    
                        processed_cases[folder_path].append({
                            'filename': file_info['filename'],
                            'type': file_info['type'],
                            'reason': file_info['reason'],
                            'echo_type': 'SE',
                            'averages': file_info['averages']
                        })

                        spar_source = path.join(folder_path, file_info['filename'] + ".SPAR")
                        sdat_source = path.join(folder_path, file_info['filename'] + ".SDAT")
                        
                        # Check both files exist before copying
                        if not path.exists(spar_source) or not path.exists(sdat_source):
                            print(f"Skipping {file_info['filename']}: Missing SPAR or SDAT file")
                            if folder_path not in failed_cases:
                                failed_cases[folder_path] = []
                            failed_cases[folder_path].append({
                                'filename': file_info['filename'],
                                'error': "Missing SPAR or SDAT file during copy"
                            })
                            continue
                        
                        try:
                            new_name = f"{case_id}-SE-{file_info['type']}"
                            new_spar_path = path.join(echo_subfolder_se, f"{new_name}.SPAR")
                            new_sdat_path = path.join(echo_subfolder_se, f"{new_name}.SDAT")
                            
                            # Copy files
                            copy2(spar_source, new_spar_path)
                            copy2(sdat_source, new_sdat_path)
                        except Exception as e:
                            print(f"Error copying SE files for {file_info['filename']}: {str(e)}")
                            if folder_path not in failed_cases:
                                failed_cases[folder_path] = []
                            failed_cases[folder_path].append({
                                'filename': file_info['filename'],
                                'error': f"Copy error: {str(e)}"
                            })
                            continue

                else:
                    print(f"\nNo SE files to assign types")
                    if folder_path not in failed_cases:
                        failed_cases[folder_path] = []
                    failed_cases[folder_path].append({
                        'filename': 'Missing',
                        'error': "No SE files to assign types."
                    })

                # Assign types to LE files
                if analysis['LE']:
                    le_types = assign_file_types(analysis['LE'], 'LE')
                    # Initialize folder entry if it doesn't exist
                    if folder_path not in processed_cases:
                        processed_cases[folder_path] = []
                    
                    for file_key, file_info in le_types.items():
                        
                        processed_cases[folder_path].append({
                            'filename': file_info['filename'],
                            'type': file_info['type'],
                            'reason': file_info['reason'],
                            'echo_type': 'LE',
                            'averages': file_info['averages']
                        })
                        
                        # Define source paths for LE files
                        spar_source = path.join(folder_path, file_info['filename'] + ".SPAR")
                        sdat_source = path.join(folder_path, file_info['filename'] + ".SDAT")
                        
                        # Check both files exist before copying
                        if not path.exists(spar_source) or not path.exists(sdat_source):
                            print(f"Skipping {file_info['filename']}: Missing SPAR or SDAT file")
                            if folder_path not in failed_cases:
                                failed_cases[folder_path] = []
                            failed_cases[folder_path].append({
                                'filename': file_info['filename'],
                                'error': "Missing SPAR or SDAT file during copy"
                            })
                            continue
                        
                        try:
                            new_name = f"{case_id}-LE-{file_info['type']}"
                            #print(f"   New filename: {new_name}")
                            new_spar_path = path.join(echo_subfolder_le, f"{new_name}.SPAR")
                            new_sdat_path = path.join(echo_subfolder_le, f"{new_name}.SDAT")
                            
                            # Copy files
                            copy2(spar_source, new_spar_path)
                            copy2(sdat_source, new_sdat_path)
                        except Exception as e:
                            print(f"Error copying LE files for {file_info['filename']}: {str(e)}")
                            if folder_path not in failed_cases:
                                failed_cases[folder_path] = []
                            failed_cases[folder_path].append({
                                'filename': file_info['filename'],
                                'error': f"Copy error: {str(e)}"
                            })
                            continue
                else:
                    if folder_path not in failed_cases:
                        failed_cases[folder_path] = []
                    failed_cases[folder_path].append({
                        'filename': 'Missing',
                        'error': "No LE files to assign types."
                    })
                    print(f"\nNo LE files to assign types")
                            
            except ValueError as e:
                print(f"Error parsing parameters. Skipping folder...")
                if folder_path not in failed_cases:
                    failed_cases[folder_path] = []
                failed_cases[folder_path].append({
                    'filename': 'Analysis',
                    'error': f"Error during analysis: {str(e)}"
                })
                continue

    print(f'\n>>> Processed {file_counter} files. Writing export logs...')

    # Write processed cases to a log file - organized by folder
    if processed_cases:
        processed_cases_file = path.join(output_directory, "processed_SPAR_cases.txt")
        with open(processed_cases_file, 'w', encoding='utf-8') as f:
            f.write(f"Processed SPAR/SDAT Cases Log - {datetime.now()}\n\n")
            
            # Write organized by folder
            for folder_idx, (folder_path, files) in enumerate(processed_cases.items(), start=1):
                f.write(f"{folder_idx}. {folder_path}\n")
                for file_info in files:
                    f.write(f"      File name: {file_info['filename']}\n")
                    f.write(f"      Echo Type: {file_info['echo_type']}\n")
                    f.write(f"      Assigned Type: {file_info['type']}\n")
                    f.write(f"      Averages: {file_info['averages']}\n")
                    f.write(f"      Reason: {file_info['reason']}\n\n")
                f.write("\n")
        
        print(f">>> Processed cases logged to {processed_cases_file}")
    
    # Write failed cases to a log file
    if failed_cases:
        failed_cases_file = path.join(output_directory, "failed_SPAR_cases.txt")
        with open(failed_cases_file, 'w', encoding='utf-8') as f:
            f.write(f"Failed SPAR/SDAT Cases Log - {datetime.now()}\n\n")
            for folder_idx, (folder_path, failures) in enumerate(failed_cases.items(), start=1):
                f.write(f"{folder_idx}. {folder_path}\n")
                for failure in failures:
                    f.write(f"      File name: {failure['filename']}\n")
                    f.write(f"      Error: {failure['error']}\n\n")
                f.write("\n")
        print(f">>> Failed cases logged to {failed_cases_file}")
    
    print('>>> Processing complete. <<<')







if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Organize SPAR/SDAT files into folders')
    parser.add_argument('--input', required=True, help='Path to the folder containing case SPAR/SDAT files')
    parser.add_argument('--output', required=True, help='Path to the output directory')
    
    args = parser.parse_args()
    organize_spar_files(args.input, args.output)



# ### Non-command line usage example
# cases_folder = r"C:\Users\lilif\OneDrive\Desktop\Dropbox\Phd\Pipeline testing\DATA SV SPAR"
# output_directory = r"C:\Users\lilif\OneDrive\Desktop\Dropbox\Phd\Pipeline testing\Output SPAR"
# #cases_folder = r"C:\Users\lilif\OneDrive\Desktop\Dropbox\Phd\DATA_SV\Glioblastoma\Raw data (spar, dicom)\SV_MGMT_SPAR"
# organize_spar_files(cases_folder, output_directory)