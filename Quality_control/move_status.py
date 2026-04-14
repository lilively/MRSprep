from pandas import read_excel
from os import listdir, path, rename
from pathlib import Path
from shutil import copy2, move


def move_status(excel_file, working_folder, output_directory ,id_col, status_label, mode):
    """
    Move files in the working_folder based on their status in the Excel file.
    
    Parameters:
    - excel_file: Path to the Excel file containing file statuses.
    - working_folder: Path to the folder containing files to be moved.
    - status_label: The status label indicating files to be moved.
    
    Returns:
    - True if operation is successful, False otherwise.
    """
    try:
        df = read_excel(excel_file)
        print(f">>> Excel file '{Path(excel_file).stem}' read successfully.")

        # data = df.loc[df['XML']== "xml"]
        label_selected= df.loc[df['Status']== status_label]
        df[id_col] = df[id_col].astype(str).str.strip()
        selected_ids = label_selected[id_col].values.tolist()

        print(f">>> Found {len(selected_ids)} files with status '{status_label}'.")

        if label_selected.empty:
            print(">>> No files to move based on the provided status label.")
            return True
        
    except Exception as e:
        print(f"    Error reading Excel file: {e}")
        return False
        
    

    output_directory = path.join(working_folder, status_label)
    if not path.exists(output_directory):
        Path(output_directory).mkdir(parents=True, exist_ok=True)
        print(f">>> Created output directory: {output_directory}\n")

    files = listdir(working_folder)
    file_counter = 0
    for file in files:
        full_path = path.join(working_folder, file)

        if path.isdir(full_path):
            print(f"    Skipping directory: {file}")
            continue

        print(f"\n>>> Processing file: {file}")
        try:
            file_stem = Path(file).stem

            if '-' in file_stem:
                extracted_id = file_stem.split('-')[0]
                suffix = '-' + '-'.join(file_stem.split('-')[1:])
            else:
                extracted_id = file_stem
                suffix = ''  # No suffix

            #print(f"    Extracted ID: '{extracted_id}' with suffix '{suffix}'")

            if extracted_id in selected_ids:
                destination = path.join(output_directory, file)
                try:
                    if mode == 'move':
                        print(f"    {status_label} detected. Moving file to {output_directory}")
                        move(full_path, destination)
                        file_counter+=1
                    elif mode == 'copy':
                        print(f"    {status_label} detected. Copying file to {output_directory}")
                        copy2(full_path, destination)
                        file_counter+=1
                except Exception as e:
                    print(f'    Error when copying/moving {file} : {e}')                        

        
        except Exception as e:
            print(f"    Error processing '{file}': {e}")
            continue
    
    print(f'>>> {(file_counter)} files move or copied')


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Move or copy files based on status in an Excel file.")
    parser.add_argument("--cases", type=str, help="Path to the Excel file containing file statuses.")
    parser.add_argument("--directrory", type=str, help="Path to the folder containing files to be moved or copied.")
    parser.add_argument("--output", type=str, help="Path to the output directory.")

    parser.add_argument("--id_col", type=str, help="Column name for IDs in the Excel file.")
    parser.add_argument("--status", type=str, help="The status label indicating files to be moved or copied.")
    parser.add_argument("--mode", type=str, choices=['move', 'copy'], default='copy', help="Operation mode: 'move' or 'copy'. Default is 'copy'.")  
    args = parser.parse_args()
    move_status(excel_file=args.cases, working_folder=args.directrory, output_directory=args.output, id_col=args.id_col, status_label=args.status, mode=args.mode)
                        
    

    

# totalExcel = r"C:\Users\lilif\OneDrive\Desktop\Dropbox\Phd\Pipeline testing\Quality Control SNR\merged_snr_fwhm_status.xlsx"
# xmlDir = r"C:\Users\lilif\OneDrive\Desktop\Dropbox\Phd\Pipeline testing\XML-SV"
# outDir= r"C:\Users\lilif\OneDrive\Desktop\Dropbox\Phd\Pipeline testing\Postprocessing"

# label = "Selected"
# id_col = 'UAB_ID'
# mode = 'copy'
# move_status(excel_file=totalExcel, working_folder=xmlDir,output_directory=outDir, id_col=id_col,status_label=label, mode=mode)