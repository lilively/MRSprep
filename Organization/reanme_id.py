from pathlib import Path
from os import listdir, path, rename
from pandas import read_excel
import sys

from pathlib import Path
from os import listdir, path, rename
from pandas import read_excel
import sys

def rename_files(excel_file, working_folder, original_id_col=None, new_id_col=None):
    """Rename files based on ID mapping from Excel file"""
    
    # Read Excel file
    try:
        df = read_excel(excel_file)
        df[original_id_col] = df[original_id_col].astype(str).str.strip()
        df[new_id_col] = df[new_id_col].astype(str).str.strip()

        print(f"Sample IDs from Excel: {df[original_id_col].head().tolist()}")
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return False
    
    # Initialize tracking lists
    id_not_found = []
    rename_errors = []
    renamed_count = 0
    
    # Main renaming loop
    print(">>> Starting file renaming process...\n")
    
    try:
        files = listdir(working_folder)
    except Exception as e:
        print(f"   Error accessing folder: {e}")
        return False
    
    for file in files:
        full_path = path.join(working_folder, file)

        if path.isdir(full_path):
            print(f"    Skipping directory: {file}")
            continue

        print(f"    Processing file: {file}")
        try:
            file_stem = Path(file).stem
            file_ext = Path(file).suffix
            
            # Extract ID from filename
            # If no dash, entire filename is the ID
            # If dash exists, ID is before the first dash
            if '-' in file_stem:
                extracted_id = file_stem.split('-')[0]
                suffix = '-' + '-'.join(file_stem.split('-')[1:])
            else:
                extracted_id = file_stem
                suffix = ''  # No suffix
            
            print(f"    Extracted ID: '{extracted_id}' with suffix '{suffix}'")
            
            # Try to find matching ID in Excel
            found_match = False
            new_id = None
            
            for _, row in df.iterrows():
                old_id = str(row[original_id_col])
                if old_id == extracted_id:  # Exact match
                    new_id = str(row[new_id_col])
                    found_match = True
                    print(f"    Found match: {old_id} -> {new_id}")
                    break
            
            if not found_match:
                print(f"    No matching ID found for: '{extracted_id}'")
                id_not_found.append(file)
                continue
            
            # Build new filename
            new_file_stem = new_id + suffix
            new_file_full = new_file_stem + file_ext
            
            # Construct paths and rename
            original = path.join(working_folder, file)
            renamed_path = path.join(working_folder, new_file_full)
            
            # Skip if name didn't change
            if original == renamed_path:
                print(f"    Skipping (no change needed)")
                continue
            
            # Skip if target already exists
            if path.exists(renamed_path):
                print(f"    WARNING: Target already exists: {new_file_full}")
                continue
            
            rename(original, renamed_path)
            print(f"    Renamed: '{file}' -> '{new_file_full}'")
            renamed_count += 1
            
        except Exception as e:
            print(f"    Error renaming '{file}': {e}")
            rename_errors.append(file)
    
    # Summary
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    print(f"Files renamed: {renamed_count}")
    print(f"IDs not found in Excel: {len(id_not_found)}")
    if id_not_found:
        print(f"  {id_not_found[:10]}")
        if len(id_not_found) > 10:
            print(f"  ... and {len(id_not_found) - 10} more")
    print(f"Rename errors: {len(rename_errors)}")
    if rename_errors:
        print(f"  {rename_errors}")
    print("="*50)
    
    return True





if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Rename files based on ID mapping from Excel file')
    parser.add_argument('--excel', required=True, help='Path to Excel file with ID mappings')
    parser.add_argument('--folder', required=True, help='Path to the folder containing files to rename')
    parser.add_argument('--original', required=True, help='Original ID column name')
    parser.add_argument('--new', required=True, help='New ID column name')
    
    args = parser.parse_args()
    rename_files(args.excel, args.folder, args.original, args.new)




# # ### Non-command line usage example
# excel= r"C:\Users\lilif\OneDrive\Desktop\Dropbox\Phd\Pipeline testing\SingleVoxel_IDs.xlsx"
# input_directory = r"C:\Users\lilif\OneDrive\Desktop\Dropbox\Phd\Pipeline testing\XML-SV"
# bv_id = 'BV_ID'
# uab_id= 'UAB_ID'

# rename_files(excel, input_directory, original_id_col=bv_id, new_id_col=uab_id)