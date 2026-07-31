import argparse
from pathlib import Path
from numpy import array, concatenate
from PIL import Image
import matplotlib.pyplot as plt
from os import path, listdir, makedirs
from datetime import datetime

def display4im(output_directory,filepath1, filepath2, filepath3=None, filepath4=None):
    image_count = 0
    failed_images = {}
    #Extract filenames
    filename1=Path(filepath1).stem
    try:
        img1 = array(Image.open(filepath1).convert('RGB'))
        # Get size of img2 and resize others to match
        target_height, target_width = img1.shape[:2]
    
    except Exception as e:
            print(f'Error processing {filepath1}: {str(e)}')
            failed_images[filepath1] = str(e)
            return
            
    try:
        filename2=Path(filepath2).stem
        img2 = array(Image.open(filepath2).convert('RGB'))
        image_count+=2
        if img2.shape[:2] != (target_height, target_width):
            img2 = array(Image.fromarray(img2).resize((target_width, target_height), Image.LANCZOS))
            print(f'Image {filename2} resized to match {filename1}')
    except Exception as e:
            print(f'Error processing {filepath2}: {str(e)}')
            failed_images[filepath2] = str(e)
            return
    
    if filepath3:
        try:
            filename3=Path(filepath3).stem
            img3 = array(Image.open(filepath3).convert('RGB'))
            image_count+=1
            if img3.shape[:2] != (target_height, target_width):
                img3 = array(Image.fromarray(img3).resize((target_width, target_height), Image.LANCZOS))
        except Exception as e:
            print(f'Error processing {filepath3}: {str(e)}')
            failed_images[filepath3] = str(e)
            return
    

    if filepath4:
        try:
            filename4=Path(filepath4).stem
            image_count+=1
            img4 = array(Image.open(filepath4).convert('RGB'))
            if img4.shape[:2] != (target_height, target_width):
                img4 = array(Image.fromarray(img4).resize((target_width, target_height), Image.LANCZOS))
        except Exception as e:
            print(f'Error processing {filepath4}: {str(e)}')
            failed_images[filepath4] = str(e)
            return
    try:    
        # Concatenate images horizontally
        if filepath3 and filepath4:
            combined = concatenate([img1, img2, img3, img4], axis=1)
        elif filepath3:
            combined = concatenate([img1, img2, img3], axis=1)
        else:
            combined = concatenate([img1, img2], axis=1)
    except Exception as e:
        print(f'Error concatenating images: {str(e)}')
        return

    # Create figure with exact aspect ratio
    height, width = combined.shape[:2]
    dpi = 300
    figsize = (width/dpi, height/dpi)

    fig, ax = plt.subplots(1, 1, figsize=figsize, dpi=dpi)
    ax.imshow(combined)
    ax.axis('off')

    #Addig titles
    # Add titles using text annotations
    title_y = -0.02  # Position above image
    ax.text(target_width/2, title_y * height, filename1, 
            ha='center', va='bottom', fontweight='bold', fontsize=50, transform=ax.transData)
    ax.text(target_width + target_width/2, title_y * height, filename2, 
            ha='center', va='bottom', fontweight='bold', fontsize=50, transform=ax.transData)

    if filepath3:
        ax.text(2*target_width + target_width/2, title_y * height, filename3, 
                ha='center', va='bottom', fontweight='bold', fontsize=50, transform=ax.transData)
    
    if filepath4:
        ax.text(3*target_width + target_width/2, title_y * height, filename4, 
                ha='center', va='bottom', fontweight='bold', fontsize=50, transform=ax.transData)    
    # Save figure
    outname = f'{filename1}.png'
    outfull = path.join(output_directory, outname)
    plt.savefig(outfull, bbox_inches='tight', pad_inches=0.1, facecolor='white', dpi=dpi)
    plt.close(fig)

    print(f'>>> Saved: {outfull}')

    if failed_images:
        failed_cases_file = path.join(output_directory, "failed_images.txt")
        with open(failed_cases_file, 'w', encoding='utf-8') as f:
            f.write(f"Failed DICOM Cases Log - {datetime.now()}\n\n")
            for case, errors in failed_images.items():
                f.write(f"Case: {case}\n")
                for error_info in errors:
                    f.write(f"    File: {error_info['filename']} - Error: {error_info['error']}\n")
                f.write("\n")
        print(f">>> Failed cases logged to {failed_cases_file}")
    




