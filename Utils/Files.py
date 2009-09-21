"""
file convenience routines
"""
import os


__all__ = ["upload", "download"]
CHUNK_SIZE = 1300 # to fit in one ethernet frame

#
# exceptions
#
class UploadError(Exception):
    pass
class DownloadError(Exception):
    pass

#
# API
#
def upload(conn, localpath, remotepath, *a, **k):
    """
    uploads a file or a directory recursively (depending on what `localpath` is)
    an optional `extentions` keyword argument may be given, specifying the 
    extensions of the files to be uploaded (relevant to directories only). if
    no extentions are given, all files will be uploaded.
    """
    if os.path.isdir(localpath):
        upload_dir(conn, localpath, remotepath, *a, **k)
    elif os.path.isfile(localpath):
        upload_file(conn, localpath, remotepath, *a, **k)
    else:
        raise UploadError("can only upload files or directories")

def download(conn, remotepath, localpath, *a, **k):
    """
    downloads a file or a directory recursively (depending on what `remotepath` is)
    an optional `extentions` keyword argument may be given, specifying the 
    extensions of the files to be downloaded (relevant to directories only). if
    no extentions are given, all files will be downloaded.
    """
    if conn.modules.os.path.isdir(remotepath):
        download_dir(conn, remotepath, localpath, *a, **k)
    elif conn.modules.os.path.isfile(remotepath):
        download_file(conn, remotepath, localpath, *a, **k)
    else:
        raise DownloadError("can only download files or directories")

#
# internal
#
def upload_file(conn, localpath, remotepath):
    lf = open(localpath, "rb")
    rf = conn.modules.__builtin__.open(remotepath, "wb")
    while True:
        chunk = lf.read(CHUNK_SIZE)
        if not chunk:
            break
        rf.write(chunk)
    lf.close()
    rf.close()

def download_file(conn, remotepath, localpath):
    lf = open(localpath, "wb")
    rf = conn.modules.__builtin__.open(remotepath, "rb")
    while True:
        chunk = rf.read(CHUNK_SIZE)
        if not chunk:
            break
        lf.write(chunk)
    lf.close()
    rf.close()

def upload_dir(conn, localpath, remotepath, extensions = [""]):
    # create the remote path
    if not conn.modules.os.path.exists(remotepath):
        conn.modules.os.makedirs(remotepath)
    
    # upload files and directories
    for fn in os.listdir(localpath):
        lfn = os.path.join(localpath, fn)
        rfn = conn.modules.os.path.join(remotepath, fn)
        
        if os.path.isdir(lfn):
            upload_dir(conn, lfn, rfn, extensions)
        
        elif os.path.isfile(lfn):
            for ext in extensions:
                if fn.endswith(ext):
                    upload_file(conn, lfn, rfn)
                    break

def download_dir(conn, remotepath, localpath, extensions = [""]):
    # create the local path
    if not os.path.exists(localpath):
        os.makedirs(localpath)
    
    # download files and directories
    for fn in conn.modules.os.listdir(remotepath):
        lfn = os.path.join(localpath, fn)
        rfn = conn.modules.os.path.join(remotepath, fn)
        
        if conn.modules.os.path.isdir(lfn):
            download_dir(conn, rfn, lfn, extensions)
        
        elif conn.modules.os.path.isfile(lfn):
            for ext in extensions:
                if fn.endswith(ext):
                    download_file(conn, rfn, lfn)
                    break


