"""
description:
  Compare and update repo to match template.

example:
    borg compare
    borg update
    borg generate <FILE>
"""

import argparse
import filecmp
import os
import logging
import shutil
import sys
import tempfile
import tomllib

from os import makedirs
from os.path import basename, dirname, join, splitext
from pathlib import Path
from urllib.parse import urljoin

import requests

TMPDIR = tempfile.TemporaryDirectory(prefix='borg')

TMP_FILES: dict[str, list] = {}

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_URL = "https://raw.githubusercontent.com/" + \
                "techservicesillinois/borg-repo-sync/refs/heads/" + \
                "main/default.borg.toml"


def get_remote_config(url):
    '''Download remote configuration file to tmpdir.'''

    logger.debug(f"Fetching remote config file {url}")
    response = requests.get(url)

    if response.status_code == 200:
        filename = join(TMPDIR.name, '.borg.toml')
        directory = dirname(filename)

        makedirs(directory, exist_ok=True)
        with open(filename, 'wb') as f:
            f.write(response.content)
    else:
        print(f"Expected remote config file is missing: {url}")
        print(f"HTTP Status code: {response.status_code}")
        exit(1)

    return filename


def remote_download(url, path):
    '''Download files from remote url to tmpdir. '''

    logger.debug(f"Fetching remote file {url}{path}")
    response = requests.get(urljoin(url, path))

    if response.status_code == 200:
        filename = join(TMPDIR.name, path)
        directory = dirname(filename)

        makedirs(directory, exist_ok=True)
        with open(filename, 'wb') as f:
            f.write(response.content)
    else:
        print(f"Expected remote file is missing: {path}. ( {url}{path} )")
        print(f"HTTP Status code: {response.status_code}")
        exit(1)

    return filename


def compare_repo(args):
    '''Compare unchanging files to template files'''
    differ = False

    for filename, tmpf in TMP_FILES.items():
        if not os.path.isfile(filename):
            print(f"{filename} is missing.", file=sys.stderr)
            differ = True
        else:
            if not filecmp.cmp(filename, tmpf, shallow=False):
                differ = True
                print(f"{filename} differs.", file=sys.stderr)

    results = warn_on_file_contents(args.file_contents)
    for warning in results:
        print(warning, file=sys.stderr)

    if len(results) > 0:
        differ = True

    if differ:
        sys.exit(1)
    else:
        sys.exit(0)


def update_repo(args):
    '''Update unchanging files to latest version from template'''
    for filename, tmpf in TMP_FILES.items():
        try:
            shutil.copyfile(tmpf, filename)
        except Exception as ex:
            print(f"Failed to update {filename}. {ex.message}",
                  file=sys.stderr)
            sys.exit(1)

    sys.exit(0)


def generate(args):
    msg = "# Ignore files managed by borg in Github PR reviews\n"
    files = args.gitattribute_files
    with open(args.FILE, "w") as file:
        if args.FILE == '.gitattributes':
            file.write(msg)
            if len(files) > 0:
                file.write(' linguist-generated\n'.join(files))
                file.write(' linguist-generated\n')


def directory(path):
    if not os.path.isdir(path):
        raise argparse.ArgumentTypeError(f"{path}: not a valid directory.")
    return path


class MakeDependencyFile(argparse.FileType):
    def __call__(self, path):
        return super().__call__(path + ".d")


def init_parser():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "-s",
        "--source-dir",
        type=directory,
        help="Local directory instead of remote git repository")
    parser.add_argument(
        "-u",
        "--config-url",
        type=str,
        default=DEFAULT_CONFIG_URL,
        help="Remote configuration file")
    parser.add_argument(
        "-c",
        "--config",
        default=".borg.toml",
        metavar="FILE",
        type=str,
        help="Open TOML config file")
    parser.add_argument(
        "-d",
        "--debug",
        action=argparse.BooleanOptionalAction,
        help="Print verbose debug output")
    subparsers = parser.add_subparsers()

    update = subparsers.add_parser('update', aliases=['up'])
    update.set_defaults(func=update_repo)

    compare = subparsers.add_parser('compare', aliases=['cmp'])
    compare.set_defaults(func=compare_repo)
    compare.add_argument(
        "-m",
        "--make-target",
        metavar="TARGET",
        type=MakeDependencyFile('w'),
        help="Writes a Makefile dependency TARGET.d file: "
        "TARGET.d will configure the TARGET to depend on "
        "the files checked by borg compare.")

    gen = subparsers.add_parser('generate', aliases=['gen'])
    gen.add_argument('FILE', choices=('.gitattributes', ),
                     help='Build certain template files')
    gen.set_defaults(func=generate)

    return parser


def exit_if_missing(file_path):
    if not os.path.isfile(file_path):
        print(f"Missing file in `--source-dir`: {file_path}",
              file=sys.stderr)
        exit(1)


def get_files_to_compare(config: dict):
    '''Returns a list of files to compare - subtracting skip_files from files.
        The template config is used to determine which files are included.
        Any file from the template config may be configured locally to be
        skipped.
    '''
    files = set(config.get('template', {}).get('files', []))
    skip_files = set(config.get('template', {}).get('skip_files', []))
    return sorted(files - skip_files)

def warn_on_file_contents(expect_contents: dict) -> list[str]:
    '''Returns False if any warnings are thrown.'''
    warnings = []
    for filename, expect_str in expect_contents:
        if not os.path.isfile(filename):
            warnings.append(f"{filename} is missing.")
        else:
            with open(filename, 'r') as f:
                if not expect_contents in f.readlines():
                    warnings.append(f"{filename} does not contain expected '{expect_str}'")

    # breakpoint()
    return warnings


def main():
    parser = init_parser()
    args = parser.parse_args()

    if (args.debug):
        logging.getLogger(__name__).addHandler(
            logging.StreamHandler(sys.stdout))
        logging.getLogger(__name__).setLevel(logging.DEBUG)
        logger.debug("Called with --debug. Printing verbose output.")

    if '.git' not in os.listdir(os.curdir):
        print("borg must run from repository root.")
        exit(1)

    config_file = None
    if Path(args.config).exists():
        logger.debug(f"borg configured from {args.config}")
        config_file = args.config
    else:
        logger.debug(f"borg configured from {args.config_url}")
        config_file = get_remote_config(args.config_url)

    with open(config_file, 'rb') as config_file:
        config = tomllib.load(config_file)

    files_url = config.get('template').get('files_url')

    if not files_url:
        print("borg config must provide `files_url`. "
              "Please add `files_url` to [template] in `.borg.toml`.")
        exit(1)

    if (not files_url.endswith('/')):
        print(f"Remote files URL must end in `/`: {files_url}."
              "Please correct `url` in `.borg.toml`.")
        exit(1)

    files_from_config = get_files_to_compare(config)
    args.file_contents = config.get('template', {}).get('file_contents', [])

    if hasattr(args, 'make_target') and args.make_target:
        target = splitext(basename(args.make_target.name))[0]
        print(f"{target}: {' '.join(files_from_config)}",
              file=args.make_target)

    for path in files_from_config:
        if args.source_dir:
            file_path = os.path.join(args.source_dir, path)
            exit_if_missing(file_path)
        else:
            file_path = remote_download(files_url, path)

        TMP_FILES[path] = file_path

    args.gitattribute_files = []
    config_generate = config.get('generate')
    config_gitattr = config_generate.get(
        'gitattributes') if config_generate else None

    if config_gitattr:
        args.gitattribute_files += config_gitattr.get('files', [])

        if config_gitattr['include_template_files']:
            args.gitattribute_files += config.get('template')['files']


    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help(sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
