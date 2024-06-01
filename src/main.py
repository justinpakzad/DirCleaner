import argparse
import shutil
import calendar
from pathlib import Path
from categories import file_cats
from datetime import datetime
from collections import defaultdict


def backup_dir(
    source_dir: str, backup_dir: str, create_backup_dir: bool = False
) -> None:
    """Back up the entire source directory to the backup directory, with an option to create a backup directory."""
    home_path = Path.home()
    source_path = home_path.joinpath(source_dir)
    backup_path = home_path.joinpath(backup_dir)
    try:
        if create_backup_dir:
            if source_path.is_dir() and not backup_path.exists():
                shutil.copytree(source_path, backup_path)
            else:
                print(
                    "Source path is not a directory or backup directory already exists"
                )
        else:
            if source_path.is_dir() and backup_path.is_dir():
                for item in source_path.iterdir():
                    d = backup_path / item.name
                    if item.resolve() == backup_path.resolve():
                        continue
                    elif item.is_dir():
                        shutil.copytree(item, d, dirs_exist_ok=True)
                    else:
                        shutil.copy(item, d)
        print(f"Backup of {source_path} created successfully at {backup_path}")
    except Exception as e:
        print(f"Error backing up directory: {e}")


def check_empty(source_path: Path) -> bool:
    """Check if the directory is empty or only contains system files like .DS_Store."""
    return all(item.name == ".DS_Store" for item in source_path.iterdir()) or not any(
        source_path.iterdir()
    )


def delete_empty_dirs(source_path: Path) -> None:
    """Delete all empty subdirectories within the specified path."""
    directories = [d for d in source_path.rglob("*") if d.is_dir()]
    directories.sort(key=lambda x: len(x.parts), reverse=True)
    for item in directories:
        if check_empty(item):
            shutil.rmtree(item)


def get_source_path(home_path: str, source_dir: str) -> Path:
    """Construct the full path to the source directory under the user's home directory."""
    return Path(home_path).joinpath(source_dir)


def clean_dir_by_suffix(source_dir: str, shallow: bool = False) -> dict:
    """Organize files by their suffix into respective directories."""
    source_path = get_source_path(Path.home(), source_dir)
    files_by_suffix_dict = defaultdict(list)
    if not source_path.is_dir():
        print("Directory does not exist")
        return files_by_suffix_dict

    files = source_path.glob("*") if shallow else source_path.rglob("*")
    for item in files:
        if item.is_file():
            file_suffix = item.suffix[1:].lower()
            for folder, suffixes in file_cats.items():
                if file_suffix in suffixes:
                    files_by_suffix_dict[folder].append(item)

    return files_by_suffix_dict


def clean_dir_by_date(
    source_dir: str, year_only: bool = False, shallow: bool = False
) -> dict:
    """Organize files by their creation date into yearly or monthly directories."""
    source_path = get_source_path(Path.home(), source_dir)
    files_by_date_dict = defaultdict(list)
    if not source_path.is_dir():
        print("Directory does not exist")
        return files_by_date_dict

    files = source_path.glob("*") if shallow else source_path.rglob("*")
    for item in files:
        if item.is_file():
            creation_date = datetime.fromtimestamp(item.stat().st_birthtime)
            if year_only:
                year = creation_date.year
                files_by_date_dict[str(year)].append(item)
            else:
                year_month = (
                    f"{calendar.month_name[creation_date.month]}_{creation_date.year}"
                )
                files_by_date_dict[year_month].append(item)
    return files_by_date_dict


def clean_dir_by_size(source_dir: str, shallow: bool = False) -> dict:
    """Categorize files by size into small, medium, or large."""
    source_path = get_source_path(Path.home(), source_dir)
    files_by_size_dict = defaultdict(list)

    if not source_path.is_dir():
        print("Directory does not exist")
        return files_by_size_dict

    files = source_path.glob("*") if shallow else source_path.rglob("*")
    for item in files:
        if item.is_file():
            mb = round((item.stat().st_size) / 1000000, 2)
            if mb < 1:
                files_by_size_dict["small_files"].append(item)
            elif mb >= 1 and mb < 100:
                files_by_size_dict["medium_files"].append(item)
            else:
                files_by_size_dict["large_files"].append(item)
    return files_by_size_dict


def move_files_to_dir(source_dir: str, files_dict: dict[list]) -> None:
    """Move files into directories based on a classification, and remove empty directories afterwards."""
    source_path = get_source_path(Path.home(), source_dir)
    for date, items in files_dict.items():
        for item in items:
            if item.is_file():
                destination_folder = source_path / date
                destination_folder.mkdir(exist_ok=True)
                shutil.move(item, destination_folder / item.name)
    delete_empty_dirs(source_path)


