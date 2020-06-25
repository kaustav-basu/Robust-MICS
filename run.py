from itertools import combinations
import networkx as nx
import configparser
from dcs import DCS
from pulp import *

config = configparser.ConfigParser()
config.read('graph_config.ini')


def gen_graph(edge_file):
    G = nx.Graph()
    G = nx.read_edgelist(edge_file, nodetype=int)
    return G


def model():
    num_nodes = int(config['GRAPH']['NUM_NODES'])
    num_transformers = int(config['GRAPH']['NUM_TRANSFORMER_NODES'])
    edge_file = config['GRAPH']['EDGE_FILE']
    G = gen_graph(edge_file)

    dcs = DCS(num_nodes, num_transformers, G)
    solutions = dcs.get_differntially_immune_solutions()


if __name__ == '__main__':
    model()
