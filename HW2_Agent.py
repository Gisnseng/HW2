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
    node = {
        "move": move,
        "state": state,
        "depth": depth,
        "parent": parent,
        "evaluation": utility(state) + depth
        # Evalution is the sum of the utility of the state and it's depth
    }

    return node

# Determines the distance between selected Ant and its target
def getDistance(a, b):
    # Returns a distance between point A and point B's coordinates
    a_X, a_Y = a.coords
    b_X, b_Y = b.coords

    return abs(a_X - b_X) + abs(a_Y - b_Y)

##############################
###
###   Required functions for HW2b
###
##############################

# Determines the best course of action (most successful Move)
def utility(state):
    me = state.whoseTurn
    enemyQueen = getEnemyInv(not me, state).getQueen()

    # If the enemy Queen will die, take the move (lowest utility)
    if enemyQueen is None or enemyQueen.health <= 0:
        return 0.0

    ################
    ###  Functionality for targeting:
    ###     Should find estimated number of moves for each ant to get to 
    ###     their goal (Workers moving food to tunnel, for example)
    ###
    ###  Current Issue:
    ###     The Workers oscillate between two tiles next to a tunnel, never
    ###     actually going to it. It seems that the state passed to the utility()
    ###     never actually contains an ant that could move there... not sure why.
    ################

    # Targets for the Worker ants (so they will collect food)
    tunnel = getConstrList(state, me, (TUNNEL,))[0]
    if (len(getConstrList(state, None, (FOOD,))) > 0):
        food = getConstrList(state, None, (FOOD,))[0]

    # Workers target the tunnels and the food sources (collecting)
    workers = getAntList(state, me, (WORKER,))
    worker_speed = 2.0
    moves_to_worker_goal = 0.0

    food_collected = getCurrPlayerInventory(state).foodCount
    food_needed = 11

    for worker in workers:
        if worker.carrying:
            # distance to tunnel only
            total_distance = getDistance(worker, tunnel)
            # print(f"WORKER COORDS: {worker.coords}")

            # Issue here: it seems that the coords to move to the tunnel are never even passed to utility
        else:
            # distance to food + distance from food to tunnel
            total_distance = getDistance(worker, food) + getDistance(food, tunnel)

        moves_for_this_worker = total_distance / worker_speed

        moves_to_worker_goal = max(moves_to_worker_goal, moves_for_this_worker)

    # Attacker Ants attack the enemy Workers first, then the enemy Queen
    soldiers = getAntList(state, me, (SOLDIER,))
    enemyWorkers = getAntList(state, not me, (WORKER,))

    # Picks a target in the enemyWorkers list (or the Queen if no Workers)
    moves_to_soldier_goal = 10
    for soldier in soldiers:
        if enemyWorkers[0]:
            workerDistance = getDistance(soldier, enemyWorkers[0])
            queenDistance = getDistance(enemyWorkers[0], enemyQueen)
        else:
            workerDistance = 0.0
            queenDistance = getDistance(soldier, enemyQueen)

        soldier_speed = 2.0
        soldier_attack = 4.0

        moves_to_worker = workerDistance / soldier_speed
        to_kill_worker = enemyWorkers[0].health / soldier_attack
        moves_to_queen = queenDistance / soldier_speed
        to_kill_queen = enemyQueen.health / soldier_attack

        moves_to_soldier_goal += (moves_to_worker + to_kill_worker + moves_to_queen + to_kill_queen) / len(soldiers)

    total_moves_needed = moves_to_worker_goal + moves_to_soldier_goal

    # reduce total moves proportionally by food already collected
    food_progress_factor = food_collected / food_needed
    total_moves_needed *= (1.0 - food_progress_factor)

    # print(f"TOTAL: {total_moves_needed}")
    return total_moves_needed

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
        super(AIPlayer,self).__init__(inputPlayerId, "Quince_and_Indiana")
    
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
        iterations = 0
        while iterations < 3:
            # Find the best utility in current frontier nodes
            # Remove from frontier nodes, and add to expanded nodes
            bestNodeChoice = bestNode(frontierNodes)
            for node in frontierNodes:
                if node == bestNodeChoice:   # had to do this to compare data, not ObjectIDs
                    frontierNodes.remove(node)
            expandedNodes.append(bestNodeChoice)

            # Expand the best node and add new nodes to frontier
            newNodes = expandNode(bestNodeChoice)
            frontierNodes.extend(newNodes)

            iterations += 1

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

# utility
# blank_state = GameState.getBasicState()
# blank_state_next = getNextState(blank_state, listAllLegalMoves(blank_state)[0])
# print(utility(blank_state_next))
# #This returns zero because the test state doesn't have any food

# # bestMove
# legal_moves = listAllLegalMoves(blank_state)
# node_list = []

# for move in legal_moves:
#     nextState = getNextState(blank_state, move)
#     depth = 1   

#     node = {
#         "move": move,
#         "state": nextState,
#         "depth": depth,
#         "parent": blank_state,
#         "evaluation": utility(nextState) + depth
        
#     }
#     node_list.append(node)
# print(bestMove(node_list))
# # This prints the move action that moves the ant at 0,0 to 1,0
# # getMove is omitted because it does the exact same thing we did to test bestMove
