import xml.etree.ElementTree as ET
from lxml import etree
from pathlib import Path
from os import listdir, path
from pandas import DataFrame


''' Get SNR from SV or MV XML files '''
def getSNR(inputXML):
    file_name = Path(inputXML).stem
    # XML reading
    tree = ET.parse(inputXML)
    root = tree.getroot()
    xmlstr = ET.tostring(root, encoding='utf8', method='xml')
    file = etree.fromstring(xmlstr)
    voxels = file.findall(".//Voxel")
    
    # Get SNR for ALL voxels
    voxel_data = []
    for voxel in voxels:
        x_pos = voxel.get('Xaxis', 'N/A')
        y_pos = voxel.get('Yaxis', 'N/A')
        snr_xml = voxel.attrib.get("SNR", 'N/A')
        
        print(f'SNR for voxel at position X: {x_pos}, Y: {y_pos} is {snr_xml}')
        voxel_data.append((file_name, x_pos, y_pos, snr_xml))
    
    return voxel_data

def extract_snr_from_xml(xml_dir, output_folder, outfilename):
    print(">>> Reading in SNR from XML files...")
    file_counter = 0
    snr_list = []
    
    for file in listdir(xml_dir):
        if file.endswith(".xml"):
            print(f">>> Processing file: {file}")
            file_path = path.join(xml_dir, file)
            voxel_list = getSNR(file_path)
            
            for filename, x_pos, y_pos, snr_value in voxel_list:
                
                snr_list.append({
                    'Filename': filename,
                    'Case_ID': str(filename.split('-')[0]).strip(),
                    'X_pos': x_pos,
                    'Y_pos': y_pos,
                    'SNR': float(snr_value) if snr_value != 'N/A' else None
                })
            file_counter += 1

    print(f'\n>>> Processed {file_counter} files.')       
    if len(snr_list) > 0 and snr_list[0]['X_pos'] == 'N/A' and snr_list[0]['Y_pos'] == 'N/A':
        for entry in snr_list:
            del entry['X_pos']
            del entry['Y_pos']
    data_xml = DataFrame(snr_list)
    
    output_path = path.join(output_folder, outfilename + '.xlsx')
    data_xml.to_excel(output_path, index=False)
    print(f">>> SNR data saved to {output_path}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Extract SNR from XML files")
    parser.add_argument("--directory", type=str, help="Directory containing XML files")
    parser.add_argument("--output", type=str, help="Directory to save the output Excel file")
    parser.add_argument("--filename", type=str, help="Output Excel filename (without extension)")
    args = parser.parse_args()
    extract_snr_from_xml(args.directory, args.output,  args.filename)

# #xml_directory = r"C:\Users\lilif\OneDrive\Desktop\Dropbox\Phd\Pipeline testing\XML-MV"
# xml_directory = r"C:\Users\lilif\OneDrive\Desktop\Dropbox\Phd\Pipeline testing\XML-SV"
# output_directory = r"C:\Users\lilif\OneDrive\Desktop\Dropbox\Phd\Pipeline testing\Quality Control SNR"
# filename = 'Test1_SV_SNR'
# extract_snr_from_xml(xml_directory, output_directory, filename)