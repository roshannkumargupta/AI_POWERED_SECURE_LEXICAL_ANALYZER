import tarfile, os
def unpack_safe(archive_path: str, dest_dir: str):
    with tarfile.open(archive_path) as tar:
        for member in tar.getmembers():
            if not os.path.abspath(os.path.join(dest_dir, member.name)).startswith(dest_dir):
                raise ValueError("Path traversal attempt")
        tar.extractall(dest_dir)
