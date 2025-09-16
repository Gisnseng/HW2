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

#HW 2 methods here
def getDistance(antID, target, inventory):
    for ant in inventory.ants:
        if ant.UniqueID == antID:
            antX, antY = ant.coords
            break

    targetX, targetY = target.coords
    return abs(antX - targetX) + abs(antY - targetY)


def utility(parentState, nextState):
    me = nextState.whoseTurn
    enemy = not me

    parentInventory = getCurrPlayerInventory(parentState)
    childInventory = getCurrPlayerInventory(nextState)
    parentEnemyInventory = getEnemyInv(enemy, parentState)
    childEnemyInventory = getEnemyInv(enemy, nextState)

    childEnemyQueen = childEnemyInventory.getQueen()
    parentEnemyQueen = parentEnemyInventory.getQueen()

    if childEnemyQueen is None or childEnemyQueen.health <= 0:
        return 1.0  # instant win

    tunnel = getConstrList(parentState, me, (TUNNEL,))[0]
    food = getConstrList(parentState, None, (FOOD,))[0]

    # --- Workers ---
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

    # --- Offensive ants ---
    offensiveBonus = 0.0
    offensiveAnts = getAntList(parentState, me, (SOLDIER,))
    if parentEnemyQueen and childEnemyQueen:
        for ant in offensiveAnts:
            parentDistance = getDistance(ant.UniqueID, parentEnemyQueen, parentInventory)
            nextDistance = getDistance(ant.UniqueID, childEnemyQueen, childInventory)

            improvement = parentDistance - nextDistance
            if improvement > 0:
                offensiveBonus += improvement

    # --- Food bonus ---
    foodCount = childInventory.foodCount
    foodBonus = foodCount / 11.0  # more food = more bonus

    # --- NEW: Ant count bonus ---
    totalAnts = len(getAntList(nextState, me, (SOLDIER,)))
    antCountBonus = totalAnts / 10.0  # normalize; adjust 20 if max ants differs

    # Combine
    value = (
        workerBonus * 0.01 +
        offensiveBonus * 0.5 +
        foodBonus * 0.02 +
        antCountBonus * 0.4  # <-- weight this fairly high to encourage building
    )

    print(f"VALUE {value}")
    return min(1.0, max(0.0, value))


def bestMove(nodes): #find best move in a given list of nodes
    best_utility = 0
    best_move = None

    for node in nodes:
        utility = node["evaluation"]
        move = node["move"]
        #print(f"UTILITY: {utility}")
        print(f"CORRESPONDING MOVE: {move}")

        if (utility > best_utility): # rank their utility and take the best
            best_utility = utility
            best_move = move

    print(f"BEST MOVE: {best_move}")
    return best_move

class AIPlayer(Player):

    #__init__
    #Description: Creates a new Player
    #
    #Parameters:
    #   inputPlayerId - The id to give the new player (int)
    #   cpy           - whether the player is a copy (when playing itself)
    ##

    def __init__(self, inputPlayerId):
        super(AIPlayer,self).__init__(inputPlayerId, "HW2AGENT")
    
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

        for move in legal_moves:
            nextState = getNextState(currentState, move)
            depth = 1   # depth stays 1 for HW A

            node = {
                "move": move,
                "state": nextState,
                "depth": depth,
                "parent": currentState,
                "evaluation": utility(currentState, nextState) + depth
                # evaluation is the sum of the utility and the depth
            }
            node_list.append(node)

        return bestMove(node_list)

    
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

