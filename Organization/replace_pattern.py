from os import listdir, path
from os import rename
from datetime import datetime
from pathlib import Path

def rename_files_in_directory(directory, old_pattern, new_pattern):

    renamed = []
    failed = []
    
    for file in listdir(directory):
        file_path = Path(file)
        file_stem = file_path.stem
        file_suffix = file_path.suffix
        
        # Replace pattern in filename
        new_stem = file_stem.replace(old_pattern, new_pattern)
        new_filename = new_stem + file_suffix
        
        try:
            original = path.join(directory, file)
            renamed_path = path.join(directory, new_filename)
            
            print(f'Renaming: {original} -> {renamed_path}')
            rename(original, renamed_path)
            renamed.append(renamed_path)
            
        except Exception as e:
            failed.append({'filename': file, 'error': str(e)})
            print(f'Failed to rename {file}: {e}')
    
    # Log failures if any occurred
    if failed:
        failed_cases_file = path.join(directory, "failed_renames.txt")
        with open(failed_cases_file, 'w', encoding='utf-8') as f:
            f.write(f"Failed renames - {datetime.now()}\n\n")
            for error_info in failed:
                f.write(f"File: {error_info['filename']} - Error: {error_info['error']}\n")
        print(f"Failed cases logged to {failed_cases_file}")
    
    print(f'\nRenamed {len(renamed)} files.')
    print(f'Failed to rename {len(failed)} files.')
    print(f'Renaming completed in directory: {directory}')

# if __name__ == "__main__":
#     import argparse
#     parser = argparse.ArgumentParser(description='Rename files in a directory by replacing a pattern.')
#     parser.add_argument('directory', type=str, 
#                         help='Path to the target directory containing files to rename.')
#     parser.add_argument('--old_pattern', type=str, required=True,
#                         help='Pattern in the filename to be replaced.')
#     parser.add_argument('--new_pattern', type=str, required=True,
#                         help='New pattern to replace the old pattern with.')
    
#     args = parser.parse_args()
    
#     rename_files_in_directory(
#         directory=args.directory,
#         old_pattern=args.old_pattern,
#         new_pattern=args.new_pattern
#     )

working_folder = r"C:\Users\Lili\Dropbox\Phd\Pseudoprogression\Segm_G\MRSgrid_0.8_NoData"
mode='replace' #options: 'append', 'replace'
old_pattern = '_grid'
new_pattern = ''
# append_pattern = '-LE'

rename_files_in_directory(directory=working_folder,
                           old_pattern=old_pattern,
                             new_pattern=new_pattern,
                             mode='replace')

