from pandas import read_excel
from os import path

def merge_data(files_path, data_id, snr_path, snr_id, fwhm_path=None, fwhm_id=None):
    print(">>> Merging data from SNR and FWHM files...")

    snr_data = read_excel(snr_path)
    print("    SNR data loaded.")
    if fwhm_path:
        fwhm_data = read_excel(fwhm_path)
        fwhm_data[fwhm_id] = fwhm_data[fwhm_id].astype(str)
        print("    FWHM data loaded.")
    else:
        fwhm_data = None
        print("    No FWHM data provided.")
    cases_data = read_excel(files_path)

    # Convert ID columns to string
    cases_data[data_id] = cases_data[data_id].astype(str)
    snr_data[snr_id] = snr_data[snr_id].astype(str)

    # '''Debug'''
    # print("SNR Data Sample:")
    # print(snr_data.head(5))  
    # # print("\nFWHM Data Sample:")
    # # print(fwhm_data.head(5))
    # print("\nCases Data Sample:")
    # print(cases_data.head(5))
    try:
        # Merge SNR data with cases data
        merged_data = cases_data.merge(
        snr_data[[snr_id, 'SNR']],
        left_on=data_id,
        right_on=snr_id,
        how='left'
    )
        # Drop duplicate ID column
        if data_id != snr_id and snr_id in merged_data.columns:
            merged_data = merged_data.drop(columns=[snr_id])
    except Exception as e:
        print(f"    Error during merging SNR data: {e}")
        return
    
    # Merge FWHM data if provided
    if fwhm_data is not None:
        try: 
            merged_data = merged_data.merge(
            fwhm_data[[fwhm_id, 'Linewidths']],
            left_on=data_id,
            right_on=fwhm_id,
            how='left'
        )
        
            # Drop duplicate ID column
            if data_id != fwhm_id and fwhm_id in merged_data.columns:
                merged_data = merged_data.drop(columns=[fwhm_id])

        except Exception as e:
            print(f"    Error during merging FWHM data: {e}")
            return
    
    print('>>> Successfully merged data from provided sources')

    return merged_data



def add_status(files_path, data_id, snr_path, snr_id, fwhm_path=None, fwhm_id=None, output_path=None, output_filename=None):
    merged_df= merge_data(files_path, data_id, snr_path, snr_id, fwhm_path, fwhm_id)
    print(">>> Adding status based on SNR and FWHM criteria...")
    if fwhm_path:
        print("    Cases are selected based on SNR > 10 and Linewidths < 8.")
        merged_df['Status'] = merged_df.apply(lambda row: 'Selected' if row['SNR'] > 10 and row['Linewidths'] < 8 else 'Discarded', axis=1)
    else:
        print("    Cases are selected based on SNR > 10.")
        merged_df['Status'] = merged_df.apply(lambda row: 'Selected' if row['SNR'] > 10 else 'Discarded', axis=1)

    if output_path and output_filename:
        output_file = path.join(output_path, output_filename)
        merged_df.to_excel(output_file, index=False)
        print(f">>> Output saved to {output_file}")




if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Add status to cases based on SNR and FWHM criteria")
    parser.add_argument('--cases', type=str, required=True, help='Path to the Excel file containing case data.')
    parser.add_argument('--data_id', type=str, required=True, help='Column name for case IDs in the case data file.')
    parser.add_argument('--snr_path', type=str, required=True, help='Path to the Excel file containing SNR data.')
    parser.add_argument('--snr_id', type=str, required=True, help='Column name for case IDs in the SNR data file.')
    parser.add_argument('--fwhm_path', type=str, default=None, help='Path to the Excel file containing FWHM data (optional).')
    parser.add_argument('--fwhm_id', type=str, default=None, help='Column name for case IDs in the FWHM data file (required if fwhm_path is provided).')
    parser.add_argument('--output', type=str, required=True, help='Directory to save the output Excel file.')
    parser.add_argument('--filename', type=str, required=True, help='Output Excel filename (with .xlsx extension).')

    args = parser.parse_args()
    add_status(files_path=args.cases, data_id=args.data_id, snr_path=args.snr_path, snr_id=args.snr_id, fwhm_path=args.fwhm_path, fwhm_id=args.fwhm_id, output_path=args.output, output_filename=args.filename)

# #Non-command line usage example
# #files_path = r"C:\Users\lilif\OneDrive\Desktop\Dropbox\Phd\Pipeline testing\SingleVoxel_IDs.xlsx"
# files_path = r"C:\Users\lilif\OneDrive\Desktop\Dropbox\Phd\Pipeline testing\Validation_MRUI_echo_SE.xlsx"
# snr_path = r"C:\Users\lilif\OneDrive\Desktop\Dropbox\Phd\Pipeline testing\Quality Control SNR\Test1_SV_SNR.xlsx"
# fwhm_path = r"C:\Users\lilif\OneDrive\Desktop\Dropbox\Phd\Pipeline testing\FWHM\FWHM_results_se_batch1.xlsx"

# snr_id = 'Case_ID'
# fwhm_id = 'SignalName'
# data_id = 'UAB_ID'
# output_path = r"C:\Users\lilif\OneDrive\Desktop\Dropbox\Phd\Pipeline testing\Quality Control SNR"
# output_filename = "merged_output_fwhm.xlsx"

# add_status(files_path=files_path, data_id=data_id, snr_path=snr_path, snr_id=snr_id, fwhm_path=None, fwhm_id=fwhm_id, output_path=output_path, output_filename=output_filename)