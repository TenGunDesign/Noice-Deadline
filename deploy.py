import os
import sys
import platform
import subprocess
import shutil


def main():
    copy_plugins_folder()
    copy_submission_folder()


def copy_plugins_folder():
    plugins_src = os.path.join(script_directory(), "src", "plugins", "Noice")
    plugins_dst = os.path.join(repository_root(), "custom", "plugins", "Noice")
    copy_directory(plugins_src, plugins_dst)


def copy_submission_folder():
    submission_src = os.path.join(script_directory(), "src", "submission")
    submission_dst = os.path.join(repository_root(), "custom", "scripts", "Submission")
    copy_directory(submission_src, submission_dst)


def copy_directory(src, dst):
    create_destination(dst)
    for file in os.listdir(src):
        src_path = os.path.join(src, file)
        dst_path = os.path.join(dst, file)
        shutil.copyfile(src_path, dst_path)


def create_destination(dst):
    try:
        os.mkdir(dst)
    except FileExistsError:
        pass


def script_directory():
    return os.path.dirname(os.path.realpath(__file__))


def repository_root():
    bin_dir = os.environ.get("DEADLINE_PATH")
    if bin_dir is None:
        print("DEADLINE_PATH variable is not set. Do you have Deadline installed?")
        sys.exit(-1)

    extension = ".exe" if platform.system() == "Windows" else ""
    program_name = "deadlinecommand{0}".format(extension)
    program_path = os.path.join(bin_dir, program_name)
    process = subprocess.run(
        [program_path, "GetRepositoryRoot"],
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL)

    if process.returncode != 0:
        print("Could not get repository path.")
        sys.exit(-1)

    return process.stdout.strip()


if __name__ == '__main__':
    main()
