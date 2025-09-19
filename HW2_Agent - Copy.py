import random
import sys
sys.path.append("..")  #so other modules can be found in parent dir
from Player import *
from Constants import *
from Construction import CONSTR_STATS
from Ant import UNIT_STATS
from Move import Move
from GameState import *
from AIPlayerUtils import *


##
#AIPlayer
#Description: The responsbility of this class is to interact with the game by
#deciding a valid move based on a given game state. This class has methods that
#will be implemented by students in Dr. Nuxoll's AI course.
#
#Variables:
#   playerId - The id of the player.
##

# Determines the distance between selected Ant and its target
def getDistance(antID, target, inventory):
    # Ants are originally searched from the parentState, so their
    #   corresponding Ant in the childState is matched via the Ant.UniqueID
    for ant in inventory.ants:
        if ant.UniqueID == antID:
            antX, antY = ant.coords
            break

    # Returns a distance between the Ant and the Target's coordinates
    targetX, targetY = target.coords
    return abs(antX - targetX) + abs(antY - targetY)

# Determines the best course of action (most successful Move)
def utility(parentState, childState):
    me = childState.whoseTurn

    # My inventories and enemy inventory for comparisons
    #       (this drives the utility function)
    parentInventory = getCurrPlayerInventory(parentState)
    childInventory = getCurrPlayerInventory(childState)
    
    enemyInventory = getEnemyInv(not me, childState)
    enemyQueen = enemyInventory.getQueen()

    # If the enemy Queen will die, take the move (highest utility)
    if enemyQueen is None or enemyQueen.health <= 0:
        return 0.0

    ################
    ###  Functionality for targeting:
    ###     Each Ant in the list is evaluated for its distance to the target
    ###     in both the parentState and the childState (allows for comparison)
    ###
    ###     If the childState has a shorter distance than the parent, this move
    ###     is encouraged by getting a higher utility (moves ants toward target)
    ################

    # Targets for the Worker ants (so they will collect food)
    tunnel = getConstrList(parentState, me, (TUNNEL,))[0]
    if (len(getConstrList(parentState, None, (FOOD,))) > 0):
        food = getConstrList(parentState, None, (FOOD,))[0]

    # Workers target the tunnels and the food sources (collecting)
    workerBonus = 0.0
    workers = getAntList(parentState, me, (WORKER,))
    for worker in workers:
        if worker.carrying:
            parentDistance = getDistance(worker.UniqueID, tunnel, parentInventory)
            nextDistance = getDistance(worker.UniqueID, tunnel, childInventory)
        else:
            parentDistance = getDistance(worker.UniqueID, food, parentInventory)
            nextDistance = getDistance(worker.UniqueID, food, childInventory)

        improvement = parentDistance - nextDistance
        if improvement > 0:
            workerBonus += improvement

    # Attacker Ants attack the enemy Workers first, then the enemy Queen
    offensiveBonus = 0.0
    offensiveAnts = getAntList(parentState, me, (DRONE, SOLDIER, R_SOLDIER))
    enemyWorkers = getAntList(parentState, not me, (WORKER,))

    # Picks a target in the enemyWorkers list (or the Queen if no Workers)
    if enemyWorkers:
        target = enemyWorkers[0]
    else:
        target = enemyQueen

    for ant in offensiveAnts:
        parentDistance = getDistance(ant.UniqueID, target, parentInventory)
        nextDistance = getDistance(ant.UniqueID, target, childInventory)
        
        improvement = parentDistance - nextDistance
        if improvement > 0:
            offensiveBonus += improvement

    # Reward for increasing the food count
    foodBonus = childInventory.foodCount * 0.1

    # Reward for building Soldiers
    numSoldiers = len(getAntList(childState, me, (SOLDIER,)))
    soldierNumBonus = numSoldiers * 0.2

    # Reward for having exactly 2 Workers at all times (if possible)
    numWorkers = len(getAntList(childState, me, (WORKER,)))
    workerNumBonus = max(0, 1 - abs(numWorkers - 2) * 0.5)
    if numWorkers > 2:
        workerBonus = -10

    # Calculate combined utility (these values are somewhat arbitrary)
    value = (
        workerBonus * 0.04 +
        offensiveBonus * 0.20 +
        foodBonus * 0.02 +
        soldierNumBonus * 0.06 +
        workerNumBonus * 0.04
    )
    #Quince: Number of moves to goal should be the average moves in a game times inverse of evaluation
    # eg. at the start of the game, we have no food or soldiers, so number of moves would be large
    avg_moves = 50 # wweeww
    return 50 - min(50, value*50)
    # Always return a maximum of 1.0

    #return min(1.0, value)


def bestMove(nodes): #find best move in a given list of nodes
    best_utility = 99 #intitialize at the move that takes 999 moves to win wweeww
    best_move = None

    for node in nodes:
        utility = node["evaluation"]
        move = node["move"]

        #if (utility > best_utility): # rank their utility and take the best
        #    best_utility = utility
        #    best_move = move
        if (utility < best_utility): #rank the number of moves to reach goal from moves and take the smallest wweeww
            best_utility = utility
            best_move = node

    return best_move

#HW 2b methods

def expandNode(node):
    state = node["state"]
    move_list = listAllLegalMoves(state)
    node_list = []
    for move in move_list:
        new_node = createNode(move, getNextState(state, move), node["depth"] + 1, state, node)
        node_list.append(new_node)
    return node_list
    
