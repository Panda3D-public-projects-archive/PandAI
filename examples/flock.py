# PANDAI WANDER TUTORIAL
# Author: Srinavin Nair

from direct.showbase.ShowBase import ShowBase
from direct.showbase.DirectObject import DirectObject
from direct.task import Task
from direct.actor.Actor import Actor
from panda3d.ai import AIWorld, AICharacter, Flock
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import Point3, TextNode

# Globals
base = ShowBase()
speed = 0.75

# Function to put instructions on the screen.
font = base.loader.loadFont("cmss12")


def addInstructions(pos, msg):
    return OnscreenText(text=msg, style=1, fg=(1, 1, 1, 1), font=font,
                        pos=(-1.3, pos), align=TextNode.ALeft, scale=.05)


class World(DirectObject):

    def __init__(self):
        self.accept("escape", base.userExit)
        base.disableMouse()
        base.cam.setPosHpr(0, 0, 85, 0, -90, 0)

        self.loadModels()
        self.setAI()
        self.setMovement()

    def loadModels(self):
        # Seeker
        self.flockers = []
        for i in range(10):
            self.flockers.append(Actor("models/ralph",
                                       {"run": "models/ralph-run"}))
            self.flockers[i].reparentTo(base.render)
            self.flockers[i].setScale(0.5)
            self.flockers[i].setPos(-10+i, 0, 0)
            self.flockers[i].loop("run")

        # Target
        self.target = base.loader.loadModel("models/arrow")
        self.target.setColor(1, 0, 0)
        self.target.setPos(0, 20, 0)
        self.target.setScale(1)
        self.target.reparentTo(base.render)

    def setAI(self):
        # Creating AI World
        self.AIworld = AIWorld(base.render)

        # Flock functions
        self.MyFlock = Flock(1, 270, 10, 2, 4, 1)
        self.AIworld.addFlock(self.MyFlock)
        self.AIworld.flockOn(1)

        self.AIchar = []
        self.AIbehaviors = []
        for i in range(10):
            self.AIchar.append(AICharacter(
                "flockers"+str(i), self.flockers[i], 100, 0.05, 5))
            self.AIworld.addAiChar(self.AIchar[i])
            self.AIbehaviors.append(self.AIchar[i].getAiBehaviors())
            self.MyFlock.addAiChar(self.AIchar[i])
            self.AIbehaviors[i].flock(0.5)
            self.AIbehaviors[i].pursue(self.target, 0.5)

        # AI World update
        base.taskMgr.add(self.AIUpdate, "AIUpdate")

    # to update the AIWorld
    def AIUpdate(self, task):
        self.AIworld.update()
        return Task.cont

# All the movement functions for the Target
    def setMovement(self):
        self.keyMap = {"left": 0, "right": 0, "up": 0, "down": 0}
        self.accept("arrow_left", self.setKey, ["left", 1])
        self.accept("arrow_right", self.setKey, ["right", 1])
        self.accept("arrow_up", self.setKey, ["up", 1])
        self.accept("arrow_down", self.setKey, ["down", 1])
        self.accept("arrow_left-up", self.setKey, ["left", 0])
        self.accept("arrow_right-up", self.setKey, ["right", 0])
        self.accept("arrow_up-up", self.setKey, ["up", 0])
        self.accept("arrow_down-up", self.setKey, ["down", 0])
        # movement task
        base.taskMgr.add(self.Mover, "Mover")

        addInstructions(0.9, "Use the Arrow keys to move the Red Target")

    def setKey(self, key, value):
        self.keyMap[key] = value

    def Mover(self, task):
        startPos = self.target.getPos()
        if (self.keyMap["left"] != 0):
            self.target.setPos(startPos + Point3(-speed, 0, 0))
        if (self.keyMap["right"] != 0):
            self.target.setPos(startPos + Point3(speed, 0, 0))
        if (self.keyMap["up"] != 0):
            self.target.setPos(startPos + Point3(0, speed, 0))
        if (self.keyMap["down"] != 0):
            self.target.setPos(startPos + Point3(0, -speed, 0))

        return Task.cont


w = World()
run()
