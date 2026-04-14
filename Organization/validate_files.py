from pandas import read_excel, DataFrame, concat
from os import listdir, path
from pathlib import Path
from datetime import datetime

def read_mrui_files(folder_path, id_col, echo_filter=None):
    """Returns two dataframes: one for water filenames, one for metabolite filenames"""
    water_data = {id_col: [], 'Water_File': []}
    metabolite_data = {id_col: [], 'Metabolite_File': []}

    for folder in listdir(folder_path):
        sub_folder_path = path.join(folder_path, folder)

        if path.isdir(sub_folder_path):
            print(f'Parsing folder: {sub_folder_path}')
            for file in listdir(sub_folder_path):
                print(f'    Processing {file}')
                filename = Path(file).stem
                suffix = Path(file).suffix
                if suffix == ".mrui":  
                    parts = filename.split('-')
                    
                    if len(parts) >= 3:
                        case_id, echo, ftype = parts[0], parts[1], parts[2].split('.')[0]
                        # Check echo filter
                        if echo_filter is None or echo == echo_filter:
                            if ftype == 'W':
                                water_data[id_col].append(case_id)
                                water_data['Water_File'].append('W')
                            elif ftype == 'M':
                                metabolite_data[id_col].append(case_id)
                                metabolite_data['Metabolite_File'].append('M')
    
    df_water = DataFrame(water_data)
    df_metabolite = DataFrame(metabolite_data)
    
    return df_water, df_metabolite


def read_xml_files(folder_path, id_col, echo_filter=None):
    """Returns dataframe with ID and XML filename"""
    xml_data = {id_col: [], 'XML_File': []}
    
    for file in listdir(folder_path):
        print(f'    Processing {file}')
        filename = Path(file).stem
        suffix = Path(file).suffix
        if suffix == ".xml":  
            parts = filename.split('-')
            
            if len(parts) >= 3:
                case_id, echo, ftype = parts[0], parts[1], parts[2].split('.')[0]
                # Check echo filter
                if echo_filter is None or echo == echo_filter:
                    xml_data[id_col].append(case_id)
                    xml_data['XML_File'].append('XML')
    
    return DataFrame(xml_data)


def read_format_files(folder_path, id_col, echo_filter=None):
    """Returns dataframe with ID and Format (DICOM or SPAR)"""
    format_data = {id_col: [], 'Format': []}
    
    for folder in listdir(folder_path):
        sub_folder_path = path.join(folder_path, folder)
        if path.isdir(sub_folder_path):
            print(f'Parsing folder: {sub_folder_path}')
            for file in listdir(sub_folder_path):
                print(f'    Processing {file}')
                filename = Path(file).stem
                suffix = Path(file).suffix
                parts = filename.split('-')
                
                # Check echo filter
                if echo_filter is None or echo_filter in filename:
                    if suffix == '':  # DICOM
                        format_data[id_col].append(parts[0])
                        format_data['Format'].append('DICOM')
                    elif suffix.upper().startswith('.SPAR'):  # SPAR
                        format_data[id_col].append(parts[0])
                        format_data['Format'].append('SPAR')
    
    return DataFrame(format_data)


