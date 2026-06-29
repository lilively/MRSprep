from pandas import DataFrame
from numpy import linspace, flip, array
from pathlib import Path
from sklearn.preprocessing import normalize
import xml.etree.ElementTree as ET
from lxml import etree
from os import path, mkdir, listdir

def get_PPM(ppm, NPoint, MaxPPM, MinPPM):
        if not (MinPPM <= ppm <= MaxPPM):
            raise ValueError(f"PPM {ppm} is out of range ({MinPPM}, {MaxPPM}).")

        delta = abs(MaxPPM - MinPPM) / (NPoint - 1)
        point = round((MaxPPM - ppm) / delta)
        return point

def validate_ppm_range(ppm_range, firstPPM, lastPPM):
    """
    Validate and adjust PPM range to stay within data boundaries
    """
    # Create a copy to avoid modifying the original
    valid_range = list(ppm_range)
    
    
    # Ensure PPM range is within data bounds
    if valid_range[0] < firstPPM:
        valid_range[0] = firstPPM

    
    if valid_range[1] > lastPPM:
        valid_range[1] = lastPPM

    print(f"    Validated PPM range: {valid_range[0]} to {valid_range[1]}")

    return tuple(valid_range)
#Function to read xml files

def readXML(filepath, ppm_range):
    
    caseID = Path(filepath).stem
# Parse XML file
    tree = ET.parse(filepath)
    root = tree.getroot()
    data = []

    for voxel in root.findall('.//Voxel'):
        #theese can be single variables, as all of them are the same
        firstPPM = float(voxel.get('FirstPPM'))
        lastPPM = float(voxel.get('LastPPM'))
        points = [float(p) for p in voxel.find('Points').text.split()]
        number_of_points = len(points)
        ppm_range = validate_ppm_range(ppm_range, firstPPM, lastPPM)

        if ppm_range[0]<firstPPM:
            ppm_range[0] = firstPPM

        if ppm_range[1]>lastPPM:
            ppm_range[1] = lastPPM

        min_point = get_PPM(ppm_range[0], number_of_points, lastPPM, firstPPM)
        max_point = get_PPM(ppm_range[1], number_of_points, lastPPM, firstPPM)
        points_filtered = points[max_point:min_point+1]

        #selecting data for columns
        voxel_data = {
        'ID' : str(Path(filepath).stem),
        'SNR': float(voxel.get('SNR')),
        'TissueType': voxel.find('Tissue').get('Type')}

        if 'Xaxis' in voxel.attrib and 'Yaxis' in voxel.attrib:
            voxel_data['Xaxis'] = int(voxel.get('Xaxis'))
            voxel_data['Yaxis'] = int(voxel.get('Yaxis'))

        voxel_data.update({'PPM_{}'.format(i): points_filtered[i] for i in range(len(points_filtered))})

        data.append(voxel_data)

    dataTable = DataFrame(data)

    xaxis = flip(linspace(ppm_range[0], ppm_range[1], len(points_filtered), endpoint=True))
    number_of_points = len(points_filtered)
    return caseID, firstPPM, lastPPM,number_of_points, points_filtered,xaxis,dataTable


def normalize_and_save_xml(filepath, output_directory, ppm_range):
    if not path.exists(output_directory):
        mkdir(output_directory)
    
    caseID, firstPPM, lastPPM, number_of_points, points_filtered, xaxis, dataTable = readXML(filepath, ppm_range=ppm_range)
    
    print(f'Number of points in spectra is {len(points_filtered)}')
    
    file_name = Path(filepath).stem
    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(filepath, parser)
    root = tree.getroot()
    
    voxels = root.findall(".//Voxel")
    
    # Update each voxel independently
    for voxel in voxels:
        # Get x and y positions if they exist
        x_pos = voxel.get('Xaxis', 'N/A')
        y_pos = voxel.get('Yaxis', 'N/A')
        
        # Get the points for THIS specific voxel
        points = [float(p) for p in voxel.find('Points').text.split()]
        
        # Filter points based on ppm_range
        min_point = get_PPM(ppm_range[0], len(points), lastPPM, firstPPM)
        max_point = get_PPM(ppm_range[1], len(points), lastPPM, firstPPM)
        voxel_points_filtered = points[max_point:min_point+1]
        
        # Normalize THIS voxel's data
        points_reshaped = array(voxel_points_filtered).reshape(1, -1)
        normalized_intensities = normalize(points_reshaped, norm='l2', axis=1).flatten()
        normalized_intensities_str = ' '.join(map(str, normalized_intensities))
        
        # Update this voxel's Points
        voxel.find('Points').text = normalized_intensities_str
        
        # Update the number of points attribute
        new_number_of_points = len(normalized_intensities)
        voxel.set('PointsNumber', str(new_number_of_points))
        
        print(f"Updated voxel at position (X={x_pos}, Y={y_pos}) with {new_number_of_points} normalized points")

    root.find('.//NrPoints').text = str(len(normalized_intensities))
    # Update PPM ranges (same for all voxels)
    for elem in root.iter():
        if "FirstPPM" in elem.attrib:
            elem.attrib["FirstPPM"] = str(xaxis[-1])
        if "LastPPM" in elem.attrib:
            elem.attrib["LastPPM"] = str(xaxis[0])
        
        for child in elem:
            if child.tag == "FirstPPM" and child.text:
                child.text = str(xaxis[-1])
            if child.tag == "LastPPM" and child.text:
                child.text = str(xaxis[0])
    
    # Save the file
    output_path = path.join(output_directory, f"{file_name}_normalized.xml")
    tree.write(output_path, pretty_print=True, xml_declaration=True, encoding='UTF-8')
    print(f"Saved normalized XML to {output_path}")



def normalize_xml_in_directory(input_directory, output_directory, ppm_range):
    if not path.exists(output_directory):
        mkdir(output_directory)
    
    files = [f for f in listdir(input_directory) if f.lower().endswith('.xml')]
    
    for file in files:
        full_path = path.join(input_directory, file)
        print(f"Processing file: {file}")
        normalize_and_save_xml(full_path, output_directory, ppm_range)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Normalize XML files in a directory based on PPM range.")
    parser.add_argument('--input', required=True, help='Path to the input directory containing XML files')
    parser.add_argument('--output', required=True, help='Path to the output directory for normalized XML files')
    parser.add_argument('--ppm_range', nargs=2, type=float, required=True, help='PPM range for normalization (e.g., --ppm_range 0 4.5)')
    args = parser.parse_args()
    normalize_xml_in_directory(args.input, args.output, tuple(args.ppm_range))
    
# xml = r"C:\Users\lilif\OneDrive\Desktop\Dropbox\Phd\Pipeline testing\XML-MV\3109_1.xml"
# xml_dir = r"C:\Users\lilif\OneDrive\Desktop\Dropbox\Phd\Pipeline testing\XML-MV"
# #xml = r"C:\Users\lilif\OneDrive\Desktop\Dropbox\Phd\Pipeline testing\XML-SV\5765-SE-M.xml"
# output_directory = r"C:\Users\lilif\OneDrive\Desktop\Dropbox\Phd\Pipeline testing\normalized"
# ppm_range=[0,4.5]
# normalize_xml_in_directory(input_directory=xml_dir, output_directory=output_directory, ppm_range=ppm_range)
