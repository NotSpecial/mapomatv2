import hashlib
import pandas as pd
import pickle

from inspect import getsource
from os import path
from os import makedirs
import errno

PICKLE_PATH = 'pickles'


def _hash_frame(df, path="test"):
    cols = sorted(df.columns.tolist())
    idxs = sorted(df.index.tolist())

    # Return bytes
    return str(cols + idxs)


def _get_name(base_path=".", function=None, *args, **kwargs):
    # Get name first
    pickle_hash = hashlib.md5()
    # args
    for arg in args:
        # Special treatment for dfs because they are huge
        if type(arg) == pd.DataFrame:
            pickle_hash.update(_hash_frame(arg))
        else:
            pickle_hash.update(str(arg))

    # Function specific
    pickle_hash.update(function.__name__)
    pickle_hash.update(getsource(function))

    # kwargs
    for key in sorted(kwargs.keys()):
        pickle_hash.update(str(key))
        arg = kwargs[key]
        # Special treatment for dfs because they are huge
        if type(kwargs[key]) == pd.DataFrame:
            pickle_hash.update(_hash_frame(arg))
        else:
            pickle_hash.update(str(arg))

    return path.join(base_path, pickle_hash.hexdigest() + '.pkl')


def cache_result(pickle_dir):
    def decorate(function):
        def decorated(cache=True,
                      new_cache=False,
                      *args,
                      **kwargs):
            if not cache:
                # No caching, do nothing
                return function(*args, **kwargs)
            else:
                # Create dir if necessary
                try:
                    makedirs(pickle_dir)
                except OSError as exc:  # Python >2.5
                    if exc.errno == errno.EEXIST and path.isdir(pickle_dir):
                        pass
                    else:
                        raise

                # Get pickle name
                pickle_file = _get_name(*args,
                                        base_path=pickle_dir,
                                        function=function,
                                        **kwargs)

                try:
                    # Make sure we dont force a new one
                    assert not(new_cache)
                    # Try to read from pickle
                    with open(pickle_file, 'rb') as f:
                        return pickle.load(f)
                except (OSError, AssertionError):
                    # Not found, execute function and save return frame
                    # as pickle
                    ret = function(*args, **kwargs)
                    with open(pickle_file, 'wb') as f:
                        pickle.dump(ret, f)
                    return ret
        return decorated
    return decorate
