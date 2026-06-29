from pathlib import Path
from os import path
from py_compile import main
from pandas import DataFrame, concat
from numpy import nan
from re import search

def delete_empty_lines(filepath):
    """Remove empty lines from a text file."""
    with open(filepath, 'r') as infile:
        newlines = [line for line in infile if line.strip()]
    with open(filepath, 'w') as outfile:
        outfile.writelines(newlines)
    print(f"\n>>> Empty lines removed from {filepath}\n")



def get_save_FWHM(hp_file, raw_file, parameter, output, outfilename):
    """Extract FWHM values from a QC file and match them with signal names from a raw file."""
    print(">>> Extracting FWHM values...")
    file_name_QC = Path(hp_file).stem
    
    column_extr = parameter
    column_read = []
    
    with open(hp_file) as input_data:
        print(f">>> Processing HLSVDPRO file: {file_name_QC}")
        hp_file = delete_empty_lines(hp_file)
        for line in input_data:
            if line.strip():
                break
        for line in input_data:
            if line.startswith(column_extr):
                break
        for line in input_data:
            if search("^[a-zA-Z]", line):
                break
            column_read.append(float(line))
    
    df = DataFrame(column_read, columns=[column_extr])
    
    with open(raw_file, 'r') as f:
        print(f">>> Reading signal file: {Path(raw_file).stem}")
        
        for line in f:
            if line.startswith('DatasetsInFile:'):
                number_of_signal = int(line.split(': ')[1])
                break
    
    signals = [f'Signal {i}' for i in range(1, number_of_signal + 1)]
    
    with open(raw_file, 'r') as f:
        for line in f:
            if line.startswith('SignalNames'):
                text = line
                break
    
    cases = text.split(': ')[1].split(';')
    labels = [elem.split('-')[0] for elem in cases if not elem.startswith('SignalNames')]
    
    df1 = DataFrame(labels, columns=['SignalName'])
    df1.replace('\n', nan, regex=True, inplace=True)
    df1.dropna(inplace=True)
    
    cases_fwhm = concat([df1, df], axis=1)
    
    for index, row in cases_fwhm.iterrows():
        print(f"    {parameter} for {row['SignalName']} found: {row[column_extr]}")
    
    outfilename = outfilename + ".xlsx"
    file_path = path.join(output, outfilename)

    cases_fwhm.to_excel(file_path, index=False)
    print(f"\n>>> Extracted linewidths saved to {file_path}")
    
    return cases_fwhm

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Extract FWHM from HLSVDPRO file and match with signal names from raw file")
    parser.add_argument("--hp_file", type=str, help="Path to the HLSVDPRO file containing FWHM values")
    parser.add_argument("--raw_file", type=str, help="Path to the raw file containing signal names")
    parser.add_argument("--parameter", type=str, help="Parameter to extract from the HLSVDPRO file")
    parser.add_argument("--output", type=str, help="Output folder to save the results")
    parser.add_argument("--outfilename", type=str, help="Output filename (without extension)")
    
    args = parser.parse_args()
    
    get_save_FWHM(args.hp_file, args.raw_file, args.parameter, args.output, args.outfilename)

# # Example usage:
# hp_file = r"C:\Users\lilif\OneDrive\Desktop\Dropbox\Phd\Pipeline testing\FWHM\Q-se-batch1.txt" #Process the files with HLSVDPro and save all results in txt file
# raw_file = r"C:\Users\lilif\OneDrive\Desktop\Dropbox\Phd\Pipeline testing\FWHM\se-batch1.txt" #Open the water files and save the metabolites without any other step (only this way we have file names)
# output = r"C:\Users\lilif\OneDrive\Desktop\Dropbox\Phd\Pipeline testing\FWHM"

# get_save_FWHM(hp_file, raw_file, "Linewidths", output, "FWHM_results_se_batch1")