def delete_files_by_time(
    source_dir: str, n_days: int = None, n_months: int = None, n_years: int = None
) -> None:
    """Delete files that are older than the specified number of days."""
    source_path = get_source_path(Path.home(), source_dir)
    files = source_path.rglob("*")
    memory_saved = []
    for item in files:
        if item.is_file():
            creation_date = datetime.fromtimestamp(item.stat().st_birthtime)
            time_diff = datetime.now() - creation_date
            mb = (item.stat().st_size) / 1000000
            if n_days:
                if time_diff.days >= n_days:
                    memory_saved.append(mb)
                    item.unlink()
            elif n_months:
                if (time_diff.days / 30) >= n_months:
                    memory_saved.append(mb)
                    item.unlink()
            elif n_years:
                if (time_diff.days / 365) >= n_years:
                    memory_saved.append(mb)
                    item.unlink()
            else:
                print("Time period not specified")

    if sum(memory_saved) >= 1000:
        print(
            f"{len(memory_saved)} files have been deleted and {round(sum(memory_saved) / 1000,2)} GB have been made available."
        )
    else:
        print(
            f"{len(memory_saved)} files have been deleted and {round(sum(memory_saved),2)} MB have been made available."
        )
    delete_empty_dirs(source_path)


def confirm_cleaning(directory):
    inp = input(f"Please confirm the cleaning of {directory} (yes/no) ")
    return inp.lower().strip() in ["y", "yes"]


def confirm_backup(directory):
    inp = input(f"Please confirm the backup of {directory}(yes/no) ")
    return inp.lower() in ["y", "yes"]


def confirm_deletion(
    directory,
):
    inp = input(f"Please confirm the deletion of files from {directory} (yes/no) ")
    return inp.lower().strip() in ["y", "yes"]


def get_args():
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument(
        "--backup", action="store_true", help="Create a backup before making changes"
    )
    parent_parser.add_argument(
        "--backup_dir", help="The directory where the backup will be stored"
    )

    parser = argparse.ArgumentParser(description="Folder cleanser")
    subparsers = parser.add_subparsers(dest="command", help="Sub-command help")

    suffix_parser = subparsers.add_parser("clean_by_suffix", parents=[parent_parser])
    suffix_parser.add_argument(
        "--source_dir", help="The directory to clean", required=True
    )
    suffix_parser.add_argument(
        "--shallow",
        help="Perform a shallow clean (do not traverse subdirectories)",
        action="store_true",
    )

    date_parser = subparsers.add_parser("clean_by_date", parents=[parent_parser])
    date_parser.add_argument(
        "--source_dir", help="The directory to clean", required=True
    )

    date_parser.add_argument(
        "--year_only",
        help="Clean directory by year only rather than the default month and year",
        action="store_true",
    )
    date_parser.add_argument(
        "--shallow",
        help="Perform a shallow clean (do not traverse subdirectories)",
        action="store_true",
    )

    size_parser = subparsers.add_parser("clean_by_size", parents=[parent_parser])
    size_parser.add_argument(
        "--source_dir", help="The directory to clean", required=True
    )
    size_parser.add_argument(
        "--shallow",
        help="Perform a shallow clean (do not traverse subdirectories)",
        action="store_true",
    )

    delete_files_parser = subparsers.add_parser("delete_files", parents=[parent_parser])
    delete_files_parser.add_argument(
        "--source_dir", help="The directory to clean", required=True
    )
    delete_files_time_group = delete_files_parser.add_mutually_exclusive_group(
        required=True
    )
    delete_files_time_group.add_argument(
        "--n_days",
        type=int,
        help="The age of the files you want to delete in days (i.e., delete everything more than 10 days old)",
    )
    delete_files_time_group.add_argument(
        "--n_months",
        type=int,
        help="The age of the files you want to delete in months",
    )
    delete_files_time_group.add_argument(
        "--n_years",
        type=int,
        help="The age of the files you want to delete in years",
    )
    return parser


def main():
    parser = get_args()
    args = parser.parse_args()
    if args.backup and args.backup_dir:
        if confirm_backup(args.source_dir):
            backup_dir(args.source_dir, args.backup_dir, args.create_backup_dir)

    if args.command == "clean_by_suffix":
        if confirm_cleaning(args.source_dir):
            suffix_dict = clean_dir_by_suffix(args.source_dir, args.shallow)
            move_files_to_dir(args.source_dir, suffix_dict)
    elif args.command == "clean_by_date":
        if confirm_cleaning(args.source_dir):
            date_dict = clean_dir_by_date(args.source_dir, args.year_only, args.shallow)
            move_files_to_dir(args.source_dir, date_dict)
    elif args.command == "clean_by_size":
        if confirm_cleaning(args.source_dir):
            size_dict = clean_dir_by_size(args.source_dir, args.shallow)
            move_files_to_dir(args.source_dir, size_dict)
    elif args.command == "delete_files":
        if confirm_deletion(args.source_dir):
            if args.n_days:
                delete_files_by_time(args.source_dir, n_days=int(args.n_days))
            elif args.n_months:
                delete_files_by_time(args.source_dir, n_months=int(args.n_months))
            elif args.n_years:
                delete_files_by_time(args.source_dir, n_years=int(args.n_years))
            else:
                print("Invalid time period")

    else:
        print("No valid commands were given for more info please check --help")


if __name__ == "__main__":
    main()
