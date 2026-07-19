# PANDAI FLEE TUTORIAL
# Author: Srinavin Nair

from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.actor.Actor import Actor
from panda3d.ai import AIWorld, AICharacter


class World(ShowBase):

    def __init__(self):
        super().__init__()
        self.accept("escape", base.userExit)
        self.disableMouse()
        self.cam.setPosHpr(0, 0, 55, 0, -90, 0)

        self.loadModels()
        self.setAI()

    def loadModels(self):
        # Seeker
        self.fleer = Actor("models/ralph",
                           {"run": "models/ralph-run"})
        self.fleer.reparentTo(self.render)
        self.fleer.setScale(0.5)
        self.fleer.setPos(2, 0, 0)
        # Target
        self.target = self.loader.loadModel("models/arrow")
        self.target.setColor(1, 0, 0)
        self.target.setPos(5, 0, 0)
        self.target.setScale(1)
        self.target.reparentTo(self.render)

    def setAI(self):
        # Creating AI World
        self.AIworld = AIWorld(self.render)

        self.AIchar = AICharacter("fleer", self.fleer, 100, 0.05, 5)
        self.AIworld.addAiChar(self.AIchar)
        self.AIbehaviors = self.AIchar.getAiBehaviors()

        self.AIbehaviors.flee(self.target, 5, 5)
        self.fleer.loop("run")

        # AI World update
        self.taskMgr.add(self.AIUpdate, "AIUpdate")

    # to update the AIWorld
    def AIUpdate(self, task):
        self.AIworld.update()
        return Task.cont


w = World()
w.run()
