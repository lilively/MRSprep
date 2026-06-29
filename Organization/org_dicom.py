from datetime import datetime
from os import path, listdir, makedirs
from shutil import copy, copy2
from pydicom import dcmread, errors
from pathlib import Path
from typing import Tuple, Optional

"""Organize DICOM files into structured folders based on metadata."""


def get_dicom_file_attributes(dicom_file_path: str) -> dict:
    """
    Extract relevant DICOM attributes from a file.
    """
    try:
        ds = dcmread(dicom_file_path, force=True)
    except (errors.InvalidDicomError, FileNotFoundError, PermissionError) as e:
        raise Exception(f"Cannot read DICOM file: {e}")
    
    modality = getattr(ds, 'Modality', 'Unknown')
    image_type = getattr(ds, 'ImageType', [])
    pulse_sequence_name = getattr(ds, 'PulseSequenceName', '')
    series_description = getattr(ds, 'SeriesDescription', '')
    acquisition_contrast = getattr(ds, 'AcquisitionContrast', '')
    protocol_name = getattr(ds, 'ProtocolName', '')
    
    # Normalize image_type to string
    if isinstance(image_type, list):
        image_type_str = ' '.join(str(item).upper() for item in image_type)
    else:
        image_type_str = str(image_type).upper()
    
    return {
        'modality': modality,
        'image_type': image_type_str,
        'pulse_sequence_name': pulse_sequence_name,
        'series_description': series_description.upper(),
        'acquisition_contrast': acquisition_contrast,
        'protocol_name': protocol_name,
        'dicom_dataset': ds
    }


def get_echo_suffix(echo_time: Optional[float]) -> str:
    """
    Determine echo time suffix based on echo time value.
    """
    if echo_time and echo_time < 50:
        return "SE"
    elif echo_time:
        return "LE"
    else:
        return "XX"


def determine_file_type(dicom_attributes: dict) -> Tuple[str, Optional[str]]:
    """
    Determine the file type based on DICOM attributes.
    """
    pulse_sequence_name = dicom_attributes['pulse_sequence_name']
    acquisition_contrast = dicom_attributes['acquisition_contrast']
    image_type_str = dicom_attributes['image_type']
    series_description = dicom_attributes['series_description']
    protocol_name = dicom_attributes['protocol_name']
    
    # Check for spectroscopy
    if (pulse_sequence_name == 'SPECTROSCOPY' and 
        acquisition_contrast == 'SPECTROSCOPY'):
        
        if not protocol_name or protocol_name in ["missing", "NaN"]:
            return "Spectroscopy", "Missing ProtocolName for echo time extraction."
        
        return "Spectroscopy", None
    
    # Check for T1-weighted image
    if 'T1' in image_type_str or 'T1' in series_description:
        return "T1-weighted Image", None
    
    # Unknown file type
    return "Unknown", "Not spectroscopy or T1-weighted image."


def get_echo_time(dicom_dataset) -> Optional[float]:
    """
    Extract effective echo time from DICOM dataset.
    """
    try:
        echo_time_effective = dicom_dataset[0x5200, 0x9230][0][0x0018, 0x9114][0][0x0018, 0x9082].value
        return echo_time_effective
    except (KeyError, IndexError, AttributeError):
        return None


def process_dicom_file(dicom_file_path: str) -> Tuple[str, Optional[str], Optional[float], Optional[str]]:
    """
    Complete pipeline to determine file type and extract relevant metadata.
    """
    try:
        attributes = get_dicom_file_attributes(dicom_file_path)
        file_type, error = determine_file_type(attributes)
        
        if error:
            return file_type, error, None, None
        
        echo_time = None
        echo_suffix = None
        
        if file_type == "Spectroscopy":
            echo_time = get_echo_time(attributes['dicom_dataset'])
            if echo_time is None:
                return file_type, "Missing EffectiveEchoTime.", None, None
            echo_suffix = get_echo_suffix(echo_time)
        
        return file_type, None, echo_time, echo_suffix
    
    except Exception as e:
        return "Unknown", str(e), None, None