def plolt_directory(output_directory, filedir1, filedir2, filedir3=None, filedir4=None):
    print(f'>>> Start matching process between directories')
    if not path.exists(output_directory):
        makedirs(output_directory, exist_ok=True)
    
    try:
        image_files1 = sorted([f for f in listdir(filedir1) if f.endswith(('.png', '.jpg', '.jpeg'))])
    except Exception as e:
        print(f"Error accessing input directory: {str(e)}")
        return
    
    try:
        image_files2 = sorted([f for f in listdir(filedir2) if f.endswith(('.png', '.jpg', '.jpeg'))])
    except Exception as e:
        print(f"Error accessing input directory: {str(e)}")
        return
    
    if filedir3:
        try:
            image_files3 = sorted([f for f in listdir(filedir3) if f.endswith(('.png', '.jpg', '.jpeg'))])
        except Exception as e:
            print(f"Error accessing input directory: {str(e)}")
            return
    if filedir4:
        try:
            image_files4 = sorted([f for f in listdir(filedir4) if f.endswith(('.png', '.jpg', '.jpeg'))])
        except Exception as e:
            print(f"Error accessing input directory: {str(e)}")
            return

    number_of_matches = 0
    nomatches = []

    # Process each file from dir1
    for k, refFile in enumerate(image_files1, 1):
        print(f'\n>>> Processing file {k}/{len(image_files1)}: {refFile}')
        filename = Path(refFile).stem
        if '-S' in filename:
            parts = filename.split('-S')
            extracted_id = parts[0] + '-S' + parts[1].split('-')[0]  # Keep base + '-S' + number
            suffix = '-' + '-'.join(parts[1].split('-')[1:]) if '-' in parts[1] else ''
        elif '-' in filename:
            extracted_id = filename.split('-')[0]
            suffix = '-' + '-'.join(filename.split('-')[1:])
        else:
            extracted_id = filename
            suffix = ''  # No suffix
        
        print(f'    Extracted case ID: {extracted_id}')

        firstFilePath = path.join(filedir1, refFile)
        matchingSecond = [f for f in image_files2 if f.startswith(extracted_id)]
        
        # Check for required match in dir2
        if not matchingSecond:
            print(f'   Warning: No matches found in dir2 for {refFile}')
            nomatches.append(refFile)
            continue
        
        # Get optional matches
        if filedir3:
            matchingThird = [f for f in image_files3 if f.startswith(extracted_id)]
            if not matchingThird:
                print(f'   Warning: No matches found in dir3 for {refFile}')
                nomatches.append(refFile)
                continue
        else:
            matchingThird = []
        
        if filedir4:
            matchingFourth = [f for f in image_files4 if f.startswith(extracted_id)]
            if not matchingFourth:
                print(f'   Warning: No matches found in dir4 for {refFile}')
                nomatches.append(refFile)
                continue
        else:
            matchingFourth = []

        # Build file paths
        secondFilePath = path.join(filedir2, matchingSecond[0])
        thirdFilePath = path.join(filedir3, matchingThird[0]) if filedir3 and matchingThird else None
        fourthFilePath = path.join(filedir4, matchingFourth[0]) if filedir4 and matchingFourth else None

        # Report if multiple matches found
        if len(matchingSecond) > 1:
            print(f'   Note: Multiple matches in dir2 for {refFile}: {matchingSecond}')
            print(f'     Using: {matchingSecond[0]}')
        if matchingThird and len(matchingThird) > 1:
            print(f'   Note: Multiple matches in dir3 for {refFile}: {matchingThird}')
            print(f'     Using: {matchingThird[0]}')
        if matchingFourth and len(matchingFourth) > 1:
            print(f'   Note: Multiple matches in dir4 for {refFile}: {matchingFourth}')
            print(f'     Using: {matchingFourth[0]}')         

        print(f'\n    Found matches:')
        print(f'    Reference file: {refFile}')
        print(f'              Dir2: {matchingSecond[0]}')
        if matchingThird:
            print(f'              Dir3: {matchingThird[0]}')
        if matchingFourth:
            print(f'              Dir4: {matchingFourth[0]}')
        
        # Actually call the display function!
        number_of_matches += 1
        display4im(output_directory, firstFilePath, secondFilePath, thirdFilePath, fourthFilePath)

    # After the loop, report results
    print(f'\n>>> Processing complete!')
    print(f'>>> Total matches found {number_of_matches}')
    if nomatches:
        print(f'>>> Files with no matches: {len(nomatches)}')
        for f in nomatches:
            print(f'    - {f}')

# if __name__ == "__main__":
#     import argparse
#     parser = argparse.ArgumentParser(description='Plot and combine images from multiple directories.')
#     parser.add_argument('--output', type=str, required=True, help='Directory to save  the combined images.')
#     parser.add_argument('--filedir1', type=str, required=True, help='First input directory containing images.')
#     parser.add_argument('--filedir2', type=str, required=True, help='Second input directory containing images.')
#     parser.add_argument('--filedir3', type=str, default=None, help='Optional third input directory containing images.')
#     parser.add_argument('--filedir4', type=str, default=None, help='Optional fourth input directory containing images.')
#     args = parser.parse_args()  
#     plolt_directory(output_directory=args.output, filedir1=args.filedir1, filedir2=args.filedir2, filedir3=args.filedir3, filedir4=args.filedir4)


f2= r"C:\Users\Lili\Dropbox\Phd\Pseudoprogression\Segm_G\Image_0.8"
f3 = r"C:\Users\Lili\Dropbox\Phd\Pseudoprogression\Segm_G\MRSgrid_0.8"
f1 = r"C:\Users\Lili\Dropbox\Phd\DATA_MV\pseudoprogression_lt\Segmentation\MRS images"
od = r"C:\Users\Lili\Dropbox\Phd\Pseudoprogression\Segm_G\Combined"

plolt_directory(filedir1=f1, filedir2=f2, filedir3=f3, output_directory=od)