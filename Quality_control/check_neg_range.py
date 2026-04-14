from pandas import DataFrame
from numpy import linspace, flip, array, float64, sqrt, sum
from pathlib import Path
from sklearn.preprocessing import normalize
import xml.etree.ElementTree as ET
from lxml import etree
from os import path, mkdir, listdir
from shutil import move, copy2

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

    #print(f"    Validated PPM range: {valid_range[0]} to {valid_range[1]}")

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


def check_negative_range(filepath, output_directory, ppm_range, mode, threshold=0):
    if not path.exists(output_directory):
        mkdir(output_directory)
    
    caseID, firstPPM, lastPPM, number_of_points, points_filtered, xaxis, dataTable = readXML(filepath, ppm_range=ppm_range)
    
    print(f'Number of points in spectra is {len(points_filtered)}')
    
    file_name = Path(filepath).stem
    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(filepath, parser)
    root = tree.getroot()
    
    voxels = root.findall(".//Voxel")
    
    negative = False
    
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

        #Test for negatives
        negatives = [p for p in voxel_points_filtered if p < threshold]
        if negatives:
            negative = True
            #print(f"    Voxel at X: {x_pos}, Y: {y_pos} has {len(negatives)} points below threshold {threshold}.")
        else:
            continue

    if negative:
        
        output_directory = path.join(output_directory, f"negatives_threshold_{threshold}")
        if not path.exists(output_directory):
            mkdir(output_directory)
        # Move the file to the output directory
        destination = path.join(output_directory, path.basename(filepath))
        if mode == 'move':
            print(f">>> Negatives found. Moving file to {output_directory}")
            move(filepath, destination)
        elif mode == 'copy':
            print(f">>> Negatives found. Copying file to {output_directory}")
            copy2(filepath, destination)
    else:
        print(f">>> No voxels with values below threshold {threshold} found.")
    return negative




def check_negative_range_directory(input_directory, output_directory, ppm_range, mode, threshold=0):
    files = [f for f in listdir(input_directory) if f.endswith('.xml')]
    
    files_moved = 0
    for file in files:
        full_path = path.join(input_directory, file)
        print(f"Processing file: {file}")
        if check_negative_range(full_path, output_directory, ppm_range, mode=mode, threshold=threshold):
            files_moved += 1

    print(f">>> Total files moved: {files_moved}")



if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Check XML files for negative ranges and move/copy them.")
    parser.add_argument("--directory", type=str, help="Directory containing XML files to check.")
    parser.add_argument("--output", type=str, help="Directory to move/copy files) with negatives.")
    parser.add_argument("--ppm_range", type=float, nargs=2, default=[0, 4.5], help="PPM range to check for negatives (default: 0 4.5).")
    parser.add_argument("--mode", type=str, choices=['move', 'copy'], default='copy', help="Whether to move or copy files with negatives (default: copy).")
    parser.add_argument("--threshold", type=float, default=0, help="Threshold below which values are considered negative (default: 0).")
    args = parser.parse_args()
    check_negative_range_directory(args.directory, args.output, args.ppm_range, args.mode, args.threshold)

                        

# xml = r"C:\Users\lilif\OneDrive\Desktop\Dropbox\Phd\Pipeline testing\XML-MV"
# #xml = r"C:\Users\lilif\OneDrive\Desktop\Dropbox\Phd\Pipeline testing\XML-SV\5765-SE-M.xml"
# output_directory = r"C:\Users\lilif\OneDrive\Desktop\Dropbox\Phd\Pipeline testing\No negatives"
# ppm_range=[0,4.5]
# th = -0.1
# check_negative_range_directory(xml, output_directory, ppm_range, mode='copy', threshold=th)
