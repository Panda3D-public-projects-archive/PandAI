# PANDAI SEEK TUTORIAL
# Author: Srinavin Nair

from direct.showbase.ShowBase import ShowBase
from direct.showbase.DirectObject import DirectObject
from direct.task import Task
from direct.actor.Actor import Actor
from panda3d.ai import AIWorld, AICharacter

base = ShowBase()


class World(DirectObject):

    def __init__(self):
        self.accept("escape", base.userExit)
        base.disableMouse()
        base.cam.setPosHpr(0, 0, 55, 0, -90, 0)

        self.loadModels()
        self.setAI()

    def loadModels(self):
        # Seeker
        self.seeker = Actor("models/ralph",
                            {"run": "models/ralph-run"})
        self.seeker.reparentTo(base.render)
        self.seeker.setScale(0.5)
        self.seeker.setPos(-10, 0, 0)
        # Target1
        self.target1 = base.loader.loadModel("models/arrow")
        self.target1.setColor(1, 0, 0)
        self.target1.setPos(10, -10, 0)
        self.target1.setScale(1)
        self.target1.reparentTo(base.render)
        # Target2
        self.target2 = base.loader.loadModel("models/arrow")
        self.target2.setColor(0, 1, 0)
        self.target2.setPos(10, 10, 0)
        self.target2.setScale(1)
        self.target2.reparentTo(base.render)
        # Target3
        self.target3 = base.loader.loadModel("models/arrow")
        self.target3.setColor(0, 0, 1)
        self.target3.setPos(-10, 10, 0)
        self.target3.setScale(1)
        self.target3.reparentTo(base.render)
        # Target4
        self.target4 = base.loader.loadModel("models/arrow")
        self.target4.setColor(1, 0, 1)
        self.target4.setPos(-10, -10, 0)
        self.target4.setScale(1)
        self.target4.reparentTo(base.render)

        self.seeker.loop("run")

    def setAI(self):
        # Creating AI World
        self.AIworld = AIWorld(base.render)

        self.AIchar = AICharacter("seeker", self.seeker, 60, 0.05, 5)
        self.AIworld.addAiChar(self.AIchar)
        self.AIbehaviors = self.AIchar.getAiBehaviors()

        # Path follow (note the order is reveresed)
        self.AIbehaviors.pathFollow()
        self.AIbehaviors.addToPath(self.target4.getPos())
        self.AIbehaviors.addToPath(self.target3.getPos())
        self.AIbehaviors.addToPath(self.target2.getPos())
        self.AIbehaviors.addToPath(self.target1.getPos())

        self.AIbehaviors.startFollow()

        # AI World update
        base.taskMgr.add(self.AIUpdate, "AIUpdate")

    # to update the AIWorld
    def AIUpdate(self, task):
        self.AIworld.update()
        return Task.cont


w = World()
run()
