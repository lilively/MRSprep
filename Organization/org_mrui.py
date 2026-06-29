from datetime import datetime
from os import path, listdir, makedirs
from pathlib import Path
from re import sub
from shutil import copy2


def type_mrui(cases_folder, output_directory):
    """
    Function to organize MRUI files by type (Metabolite or Water) based on filename suffix.
    """
    type_folders_created = set()
    failed_cases = {} 
    processed_cases = {} 
    file_counter = 0
    type_map = {'0': 'M', '1': 'W'}
    
    # Process files in folder
    for file in listdir(cases_folder):
        file_path = path.join(cases_folder, file)
        print(f'>>> Processing {Path(file_path).stem}')
        
        # Determine file type (Metabolite or Water)
        suffix = Path(file_path).stem.split('E_')[-1]
        print(f"    Extracted suffix: {suffix}")
        
        # Check if suffix is valid BEFORE using it
        if suffix not in ['0', '1']:
            print(f"    Skipping {file_path}, unrecognized suffix '{suffix}'")
            failed_cases[file] = f'Unrecognized suffix: {suffix}'
            continue
        
        scan_type = type_map[suffix]
        
        # Construct new filename
        p = Path(file_path)
        print(f"    Original filename: {p.name}")
        
        # Replace _0 or _1 at the end of the stem
        new_stem = sub(r'_1$', '-W', p.stem)
        new_stem = sub(r'_0$', '-M', new_stem)
        new_filename = f"{new_stem}{p.suffix}"
        print(f"    Renaming to {new_filename}")
        
        # Create type subfolder if needed
        type_subfolder = path.join(output_directory, scan_type)
        if scan_type not in type_folders_created:
            makedirs(type_subfolder, exist_ok=True)
            type_folders_created.add(scan_type)
        
        # Copy file
        try:
            new_path = path.join(type_subfolder, new_filename)
            copy2(file_path, new_path)
            processed_cases[file] = new_filename
            file_counter += 1
        except Exception as e:
            print(f"    Failed to copy {file_path}: {e}")
            failed_cases[file] = str(e)

    print(f'>>> Processed {file_counter} files. Writing export logs...')

    if processed_cases:
        with open(path.join(output_directory, 'processed_cases.txt'), 'w') as f:
            f.write(f"Processed MRUI Cases Log - {datetime.now()}\n\n")
            f.write(f"Original filename     Renamed filename\n")
            for i, (case, reason) in enumerate(processed_cases.items(), 1):
                f
                f.write(f"{i}.{case}    {reason}\n")
        
    else:
        print(">>> No succesful cases to log.")
    
    if failed_cases:
        with open(path.join(output_directory, 'failed_cases.txt'), 'w') as f:
            f.write(f"Failed MRUI Cases Log - {datetime.now()}\n\n")
            for i, (case, new_name) in enumerate(failed_cases.items(), 1):
                f.write(f"{i}.{case} -> {new_name}\n")
    else:
        print(">>> No failed cases to log.")
    
    print('>>> Processing complete.')

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Organize MRUI files into folders')
    parser.add_argument('--input', required=True, help='Path to the folder containing case MRUI files')
    parser.add_argument('--output', required=True, help='Path to the output directory')
    
    args = parser.parse_args()
    type_mrui(args.input, args.output) 


# # ### Non-command line usage example
# cases_folder= r"C:\Users\lilif\OneDrive\Desktop\Dropbox\Phd\Pipeline testing\DATA SV MRUI"
# output_directory = r"C:\Users\lilif\OneDrive\Desktop\Dropbox\Phd\Pipeline testing\Output MRUI"
# type_mrui(cases_folder, output_directory)
