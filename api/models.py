"""
api/models.py
"""
from django.conf import settings

import datetime
import time
import os
import logging
import plistlib
from xml.parsers.expat import ExpatError

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

from munkiwebadmin.utils import MunkiGit
from process.utils import record_status

REPO_DIR = settings.MUNKI_REPO_DIR

LOGGER = logging.getLogger('munkiwebadmin')

try:
    GIT = settings.GIT_PATH
except AttributeError:
    GIT = None

class FileError(Exception):
    '''Class for file errors'''
    pass


class FileReadError(FileError):
    '''Error reading a file'''
    pass


class FileWriteError(FileError):
    '''Error writing a file'''
    pass


class FileDeleteError(FileError):
    '''Error deleting a file'''
    pass


class FileDoesNotExistError(FileError):
    '''Error when file doesn't exist at pathname'''
    pass


class FileAlreadyExistsError(FileError):
    '''Error when creating a new file at an existing pathname'''
    pass


def is_yaml_file(filepath):
    """Check if a file path has a YAML extension"""
    if not filepath:
        return False
    file_extension = os.path.splitext(filepath)[1].lower()
    return file_extension in ['.yaml', '.yml']


def is_likely_yaml_content(content):
    """Detect if file content is likely YAML based on content analysis"""
    if not content:
        return False
    
    content = content.strip()
    
    # Check for YAML document separator
    if content.startswith('---'):
        return True
    
    # Check for XML/plist header
    if content.startswith('<?xml') or content.startswith('<plist'):
        return False
    
    # Look for YAML-style key-value patterns (key: value)
    lines = content.split('\n')[:10]
    yaml_like_lines = 0
    xml_like_lines = 0
    
    for line in lines:
        trimmed_line = line.strip()
        if not trimmed_line or trimmed_line.startswith('#'):
            continue  # Skip empty lines and comments
        
        # YAML patterns
        if ':' in trimmed_line and not trimmed_line.startswith('<'):
            yaml_like_lines += 1
        
        # XML/plist patterns
        if trimmed_line.startswith('<') and trimmed_line.endswith('>'):
            xml_like_lines += 1
    
    # If we see more YAML-like patterns than XML-like, probably YAML
    return yaml_like_lines > xml_like_lines


def read_plist_or_yaml(filepath):
    """Read a file that could be either plist or YAML format using smart detection"""
    if not os.path.exists(filepath):
        raise FileDoesNotExistError('%s not found' % filepath)
    
    try:
        with open(filepath, 'r') as fileref:
            content = fileref.read()
    except (IOError, OSError) as err:
        raise FileReadError('Could not read %s: %s' % (filepath, err))
    
    # Try to determine format based on file extension first
    prefer_yaml = is_yaml_file(filepath)
    
    # If no extension hint, use content detection
    if not prefer_yaml and not filepath.endswith('.plist'):
        prefer_yaml = is_likely_yaml_content(content)
    
    if prefer_yaml and YAML_AVAILABLE:
        # Try YAML first, fallback to plist
        try:
            return yaml.safe_load(content)
        except yaml.YAMLError:
            # YAML failed, try plist
            try:
                return plistlib.loads(content.encode('utf-8'))
            except (ExpatError, IOError):
                # Both failed, return empty dict
                return {}
    else:
        # Try plist first, fallback to YAML
        try:
            return plistlib.loads(content.encode('utf-8'))
        except (ExpatError, IOError):
            # Plist failed, try YAML if available
            if YAML_AVAILABLE:
                try:
                    return yaml.safe_load(content)
                except yaml.YAMLError:
                    # Both failed, return empty dict
                    return {}
            else:
                # No YAML support, return empty dict
                return {}


def write_plist_or_yaml(data, filepath, prefer_yaml=False):
    """Write data as either YAML or plist format"""
    if prefer_yaml and YAML_AVAILABLE:
        # Write as YAML
        try:
            yaml_content = yaml.dump(data, default_flow_style=False, indent=2, 
                                   allow_unicode=True, sort_keys=False)
            return yaml_content
        except yaml.YAMLError as err:
            raise FileWriteError('Could not serialize as YAML: %s' % err)
    else:
        # Write as plist
        try:
            return plistlib.dumps(data).decode('utf-8')
        except Exception as err:
            raise FileWriteError('Could not serialize as plist: %s' % err)


