import logging
import json
import os
import progressbar
import validators

from python_utils.terminal import get_terminal_size
from ._errors import ImplementationError

CHUNK_SIZE = 1024

''' Models '''

class HTTPMethods():
    """
    Supported HTTP Methods
    """

    GET  = 'get'
    HEAD = 'head'
    POST = 'post'

    values = ['get', 'head', 'post']

class HTTPResponse():
    """
    Supported HTTP Responses
    """

    RAW  = 'raw'
    TEXT = 'text'
    JSON = 'json'

    values = ['raw', 'text', 'json']

class DownloadData():
    """
    Wrapper to require the download of a file.
    """
    def __init__(self, path, method, url, params=None, data=None):
        """
        Init a download request.

        Params:
            path (str)   : Path where save the downloaded file
            method (str) : HTTP Method to use for download (HTTPMethods.GET or HTTPMethods.POST)
            url (str)    : URL where retrieve the content
            params       : Dictionary or bytes to be sent in the query string (GET data)
            data         : Dictionary or list of tuples ``[(key, value)]`` (will be form-encoded), bytes, or file-like object to send in the body (POST data)
        """

        # Check and set method
        if method in (HTTPMethods.GET, HTTPMethods.POST):
            self._method = method
        else:
            raise ImplementationError('DownloadData: the method "{}" is invalid'.format(method))

        # Check and set path
        if (path and is_string(path)):
            self._path = path
        else:
            raise ImplementationError('DownloadData: the path "{}" is invalid'.format(path))

        # Check and set URL
        if validators.url(url):
            self._url = url
        else:
            raise ImplementationError('DownloadData: the url "{}" is invalid'.format(url))

        # Check and set params
        if params is None or isinstance(params, (dict, str, bytes)):
            self._params = params
        else:
            raise ImplementationError('DownloadData: the params "{}" is invalid'.format(params))

        # Check and set data
        if data is None or (isinstance(data, (dict, list)) and all(len(x)==2 for x in data)):
            self._data = data
        else:
            raise ImplementationError('DownloadData: the data "{}" is invalid'.format(data))

    def __repr__(self):
        return "<path={} ; method={} ; URL={} ; params={} ; data={}>" \
        .format(self._path, self._method, self._url, self._params, self._data)

    __str__ = __repr__

    @property
    def method(self):
        return self._method

    @property
    def url(self):
        return self._url

    @property
    def params(self):
        return self._params

    @property
    def data(self):
        return self._data

    @property
    def path(self):
        return self._path

def dl_get(path, url, params=None, data=None):
    """
    Shortcut to make a DownloadData object which provides a GET request.

    All params meaning are the same of DownloadData '__init__' method.
    """
    return DownloadData(
            path,
            HTTPMethods.GET,
            url,
            params,
            data
        )

def dl_post(filename, url, params=None, data=None):
    """
    Shortcut to make a DownloadData object which provides a POST request.

    All params meaning are the same of DownloadData '__init__' method.
    """
    return DownloadData(
            path,
            HTTPMethods.POST,
            url,
            params,
            data
        )

