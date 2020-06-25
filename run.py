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
    nodeWeights = dict()
    for line in f:
        x = line.replace('\n', '').split(' ')
        nodeWeights[int(x[0])] = int(x[1])
    return nodeWeights

def coloring(solution, attack, tnodes, G):
    color = ['0' for i in range(len(tnodes))]
    
    for i in solution:
        if i == attack:
            continue
        else:
            neighbor = list(G.neighbors(i))
            for node in neighbor:
                color[node - 1] = color[node - 1] + '+' + str(i)
    return color

    
def uniqueness(color):
    
    nodeWeights = readNodeWeights()
    defSum = 0
    totalSum = 0
    
    unique = []
    
    for _, v in nodeWeights.items():
        totalSum += v
    
    if len(color) == len(set(color)) and '0' not in color:
        for _, v in nodeWeights.items():
            defSum += v
        
        return totalSum, defSum
    
    else:
        counter = collections.Counter(color)
        for k, v in counter.items():
            if v == 1 and k != '0':
                unique.append(k)
        for i in unique:
            ind = color.index(i)
            defSum += nodeWeights[ind + 1]
        
        return totalSum, defSum
    
def uniqueColoring(solutions, attack, tnodes, G, write_file):
    
    gameMatrix = dict()
      
    ind = 1
    for solution in solutions:
        for atck in attack:
            color = coloring(solution, atck, tnodes, G)
            print(solution)
            print(atck)
            print(color)
            totalSum, defSum = uniqueness(color)  
            gameMatrix[str(ind) + "_" + str(atck)] = (defSum, totalSum - defSum)
        ind += 1
    print(gameMatrix)
    
    s = ""
    s += str(len(solutions)) + "\n"
    s += str(1) + "\n"
    s += str(1) + "\n"
    s += str(len(attack)) + "\n"
    
    attackString = [str(a) for a in attack]
    s += "|".join(attackString) + "\n"
    
    #for i in range(len(solutions)):
    count = 0
    for k, v in gameMatrix.items():
        s += str(v[0]) + "," + str(v[1]) + " "
        count += 1
        if count % len(attack) == 0:
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
    solutions = dcs.get_differntially_immune_solutions()
    print(solutions)
    attack = []
    for soln in solutions:
        for i in soln:
            attack.append(i)
            
    uniqueColoring(solutions, attack, dcs.t_nodes, G, write_file)



if __name__ == '__main__':
    model()
