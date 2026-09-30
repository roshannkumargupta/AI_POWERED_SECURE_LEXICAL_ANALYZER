import tarfile
def unpack_archive(archive_path: str, dest_dir: str):
    with tarfile.open(archive_path) as tar:
        tar.extractall(dest_dir)