def download_progressbar(total_size):
    """
    Create a progress bar to show in real-time a download status
    """

    # Compute DownaloadProgressBar max value
    if total_size <= 0:
        max_val = progressbar.UnknownLength
    else:
        max_val = int(total_size/CHUNK_SIZE)

    # DownaloadProgressBar settings
    MARKER          = '█'
    PREFIXES        = ('', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')[1:]
    POLL_INTERVAL   = 0.8

    # DownaloadProgressBar spacing
    LEFT_SPACE          = 4
    PERCENTAGE_SPACE    = 4
    PRE_BAR_SPACE       = 1
    BAR_SPACE           = 35
    POST_BAR_SPACE      = 1
    DATA_SIZE_SPACE     = 8
    PRE_SPEED_SPACE     = 1
    SPEED_SPACE         = 8

    # Compute right spacing, and ensure that is not negative
    try:
        right_space = int(get_terminal_size()[0]) - \
        LEFT_SPACE - PERCENTAGE_SPACE - PRE_BAR_SPACE - BAR_SPACE - \
        POST_BAR_SPACE - DATA_SIZE_SPACE - PRE_SPEED_SPACE - SPEED_SPACE
        if right_space < 0:
            right_space = 0
    except (ValueError, TypeError, ArithmeticError):
        right_space = 0

    # Define DownaloadProgressBar skin
    bar_skin=([
        LEFT_SPACE * ' ',
        progressbar.Percentage(),
        PRE_BAR_SPACE * ' ',
        progressbar.Bar(marker=MARKER),
        POST_BAR_SPACE * ' ',
        progressbar.DataSize(prefixes=PREFIXES),
        PRE_SPEED_SPACE * ' ',
        progressbar.AdaptiveTransferSpeed(prefixes=PREFIXES),
        right_space * ' '
        ])

    # Generate DownaloadProgressBar
    return progressbar.ProgressBar(
        max_value=max_val, widgets=bar_skin, poll_interval=POLL_INTERVAL)


''' OS '''

from subprocess import run, CalledProcessError
import os, winreg, winvers

class WinEnvPath():
    """
    Utility class to edit Windows Environment "Path" variable.

    Version:
        0.1

    Warning:
        - Requires Python v3.3 or newer
        - Requires Windows XP SP2 or newer
        - To edit the variable, you must be Administrator

    Sources:
        https://docs.python.org/3.6/library/winreg.html#value-types
        https://docs.python.org/3.6/library/winreg.html#access-rights
        https://docs.python.org/3.6/library/winreg.html#winreg.OpenKeyEx
        https://docs.python.org/3.6/library/winreg.html#winreg.QueryValueEx
        https://docs.python.org/3.6/library/winreg.html#winreg.SetValueEx
        https://docs.python.org/3.6/library/winreg.html#winreg.FlushKey
    """

    def __init__(self):
        self._root_key      = winreg.HKEY_LOCAL_MACHINE
        self._sub_key       = r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment'
        self._value_name    = 'PATH'
        self._update_cmd    = 'cmd /c RefreshEnv.bat'
        self._paths         = []
        self._load()

    def _load(self):
        """
        Load System Path from registry and put it in the '_paths' attribute.

        Params:
            None

        Returns:
            None
        """
        with winreg.OpenKeyEx(self._root_key, self._sub_key, 0, winreg.KEY_READ) as key:
            value, _ = winreg.QueryValueEx(key, self._value_name)
        if value.endswith(';'):
            value = value[:-1]
        self._paths = sorted(value.split(os.pathsep))

    def _save(self):
        """
        Save '_paths' System Path into registry.

        Params:
            None

        Returns:
            None
        """
        value = os.pathsep.join(self._paths) + ';'
        with winreg.OpenKeyEx(self._root_key, self._sub_key, 0, winreg.KEY_WRITE) as key:
            winreg.SetValueEx(key, self._value_name, 0, winreg.REG_EXPAND_SZ, value)
            winreg.FlushKey(key)
        try:
            # Refresh System Path on currect shells
            with open(os.devnull, 'w') as devnull:
                run(self._update_cmd, stdout=devnull, stderr=devnull, shell=True, check=True)
        except CalledProcessError:
            raise WindowsError('Cannot propagate System Path changes. Restart all opened shells to see the changes.')

    def get(self):
        """
        Get System Path value as a list.

        Params:
            None

        Returns:
            list: system path value
        """
        return self._paths[:]

    def get_str(self):
        """
        Get System Path value as a string.

        Params:
            None

        Returns:
            str: system path value
        """
        return os.pathsep.join(self._paths) + ';'

    def add(self, path):
        """
        Add a path in the System Path.

        Params:
            path (str): path to add

        Returns:
            None

        Raises:
            WindowsError
        """
        if not os.path.isdir(path):
            raise WindowsError('The path "{}" not exist or is not a dir'.format(path))
        if path in self._paths:
            return
        try:
            self._paths = sorted(self._paths + [path])
            self._save()
        except ValueError as ex:
            raise WindowsError(ex)

    def remove(self, path):
        """
        Remove a path from the System Path.

        Params:
            path (str): path to remove

        Returns:
            None

        Raises:
            WindowsError
        """
        if not os.path.exists(path):
            raise WindowsError('The path "{}" not exist, so cannot be contained in the system path'.format(path))
        if not path in self._paths:
            return
        try:
            self._paths.remove(path)
            self._save()
        except ValueError as ex:
            raise WindowsError(ex)

# Edited version of shutil.copytree(...), that allow folders overwrite
from shutil import copy2 as _default_copy
def copytree(src, dst, symlinks=False, ignore=None, copy_function=_default_copy,
             ignore_dangling_symlinks=False):
    """Recursively copy a directory tree.
    The destination directory must not already exist.
    If exception(s) occur, an Error is raised with a list of reasons.
    If the optional symlinks flag is true, symbolic links in the
    source tree result in symbolic links in the destination tree; if
    it is false, the contents of the files pointed to by symbolic
    links are copied. If the file pointed by the symlink doesn't
    exist, an exception will be added in the list of errors raised in
    an Error exception at the end of the copy process.
    You can set the optional ignore_dangling_symlinks flag to true if you
    want to silence this exception. Notice that this has no effect on
    platforms that don't support os.symlink.
    The optional ignore argument is a callable. If given, it
    is called with the `src` parameter, which is the directory
    being visited by copytree(), and `names` which is the list of
    `src` contents, as returned by os.listdir():
        callable(src, names) -> ignored_names
    Since copytree() is called recursively, the callable will be
    called once for each directory that is copied. It returns a
    list of names relative to the `src` directory that should
    not be copied.
    The optional copy_function argument is a callable that will be used
    to copy each file. It will be called with the source path and the
    destination path as arguments. By default, copy2() is used, but any
    function that supports the same signature (like copy()) can be used.
    """
    from shutil import copystat, copy2, Error

    names = os.listdir(src)
    if ignore is not None:
        ignored_names = ignore(src, names)
    else:
        ignored_names = set()

    # EDIT: Allow folder overwriting
    if not os.path.isdir(dst):
        os.makedirs(dst)

    errors = []
    for name in names:
        if name in ignored_names:
            continue
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        try:
            if os.path.islink(srcname):
                linkto = os.readlink(srcname)
                if symlinks:
                    # We can't just leave it to `copy_function` because legacy
                    # code with a custom `copy_function` may rely on copytree
                    # doing the right thing.
                    os.symlink(linkto, dstname)
                    copystat(srcname, dstname, follow_symlinks=not symlinks)
                else:
                    # ignore dangling symlink if the flag is on
                    if not os.path.exists(linkto) and ignore_dangling_symlinks:
                        continue
                    # otherwise let the copy occurs. copy2 will raise an error
                    if os.path.isdir(srcname):
                        copytree(srcname, dstname, symlinks, ignore,
                                 copy_function)
                    else:
                        copy_function(srcname, dstname)
            elif os.path.isdir(srcname):
                copytree(srcname, dstname, symlinks, ignore, copy_function)
            else:
                # Will raise a SpecialFileError for unsupported file types
                copy_function(srcname, dstname)
        # catch the Error from the recursive copytree so that we can
        # continue with other files
        except Error as err:
            errors.extend(err.args[0])
        except OSError as why:
            errors.append((srcname, dstname, str(why)))
    try:
        copystat(src, dst)
    except OSError as why:
        # Copying file access times may fail on Windows
        if getattr(why, 'winerror', None) is None:
            errors.append((src, dst, str(why)))
    if errors:
        raise Error(errors)
    return dst


''' Time '''

def format_time(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return '%02d:%02d:%02d' % (h, m, s)


''' Check '''

def is_string(x):
    return isinstance(x, str)

def is_dict(x):
    return isinstance(x, dict)

def is_set(x):
    return isinstance(x, set)

def is_list(x):
    return isinstance(x, list)

def is_dl_data(x):
    return isinstance(x, DownloadData)

def is_int(x):
    try:
        int(x)
        return True
    except ValueError:
        return False

def is_float(x):
    try:
        float(x)
        return True
    except ValueError:
        return False

def is_two_power(n):
	return is_int(n) and n != 0 and ((n & (n - 1)) == 0)

def is_divisible(n, d):
    try:
        return n % d == 0
    except (ValueError, ArithmeticError):
        return False