def validate_files(
    potential_case_path,
    id_col,
    output_directory,
    echo_filter=None,
    mrui_folder=None,
    xml_folder=None,
    dicom_folder=None,
    spar_folder=None,
    sheet_name='Cases'
):
    """
    Merge multiple data sources with potential_cases dataframe.
    Each source adds 1-2 columns to the result.
    """
    
    # Validate mandatory input
    if not path.exists(potential_case_path):
        raise ValueError(f"Potential cases file not found: {potential_case_path}")
    
    # Validate that at least one optional source is provided
    data_sources_provided = any([mrui_folder, xml_folder, dicom_folder, spar_folder])
    if not data_sources_provided:
        raise ValueError("At least one of the following must be provided: mrui_folder, xml_folder, dicom_folder, or spar_folder")
    
    # Load potential cases
    try:
        print(f"Loading potential cases from: {potential_case_path}")
        df_potential = read_excel(potential_case_path, sheet_name=sheet_name)
        
        if df_potential.empty:
            raise ValueError("Potential cases dataframe is empty")
        
        if id_col not in df_potential.columns:
            raise ValueError(f"ID column '{id_col}' not found in potential cases file")
        
        # Check and remove duplicates
        original_count = len(df_potential)
        duplicate_count = df_potential[id_col].duplicated().sum()
        
        if duplicate_count > 0:
            print(f"  Found {duplicate_count} duplicate IDs in {original_count} rows")
            df_potential = df_potential.drop_duplicates(subset=[id_col], keep='first')
            print(f"  After deduplication: {len(df_potential)} unique cases")
        else:
            print(f"  Loaded {len(df_potential)} potential cases (no duplicates)")
        
        # Ensure ID is string type
        df_potential[id_col] = df_potential[id_col].astype(str).str.strip()
        
    except Exception as e:
        raise ValueError(f"Error loading potential cases: {str(e)}")
    
    # Start with potential cases
    df_merged = df_potential.copy()
    
    # Add Echo column if filtering
    if echo_filter:
        df_merged['Echo'] = echo_filter
    
    # Process MRUI files - adds 2 columns: Water_File, Metabolite_File
    if mrui_folder:
        try:
            print(f"\nProcessing MRUI files from: {mrui_folder}")
            
            if not path.exists(mrui_folder):
                print(f"  Warning: MRUI folder not found: {mrui_folder}")
            else:
                df_water, df_metabolite = read_mrui_files(mrui_folder, id_col, echo_filter=echo_filter)
                
                if not df_water.empty:
                    df_water[id_col] = df_water[id_col].astype(str).str.strip()
                    df_water = df_water.drop_duplicates(subset=[id_col], keep='first')
                    df_merged = df_merged.merge(df_water, on=id_col, how='left')
                    print(f"  Added Water_File column ({df_water[id_col].nunique()} IDs)")
                
                if not df_metabolite.empty:
                    df_metabolite[id_col] = df_metabolite[id_col].astype(str).str.strip()
                    df_metabolite = df_metabolite.drop_duplicates(subset=[id_col], keep='first')
                    df_merged = df_merged.merge(df_metabolite, on=id_col, how='left')
                    print(f"  Added Metabolite_File column ({df_metabolite[id_col].nunique()} IDs)")
                    
        except Exception as e:
            print(f"  Error processing MRUI files: {str(e)}")
    
    # Process XML files - adds 1 column: XML_File
    if xml_folder:
        try:
            print(f"\nProcessing XML files from: {xml_folder}")
            
            if not path.exists(xml_folder):
                print(f"  Warning: XML folder not found: {xml_folder}")
            else:
                df_xml = read_xml_files(xml_folder, id_col, echo_filter=echo_filter)
                
                if not df_xml.empty:
                    df_xml[id_col] = df_xml[id_col].astype(str).str.strip()
                    df_xml = df_xml.drop_duplicates(subset=[id_col], keep='first')
                    df_merged = df_merged.merge(df_xml, on=id_col, how='left')
                    print(f"  Added XML_File column ({df_xml[id_col].nunique()} IDs)")
                    
        except Exception as e:
            print(f"  Error processing XML files: {str(e)}")
    
    # Process Format files (DICOM and SPAR) - adds 1 column: Format
    format_folders = []
    if dicom_folder and path.exists(dicom_folder):
        format_folders.append(dicom_folder)
    if spar_folder and path.exists(spar_folder):
        format_folders.append(spar_folder)
    
    if format_folders:
        try:
            print(f"\nProcessing Format files")
            all_format_data = []
            
            for folder in format_folders:
                df_format = read_format_files(folder, id_col, echo_filter=echo_filter)
                if not df_format.empty:
                    all_format_data.append(df_format)
            
            if all_format_data:
                df_formats = concat(all_format_data, ignore_index=True)
                df_formats[id_col] = df_formats[id_col].astype(str).str.strip()
                # If multiple formats per ID, join them
                df_formats = df_formats.groupby(id_col)['Format'].apply(
                    lambda x: ', '.join(sorted(set(x)))
                ).reset_index()
                df_merged = df_merged.merge(df_formats, on=id_col, how='left')
                print(f"  Added Format column ({df_formats[id_col].nunique()} IDs)")
                    
        except Exception as e:
            print(f"  Error processing Format files: {str(e)}")
    
    print(f"\nMerge complete. Final dataframe shape: {df_merged.shape}")
    print(f"Unique IDs in result: {df_merged[id_col].nunique()}")
        
    # Save merged dataframe to Excel
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    sources = []
    if mrui_folder:
        sources.append('mrui')
    if xml_folder:
        sources.append('xml')
    if dicom_folder or spar_folder:
        sources.append('format')
    
    sources_str = '_'.join(sources)
    echo_str = f'_echo{echo_filter}' if echo_filter else ''
    
    output_filename = f'merged_data_{sources_str}{echo_str}_{timestamp}.xlsx'
    output_path = path.join(output_directory, output_filename)
    df_merged = df_merged.fillna('Missing')  # Replace NaN with empty string for saving
    df_merged.to_excel(output_path, index=False)
    print(f"Merged data saved to: {output_path}")
    
    return df_merged

