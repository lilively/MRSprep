import xml.etree.ElementTree as ET
from lxml import etree
from pathlib import Path
from os import path




def getCaseIDS(inputXML):
    tree = ET.parse(inputXML)
    root = tree.getroot()
    xmlstr = ET.tostring(root, encoding='utf8', method='xml')
    file = etree.fromstring(xmlstr)
    voxels =file.findall(".//Case")

    casesXML = []

    for elem in voxels:
        caseID = elem.attrib['ID'].split('-')[0]
        echo = elem.attrib['ID'].split('-')[1]
        casesXML.append(caseID)
    
    return echo, casesXML

# Erase non-common cases from both files
def eraseNonCommonCases(inputXML, commonCases, echo, outputDir):
    filename = Path(inputXML).stem
    
    tree = ET.parse(inputXML)
    root = tree.getroot()
    xmlstr = ET.tostring(root, encoding='utf8', method='xml')
    file = etree.fromstring(xmlstr)
    voxels =file.findall(".//Case")

    for elem in voxels:
        caseID = elem.attrib['ID'].split('-')[0]
        if caseID not in commonCases:
            parent = elem.getparent()
            parent.remove(elem)

    output_path = path.join(outputDir, f'{filename}_common_{echo}.xml')
    tree = ET.ElementTree(file)
    tree.write(output_path, encoding='utf-8', xml_declaration=True)
    print(f'>>> Saved cleaned XML for echo {echo} at:', output_path)


def concatenate_data(xml_path1, xml_path2, output_directory):
    try:
        print(f'>>> Reading in xml files...')
        echo1, cases1 = getCaseIDS(xml_path1)
        echo2, cases2 = getCaseIDS(xml_path2)
        
    except Exception as e:
        print('Error reading XML files:', e)
        exit(1)

    print(f'    Cases in first directory (echo: {echo1}):', len(cases1))
    print(f'    Cases in second directory (echo: {echo2}):', len(cases2))

    # Find common cases
    common_cases = set(cases1).intersection(set(cases2))
    print(f'    Common cases:', len(common_cases))

    # Erase non-common cases from both XML files
    try:
        eraseNonCommonCases(xml_path1, common_cases, echo1, output_directory)
        eraseNonCommonCases(xml_path2, common_cases, echo2, output_directory)
        print('>>> Finished processing XML files.')
    except Exception as e:
        print('Error processing XML files:', e)
        exit(1)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Concatenate XML data based on common Case IDs.')
    parser.add_argument('--xml1', type=str, help='Path to the first XML file.')
    parser.add_argument('--xml2', type=str, help=' Path to the second XML file.')
    parser.add_argument('--output', type=str, help='Output directory for processed XML files.')

    args = parser.parse_args() 
    concatenate_data(args.xml1, args.xml2, args.output)    


# #Non command line

# xml_path1 = r"C:\Users\lilif\OneDrive\Desktop\Dropbox\Phd\Pipeline testing\Old\Analysis preparation\Spectra Classifier SE XML.xml"
# xml_path2 = r"C:\Users\lilif\OneDrive\Desktop\Dropbox\Phd\Pipeline testing\Old\Analysis preparation\Spectra Classifier LE XML.xml"

# output_directory = r"C:\Users\lilif\OneDrive\Desktop\Dropbox\Phd\Pipeline testing"
# concatenate_data(xml_path1, xml_path2, output_directory)