import hashlib
import pandas as pd
import pickle

from inspect import getsource
from os import path
from os import makedirs

PICKLE_PATH = 'pickles'


def _hash_frame(df, path="test"):
    cols = sorted(df.columns.tolist())
    idxs = sorted(df.index.tolist())

    # Return bytes
    return bytes(str(cols + idxs), 'UTF-8')


def _get_name(base_path=".", function=None, *args, **kwargs):
    # Get name first
    pickle_hash = hashlib.md5()
    # args
    for arg in args:
        # Special treatment for dfs because they are huge
        if type(arg) == pd.DataFrame:
            pickle_hash.update(_hash_frame(arg))
        else:
            pickle_hash.update(bytes(str(arg), 'UTF-8'))

    # Function specific
    pickle_hash.update(bytes(function.__name__, 'UTF-8'))
    pickle_hash.update(bytes(getsource(function), 'UTF-8'))

    # kwargs
    for key in sorted(kwargs.keys()):
        pickle_hash.update(bytes(str(key), 'UTF-8'))
        arg = kwargs[key]
        # Special treatment for dfs because they are huge
        if type(kwargs[key]) == pd.DataFrame:
            pickle_hash.update(_hash_frame(arg))
        else:
            pickle_hash.update(bytes(str(arg), 'UTF-8'))

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
                makedirs(pickle_dir, exist_ok=True)

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
                except (FileNotFoundError, AssertionError):
                    # Not found, execute function and save return frame
                    # as pickle
                    ret = function(*args, **kwargs)
                    with open(pickle_file, 'wb') as f:
                        pickle.dump(ret, f)
                    return ret
        return decorated
    return decorate
