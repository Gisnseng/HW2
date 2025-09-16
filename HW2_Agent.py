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
def manhattanDist(a, b):
    """Return Manhattan distance between two coordinates a and b."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def utility(state):
    me = state.whoseTurn
    enemy = not me

    myInv = getCurrPlayerInventory(state)
    enemyInv = getEnemyInv(enemy, state)

    myQueen = myInv.getQueen()
    enemyQueen = enemyInv.getQueen()
    if enemyQueen is None or enemyQueen.health <= 0:
        return 1.0  # instant win

    # --- Tunnel and food ---
    tunnel = getConstrList(state, me, (TUNNEL,))[0]
    foods = getConstrList(state, None, (FOOD,))

    # Find closest food to tunnel
    closestFood = None
    bestDist = 9999
    for food in foods:
        dist = manhattanDist(food.coords, tunnel.coords)
        if dist < bestDist:
            closestFood = food
            bestDist = dist

    # --- Workers ---
    workers = getAntList(state, me, (WORKER,))
    carryingWorkers = [w for w in workers if w.carrying]
    nonCarryingWorkers = [w for w in workers if not w.carrying]

    # Reward carrying workers moving toward tunnel
    carryingScore = 0.0
    if carryingWorkers:
        avgDist = sum(manhattanDist(w.coords, tunnel.coords) for w in carryingWorkers) / len(carryingWorkers)
        carryingScore = max(0, 10 - avgDist) / 10.0

    # Reward non-carrying workers moving toward closest food
    seekFoodScore = 0.0
    if nonCarryingWorkers and closestFood:
        avgDist = sum(manhattanDist(w.coords, closestFood.coords) for w in nonCarryingWorkers) / len(nonCarryingWorkers)
        seekFoodScore = max(0, 10 - avgDist) / 10.0

    # --- Offensive ants ---
    drones = getAntList(state, me, (DRONE,))
    soldiers = getAntList(state, me, (SOLDIER,))
    offensive = drones + soldiers
    offenseScore = 0.0
    if offensive:
        avgDist = sum(manhattanDist(a.coords, enemyQueen.coords) for a in offensive) / len(offensive)
        offenseScore = max(0, 10 - avgDist) / 10.0

    # --- Queen danger ---
    enemyDrones = getAntList(state, enemy, (DRONE,))
    enemySoldiers = getAntList(state, enemy, (SOLDIER,))
    enemyOffensive = enemyDrones + enemySoldiers
    queenPenalty = 0.0
    if myQueen and enemyOffensive:
        avgDist = sum(manhattanDist(myQueen.coords, a.coords) for a in enemyOffensive) / len(enemyOffensive)
        queenPenalty = max(0, 10 - avgDist) / 10.0  # closer to danger → higher penalty

    # --- Ant count bonus ---
    allMyAnts = getAntList(state, me, (WORKER, DRONE, SOLDIER, QUEEN))
    antCountScore = min(1.0, len(allMyAnts) / 10.0)  # normalize, max at 10 ants

    # --- Combine with weights ---
    value = (
        carryingScore * 0.5 +
        seekFoodScore * 0.8 +
        offenseScore * 0.25 +
        (1 - queenPenalty) * 0.15 +
        antCountScore * 0.2
    )

    return min(1.0, max(0.0, value))


def bestMove(nodes): #find best move in a given list of nodes
    best_utility = 0
    best_move = None

    for node in nodes:
        utility = node["evaluation"]
        move = node["move"]
        print(f"UTILITY: {utility}")
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
                "evaluation": utility(nextState) + depth
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

