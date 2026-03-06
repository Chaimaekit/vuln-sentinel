import subprocess
import os


#source code ext as non binary
SOURCE_EXTENSIONS = {
    ".c", ".cpp", ".h", ".py", ".js", ".ts",
    ".java", ".go", ".rb", ".php", ".cs", ".rs"
}


def is_binary(filepath):
    """
    Returns True if file is a compiled binary.
    Uses two checks:
    1. File extension
    2. 'file' command output
    """
    ext = os.path.splitext(filepath)[1].lower()
    if ext in SOURCE_EXTENSIONS:
        return False

    result = subprocess.getoutput(f"file {filepath}")
    binary_keywords = ["ELF", "executable", "binary", "compiled"]
    return any(keyword in result for keyword in binary_keywords)


def get_file_type(filepath):
    """
    Returns a human readable file type string.
    """
    return subprocess.getoutput(f"file {filepath}")


def is_analyzable(filepath):
    """
    Returns True if we can actually analyze this file.
    Skips things like images, archives, empty files.
    """
    if os.path.getsize(filepath) == 0:
        return False

    file_type = get_file_type(filepath).lower()

    skip_keywords = [#not treated type of files
        "image", "jpeg", "png", "gif",
        "zip", "tar", "gzip", "archive",
        "audio", "video", "mp4", "mp3"
    ]
    return not any(keyword in file_type for keyword in skip_keywords)