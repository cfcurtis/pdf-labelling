# Marusia Luciuk (mluci567@mtroyal.ca)                                                                                                                                                                      

import os, shutil, csv, fitz
import pdf_to_imgs
import multiprocessing

def read_directory(directory: str, csv_filename: str) -> list:
    " Read in filenames to be mapped from input directory "
    # Get list of filenames already present in the CSV
    csv_files = set()
    with open(csv_filename, 'r', newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            csv_files.add(row[0])
    # Add only files that are not already present in the CSV
    file_names = []
    for file in os.listdir(directory):
        if file.endswith('.pdf') and not file.startswith('._') and file not in csv_files and file not in file_names:
            file_names.append(file)

    return file_names

def get_origin_dir() -> str:
    " Input path to directory to be processed "

    directory = input("directory path: ")
    while not os.path.exists(directory):
        print("invalid directory path, please try again")
        directory = input("directory path: ")

    return directory

def get_csv_filename() -> str:
    " Input path to .csv file "

    csv_filename = input("csv filename path: ")
    while not os.path.exists(csv_filename):
        print("invalid csv filename path, please try again")
        csv_filename = input("csv filename path: ")

    return csv_filename

def get_newdir() -> str:
    " Get destination directory for processed files "

    newdir = input("enter path for new directory: ")
    if not os.path.exists(newdir):
        os.makedirs(newdir)

    return newdir

def get_filenum(csv_filename: str) -> int:
    " Get last filename and extract file number to increment "

    with open(csv_filename, 'r', newline='') as csvfile:
        reader = csv.reader(csvfile)
        data = list(reader) #2d list where each row represents a line in the csv file, 
                            # with two colums, one for the original filename and one for the updated filename 
    try:
        last_row = data[-1] #blank line issue, definitely a better way to do this                                                                                                                           
    except IndexError:
        last_row = data[-2]

    last_name = last_row[-1]
    
    last_name = ''.join(filter(str.isdigit,(f'{last_name}')))

    new_num = (int(last_name)) + 1

    return new_num

def process_csv(csv_filename: str, file_names: list, directory: str, newdir: str) -> None:
    " Write original and new filenames to .csv file, then copy renamed files to new directory "

    new_num = get_filenum(csv_filename)

    #write original filename and new filenames to csv                                                                                                                                                       
    with open(csv_filename, 'a', encoding='UTF8') as csvf:
        for file in file_names:
            new_name = '{:04d}.pdf'.format(new_num)

            writer = csv.writer(csvf, quoting=csv.QUOTE_ALL)
            writer.writerow([file, new_name])

            try:
                og_path = (f'{directory}/{file}')
                intermediate_path = (f'{newdir}/{file}')
                new_path = (f'{newdir}/{new_name}')

                shutil.copy(og_path, newdir)
                os.rename(intermediate_path, new_path)

            except PermissionError:
                assert os.path.isfile(og_path)
                assert os.path.isfile(intermediate_path)
                assert os.path.isfile(new_path)

                shutil.copy(og_path, newdir)
                os.rename(intermediate_path, new_path)

            except FileNotFoundError:
               print(f"{file} does not exist.")

            new_num += 1

    return

"""
def convert_to_img(newdir: str) -> None:
    " convert renamed pdfs to img using pdf_to_imgs (old method) "

    for file in os.listdir(newdir):
        if file.endswith('.pdf'):
            try:
                conversion_path = (f'{newdir}/{file}')
                pdf_to_imgs.main(conversion_path)
            except PermissionError:
                assert os.path.isfile(conversion_path) #permission workaround                                                                                                                               
                pdf_to_imgs.main(conversion_path)
            except fitz.fitz.FileDataError:
                print(f"FileDataError: cannot open broken document {file}")

    return
"""

def convert_file_to_img(file_path):
    " convert single file to img using pdf_to_imgs "
    try:
        pdf_to_imgs.main(file_path)
    except PermissionError:
        assert os.path.isfile(file_path) #permission workaround                                                                                                                               
        pdf_to_imgs.main(file_path)
    except fitz.fitz.FileDataError:
        print(f"FileDataError: cannot open broken document {file_path}")

def convert_to_img(newdir: str, file_names: list) -> None:
    " convert directory of renamed pdfs to img using pdf_to_imgs (using multiprocessing) "

    file_paths = [os.path.join(newdir, file) for file in os.listdir(newdir) if file.endswith('.pdf')and file in file_names]

    with multiprocessing.Pool() as pool:  # not sure if this is actually faster or more efficient, but it might be 
        pool.map(convert_file_to_img, file_paths)

def main() -> None:
    use_preset_paths = input("use preset paths? y/n: ")

    if use_preset_paths == 'y':
        directory = "/projects/pattern-labelling/documents/gdrive_sync" #updated default directory path 
        csv_filename = "/projects/pattern-labelling/documents/processed_pdfs/filename_mapping.csv"
        newdir = "/projects/pattern-labelling/documents/processed_pdfs"
    else:
        # these will be consolidated into one general function later
        directory = get_origin_dir()
        csv_filename = get_csv_filename()
        newdir = get_newdir()

    file_names = read_directory(directory, csv_filename)
    process_csv(csv_filename, file_names, directory, newdir)
    convert_to_img(newdir, file_names)

if __name__ == "__main__":
    main()
