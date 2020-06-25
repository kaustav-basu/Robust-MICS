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


def readNodeWeights():
    f = open(config["GRAPH"]["NODE_WEIGHTS_FILE"])
    node_weights = dict()
    for line in f:
        x = line.replace('\n', '').split(' ')
        node_weights[int(x[0])] = int(x[1])
    return node_weights


def get_color_codes(solution, attack, t_nodes, G):
    color = ['0' for i in range(len(t_nodes))]
    for i in solution:
        if not i == attack:
            neighbor = list(G.neighbors(i))
            for node in neighbor:
                color[node - 1] = color[node - 1] + '+' + str(i)
    return color


def check_uniqueness(color):
    node_weights = readNodeWeights()
    total_sum = sum(node_weights.values())

    r_D = 0
    unique = []
    # If all nodes have unique non zero color
    if len(color) == len(set(color)) and '0' not in color:
        r_D = total_sum

    # Otherwise
    else:
        counter = collections.Counter(color)
        for k, v in counter.items():
            if v == 1 and k != '0':
                unique.append(k)
        for i in unique:
            ind = color.index(i)
            r_D += node_weights[ind + 1]

    return total_sum, r_D


def generate_game_matrix(def_actions, attacks, t_nodes, graph, write_file):
    game_matrix = dict()

    index = 1
    for a_D in def_actions:
        for a_A in attacks:
            color_codes = get_color_codes(a_D, a_A, t_nodes, graph)
            total_sum, r_D = check_uniqueness(color_codes)
            game_matrix["{}_{}".format(index, a_A)] = (r_D, total_sum - r_D)
        index += 1

    s = ""
    s += str(len(def_actions)) + "\n"
    s += str(1) + "\n"
    s += str(1) + "\n"
    s += str(len(attacks)) + "\n"

    attackString = [str(a) for a in attacks]
    s += "|".join(attackString) + "\n"

    count = 0
    for k, v in game_matrix.items():
        s += "{},{} ".format(v[0], v[1])
        count += 1
        if count % len(attacks) == 0:
            s += "\n"

    with open(write_file, "w") as f:
        f.write(s)
    f.close()


def model():
    num_nodes = int(config['GRAPH']['NUM_NODES'])
    num_transformers = int(config['GRAPH']['NUM_TRANSFORMER_NODES'])
    edge_file = config['GRAPH']['EDGE_FILE']
    write_file = config['GRAPH']['WRITE_FILE']
    G = gen_graph(edge_file)

    dcs = DCS(num_nodes, num_transformers, G)
    solutions = dcs.get_differentially_immune_solutions()
    
    min_length = 999999
    for solution in solutions:
        if len(solution) < min_length:
            min_length = len(solution)
    
    min_solutions = []
    
    for solution in solutions:
        if len(solution) == min_length:
            min_solutions.append(solution)

    # All possible nodes where sensors can be deployed can be attacked.
    attacks = set()
    for solution in min_solutions:
        for node in solution:
            attacks.add(node)

    generate_game_matrix(min_solutions, list(attacks), dcs.t_nodes, G, write_file)


if __name__ == '__main__':
    model()
