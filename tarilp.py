__author__ = "Kaustav Basu"

'''
This code was developed for the paper entitled "Health Monitoring of Critical Power System Equipments using Identifying Codes".
'''
# Packages required in this program
import networkx as nx
from pulp import *
import time
from itertools import combinations
import pandas as pd
import numpy as np
import collections

# To read edge-lists stored as txt files
def genGraph():
    G = nx.Graph()
    G = nx.read_edgelist("Graphs/14_bus_Graph(k=2).txt", nodetype = int)
    return G

def readNodeWeights():
    f = open("Graphs/14_bus_node_weights.txt")
    nodeWeights = dict()
    for line in f:
        x = line.replace('\n', '').split(' ')
        nodeWeights[int(x[0])] = int(x[1])
    return nodeWeights
        
# This function computes the optimal MDCS for the input graph
def model():
    # Inputs the total number of nodes in the graph
    numNodes = int(input("Enter the number of nodes: "))
    # Inputs the nodes to be uniquely monitored in the graph
    transformers = int(input("Enter the number of transformers: "))
    start = time.time()
    
    nodes = [i + 1 for i in range(transformers, numNodes)]
    tnodes = [i + 1 for i in range(transformers)]
    totNodes = tnodes + nodes
    G = genGraph()

    print("Initializing Integer Linear Program")
    print("-----------------------------------")
    problem = LpProblem("IdentifyingCodes1", LpMinimize)
    x = LpVariable.dict("x_%s", totNodes, 0, 1, LpBinary)

    problem += sum(x[i] for i in nodes)
    valColor = 0
    neighbor = []

    print("Adding Coloring Constraints")
    print("-----------------------------------")
    for i in tnodes:
        valColor = 0
        neighbor = list(G.neighbors(i))
        #print(i)
        #print(list(G.neighbors(i)))
        #print(neighbor)
        for j in neighbor:
            valColor += x[j]
        problem += valColor >= 1, "Coloring_Constraint_{}".format(i)
    valUnique = 0
    neighbor_i = []
    neighbor_j = []

    print("Adding Uniqueness Constraints")
    print("-----------------------------------")
    comb = combinations(tnodes, 2)
    for i in comb:
        pair = list(i)
        #print(pair)
        node1 = pair[0]
        node2 = pair[1]
        neighbor1 = list(G.neighbors(node1))
        neighbor2 = list(G.neighbors(node2))
        set1 = set(neighbor1)
        set2 = set(neighbor2)
        unique = list(set1.symmetric_difference(set2))
        #print(unique)
        for k in unique:
            valUnique += x[k]
        problem += valUnique >= 1, "Uniqueness_Constraint_{}".format(i)
        valUnique = 0

    print("Solving")
    print("-------------------------------------------------------")
    solution = []
    flag = 1
    while flag != 0:
        val = []
        for soln in solution:
            for i in soln:
            #print(i)
                problem += x[i] == 0, ""
        problem.solve(GUROBI())
        if LpStatus[problem.status] == 'Optimal':
            for v in problem.variables():
                if v.varValue == 1:
                    #print(v.name, "=", v.varValue)
                    val.append(int(v.name.split("_")[1]))
            solution.append(val)
            flag = 1
        else:
            flag = 0
            print("No More Alternate Optimal Solutions Exist.")
            break
        print(len(solution))
    
    attack = []
    for soln in solution:
        for i in soln:
            attack.append(i)
            
    uniqueColoring(solution, attack, tnodes, G)
    exit()
    #for k, v in problem.constraints.items():
        #print(k, v)
    print("Solutions: ", solution)
    print("Number of Alternate Solutions:", len(solution))
    
    print("-------------------------------------------------------")
    print("Amount of Resources Required for Unique Monitoring: {}".format(value(problem.objective)))
    print("Total Number of Nodes to be Uniquely Monitored: {}".format(len(tnodes)))
    print("% Savings: {}".format(float(100 * (len(tnodes) - int(value(problem.objective))) / len(tnodes))))
    print("-------------------------------------------------------")
    print("Time taken = {} seconds".format(time.time() - start))
    print("-------------------------------------------------------")
    #print(G.number_of_edges())
    

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
    
def uniqueColoring(solutions, attack, tnodes, G):
    
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

def main():
    model()
    #readNodeWeights()
if __name__ == '__main__':
    main()