def organize_dicom_files(cases_folder, output_directory):
    """
    Organize DICOM files by type and echo time.
    """
    # Create main output folders
    spectroscopy_folder = path.join(output_directory, 'Spectroscopy')
    image_folder = path.join(output_directory, 'Images')
    makedirs(spectroscopy_folder, exist_ok=True)
    
    # Image subfolder tracking
    image_folder_created = set()
    
    # Echo subfolder tracking
    echo_folders_created = set()
    failed_cases = {} 
    processed_cases = {} 
    file_counter = 0
    
    # Process each case folder
    for folder in listdir(cases_folder):
        folder_path = path.join(cases_folder, folder, 'DICOM')
        if path.isdir(folder_path):
            
            folder_number = str(folder)
            print(f'Parsing folder: {folder_path}')
            
            spectroscopy_files_by_echo = {}  # Track files per echo type

            # Process files in this case
            for file in listdir(folder_path):
                file_path = path.join(folder_path, file)
                print(f'    Processing {Path(file_path).stem}')

                if path.isfile(file_path):
                    try:
                        file_type, error, echo_time, echo_suffix = process_dicom_file(file_path)
                        _, extension = path.splitext(file)

                        # Handle spectroscopy files
                        if file_type == "Spectroscopy":
                            print(f'>>> Spectroscopy file found!')

                            if error:
                                print(f">>> {error}. Skipping.")
                                if folder_path not in failed_cases:
                                    failed_cases[folder_path] = []
                                failed_cases[folder_path].append({
                                    'filename': file,
                                    'error': error
                                })
                                continue
                            
                            # Track by echo type
                            if echo_suffix not in spectroscopy_files_by_echo:
                                spectroscopy_files_by_echo[echo_suffix] = []
                            spectroscopy_files_by_echo[echo_suffix].append(file_path)
                            
                            # Check for duplicates for THIS echo type
                            if len(spectroscopy_files_by_echo[echo_suffix]) > 1:
                                print(f'>>> Warning: Multiple {echo_suffix} spectroscopy files found in {folder_path}.')
                                failed_cases[folder_path] = failed_cases.get(folder_path, []) + [{
                                    'filename': ','.join([Path(f).stem for f in spectroscopy_files_by_echo[echo_suffix]]),
                                    'error': f"Multiple {echo_suffix} spectroscopy files found. Please check."
                                }]
                                continue

                            print(f'    Echo time is {echo_time}')
                            print(f'    Suffix for echo time: {echo_suffix}')

                            # Create echo-specific subfolder only when needed
                            echo_subfolder = path.join(spectroscopy_folder, echo_suffix)
                            if echo_suffix not in echo_folders_created:
                                makedirs(echo_subfolder, exist_ok=True)
                                echo_folders_created.add(echo_suffix)
                            
                            new_filename = f"{folder_number}-{echo_suffix}{extension}" 
                            print(f'>>> New filename is {new_filename}')

                            # Copy to appropriate echo subfolder
                            try:
                                copy2(file_path, path.join(echo_subfolder, new_filename))
                                if folder_path not in processed_cases:
                                    processed_cases[folder_path] = []
                                processed_cases[folder_path].append({
                                    'filename': file,
                                    'new_filename': new_filename,
                                    'file_type': file_type,
                                    'echo_type': echo_suffix,
                                    'echo_time': echo_time
                                })
                            except Exception as e:
                                print(f"Error copying spectroscopy file {file}: {str(e)}")
                                if folder_path not in failed_cases:
                                    failed_cases[folder_path] = []
                                failed_cases[folder_path].append({
                                    'filename': file,
                                    'error': f"Copy error: {str(e)}"
                                })

                        # Handle T1-weighted images
                        elif file_type == "T1-weighted Image":
                            print(f'>>> T1-weighted image found.')
                            new_filename = f"{folder_number}-T1{extension}"
                            print(f'>>> New filename is {new_filename}')
                        
                            # Create Images folder only when needed
                            images_folder = path.join(output_directory, 'Images')
                            if 'Images' not in image_folder_created:
                                makedirs(images_folder, exist_ok=True)
                                image_folder_created.add('Images')

                            try:
                                copy(file_path, path.join(images_folder, new_filename))
                                if folder_path not in processed_cases:
                                    processed_cases[folder_path] = []
                                processed_cases[folder_path].append({
                                    'filename': file,
                                    'new_filename': new_filename,
                                    'file_type': file_type
                                })
                            except Exception as e:
                                print(f"Error copying T1 image {file}: {str(e)}")
                                if folder_path not in failed_cases:
                                    failed_cases[folder_path] = []
                                failed_cases[folder_path].append({
                                    'filename': file,
                                    'error': f"Copy error: {str(e)}"
                                })
                        
                        # Handle unknown file types
                        else:
                            print(f'>>> File is neither spectroscopy nor T1-weighted image. Skipping.')
                            if folder_path not in failed_cases:
                                failed_cases[folder_path] = []
                            failed_cases[folder_path].append({
                                'filename': file,
                                'error': error if error else "Unknown file type."
                            })
       
                        file_counter += 1
                        
                    except (errors.InvalidDicomError, FileNotFoundError, PermissionError) as e:
                        print(f"*** Skipping non-DICOM or unreadable file: {Path(file_path).stem} - {e}")
                        if folder_path not in failed_cases:
                            failed_cases[folder_path] = []
                        failed_cases[folder_path].append({
                            'filename': file,
                            'error': str(e)
                        })
                        continue                
                    except Exception as e:
                        print(f"*** Error processing {file_path}: {e}")
                        if folder_path not in failed_cases:
                            failed_cases[folder_path] = []
                        failed_cases[folder_path].append({
                            'filename': file,
                            'error': str(e)
                        })
        else:
            print(f'*** DICOM folder not found in {folder_path}.')
            if folder_path not in failed_cases:
                failed_cases[folder_path] = []
            failed_cases[folder_path].append({
                'filename': 'N/A',
                'error': "DICOM folder not found. Check folder structure."
            })

    print(f'>>> Processed {file_counter} files. Writing export logs...')
    
    # Write processed cases to a log file - organized by folder
    if processed_cases:
        processed_cases_file = path.join(output_directory, "processed_DICOM_cases.txt")
        with open(processed_cases_file, 'w', encoding='utf-8') as f:
            f.write(f"Processed DICOM Cases Log - {datetime.now()}\n\n")
            
            # Write organized by folder
            for folder_idx, (folder_path, files) in enumerate(processed_cases.items(), start=1):
                f.write(f"{folder_idx}. {folder_path}\n")
                for file_info in files:
                    f.write(f"      Original filename: {file_info['filename']}\n")
                    f.write(f"      New filename: {file_info['new_filename']}\n")
                    f.write(f"      File type: {file_info['file_type']}\n")
                    if file_info['file_type'] == 'Spectroscopy':
                        f.write(f"      Echo Type: {file_info['echo_type']}\n")
                        f.write(f"      Echo Time: {file_info['echo_time']}\n")
                    f.write(f"\n")
                f.write("\n")
        
        print(f">>> Processed cases logged to {processed_cases_file}")
    
    # Write failed cases to a log file
    if failed_cases:
        failed_cases_file = path.join(output_directory, "failed_DICOM_cases.txt")
        with open(failed_cases_file, 'w', encoding='utf-8') as f:
            f.write(f"Failed DICOM Cases Log - {datetime.now()}\n\n")
            for folder_idx, (folder_path, failures) in enumerate(failed_cases.items(), start=1):
                f.write(f"{folder_idx}. {folder_path}\n")
                for failure in failures:
                    f.write(f"      File name: {failure['filename']}\n")
                    f.write(f"      Error: {failure['error']}\n\n")
                f.write("\n")
        print(f">>> Failed cases logged to {failed_cases_file}")
    
    print('>>> Processing complete.')

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Organize DICOM files into folders')
    parser.add_argument('--input', required=True, help='Path to the folder containing case DICOM files')
    parser.add_argument('--output', required=True, help='Path to the output directory')
    
    args = parser.parse_args()
    organize_dicom_files(args.input, args.output)


# # ### Non-command line usage example
# cases_folder= r"C:\Users\lilif\OneDrive\Desktop\Dropbox\Phd\Pipeline testing\Data MV DICOM"
# output_directory = r"C:\Users\lilif\OneDrive\Desktop\Dropbox\Phd\Pipeline testing\Organized DICOMs MV"
# organize_dicom_files(cases_folder, output_directory)
