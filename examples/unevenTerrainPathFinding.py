# Author: Ryan Myers
# Models: Jeff Styers, Reagan Heller

from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from direct.showbase.DirectObject import DirectObject
from direct.task import Task
from direct.actor.Actor import Actor
from panda3d.ai import AIWorld, AICharacter
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import CollisionHandlerQueue, CollisionRay, BitMask32
from panda3d.core import CollisionTraverser, CollisionNode
from panda3d.core import NodePath, TextNode, PandaNode, Vec4

base = ShowBase()
SPEED = 0.5
font = base.loader.loadFont("cmss12")


def addInstructions(pos, msg):
    """Function to put instructions on the screen."""
    return OnscreenText(text=msg, style=1, fg=(1, 1, 1, 1), font=font,
                        pos=(-1.3, pos), align=TextNode.ALeft, scale=.05)


def addTitle(text):
    """Function to put title on the screen."""
    return OnscreenText(text=text, style=1, fg=(1, 1, 1, 1), font=font,
                        pos=(1.3, -0.95), align=TextNode.ARight, scale=.07)


class World(DirectObject):

    def __init__(self):

        # self.switchState = False
        self.switchState = True
        self.switchCam = False
        self.path_no = 1
        base.win.setClearColor(Vec4(0, 0, 0, 1))
        base.cam.setPosHpr(17.79, -87.64, 90.16, 38.66, 325.36, 0)
        # Post the instructions

        self.title = addTitle(
            "Pandai Tutorial: Roaming Ralph (Walking on Uneven Terrain) working with pathfinding")
        self.inst1 = addInstructions(0.95, "[ESC]: Quit")
        self.inst2 = addInstructions(
            0.90, "[Space - do Only once]: Start Pathfinding")
        self.inst3 = addInstructions(0.85, "[Enter]: Change camera view")

        # Set up the environment
        #
        # This environment model contains collision meshes.  If you look
        # in the egg file, you will see the following:
        #
        #    <Collide> { Polyset keep descend }
        #
        # This tag causes the following mesh to be converted to a collision
        # mesh -- a mesh which is optimized for collision, not rendering.
        # It also keeps the original mesh, so there are now two copies ---
        # one optimized for rendering, one for collisions.

        self.environ = base.loader.loadModel("models/world")
        self.environ.reparentTo(base.render)
        self.environ.setPos(12, 0, 0)

        self.box = base.loader.loadModel("models/box")
        self.box.reparentTo(base.render)
        self.box.setPos(-29.83, 0, 0)
        self.box.setScale(1)

        self.box1 = base.loader.loadModel("models/box")
        self.box1.reparentTo(base.render)
        self.box1.setPos(-51.14, -17.90, 0)
        self.box1.setScale(1)

        # Create the main character, Ralph

        self.ralph = Actor("models/ralph",
                           {"run": "models/ralph-run",
                            "walk": "models/ralph-walk"})
        self.ralph.reparentTo(base.render)
        self.ralph.setScale(1)
        self.ralph.setPos(-98.64, -20.60, 0)

        self.pointer1 = base.loader.loadModel("models/arrow")
        self.pointer1.setColor(1, 0, 0)
        self.pointer1.setPos(-98.64, -20.60, 0)
        self.pointer1.setScale(3)
        self.pointer1.reparentTo(base.render)

        self.pointer2 = base.loader.loadModel("models/arrow")
        self.pointer2.setColor(0, 0, 1)
        self.pointer2.setPos(-7.5, -1.2, 0)
        self.pointer2.setScale(3)
        self.pointer2.reparentTo(base.render)

        # Create a floater object.  We use the "floater" as a temporary
        # variable in a variety of calculations.

        self.floater = NodePath(PandaNode("floater"))
        self.floater.reparentTo(base.render)

        # Accept the control keys for movement and rotation

        self.accept("escape", base.userExit)
        self.accept("enter", self.activateCam)

        # Game state variables
        self.isMoving = False

        # Set up the camera

        # We will detect the height of the terrain by creating a collision
        # ray and casting it downward toward the terrain.  One ray will
        # start above ralph's head, and the other will start above the camera.
        # A ray may hit the terrain, or it may hit a rock or a tree.  If it
        # hits the terrain, we can detect the height.  If it hits anything
        # else, we rule that the move is illegal.

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

        self.camGroundRay = CollisionRay()
        self.camGroundRay.setOrigin(0, 0, 1000)
        self.camGroundRay.setDirection(0, 0, -1)
        self.camGroundCol = CollisionNode('camRay')
        self.camGroundCol.addSolid(self.camGroundRay)
        self.camGroundCol.setFromCollideMask(BitMask32.bit(0))
        self.camGroundCol.setIntoCollideMask(BitMask32.allOff())
        self.camGroundColNp = base.camera.attachNewNode(self.camGroundCol)
        self.camGroundHandler = CollisionHandlerQueue()
        self.cTrav.addCollider(self.camGroundColNp, self.camGroundHandler)

        # Uncomment this line to see the collision rays
        # self.ralphGroundColNp.show()
        # self.camGroundColNp.show()

        # Uncomment this line to show a visual representation of the
        # collisions occuring
        # self.cTrav.showCollisions(base.render)

        self.setAI()

    def activateCam(self):
        self.switchCam = not self.switchCam
        if (self.switchCam is True):
            base.cam.setPosHpr(0, 0, 0, 0, 0, 0)
            base.cam.reparentTo(self.ralph)
            base.cam.setY(base.cam.getY() + 30)
            base.cam.setZ(base.cam.getZ() + 10)
            base.cam.setHpr(180, -15, 0)
        else:
            base.cam.reparentTo(base.render)
            base.cam.setPosHpr(17.79, -87.64, 90.16, 38.66, 325.36, 0)

    # Records the state of the arrow keys

    def setKey(self, key, value):
        self.keyMap[key] = value

    # Accepts arrow keys to move either the player or the menu cursor,
    # Also deals with grid checking and collision detection

    def move(self):

        # Get the time elapsed since last frame. We need this
        # for framerate-independent movement.
        elapsed = globalClock.getDt()

        # If the camera-left key is pressed, move camera left.
        # If the camera-right key is pressed, move camera right.
        if (self.switchState is False):
            base.camera.lookAt(self.ralph)
            if (self.keyMap["cam-left"] != 0):
                base.camera.setX(base.camera, -(elapsed*20))
            if (self.keyMap["cam-right"] != 0):
                base.camera.setX(base.camera, +(elapsed*20))

        # save ralph's initial position so that we can restore it,
        # in case he falls off the map or runs into something.

        startpos = self.ralph.getPos()

        # If the camera is too far from ralph, move it closer.
        # If the camera is too close to ralph, move it farther.
        if (self.switchState is False):
            camvec = self.ralph.getPos() - base.camera.getPos()
            camvec.setZ(0)
            camdist = camvec.length()
            camvec.normalize()
            if (camdist > 10.0):
                base.camera.setPos(base.camera.getPos() + camvec*(camdist-10))
                camdist = 10.0
            if (camdist < 5.0):
                base.camera.setPos(base.camera.getPos() - camvec*(5-camdist))
                camdist = 5.0

        # Now check for collisions.

        self.cTrav.traverse(base.render)

        # Adjust ralph's Z coordinate.  If ralph's ray hit terrain,
        # update his Z. If it hit anything else, or didn't hit anything, put
        # him back where he was last frame.

        entries = []
        for i in range(self.ralphGroundHandler.getNumEntries()):
            entry = self.ralphGroundHandler.getEntry(i)
            entries.append(entry)
        entries.sort(key=lambda x: x.getSurfacePoint(
            base.render).getZ(), reverse=True)
        if len(entries) > 0 \
                and entries[0].getIntoNode().getName() == "terrain":
            self.ralph.setZ(entries[0].getSurfacePoint(base.render).getZ())
        else:
            self.ralph.setPos(startpos)

        # Keep the camera at one foot above the terrain,
        # or two feet above ralph, whichever is greater.

        if (self.switchState is False):
            entries = []
            for i in range(self.camGroundHandler.getNumEntries()):
                entry = self.camGroundHandler.getEntry(i)
                entries.append(entry)
            entries.sort(lambda x: x.getSurfacePoint(
                base.render).getZ(), reverse=True)
            if len(entries) > 0 \
                    and entries[0].getIntoNode().getName() == "terrain":
                base.camera.setZ(entries[0].getSurfacePoint(
                    base.render).getZ()+1.0)
            if (base.camera.getZ() < self.ralph.getZ() + 2.0):
                base.camera.setZ(self.ralph.getZ() + 2.0)

            # The camera should look in ralph's direction,
            # but it should also try to stay horizontal, so look at
            # a floater which hovers above ralph's head.

            self.floater.setPos(self.ralph.getPos())
            self.floater.setZ(self.ralph.getZ() + 2.0)
            base.camera.setZ(base.camera.getZ())
            base.camera.lookAt(self.floater)

        self.ralph.setP(0)
        return Task.cont

    def setAI(self):
        # Creating AI World
        self.AIworld = AIWorld(base.render)

        self.accept("space", self.setMove)
        self.AIchar = AICharacter("ralph", self.ralph, 60, 0.05, 25)
        self.AIworld.addAiChar(self.AIchar)
        self.AIbehaviors = self.AIchar.getAiBehaviors()

        self.AIbehaviors.initPathFind("models/navmeshUnevenTerrain.csv")

        # AI World update
        base.taskMgr.add(self.AIUpdate, "AIUpdate")

    def setMove(self):
        self.AIbehaviors.addStaticObstacle(self.box)
        self.AIbehaviors.addStaticObstacle(self.box1)
        self.AIbehaviors.pathFindTo(self.pointer2)
        self.ralph.loop("run")

    # to update the AIWorld
    def AIUpdate(self, task):
        self.AIworld.update()
        self.move()

        if self.path_no == 1 \
                and self.AIbehaviors.behaviorStatus("pathfollow") == "done":
            self.path_no = 2
            self.AIbehaviors.pathFindTo(self.pointer1, "addPath")
            print("inside")

        if self.path_no == 2 \
                and self.AIbehaviors.behaviorStatus("pathfollow") == "done":
            self.path_no = 1
            self.AIbehaviors.pathFindTo(self.pointer2, "addPath")
            print("inside2")

        return Task.cont


w = World()
base.run()
