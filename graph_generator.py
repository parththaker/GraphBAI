"""
Graph Generating Library

All the functions for generating different type of graph based models for Best-Arm Identification
Current supported models:
    1. Erdos Renyi graph
    2. Clustered graph
    3. Stochastic block model

"""

import toml
import numpy as np
import networkx
import matplotlib.pyplot as plt
import networkx as nx


def show_graph_with_labels(adjacency_matrix):
    """
    Plots the graph structure based on adjacency matrix data.

    Parameters
    ----------
    adjacency_matrix : np.array() object encoding the edges of the graph.

    """
    rows, cols = np.where(adjacency_matrix == 1)
    edges = zip(rows.tolist(), cols.tolist())
    gr = nx.Graph()
    gr.add_edges_from(edges)
    nx.draw(gr, node_size=500)
    plt.show()


def create_dict(num, k):
    """

    Parameters
    ----------
    num : number of clusters
    k : number of nodes

    Returns
    -------
    A : dict

    """
    A = {}
    for i in range(k):
        A[i] = i + k*num
    return A


def generate_means(k, num, cluster_means):
    """
    Create array with same mean value for nodes in the same cluster.

    Parameters
    ----------
    k : number of nodes per cluster
    num : number of clusters
    cluster_means : size(num) - array with value of means per cluster

    Returns
    -------
    means : size(k*num) - array with value of mean per node.
    """

    # TODO : Currently only allows for the setting with equal means for each cluster.
    #        Need to implement other modules (noisy, etc.)

    means = np.zeros(k*num)

    if len(cluster_means)!=num:
        print("No of cluster means is not equal to number of clusters. Returning 0 mean vector.")
        return means

    for i in range(num):
        for j in range(k):
            means[j+i*k] = cluster_means[i]

    return means


def modify_means(means, index, new_mean):
    """
    Insert a new value to the existing array

    Parameters
    ----------
    means : array-like object
    index : location to insert the value
    new_mean : new value to insert

    Returns
    -------
    array-like object with size len(means) + 1

    """
    return np.insert(means, index, new_mean)


def modify_matrix(mat, index, new_value):
    """
    Insert row-column of new value to the existing matrix

    Parameters
    ----------
    mat : matrix-like object
    index : location to insert a new row and column
    new_value : new value to insert

    Returns
    -------
    matrix-like object with shape (len(mat) + 1, len(mat)+ 1)

    """
    temp_mat = np.insert(mat, index, new_value, axis=0)
    return np.insert(temp_mat, index, new_value, axis=1)


def one_off_setup(adj, degree, means, one_off_mean, index=0):
    """
    Wrapper function for adding an isolated node to the current graph

    Parameters
    ----------
    adj : Adjacency matrix
    degree : Degree matrix
    means : Mean vector
    one_off_mean : Mean value of isolated node
    index : location of the isolated node

    Returns
    -------
    new_adj : New adjacency matrix
    new_degree : New degree matrix
    new_means : New mean vector

    """
    new_adj = modify_matrix(adj, index, 0)
    new_degree = modify_matrix(degree, index, 0)
    new_means = modify_means(means, index, one_off_mean)

    return new_adj, new_degree, new_means


def fill_dict(new_dict, mean, adj, degree):
    """
    Create dictionary entry to store in .toml

    Parameters
    ----------
    new_dict : Dictionary object
    mean : Mean vector
    adj : Adjacency matrix
    degree : Degree matrix

    Returns
    -------
    new_dict : Filled up dictionary entry

    """
    new_dict["nodes"] = len(mean)
    new_dict["node_means"] = mean
    new_dict["Adj"] = adj
    new_dict["Degree"] = degree
    return new_dict


def erdos_renyi_graph(n, p):
    """
    Erdos-Renyi graph generator

    Parameters
    ----------
    n : number of nodes
    p : probability of edge between nodes

    Returns
    -------
    Degree : Degree matrix
    Adj : Adjacency matrix

    """

    g = networkx.generators.random_graphs.erdos_renyi_graph(n, p)

    Adj = np.zeros((n, n))
    Degree = np.zeros((n, n))

    for i, j in g.edges():
        Adj[i, j] = 1.0
        Adj[j, i] = 1.0
        Degree[i, i] += 1.0
        Degree[j, j] += 1.0

    # FIXME : not sure what the purpose the commented out code is serving.
    # for i in range(n):
    #     for j in range(n):
    # Adj[i,j] = np.format_float_positional(Adj[i,j], trim='k')
    # Degree[i, j] = np.format_float_positional(Degree[i,j], trim='k')


    # show_graph_with_labels(Adj)
    return Degree, Adj


def sbm(k, num, p, q):
    """
    Stochastic-Block-Model graph generator

    Parameters
    ----------
    k : number of nodes per cluster
    num : number of clusters
    p : probability of intra cluster connection
    q : probability of inter cluster connection

    Returns
    -------
    Degree : Degree matrix
    Adj : Adjacency matrix

    """

    # TODO : Need to write code for different-sized clusters.

    sizes = k*np.ones(num, dtype=np.int8)
    probs = (p-q)*np.diag(np.ones(num))+q*np.ones((num, num))

    g = nx.stochastic_block_model(sizes, probs, seed=42)

    nodes = k*num
    Adj = np.zeros((nodes, nodes))
    Degree = np.zeros((nodes, nodes))

    for i, j in g.edges():
        Adj[i, j] = 1.0
        Adj[j, i] = 1.0
        Degree[i, i] += 1.0
        Degree[j, j] += 1.0

    return Degree, Adj


def n_cluster_graph(k, num, p):
    """
    Clustered graph

    Parameters
    ----------
    k : number of nodes per cluster
    num : number of clusters
    p : probability of intra cluster connection

    Returns
    -------
    Degree : Degree matrix
    Adj : Adjacency matrix

    """
    g = []
    n = k * num
    for i in range(num):
        mapping = create_dict(len(g), k)
        a = networkx.generators.random_graphs.erdos_renyi_graph(k, p)
        b = networkx.relabel_nodes(a, mapping)
        g.append(b)

    h = networkx.Graph()
    for i in range(num):
        h.add_nodes_from(g[i])
        h.add_edges_from(g[i].edges())

    Adj = np.zeros((n, n))
    Degree = np.zeros((n, n))

    for i, j in h.edges():
        Adj[i, j] = 1.0
        Adj[j, i] = 1.0
        Degree[i, i] += 1.0
        Degree[j, j] += 1.0

    for i in range(n):
        for j in range(n):
            Adj[i, j] = np.format_float_positional(Adj[i, j], trim='k')
            Degree[i, j] = np.format_float_positional(Degree[i, j], trim='k')

    return Degree, Adj


def call_generator(node_per_cluster, clusters, p, cluster_means):
    """
    Wrapper function to call for getting graph related matrices

    Parameters
    ----------
    node_per_cluster : number of nodes per cluster
    clusters : number of cluster
    p : probability of intra cluster connection
    cluster_means : size(clusters) - array with value of means per cluster

    Returns
    -------
    new_dict : dictionary with graph related data.

    """
    # deg, adj = n_cluster_graph(node_per_cluster, clusters, p)

    # TODO : Only works properly for SBM with p,q = 1.0, 0.0 since the error is not included in conf bound calculation.
    deg, adj = sbm(node_per_cluster, clusters, p, 0.0)
    mean_vector = generate_means(node_per_cluster, clusters, cluster_means)
    adj, deg, mean_vector = one_off_setup(adj, deg, mean_vector, node_per_cluster*clusters*1.05)

    new_dict = {}
    new_dict = fill_dict(new_dict, mean_vector, adj, deg)
    return new_dict