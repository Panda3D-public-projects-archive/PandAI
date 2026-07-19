# PANDAI SEEK TUTORIAL
# Author: Srinavin Nair

from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.actor.Actor import Actor
from panda3d.ai import AIWorld, AICharacter


class World(ShowBase):

    def __init__(self):
        super().__init__()
        self.accept("escape", self.userExit)
        self.disableMouse()
        self.cam.setPosHpr(0, 0, 55, 0, -90, 0)

        self.loadModels()
        self.setAI()

    def loadModels(self):
        # Seeker
        self.seeker = Actor("models/ralph",
                            {"run": "models/ralph-run"})
        self.seeker.reparentTo(self.render)
        self.seeker.setScale(0.5)
        self.seeker.setPos(-10, 0, 0)
        # Target
        self.target = self.loader.loadModel("models/arrow")
        self.target.setColor(1, 0, 0)
        self.target.setPos(5, 0, 0)
        self.target.setScale(1)
        self.target.reparentTo(self.render)

    def setAI(self):
        # Creating AI World
        self.AIworld = AIWorld(self.render)

        self.AIchar = AICharacter("seeker", self.seeker, 100, 0.05, 5)
        self.AIworld.addAiChar(self.AIchar)
        self.AIbehaviors = self.AIchar.getAiBehaviors()

        self.AIbehaviors.seek(self.target)
        self.seeker.loop("run")

        # AI World update
        self.taskMgr.add(self.AIUpdate, "AIUpdate")

    # to update the AIWorld
    def AIUpdate(self, task):
        self.AIworld.update()
        return Task.cont


w = World()
w.run()
