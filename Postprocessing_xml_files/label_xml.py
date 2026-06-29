
from pathlib import Path
from pandas import read_excel
from os import listdir, path
import xml.etree.ElementTree as ET
from lxml import etree
from datetime import datetime

''' Update the Tissue Type label in an XML file'''
def update_xml_label(xml_filepath, new_label, output_directory, MV=None):
    tree = ET.parse(xml_filepath)
    root = tree.getroot()
    xmlstr = ET.tostring(root, encoding='utf8', method='xml')
    file = etree.fromstring(xmlstr)
    tissue =file.findall(".//Tissue")


    for elem in tissue: 
        elem.attrib['Type'] = new_label

    outPath = path.join(output_directory, Path(xml_filepath).name)
    # with open(outPath,'wb') as f: ## Write document to file
    #     f.write(etree.tostring(file,pretty_print=True))
    
    print( '    XML saved to:', outPath)

def get_xml_positions(xml_filepath):
    tree = ET.parse(xml_filepath)
    root = tree.getroot()
    xmlstr = ET.tostring(root, encoding='utf8', method='xml')
    file = etree.fromstring(xmlstr)
    positions = []
    voxels =file.findall(".//Voxel")

    for voxel in voxels:
        x = str(voxel.get('Xaxis'))
        y = str(voxel.get('Yaxis'))
        positions.append((x,y))
    return positions



def label_xml_files(folderPath, labelPath, output_directory, id_col, label_col, type=None, xcol=None, ycol=None):
    labels = read_excel(labelPath)
    label_dict = labels.set_index(labels[id_col].astype(str))[label_col].to_dict()
    
    if type == 'MV' and xcol in labels.columns and ycol in labels.columns:
        print(">>> Labeling Multi-Voxel XML files...")
        # Create a multi-index dictionary with (id, x, y) as key
        labels[id_col] = labels[id_col].astype(str)
        label_dict = {}
        for _, row in labels.iterrows():
            key = (str(row[id_col]), str(row[xcol]), str(row[ycol]))
            label_dict[key] = row[label_col]
    else:
        print(">>> Labeling Single-Voxel XML files...")
        label_dict = labels.set_index(labels[id_col].astype(str))[label_col].to_dict()

    failed_cases = {}
    renamed_cases= []
    for file in listdir(folderPath):
        filepath = path.join(folderPath,file)

        filename = Path(file).stem
        if Path(filepath).suffix.lower() != '.xml':
            if file not in failed_cases:
                failed_cases[file] = []
                failed_cases[file].append({
                    'filename': file,
                    'error': 'Not an XML file'
                })
                continue
        
        print(f">>> Processing file: {file}")
        case_id = str(filename.split('-')[0]).strip()
        print(f"    Extracted case ID: {case_id}")
        if type == 'MV':
            postions = get_xml_positions(filepath)
            for pos in postions:
                key = (case_id, pos[0], pos[1])
                new_label = label_dict.get(key)
                print(f"    Found label: {new_label} for position X:{pos[0]} Y:{pos[1]}")
        else:
            new_label = label_dict.get(case_id)
            print(f"    Found label: {new_label}")
            
            if new_label is None:
                print(f"    No label found for case ID: {case_id}. Skipping file.")
                if file not in failed_cases:
                    failed_cases[file] = []
                failed_cases[file].append({
                    'filename': file,
                    'error': f'No label found for case ID!'
                })
                continue
  
            try:
                update_xml_label(filepath, new_label, output_directory)
                renamed_cases.append(file)
            except Exception as e:
                print(f"    Failed to update {file}: {e}")
                if file not in failed_cases:
                    failed_cases[file] = []
                failed_cases[file].append({
                    'filename': file,
                    'error': str(e)
                })
        


    print(f'\n>>> Renamed {len(renamed_cases)} files.')

    if failed_cases:
        failed_cases_file = path.join(output_directory, "failed_to_label.txt")
        with open(failed_cases_file, 'w', encoding='utf-8') as f:
            f.write(f"Failed DICOM Cases Log - {datetime.now()}\n\n")
            for case, errors in failed_cases.items():
                f.write(f"Case: {case}\n")
                for error_info in errors:
                    f.write(f"    File: {error_info['filename']} - Error: {error_info['error']}\n")
                f.write("\n")
        print(f">>> Failed cases logged to {failed_cases_file}")
    else:
        print(">>> All files processed successfully.")



#Command line usage example
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Rename XML files based on labels from an Excel file.')
    parser.add_argument('--xml_folder', required=True, help='Path to the folder containing the XML files')
    parser.add_argument('--label_excel', required=True, help='Path to the Excel file containing labels')
    parser.add_argument('--output', required=True, help='Path to the output directory')
    parser.add_argument('--id_col', required=True, help='Column name for IDs in XML files')
    parser.add_argument('--label_col', required=True, help='Column name for the new labels in the Excel file')
    parser.add_argument('--type', required=False, help='MV for Multi-Voxel, leave empty for Single-Voxel')
    parser.add_argument('--xcol', required=False, help='Column name for X coordinate (if type is MV)')
    parser.add_argument('--ycol', required=False, help='Column name for Y coordinate (if type is MV)')
    
    args = parser.parse_args()
    label_xml_files(args.xml_folder, args.label_excel, args.output, args.id_col, args.label_col, args.type, args.xcol, args.ycol)

# # # Example usage
# folderPath = r"C:\Users\lilif\OneDrive\Desktop\Dropbox\Phd\Pipeline testing\XML-SV"
# labelPath =r"C:\Users\lilif\OneDrive\Desktop\Dropbox\Phd\Pipeline testing\SingleVoxel_IDs.xlsx"
# output_directory = r"C:\Users\lilif\OneDrive\Desktop\Dropbox\Phd\Pipeline testing\XML-SV"
# id_col = 'BV_ID'
# label_col = 'Dataset'
# type = None
# x
# label_xml_files(folderPath, labelPath, output_directory, id_col, label_col, type,xcol=None, ycol=None)    