def get_file_format_info(filepath):
    """Returns a dictionary with file format information"""
    info = {
        'format': 'unknown',
        'can_read_yaml': YAML_AVAILABLE,
        'extension': os.path.splitext(filepath)[1].lower()
    }
    
    if not os.path.exists(filepath):
        return info
    
    try:
        with open(filepath, 'r') as fileref:
            content = fileref.read(1000)  # Read first 1000 chars for detection
    except (IOError, OSError):
        return info
    
    if is_yaml_file(filepath):
        info['format'] = 'yaml'
    elif filepath.endswith('.plist'):
        info['format'] = 'plist'
    elif is_likely_yaml_content(content):
        info['format'] = 'yaml'
    elif content.strip().startswith('<?xml') or content.strip().startswith('<plist'):
        info['format'] = 'plist'
    else:
        info['format'] = 'unknown'
    
    return info


class Plist(object):
    '''Pseudo-Django object'''
    @classmethod
    def list(cls, kind):
        '''Returns a list of available plists'''
        kind_dir = os.path.join(REPO_DIR, kind)
        plists = []
        for dirpath, dirnames, filenames in os.walk(kind_dir):
            record_status(
                '%s_list_process' % kind,
                message='Scanning %s...' % dirpath[len(kind_dir)+1:])
            # don't recurse into directories that start with a period.
            dirnames[:] = [name for name in dirnames
                           if not name.startswith('.')]
            subdir = dirpath[len(kind_dir):].lstrip(os.path.sep)
            if os.path.sep == '\\':
                plists.extend([os.path.join(subdir, name).replace('\\', '/')
                               for name in filenames
                               if not name.startswith('.')])
            else:
                plists.extend([os.path.join(subdir, name)
                               for name in filenames
                               if not name.startswith('.')])
        return plists

    @classmethod
    def new(cls, kind, pathname, user, plist_data=None):
        '''Returns a new plist object'''
        filepath = os.path.join(REPO_DIR, kind, os.path.normpath(pathname))
        if os.path.exists(filepath):
            raise FileAlreadyExistsError(
                '%s/%s already exists!' % (kind, pathname))
        plist_parent_dir = os.path.dirname(filepath)
        if not os.path.exists(plist_parent_dir):
            try:
                # attempt to create missing intermediate dirs
                os.makedirs(plist_parent_dir)
            except (IOError, OSError) as err:
                createerrortimestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
                LOGGER.error('%s - %s: Create failed for %s/%s: %s', createerrortimestamp, user, kind, pathname, err)
                raise FileWriteError(err)
        if plist_data:
            plist = plist_data
        else:
            # create a useful empty plist
            if kind == 'manifests':
                plist = {}
                for section in [
                        'catalogs', 'included_manifests', 'managed_installs',
                        'managed_uninstalls', 'managed_updates',
                        'optional_installs']:
                    plist[section] = []
            elif kind == "pkgsinfo":
                plist = {
                    'name': 'ProductName',
                    'display_name': 'Display Name',
                    'description': 'Product description',
                    'version': '1.0',
                    'catalogs': ['development']
                }
        
        # Determine if we should create as YAML based on filename or preference
        prefer_yaml = False
        if pathname.endswith('.yaml') or pathname.endswith('.yml'):
            prefer_yaml = True
        elif not pathname.endswith('.plist'):
            # No explicit extension, check global preference
            try:
                prefer_yaml = getattr(settings, 'PREFER_YAML_FORMAT', False)
            except AttributeError:
                prefer_yaml = False
        
        data = write_plist_or_yaml(plist, filepath, prefer_yaml)
        try:
            with open(filepath, 'w') as fileref:
                fileref.write(data)
            createtimestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
            format_type = 'YAML' if prefer_yaml else 'plist'
            LOGGER.info('%s - %s: Created %s/%s as %s', createtimestamp, user, kind, pathname, format_type)
            if user and GIT:
                MunkiGit().add_file_at_path(filepath, user)
        except (IOError, OSError) as err:
            createerrortimestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
            LOGGER.info('%s - %s: Create failed for %s/%s: %s', createerrortimestamp, user, kind, pathname, err)
            raise FileWriteError(err)
        return data

    @classmethod
    def read(cls, kind, pathname):
        '''Reads a plist or YAML file and returns the data as a dictionary'''
        filepath = os.path.join(REPO_DIR, kind, os.path.normpath(pathname))
        try:
            return read_plist_or_yaml(filepath)
        except FileDoesNotExistError:
            raise FileDoesNotExistError('%s/%s not found' % (kind, pathname))
        except (FileReadError, FileWriteError) as err:
            LOGGER.error('Read failed for %s/%s: %s', kind, pathname, err)
            raise FileReadError(err)

    @classmethod
    def write(cls, data, kind, pathname, user):
        '''Writes a text data to (plist) file'''
        filepath = os.path.join(REPO_DIR, kind, os.path.normpath(pathname))
        plist_parent_dir = os.path.dirname(filepath)
        if not os.path.exists(plist_parent_dir):
            try:
                # attempt to create missing intermediate dirs
                os.makedirs(plist_parent_dir)
            except OSError as err:
                LOGGER.error('Create failed for %s/%s: %s', kind, pathname, err)
                raise FileWriteError(err)
        try:
            with open(filepath, 'w') as fileref:
                fileref.write(data)
            writetimestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
            LOGGER.info('%s - %s: Wrote %s/%s', writetimestamp, user, kind, pathname)
            if user and GIT:
                MunkiGit().add_file_at_path(filepath, user)
        except (IOError, OSError) as err:
            writeerrortimestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
            LOGGER.error('%s - %s: Write failed for %s/%s: %s', writeerrortimestamp, user, kind, pathname, err)
            raise FileWriteError(err)

    @classmethod
    def write_object(cls, data_object, kind, pathname, user, prefer_yaml=None):
        '''Writes a data object as plist or YAML file based on preference'''
        if prefer_yaml is None:
            # Check if there's a global preference
            try:
                prefer_yaml = getattr(settings, 'PREFER_YAML_FORMAT', False)
            except AttributeError:
                prefer_yaml = False
        
        # Override preference based on file extension if present
        if pathname.endswith('.yaml') or pathname.endswith('.yml'):
            prefer_yaml = True
        elif pathname.endswith('.plist'):
            prefer_yaml = False
        
        filepath = os.path.join(REPO_DIR, kind, os.path.normpath(pathname))
        plist_parent_dir = os.path.dirname(filepath)
        if not os.path.exists(plist_parent_dir):
            try:
                # attempt to create missing intermediate dirs
                os.makedirs(plist_parent_dir)
            except OSError as err:
                LOGGER.error('Create failed for %s/%s: %s', kind, pathname, err)
                raise FileWriteError(err)
        
        try:
            # Generate the file content in the appropriate format
            file_content = write_plist_or_yaml(data_object, filepath, prefer_yaml)
            
            with open(filepath, 'w') as fileref:
                fileref.write(file_content)
            writetimestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
            format_type = 'YAML' if prefer_yaml else 'plist'
            LOGGER.info('%s - %s: Wrote %s/%s as %s', writetimestamp, user, kind, pathname, format_type)
            if user and GIT:
                MunkiGit().add_file_at_path(filepath, user)
        except (IOError, OSError) as err:
            writeerrortimestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
            LOGGER.error('%s - %s: Write failed for %s/%s: %s', writeerrortimestamp, user, kind, pathname, err)
            raise FileWriteError(err)

    @classmethod
    def delete(cls, kind, pathname, user):
        '''Deletes a plist file'''
        filepath = os.path.join(REPO_DIR, kind, os.path.normpath(pathname))
        if not os.path.exists(filepath):
            raise FileDoesNotExistError(
                '%s/%s does not exist' % (kind, pathname))
        try:
            os.unlink(filepath)
            deletetimestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
            LOGGER.info('%s - %s: Deleted %s/%s', deletetimestamp, user, kind, pathname)
            if user and GIT:
                MunkiGit().delete_file_at_path(filepath, user)
        except (IOError, OSError) as err:
            deleteerrortimestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
            LOGGER.error('%s - %s: Delete failed for %s/%s: %s', deleteerrortimestamp, user, kind, pathname, err)
            raise FileDeleteError(err)


