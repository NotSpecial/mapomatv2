import pandas as pd
import numpy as np
import networkx as nx
from operator import itemgetter
import community
from .cache import cache_result


def _partitions(graph):
    """
    Internal use only.
    Finds partitions with louvain method and returns dict
    """
    # Get Partitions with Louvain method
    part = community.best_partition(graph)

    # Structure them for info purpose
    parts = {}
    for item in part:
        n = part[item]  # Partition number
        if n not in parts:  # Check if list for partition exists
            parts[n] = []

        # add node with degree in graph (for sorting) as tuples to list
        parts[n].append(item)  # ((item, graph.degree()[item]))

    # Use degree to find name for category
    names = {key: max(
        [(item, graph.degree(weight='weight')[item]) for item in parts[key]],
        key=itemgetter(1))
        [0] for key in parts}

    # New return dict. ToDo: make it like thisright away
    res = {key: {'name': names[key], 'categories': parts[key]}
           for key in parts}

    return res


def _get_cat(data, catlist):
    """
    Internal use only.
    return data to add to column
    """
    # For every supercat
    # sum along row to get the number to see how many categories beloning to
    # the supercat are in there
    supercatframe = pd.DataFrame(
        [data[catlist[key]['categories']].sum(axis=1) for key in catlist])

    # Just use argmax to assign supercat to business: TODO: Better way?
    catmap = supercatframe.idxmax()

    # Add supercat to dataframe
    return catmap


@cache_result("pickles")
def add_supercats(df_in):
    """Requires df with businesses.
    Converts this to graph, then uses louvain method to find clusters

    Returns tuple of df with added super categories and mapping of supercat
    to a possible name

    super category "-1" means "uncategorized"

    Args:
        df_in (pandas.DataFrame): dataframe , needs a column 'categories'

    Returns:
        (df_out, supercatnames, supercats, adjacency, graph):
        df_out (pandas.DataFrame): Dataframe with added column for categories
        parts (dict): dictionary containing:
            'name' (string): Name of the super category
            'categories' (list): List of categories in super category
            'sub_categories' (dict): Like the original dict, has:
                'name' (string): Name of sub category
                'categories': List of categories in sub category
        combos (dict): list of all category combos with tuple as key and name
        """

    # Prepare data
    busicat = df_in['categories']

    # Find unique categories
    # all categories are lists, simply put them all together
    l = []
    for entry in busicat:
        l += entry

    # drop duplicates by converting to set
    cats = set(l)

    # Convert category entries to columns
    data = busicat.apply(lambda x: pd.Series(1, index=x))

    # Create list of data series
    mapdata = {}
    for cat in cats:
        mapdata[cat] = (data[data[cat] == 1].count())

    # Modify data to create adjacency matrix: set all values above 1 to 1
    # and set diagonal to 0
    df = pd.DataFrame(mapdata)

    np.fill_diagonal(df.values, 0)

    # Make graph from adjacency matrix
    graph = nx.from_numpy_matrix(df.values)

    # Relable nodes
    mapping = dict(zip(range(len(cats)), sorted(list(cats))))

    nx.relabel_nodes(graph, mapping, False)

    parts = _partitions(graph)

    # Prepare frame
    df_out = df_in.copy(deep=True)
    df_out['super_category'] = np.nan
    df_out['sub_category'] = np.nan

    # Add 'super category' column to df
    df_out.loc[:, 'super_category'] = _get_cat(data, parts)

    # Now find sub categories
    for key in parts:
        # List of nodes for the subgraph: all cats without the namegiving one
        catlist = [item for item in parts[key]['categories']
                   if (item is not parts[key]['name'])]
        # subgraph
        subgraph = graph.subgraph(catlist)
        # This subgraph will now contain some single "stray" nodes
        # that were only connected to the namegiving node. Remove them
        components = nx.connected_component_subgraphs(subgraph)
        connected = max(components, key=len)  # Only take largest

        # partitioning
        subparts = _partitions(connected)
        # Adding to result dict
        parts[key]['sub_categories'] = subparts
        # Add to dataframe
        sub_key = _get_cat(data, subparts)
        df_out.loc[df_out['super_category'] == key, 'sub_category'] = (
            sub_key)

    # Special case: No category at all will be -1
    parts[-1] = {
        'name': 'Uncategorized', 'categories': [], 'sub_categories': {}}
    for key in parts:
        parts[key]['sub_categories'][-1] = {
            'name': 'Uncategorized', 'categories': []}
    df_out[['super_category', 'sub_category']] = (
        df_out[['super_category', 'sub_category']].fillna(-1))

    # Make sure they are integers - this was a problem somehow
    df_out[['super_category', 'sub_category']] = (
        df_out[['super_category', 'sub_category']].astype(int))

    # Add a general "category" tuple for easy grouping
    df_out['category'] = df_out.apply(
        lambda row: (row['super_category'], row['sub_category']), axis=1)

    # Get a handy dict for all combinations
    combos = {}
    for super_key in parts:
        sub_parts = parts[super_key]['sub_categories']
        for sub_key in sub_parts:
            combos[(super_key, sub_key)] = ("%s/%s"
                % (parts[super_key]['name'], sub_parts[sub_key]['name']))

    return (df_out, parts, combos)
