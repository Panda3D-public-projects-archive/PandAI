# Author: Ryan Myers
# Models: Jeff Styers, Reagan Heller

from direct.showbase.ShowBase import ShowBase
from pandac.PandaModules import CollisionTraverser, CollisionNode
from pandac.PandaModules import CollisionHandlerQueue, CollisionRay
from pandac.PandaModules import TextNode
from pandac.PandaModules import Vec3, Vec4, BitMask32
from direct.gui.OnscreenText import OnscreenText
from direct.actor.Actor import Actor
from direct.task.Task import Task

# for Pandai
from panda3d.ai import AIWorld, AICharacter


def addInstructions(pos, msg):
    """Function to put instructions on the screen."""
    return OnscreenText(text=msg, style=1, fg=(1, 1, 1, 1), font=font,
                        pos=(-1.3, pos), align=TextNode.ALeft, scale=.05)


def addTitle(text):
    """Function to put title on the screen."""
    return OnscreenText(text=text, style=1, fg=(1, 1, 1, 1), font=font,
                        pos=(1.3, -0.95), align=TextNode.ARight, scale=.07)


class World(ShowBase):

    def __init__(self):
        super().__init__()
        self.accept("escape", self.userExit)

        global font
        font = self.loader.loadFont("cmss12")

        self.path_no = 1
        self.win.setClearColor(Vec4(0, 0, 0, 1))
        self.cam.setPosHpr(17.79, -87.64, 90.16, 38.66, 325.36, 0)

        # Post the instructions
        self.title = addTitle(
            "Pandai Tutorial: Roaming Ralph (Walking on Uneven Terrain) working with pathfinding")
        self.inst1 = addInstructions(0.95, "[ESC]: Quit")

        self.environ = self.loader.loadModel("models/world")
        self.environ.reparentTo(self.render)
        self.environ.setPos(12, 0, 0)

        self.box = self.loader.loadModel("models/box")
        self.box.reparentTo(self.render)
        self.box.setPos(-29.83, 0, 0)
        self.box.setScale(1)

        self.box1 = self.loader.loadModel("models/box")
        self.box1.reparentTo(self.render)
        self.box1.setPos(-51.14, -17.90, 0)
        self.box1.setScale(1)

        # Create the main character, Ralph

        ralphStartPos = Vec3(-98.64, -20.60, 0)
        self.ralph = Actor("models/ralph", {
            "run": "models/ralph-run",
            "walk": "models/ralph-walk"})
        self.ralph.reparentTo(self.render)
        self.ralph.setScale(1)
        self.ralph.setPos(ralphStartPos)

        self.pointer1 = self.loader.loadModel("models/arrow")
        self.pointer1.setColor(0, 0, 1)
        self.pointer1.setPos(-98.64, -20.60, 0)
        self.pointer1.setScale(3)
        self.pointer1.reparentTo(self.render)

        self.pointer2 = self.loader.loadModel("models/arrow")
        self.pointer2.setColor(1, 0, 0)
        self.pointer2.setPos(-7.5, -1.2, 0)
        self.pointer2.setScale(3)
        self.pointer2.reparentTo(self.render)

        self.cTrav = CollisionTraverser()

        self.ralphGroundRay = CollisionRay()
        self.ralphGroundRay.setOrigin(0, 0, 1000)
        self.ralphGroundRay.setDirection(0, 0, -1)
        self.ralphGroundCol = CollisionNode('ralphRay')
        self.ralphGroundCol.addSolid(self.ralphGroundRay)
        self.ralphGroundCol.setFromCollideMask(BitMask32.bit(0))
        self.ralphGroundCol.setIntoCollideMask(BitMask32.allOff())
        self.ralphGroundColNp = self.ralph.attachNewNode(self.ralphGroundCol)
        self.ralphGroundHandler = CollisionHandlerQueue()
        self.cTrav.addCollider(self.ralphGroundColNp, self.ralphGroundHandler)

        # Uncomment this line to see the collision rays
        # self.ralphGroundColNp.show()

        # Uncomment this line to show a visual representation of the
        # collisions occuring
        # self.cTrav.showCollisions(render)

        self.setAI()
        self.setMove()

    # Accepts arrow keys to move either the player or the menu cursor,
    # Also deals with grid checking and collision detection
    def move(self):
        # save ralph's initial position so that we can restore it,
        # in case he falls off the map or runs into something.
        startpos = self.ralph.getPos()

        # Now check for collisions.
        self.cTrav.traverse(self.render)

        # Adjust ralph's Z coordinate.  If ralph's ray hit terrain,
        # update his Z. If it hit anything else, or didn't hit anything, put
        # him back where he was last frame.
        entries = []
        for i in range(self.ralphGroundHandler.getNumEntries()):
            entry = self.ralphGroundHandler.getEntry(i)
            entries.append(entry)
        entries.sort(key=lambda x: x.getSurfacePoint(self.render).getZ(),
                     reverse=True)
        intoNodeName = entries[0].getIntoNode().getName()
        if len(entries) > 0 and intoNodeName == "terrain":
            self.ralph.setZ(entries[0].getSurfacePoint(self.render).getZ())
        else:
            self.ralph.setPos(startpos)

        self.ralph.setP(0)
        return Task.cont

    def setAI(self):
        # Creating AI World
        self.AIworld = AIWorld(self.render)

        self.AIchar = AICharacter("ralph", self.ralph, 60, 0.05, 25)
        self.AIworld.addAiChar(self.AIchar)
        self.AIbehaviors = self.AIchar.getAiBehaviors()

        self.AIbehaviors.initPathFind("models/navmeshUnevenTerrain.csv")

        # AI World update
        self.taskMgr.add(self.AIUpdate, "AIUpdate")

    def setMove(self):
        self.AIbehaviors.addStaticObstacle(self.box)
        self.AIbehaviors.addStaticObstacle(self.box1)
        self.AIbehaviors.pathFindTo(self.pointer2)
        self.ralph.loop("run")

    # to update the AIWorld
    def AIUpdate(self, task):
        self.AIworld.update()
        self.move()

        aiDone = self.AIbehaviors.behaviorStatus("pathfollow") == "done"
        if self.path_no == 1 and aiDone:
            self.path_no = 2
            self.AIbehaviors.pathFindTo(self.pointer1, "addPath")
            print("inside")
        elif self.path_no == 2 and aiDone:
            print("inside2")
            self.path_no = 1
            self.AIbehaviors.pathFindTo(self.pointer2, "addPath")

        return Task.cont


w = World()
w.run()
