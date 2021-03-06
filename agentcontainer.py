import random, itertools
from hfo import *
from scripts.environment import SoccerEnvironment
import time
from utils import *
import itertools
from agents.globals import MyGlobals
import Queue as Q
import copy
from pdb import set_trace as bp
def printQueue(q):
    while not q.empty():
        print (q.get()),
    print ''


def debug():
    print 'Entering debug'


class History(object):

    """Container for storing collection of states."""
    def __init__(self,size):
        super(History, self).__init__()
        self.store=[]
        self.size=size

    def addState(self,state):
        self.store.append(state)
        self.checkConditionAndModify()

    def checkConditionAndModify(self):
        if len(self.store)>self.size:
            self.store= self.store[len(self.store)-self.size:len(self.store)]

    def getStates(self,k):
        return self.store[len(self.store)-k:len(self.store)]



class AgentContainer(object):

    """docstring for AgentContainer."""
    def __init__(self, agent,id,teamSize,opponentTeam,queue,rewardargs, featuretransformargs):
        super(AgentContainer, self).__init__()
        self.agent = agent
        self.id =id
        self.teamSize=teamSize
        self.opponentTeam=opponentTeam
        self.q=queue
        self.rewardargs =rewardargs
        self.featuretransformargs = featuretransformargs #May include flush rates

    def run(self):
        print '-----------------------Starting Agent with ID:'+str(self.id)
        hfo = HFOEnvironment()
        # print MOVE
        # print SHOOT
        # print PASS
        # print DRIBBLE
        # print CATCH
        # Connect to the server with the specified
        # feature set. See feature sets in hfo.py/hfo.hpp.
        time.sleep(1)
        hfo.connectToServer(HIGH_LEVEL_FEATURE_SET,
        'bin/teams/base/config/formations-dt', 6000,
        'localhost', 'base_left', False)
        rewards= []

        print '-----------------------Connection Successful Agent with ID:'+str(self.id)
        for episode in xrange(2000):
            print '-----------------------INSIDE EPISODE Agent with ID:'+str(self.id)
            status = IN_GAME
            total_reward=0
            freward=0
            # If status is IN_GAME continue
            while status == IN_GAME:


                # Get the vector of state features for the current state
                state = hfo.getState()

                #Adding into the queue for synchronization
                self.q.put(state)
                while (self.q.qsize())<self.teamSize:
                    time.sleep(0)

                self.history = History(10)
                #From Queue , get states from other agents
                stateCollection=list(self.q.queue)

                #Preprocess State
                agentState,teamState,opponentState= self.transformState(state,stateCollection,[])

                #Add the current state to history
                self.history.addState([agentState,teamState,opponentState])

                # Calculate reward for the last action
                reward = self.calculateReward(self.history.getStates(3),agentState,teamState,opponentState,[],status)
                #print "Reward: "+str(reward)
                total_reward+=reward
                # Update Parameters of the agent

                self.agent.perceive(agentState,teamState,opponentState,reward,False)

                combinedState = list(itertools.chain(agentState,teamState, opponentState))

                # # Predict Action to be performed
                action =self.agent.getAction(np.array(combinedState))
                action =action +8
                # Perform the Action
                # if action==int(MOVE):
                #     hfo.act(MOVE)
                # elif action==int(SHOOT):
                #     hfo.act(SHOOT)
                # elif action==int(PASS):
                #     hfo.act(PASS,t)
                # elif action==int(DRIBBLE):
                #     hfo.act(DRIBBLE)
                # else:
                #     action=hfo.act(CATCH)

                if action==8:
                    hfo.act(MOVE)
                elif action==9:
                    if state[5]==1:
                        hfo.act(SHOOT)
                elif action==10:
                    if state[5]==1:
                        hfo.act(DRIBBLE)
                elif action>=11:
                    if state[5]==1 and self.id!=2:
                        action=hfo.act(PASS,2)

                # Advance the environment and get the game status
                self.q.put(1)
                if self.q.qsize()==2*self.teamSize:
                    with self.q.mutex:
                        self.q.queue.clear()
                status = hfo.step()
            #status=hfo.step()
            if status !=IN_GAME:
                #print "Danger averted"
                prevState=combinedState
                #print len(prevState)
                state=hfo.getState()
                for i in range(11):
                    prevState[i]= state[i]
                #print len(prevState)
                if status == GOAL:
                    freward=300
                elif status ==CAPTURED_BY_DEFENSE:
                    freward=-200
                elif status ==OUT_OF_BOUNDS:
                    freward =  -100*(np.exp(state[6]))
                elif status == OUT_OF_TIME:
                    freward = -100*(np.exp(state[6]))
                reward+=freward
                self.agent.perceive(agentState,teamState,opponentState,reward,False)
            print "End Episode Reward for Agent "+str(self.id)+" : "+str(freward)
            print "Total Reward for Agent "+str(self.id)+" : "+str(total_reward)
            #     #If status is bad, update agent with different rewards and break
            # while (self.q.qsize()!=0):
            #     print "Previous:"+str(self.q.qsize())
            #     time.sleep(0)
            # print 'pass'
            # #ONCE GAME IS DONE, perform last update
            # # Perform last update
            # # Get the vector of state features for the current state
            # state = hfo.getState()
            #
            #
            #
            # #Adding into the queue for synchronization
            # self.q.put(state)
            # while (self.q.qsize())<self.teamSize:
            #     print "Next:"+str(self.q.qsize())
            #     time.sleep(0)
            #
            # self.history = History(10)
            # #From Queue , get states from other agents
            # stateCollection=list(self.q.queue)
            #
            # #Preprocess State
            # agentState,teamState,opponentState= self.transformState(state,stateCollection,[])
            #
            # #Add the current state to history
            # self.history.addState([agentState,teamState,opponentState])
            #
            # # Calculate reward for the last action
            # reward = self.calculateReward(self.history.getStates(3),agentState,teamState,opponentState,[],status)
            # print reward

            # Update Parameters of the agent
            #self.agent.perceive(agentState,teamState,opponentState,reward)
            print(' ID : '+ str(self.id) +' Episode %d ended with %s'%(episode, statusToString(status)))
            # Quit if the server goes down
            if status == SERVER_DOWN:
                hfo.act(QUIT)
                break
        self.end()


    def end(self):
        print 'Ending Agent '+str(self.id)



    def calculateReward(self,historyTuple,agentState,teamState,opponentState,rewardargs,status):
        if status==GOAL:
            return 3
        elif status == CAPTURED_BY_DEFENSE:
            return -3
        elif status== OUT_OF_BOUNDS:
            return -3
        elif status==OUT_OF_TIME:
            return -2
        #print 'Custom reward Function'
        reward =0
        #Penalizes length of the match
        reward += -1
        # Calculates Proximity Reward
        #print "Agent State: "+str(agentsta)
        if agentState[6]<-1:
            proximityReward=2 *agentState[6]
        else:
            proximityReward=-2 *agentState[6]
        #Multiplicative Factor
        posessionreward= 1 *proximityReward if agentState[5] == 0 else 0 # Take into account goal proximity
        reward +=posessionreward
        reward+=proximityReward
        #Find a way to reward passing behavior skip for now
        return reward


    """Takes as input: last k states, currentState, rewardargs
      Transform State Function returns 3 state vectors
      Agent State (Size of 9 + T) -> [Features 1-9 described in the manual and passing angles to each of the opponents]
      Team State (Size of (9 + T ) *T-1 )-> Simply concatenating agent state vectors of the teammates
      Opponent State ( 3*O ) -> Vector contains history information of each of the opponents information """
    def transformState(self,rawAgentState,stateCollection,featuretransformargs):
        #print 'Transform state'
        agentState= np.append(rawAgentState[0:10] ,rawAgentState [10+2*(self.teamSize-1):10+3*(self.teamSize-1)])
        #print "Agent State: "+str(agentState)
        teamState=[]
        #Weird Synchronization fix
        stateCollection = [x for x in stateCollection if type(x)!=type(1)]
        for u in range(len(stateCollection)):
            try:
                if stateCollection[u][0]!=agentState[0] or stateCollection[u][1]!=agentState[1]:
                    teamState +=  stateCollection[u][0:10].tolist()
            except:
                #print stateCollection
                #print u
                #print stateCollection[u]\
                #print "Inside Bad"
                bp()
        #print "team state is as :"+str(teamState)
        opponentState= rawAgentState [10+6*(self.teamSize-1)-1:-1]
        return agentState,teamState,opponentState
