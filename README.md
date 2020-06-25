### Dependencies
Install the Conda environment.
```
conda env create -f env.yml -n rob-mics
```
You will need to install Gurobi and the `gurobipy` python module.

### Running the code
Obtaining differntially immune MICS and the corresponding game matrix given graph.
Config for the graph can be specified in `graph_config.ini`
```
python run.py
```

Obtaining Stackelberg Eq. strategy given the game matrix.
```
python StackelbergEquilibribumSolvers/src/DOBSS/BSG_miqp.py 14_Bus_Game_Matrix.txt
```
Needs one to get the submodule while cloning. To do this run the following commands after cloning.
```
git submodule init
git submodule update
```