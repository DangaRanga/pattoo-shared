# Importing python packages
from __future__ import print_function
import os
import shutil
import re
import getpass
from subprocess import check_output, call
from pathlib import Path
import yaml

# Importing installation libraries
from pattoo_shared.installation import shared


def _filepaths(directory, full_paths=True):
    """Get the filenames in the directory.

    Args:
        directory: Directory with the files
        full_paths: Give full paths if True

    Returns:
        result: List of filenames

    """
    # Initialize key variables
    if bool(full_paths) is True:
        result = [
            os.path.join(directory, filename) for filename in os.listdir(
                directory) if os.path.isfile(
                    os.path.join(directory, filename))]
    else:
        result = [filename for filename in os.listdir(
            directory) if os.path.isfile(os.path.join(directory, filename))]

    return result


def copy_service_files(target_directory, template_dir):
    """Copy service files to target directory.

    Args:
        target_directory: Target directory
        exec_dir: The directory the script is being executed in

    Returns:
        destination_filepaths: List of destination filepaths

    """
    # Initialize key variables
    src_dst = {}
    destination_filepaths = []

    # Determine the directory with the service files
   # source_directory = '{1}{0}systemd{0}system'.format(
       #         os.sep,
           #     os.path.abspath(os.path.join(exec_dir, os.pardir)))

    # Get source and destination file paths
    source_filepaths = _filepaths(template_dir)
    for filepath in source_filepaths:
        src_dst[filepath] = '{}/{}'.format(
            target_directory, os.path.basename(filepath))

    # Copy files
    for source_filepath, destination_filepath in sorted(src_dst.items()):
        shutil.copyfile(source_filepath, destination_filepath)
        destination_filepaths.append(destination_filepath)

    # Make systemd aware of the new services
    activation_command = 'systemctl daemon-reload'
    if getpass.getuser() == 'root':
        call(activation_command.split())

    # Return
    return destination_filepaths


def symlink_dir(directory):
    """Get directory in which the symlinked files are located.

    Args:
        directory: Directory with the symlinks

    Returns:
        result: Directory to which the files have symlinks

    """
    # Initialize key variables
    data_dictionary = {}
    result = None
    # Get all the filenames in the directory
    filenames = _filepaths(directory)

    # Get the name of the directory to which the files are symlinked
    for filename in filenames:
        if os.path.islink(filename) is False:
            continue
        if '/etc/systemd/system/multi-user.target.wants' not in filename:
            continue
        data_dictionary[Path(filename).resolve().absolute()] = True

    # Get the first directory in the dictionary
    for key in sorted(data_dictionary.keys()):
        if '/lib/' not in str(key):
            continue
        result = os.path.dirname(str(key))
        break
    # Die if there are no symlinks
    if bool(result) is False:
        shared.log(
            'No symlinks found in the directory: "{}"'.format(directory))
    return result


def update_environment_strings(
        filepaths, config_dir, pip_dir, username, group):
    """Update the environment variables in the filepaths files.

    Args:
        filepaths: List of filepaths
        config_dir: Directory where configurations will be stored
        pip_dir: The directory where the pip packages will be installed
        username: Username to run daemon
        group: Group of user to run daemon

    Returns:
        None

    """
    # Initialize key variables
    env_config_path = '^Environment="PATTOO_CONFIGDIR=(.*?)"$'
    env_pip_path = '^Environment="PYTHONPATH=(.*?)"$'
    env_user = '^User=(.*?)$'
    env_group = '^Group=(.*?)$'
    env_run = '^RuntimeDirectory=(.*?)$'

    execution_dir = os.path.dirname(os.path.realpath(__file__))
    install_dir = os.path.abspath(os.path.join(os.path.abspath(
            os.path.join(
                execution_dir, os.pardir)), os.pardir))

    # Do the needful
    for filepath in filepaths:
        # Read files and replace matches
        lines = []
        with open(filepath, 'r') as _fp:
            line = _fp.readline()

            while line:
                # Strip line
                _line = line.strip()

                # Fix the binary directory
                _line = _line.replace('INSTALLATION_DIRECTORY', install_dir)

                # Test PATTOO_CONFIGDIR
                if bool(re.search(env_config_path, line)) is True:
                    _line = 'Environment="PATTOO_CONFIGDIR={}"'.format(
                        config_dir)

                # Add Python path
                if bool(re.search(env_pip_path, line)) is True:
                    _line = 'Environment="PYTHONPATH={}"'.format(pip_dir)

                # Add RuntimeDirectory and create
                if bool(re.search(env_run, line)) is True:
                    (run_path,
                     relative_run_path) = _get_runtime_directory(config_dir)
                    _line = 'RuntimeDirectory={}'.format(relative_run_path)
                    if getpass.getuser == 'root':
                        os.makedirs(run_path, 0o750, exist_ok=True)
                        shutil.chown(run_path, user=username, group=group)

                # Add user
                if bool(re.search(env_user, line)) is True:
                    _line = 'User={}'.format(username)

                # Add group
                if bool(re.search(env_group, line)) is True:
                    _line = 'Group={}'.format(group)

                lines.append(_line)
                line = _fp.readline()

        # Write new output
        with open(filepath, 'w') as _fp:
            _fp.writelines('{}\n'.format(line) for line in lines)


