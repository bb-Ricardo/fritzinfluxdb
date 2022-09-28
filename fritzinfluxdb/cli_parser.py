# -*- coding: utf-8 -*-
#  Copyright (c) 2022 - 2022 Ricardo Bartels. All rights reserved.
#
#  fritzinfluxdb.py
#
#  This work is licensed under the terms of the MIT license.
#  For a copy, see file LICENSE.txt included in this
#  repository or visit: <https://opensource.org/licenses/MIT>.


import os

from argparse import ArgumentParser, RawDescriptionHelpFormatter


def parse_command_line(version=None, self_description=None, version_date=None, url=None, default_config_file_path=None):
    """
    parse command line arguments, also add current version and version date to description

    Parameters
    ----------
    version: str
        version of this program
    self_description: str
        short self description of this program
    version_date: str
        release date of this version
    url: str
        project url
    default_config_file_path: str
        path to default config file

    Returns
    -------
    ArgumentParser object: with parsed command line arguments
    """

    # define command line options
    description = f"{self_description}\nVersion: {version} ({version_date})\nProject URL: {url}"

    parser = ArgumentParser(description=description, formatter_class=RawDescriptionHelpFormatter)

    parser.add_argument("-c", "--config", default=[], dest="config_file", nargs='+',
                        help=f"points to the config file to read config data from which is not installed "
                             f"under the default path '{default_config_file_path}'",
                        metavar=os.path.basename(default_config_file_path))

    parser.add_argument("-d", "--daemon", action='store_true',
                        help="define if the script is run as a systemd daemon")

    parser.add_argument("-v", "--verbose", action='count', default=0,
                        help="turn on verbose output to get debug logging. "
                             "Defining '-vv' will also print out all http calls")

    args = parser.parse_args()

    # fix supplied config file path
    fixed_config_files = list()
    for config_file in args.config_file:

        if config_file != default_config_file_path and config_file[0] != os.sep:
            config_file = os.path.realpath(os.getcwd() + os.sep + config_file)
        fixed_config_files.append(config_file)

    args.config_file = fixed_config_files

    return args

# EOF