def createNode(move, nextState, depth, currentState, node):
    new_node = {
    "move": move,
    "state": nextState,
    "depth": depth,
    "parent": node,
    "evaluation": utility(currentState, nextState) + depth
    # evaluation is the sum of the utility and the depth
    }
    return new_node

class AIPlayer(Player):

    #__init__
    #Description: Creates a new Player
    #
    #Parameters:
    #   inputPlayerId - The id to give the new player (int)
    #   cpy           - whether the player is a copy (when playing itself)
    ##

    def __init__(self, inputPlayerId):
        super(AIPlayer,self).__init__(inputPlayerId, "Tester")
    
    ##
    #getPlacement
    #
    #Description: called during setup phase for each Construction that
    #   must be placed by the player.  These items are: 1 Anthill on
    #   the player's side; 1 tunnel on player's side; 9 grass on the
    #   player's side; and 2 food on the enemy's side.
    #
    #Parameters:
    #   construction - the Construction to be placed.
    #   currentState - the state of the game at this point in time.
    #
    #Return: The coordinates of where the construction is to be placed
    ##
    def getPlacement(self, currentState):
        numToPlace = 0
        #implemented by students to return their next move
        if currentState.phase == SETUP_PHASE_1:    #stuff on my side
            numToPlace = 11
            moves = []
            for i in range(0, numToPlace):
                move = None
                while move == None:
                    #Choose any x location
                    x = random.randint(0, 9)
                    #Choose any y location on your side of the board
                    y = random.randint(0, 3)
                    #Set the move if this space is empty
                    if currentState.board[x][y].constr == None and (x, y) not in moves:
                        move = (x, y)
                        #Just need to make the space non-empty. So I threw whatever I felt like in there.
                        currentState.board[x][y].constr == True
                moves.append(move)
            return moves
        elif currentState.phase == SETUP_PHASE_2:   #stuff on foe's side
            numToPlace = 2
            moves = []
            for i in range(0, numToPlace):
                move = None
                while move == None:
                    #Choose any x location
                    x = random.randint(0, 9)
                    #Choose any y location on enemy side of the board
                    y = random.randint(6, 9)
                    #Set the move if this space is empty
                    if currentState.board[x][y].constr == None and (x, y) not in moves:
                        move = (x, y)
                        #Just need to make the space non-empty. So I threw whatever I felt like in there.
                        currentState.board[x][y].constr == True
                moves.append(move)
            return moves
        else:
            return [(0, 0)]
        
    ##
    #getMove
    #Description: Gets the next move from the Player.
    #
    #Parameters:
    #   currentState - The state of the current game waiting for the player's move (GameState)
    #
    #Return: The Move to be made
    ##    

    def getMove(self, currentState):
        legal_moves = listAllLegalMoves(currentState)
        node_list = []

        frontiernodes = []
        expandednodes = []
        #root node from current state
        parent_node = createNode(None, currentState, 0, currentState, "Test")
        frontiernodes.append(parent_node)

        for i in range(3):
            best_frontier = bestMove(frontiernodes) # find best node in frontiernodes
            frontiernodes.remove(best_frontier) # remove it from frontier nodes
            expandednodes.append(best_frontier) # append to expanded nodes
            nodes = expandNode(best_frontier)# expand best frontier
            for j in nodes:
                frontiernodes.append(j) #append the new frontiers to frontier
                    
        best_frontier_new = bestMove(frontiernodes)

        depth = best_frontier_new["depth"]
        while True:
            if best_frontier_new["parent"] is parent_node:
                break
            else:
                best_frontier_new = best_frontier_new["parent"]


        #for move in legal_moves:
        #    nextState = getNextState(currentState, move)
        #    depth = 1   # depth stays 1 for HW A
        #    node = createNode(move, nextState, depth, currentState, parent_node)
        #    node_list.append(node)

        #return bestMove(node_list)["move"]
        print(best_frontier_new["evaluation"])
        return best_frontier_new["move"]

    
    ##
    #getAttack
    #Description: Gets the attack to be made from the Player
    #
    #Parameters:
    #   currentState - A clone of the current state (GameState)
    #   attackingAnt - The ant currently making the attack (Ant)
    #   enemyLocation - The Locations of the Enemies that can be attacked (Location[])
    ##
    def getAttack(self, currentState, attackingAnt, enemyLocations):
        #Attack a random enemy.
        return enemyLocations[random.randint(0, len(enemyLocations) - 1)]

    ##
    #registerWin
    #
    # This agent doens't learn
    #
    def registerWin(self, hasWon):
        #method templaste, not implemented
        pass

# Unit tests

# utility
blank_state = GameState.getBasicState()
blank_state_next = getNextState(blank_state, listAllLegalMoves(blank_state)[0])
print(utility(blank_state, blank_state_next))
#This returns zero because the test state doesn't have any food

# bestMove
legal_moves = listAllLegalMoves(blank_state)
node_list = []

for move in legal_moves:
    nextState = getNextState(blank_state, move)
    depth = 1   

    node = {
        "move": move,
        "state": nextState,
        "depth": depth,
        "parent": blank_state,
        "evaluation": utility(blank_state, nextState) + depth
        
    }
    node_list.append(node)
print(bestMove(node_list))
# This prints the move action that moves the ant at 0,0 to 1,0
# getMove is omitted because it does the exact same thing we did to test bestMove