class MunkiFile(object):
    '''Pseudo-Django object'''
    @classmethod
    def get_fullpath(cls, kind, pathname):
        '''Returns full filesystem path to requested resource'''
        return os.path.join(REPO_DIR, kind, pathname)

    @classmethod
    def list(cls, kind):
        '''Returns a list of available plists'''
        files_dir = os.path.join(REPO_DIR, kind)
        files = []
        for dirpath, dirnames, filenames in os.walk(files_dir):
            # don't recurse into directories that start with a period.
            dirnames[:] = [name for name in dirnames if not name.startswith('.')]
            subdir = dirpath[len(files_dir):].lstrip(os.path.sep)
            if os.path.sep == '\\':
                files.extend([os.path.join(subdir, name).replace('\\', '/')
                              for name in filenames
                              if not name.startswith('.')])
            else:
                files.extend([os.path.join(subdir, name)
                              for name in filenames
                              if not name.startswith('.')])
        return files

    @classmethod
    def new(cls, kind, fileupload, pathname, user):
        '''Creates a new file from a file upload; returns
        FileAlreadyExistsError if the file already exists at the path'''
        filepath = os.path.join(REPO_DIR, kind, os.path.normpath(pathname))
        if os.path.exists(filepath):
            raise FileAlreadyExistsError(
                '%s/%s already exists!' % (kind, pathname))
        file_parent_dir = os.path.dirname(filepath)
        if not os.path.exists(file_parent_dir):
            try:
                # attempt to create missing intermediate dirs
                os.makedirs(file_parent_dir)
            except (IOError, OSError) as err:
                LOGGER.error(
                    'Create failed for %s/%s: %s', kind, pathname, err)
                raise FileWriteError(err)
        cls.write(kind, fileupload, pathname, user)

    @classmethod
    def write(cls, kind, fileupload, pathname, user):
        '''Retreives a file upload and saves it to pathname'''
        filepath = os.path.join(REPO_DIR, kind, os.path.normpath(pathname))
        try:
            with open(filepath, 'w') as fileref:
                for chunk in fileupload.chunks():
                    fileref.write(chunk)
            writetimestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
            LOGGER.info('%s - %s: Wrote %s/%s', writetimestamp, user, kind, pathname)
        except (IOError, OSError) as err:
            writeerrortimestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
            LOGGER.info('%s - %s: Write failed for %s/%s: %s', writeerrortimestamp, user, kind, pathname, err)
            raise FileWriteError(err)

    @classmethod
    def writedata(cls, kind, filedata, pathname, user):
        '''Retreives a file upload and saves it to pathname'''
        filepath = os.path.join(REPO_DIR, kind, os.path.normpath(pathname))
        try:
            with open(filepath, 'w') as fileref:
                fileref.write(filedata)
            writedatatimestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
            LOGGER.info('%s - %s: Wrote %s/%s', writedatatimestamp, user, kind, pathname)
        except (IOError, OSError) as err:
            writedataerrortimestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
            LOGGER.info('%s - %s: Write failed for %s/%s: %s', writedataerrortimestamp, user, kind, pathname, err)
            raise FileWriteError(err)

    @classmethod
    def delete(cls, kind, pathname, user):
        '''Deletes file at pathname'''
        filepath = os.path.join(REPO_DIR, kind, os.path.normpath(pathname))
        if not os.path.exists(filepath):
            raise FileDoesNotExistError(
                '%s/%s does not exist' % (kind, pathname))
        try:
            os.unlink(filepath)
            deletedatatimestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
            LOGGER.info('%s - %s: Deleted %s/%s', deletedatatimestamp, user, kind, pathname)
        except (IOError, OSError) as err:
            deletedataerrortimestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
            LOGGER.info('%s - %s: Delete failed for %s/%s: %s', deletedataerrortimestamp, user, kind, pathname, err)
            raise FileDeleteError(err)
        