def _get_runtime_directory(config_directory):
    """Get the RuntimeDirectory.

    Args:
        config_dir: Configuration directory

    Returns:
        tuple: (Path, Relative Path to /var/run)

    """
    result = None
    filepath = os.path.join(config_directory, 'pattoo.yaml')
    if os.path.isfile(filepath) is False:
        shared.log('{} does not exist'.format(filepath))
    with open(filepath, 'r') as file_handle:
        yaml_from_file = file_handle.read()
    config = yaml.safe_load(yaml_from_file)
    pattoo = config.get('pattoo')
    if bool(pattoo) is True:
        result = pattoo.get('system_daemon_directory')
    if result is None:
        shared.log('''\
"system_daemon_directory" parameter not found in the {} configuration file\
'''.format(filepath))
    _result = result.replace('/var/run/', '')
    _result = _result.replace('/run/', '')
    return (result, _result)


def preflight(config_dir, etc_dir):
    """Make sure the environment is OK.

    Args:
        config_dir: Location of the configuratiion directory
        etc_dir: Location of the systemd files

    Returns:
        None

    """
    # Make sure config_dir exists
    if os.path.isdir(config_dir) is False:
        shared.log('''\
Expected configuration directory "{}" does not exist.'''.format(config_dir))

    # Verify whether the script is being run by root or sudo user
    if bool(os.getuid()) is True:
        shared.log('This script must be run as the "root" user '
            'or with "sudo" privileges')

    # Check to see whether this is a systemd system
    try:
        check_output(['pidof', 'systemd'])
    except:
        shared.log('This is not a "systemd" system. This script should not be run.')

    # Check existence of /etc/systemd/system/multi-user.target.wants directory
    if os.path.isdir(etc_dir) is False:
        shared.log('Expected systemd directory "{}" does not exist.'.format(etc_dir))


def _check_symlinks(etc_dir, daemons):
    """Ensure the files in the etc dir are symlinks.

    Args:
        etc_dir: The directory that the symlinks are located in
        symlink_dir: The directory that the symlinks point to
        daemons: The list of system daemons

    Returns:
        None

    """
    for daemon in daemons:
        # Initialize key variables
        symlink_path = os.path.join(etc_dir, daemon)

        # Say what we are doing
        print('Checking if the {}.service file is a symlink '.format(daemon))
        link = os.path.islink('{0}.service'.format(symlink_path))
        if link is False:
            if getpass.getuser() != 'root':
                shared.log('Current user is not root')
            print('Creating symlink for {}'.format(daemon))
            # Create symlink if it doesn't exist
            shared.run_script('systemctl enable {}'.format(daemon))


def start_daemon(daemon_name):
    """Enable and start respective pattoo daemons.

    Args:
        daemon_name: The name of the daemon being started

    Returns:
        None

    """
    # Enable daemon
    shared.run_script('systemctl enable {}'.format(daemon_name))
    # Start daemon
    shared.run_script('systemctl start {}'.format(daemon_name))


def install_daemons(daemon_list, template_dir):
    """Installs and runs all daemons entered.

    Args:
        daemon_list: A list of the daemons to be run and installed
        template_dir: The directory the tempalte files are located in

    Returns:
        None

    """
    # Initialize key variables
    etc_dir = '/etc/systemd/system/multi-user.target.wants'
    config_dir = '/etc/pattoo'
    pip_dir = '/opt/pattoo-daemon/.python'

    # Make sure this system supports systemd and that
    # the required directories exist
    preflight(config_dir, etc_dir)

    # Check symlink location of files in that directory
    target_directory = symlink_dir(etc_dir)

    # Copy files
    destination_filepaths = copy_service_files(target_directory, template_dir)

    # Update the environment strings
    update_environment_strings(
        destination_filepaths,
        config_dir,
        pip_dir,
        'pattoo',
        'pattoo')

    # Perform daemon reload
    shared.run_script('systemctl daemon-reload')

    # Loop through daemon list and start daemons
    for daemon in daemon_list:
        start_daemon(daemon)

    # Check if symlinks got created
    _check_symlinks(etc_dir, daemon_list)
