# Downloading mdbtools
import subprocess
import platform
import os
import tarfile
from urllib.request import urlretrieve
import sys
import pandas as pd

# Need to run:
# cp libmdb.so.2.0.1 libmdb.so.2
# cp libiconv.so.2.6.1 libiconv.so.2
# And repackage the tar file
def read_synergi_data(database_name, table_name):
    operating_system = platform.system()
    current_dir = os.path.realpath(os.path.dirname(__file__))
    if operating_system == "Windows":
        cmd = [os.path.join(current_dir, 'mdbtools', "mdb-export.exe"), database_name, table_name]
    else:    
        cmd = [os.path.join(current_dir, 'mdbtools','bin', "mdb-export"), database_name, table_name]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    return pd.read_csv(proc.stdout)


def download_mdbtools():
    current_dir = os.path.realpath(os.path.dirname(__file__))
    tar_file_name = os.path.join(current_dir, "mdbtools.tar.gz")
    mdb_dir = os.path.join(current_dir, "mdbtools")
    
    if platform.system() == "Windows":
        url = "https://github.com/kdheepak/mdbtools/releases/download/download/mdbtools-win.tar.gz"
    elif platform.system() == "Darwin":
        url = "https://github.com/kdheepak/mdbtools/releases/download/download/mdbtools-osx.tar.gz"
    else:
        url = "https://github.com/kdheepak/mdbtools/releases/download/download/mdbtools-linux.tar.gz"

    if os.path.exists(mdb_dir):
        print("mdbtools folder already exists. Skipping download")
        return
    print("Downloading mdbtools")
    urlretrieve(url, tar_file_name)
    print("Extracting mdbtools")
    with tarfile.open(tar_file_name) as tf:
        def is_within_directory(directory, target):
            
            abs_directory = os.path.abspath(directory)
            abs_target = os.path.abspath(target)
        
            prefix = os.path.commonprefix([abs_directory, abs_target])
            
            return prefix == abs_directory
        
        def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
        
            for member in tar.getmembers():
                member_path = os.path.join(path, member.name)
                if not is_within_directory(path, member_path):
                    raise Exception("Attempted Path Traversal in Tar File")
        
            tar.extractall(path, members, numeric_owner=numeric_owner) 
            
        
        safe_extract(tf, mdb_dir)
