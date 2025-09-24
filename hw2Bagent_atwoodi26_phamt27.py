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
import pdb

##############################
###
###   Helper functions for HW2b
###
##############################

# Used to create root node and subsequent child nodes
def createNode(move, state, depth, parent):
    if parent:
        evaluation = utility(parent["state"], state) + depth
    else:  
        evaluation = 0  # undefined evaluation (root state)

    node = {
        "move": move,
        "state": state,
        "depth": depth,
        "parent": parent,
        "evaluation": evaluation
        # Evalution is the sum of the utility of the state and it's depth
    }

    return node

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

##############################
###
###   Required functions for HW2b
###
##############################

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
    return (1.5 - value) * avg_moves

## EXPAND NODE
def expandNode(currentNode):
    # Get the state at the current node, list all legal moves
    currentState = currentNode["state"]
    legal_moves = listAllLegalMoves(currentState)
    node_list = []

    # Get next state for each move, increment the depth from the current node
    for move in legal_moves:
        nextState = getNextState(currentState, move)
        depth = currentNode["depth"] + 1

        expandedNode = createNode(move, nextState, depth, currentNode)

        node_list.append(expandedNode)

    # Return nodes of next depth
    return node_list

## BEST MOVE
def bestNode(nodes):
    # Find best node in a given list of nodes
    least_utility = 100
    best_node = None

    # Find the smallest utility and return the associated node
    for node in nodes:
        utility = node["evaluation"]

        # Rank their utility and take the best
        if (utility < least_utility):
            least_utility = utility
            best_node = node

    return best_node


##
#AIPlayer
#Description: The responsbility of this class is to interact with the game by
#deciding a valid move based on a given game state. This class has methods that
#will be implemented by students in Dr. Nuxoll's AI course.
#
#Variables:
#   playerId - The id of the player.
##
class AIPlayer(Player):

    #__init__
    #Description: Creates a new Player
    #
    #Parameters:
    #   inputPlayerId - The id to give the new player (int)
    #   cpy           - whether the player is a copy (when playing itself)
    ##

    def __init__(self, inputPlayerId):
        super(AIPlayer,self).__init__(inputPlayerId, "Quince_and_Indiana_HW2B")
    
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
        # Create lists for frontier and expanded nodes
        frontierNodes = []
        expandedNodes = []

        # Root node has no move, no depth, and no parent node
        rootNode = createNode(None, currentState, 0, None)

        # Add root node to frontierNodes
        frontierNodes.append(rootNode)

        # Iterates to depth 3
        for _ in range(3):
            # Find the best utility in current frontier nodes
            # Remove from frontier nodes, and add to expanded nodes
            bestNodeChoice = bestNode(frontierNodes)
            for node in frontierNodes:
                if node == bestNodeChoice:   # had to do "==" to compare data, not ObjectIDs
                    frontierNodes.remove(node)
            expandedNodes.append(bestNodeChoice)

            # Expand the best node and add new nodes to frontier
            newNodes = expandNode(bestNodeChoice)
            frontierNodes.extend(newNodes)

        # Chose the best node out of all frontier nodes
        # Go back to parent (at depth == 1), and return the associated move
        chosenNode = bestNode(frontierNodes)
        while True:
            if chosenNode["depth"] == 1:
                break
            else:
                chosenNode = chosenNode["parent"]
        
        return chosenNode["move"]

    
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
print("####### UNIT TESTS ########")

# utility test
blank_state = GameState.getBasicState()
next_state = blank_state.clone()
next_state.foodCount = 1
util = utility(blank_state, next_state)
if util <= 0:
    print("Utility returned negative value")
else:
    print(f"TEST UTILITY: {util}")

# expandNode/bestNode test
legal_moves = listAllLegalMoves(blank_state)
node = createNode(legal_moves[0], blank_state, 0, None)
bestNodeChoice = bestNode(expandNode(node))
if bestNodeChoice:
    print(f"BEST NODE: {bestNodeChoice}")
else:
    print("expandNode or bestNode failed")

# Print statement for bestNode omitted because it prints a large list,
#   and the bestNodeChoice from that list is more useful