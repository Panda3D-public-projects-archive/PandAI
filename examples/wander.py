# PANDAI WANDER TUTORIAL
# Author: Srinavin Nair

from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.actor.Actor import Actor
from panda3d.ai import AIWorld, AICharacter


class World(ShowBase):

    def __init__(self):
        super().__init__()
        self.disableMouse()
        self.cam.setPosHpr(0, 0, 55, 0, -90, 0)

        self.loadModels()
        self.setAI()

    def loadModels(self):
        # Seeker
        self.wanderer = Actor("models/ralph",
                              {"run": "models/ralph-run"})
        self.wanderer.reparentTo(self.render)
        self.wanderer.setScale(0.5)

    def setAI(self):
        # Creating AI World
        self.AIworld = AIWorld(self.render)

        self.AIchar = AICharacter("wanderer", self.wanderer, 100, 0.05, 5)
        self.AIworld.addAiChar(self.AIchar)
        self.AIbehaviors = self.AIchar.getAiBehaviors()

        self.AIbehaviors.wander(5, 0, 10, 1.0)
        self.wanderer.loop("run")

        # AI World update
        self.taskMgr.add(self.AIUpdate, "AIUpdate")

    # to update the AIWorld
    def AIUpdate(self, task):
        self.AIworld.update()
        return Task.cont


w = World()
w.run()