# # Example usage
# potential_case_path = r"C:\Users\lilif\OneDrive\Desktop\Dropbox\Phd\Pipeline testing\SingleVoxel_IDs.xlsx"
# # cases_path = r"C:\Users\lilif\OneDrive\Desktop\Dropbox\Phd\DATA_SV\SingleVoxel_IDs - safe.xlsx"
# folder_path_mrui = r"C:\Users\lilif\OneDrive\Desktop\Dropbox\Phd\Pipeline testing\Output MRUI"
# # cases = read_excel(cases_path, sheet_name='Cases')['BV_ID'].tolist()
# folder_path = r"C:\Users\lilif\OneDrive\Desktop\Dropbox\Phd\Pipeline testing\XML test"
# output_directory = r"C:\Users\lilif\OneDrive\Desktop\Dropbox\Phd\Pipeline testing"

# folder_path_spar = r"C:\Users\lilif\OneDrive\Desktop\Dropbox\Phd\Pipeline testing\Output SPAR\Spectroscopy"
# #folder_path_dicom = r"C:\Users\lilif\OneDrive\Desktop\Dropbox\Phd\Pipeline testing\Organized DICOMs MV\Spectroscopy"
# folder_path_dicom = r"C:\Users\lilif\OneDrive\Desktop\Dropbox\Phd\Pipeline testing\Organized DICOMs SV\Spectroscopy"
# id_col = 'BV_ID'
# echo = 'LE'

# df_merged = merge_data_sources(
#     potential_case_path=potential_case_path,
#     id_col=id_col,
#     output_directory=output_directory,
#     echo_filter=echo,
#     mrui_folder=folder_path_mrui,
#     xml_folder=folder_path,
#     dicom_folder=folder_path_dicom,
#     spar_folder=folder_path_spar,
#     sheet_name='Cases',
# )
    
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description='Valideate and merge data sources based on potential cases from Excel file')
    
    # Required arguments
    parser.add_argument('--cases', required=True, help='Path to Excel file with potential cases')
    parser.add_argument('--id-col', required=True, help='Name of the ID column')
    parser.add_argument('--echo', required=True, help='Echo filter (''SE'' or ''LE'')')
    parser.add_argument('--output', required=True, help='Directory to save merged output')
    
    # Optional data source folders
    parser.add_argument('--mrui', help='Path to MRUI files folder')
    parser.add_argument('--xml', help='Path to XML files folder')
    parser.add_argument('--dicom', help='Path to DICOM files folder')
    parser.add_argument('--spar', help='Path to SPAR files folder')
    parser.add_argument('--sheet', default='Cases', help='Excel sheet name (default: Cases)')
    
    args = parser.parse_args()
    
    # Call the merge function
    df_result = validate_files(
        potential_case_path=args.cases,
        id_col=args.id_col,
        output_directory=args.output_dir,
        echo_filter=args.echo,
        mrui_folder=args.mrui,
        xml_folder=args.xml,
        dicom_folder=args.dicom,
        spar_folder=args.spar,
        sheet_name=args.sheet
    )
    
    print(f"\n>>> Processed {len(df_result)} cases")

if __name__ == '__main__':
    main()