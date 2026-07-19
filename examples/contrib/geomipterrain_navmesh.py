"""Generate a PandAI navmesh.csv directly from a GeoMipTerrain heightmap.

Recovered from the Panda3D forum: posted by user "Chia_Pet" on 2010-03-30 in the
thread "AI Libraries for Panda3D", post #102 -- https://discourse.panda3d.org/t/6746/102
(bug-fixed later in the same thread with help from user "|Craig|", who cut the
runtime from roughly 6 minutes to 2 seconds).

Kept here because it is the only known way to produce a PandAI nav grid without
going through Max, Maya or Blender -- and the Blender exporter that survives is
the superseded X-Z-plane build. See COMMUNITY-NOTES.md.

Reproduced verbatim apart from this header. It is Python 2 and targets the
Panda3D of its day, so it will not run unmodified today; treat it as a reference
implementation of the navmesh.csv layout rather than a working tool. Note the
9-rows-per-cell structure it emits: one main node followed by eight neighbours.
"""

import direct.directbase.DirectStart
from direct.showbase.DirectObject import DirectObject
from panda3d.core import PNMImageHeader, Vec3, Texture, GeoMipTerrain, VBase4
from panda3d.core import Filename, BitMask32, TextureStage
#import csv
class World(DirectObject):
    def __init__(self):
        """
        This is a simple system to make PandaAI work with Geomip terrain
        Use ctrl-F to find the line you need to change by using the code inserted at the number in this text
        Things you need to change to make this work:
        1.use your heightmap                            - self.terrain.setHeightfield(Filename("Terrain/Level 1/terraintest.bmp"))
        2.change to number of blocks you want to use    - self.terrain.setBlockSize(64)
        3.Change your texture                           - loader.loadTexture('Terrain/Level 1/ground.jpg')
        4.change this to your heightmap again           - header.readHeader(Filename("Terrain/Level 1/terraintest.bmp"))
        
        Now you can use this code to make your Navmesh.csv for PandaAI.
        """
        base.cam.setPos(-100,512,3000)
        base.cam.lookAt(512,512,0)
        #Load the first environment model
        self.terrain = GeoMipTerrain("ground")
        self.terrain.setHeightfield(Filename("Terrain/Level 1/terraintest.bmp")) #Terrain/game heightmap.bmp
        # Set terrain properties
        self.terrain.setBlockSize(256)
        self.terrain.getRoot().reparentTo(render)
        self.terrain_tex = loader.loadTexture('Terrain/Level 1/ground.jpg')
        self.terrain_tex.setMagfilter (Texture.FTLinear) 
        self.terrain_tex.setMinfilter(Texture.FTLinearMipmapLinear)

        # Store root NodePath for convenience then set root settings for the terrain
        root = self.terrain.getRoot()
        #Set the terrain itself to be collide-able.
        root.setCollideMask(BitMask32.bit(0))
        root.reparentTo(render)
        ts = TextureStage('ts')
        root.setPos(0,0,0)
        root.setSz(50)
        root.setTexScale(ts.getDefault(),15,15)
        root.setTexture(self.terrain_tex,1)
        root.setTwoSided(True)
        
        header = PNMImageHeader()
        header.readHeader(Filename("Terrain/Level 1/terraintest.bmp"))
        hy = header.getYSize()
        hx = header.getXSize()
        bs = self.terrain.getBlockSize()
        cuber = (hx-1)/bs
        cubing2 = ((hx-1)/bs)/2

        file=open("navmesh.csv", "w")
        def doLine(*x): file.write(','.join( str(v) for v in x)+'\n')
        
        doLine("Grid Size",bs)
                
        doLine("NULL","NodeType","GridX","GridY","Length","Width","Height","PosX","PosY","PosZ")
        
        for j in range(bs):
            cubing = ((hx-1)/bs)/2
            for i in range(bs):
                
                def h(f,a,b,c=1):
                    if f: doLine(1,1,0,0,0,0,0,0,0,0)
                    else: doLine(0,c,i+a,j+b,cuber,cuber,0,cubing+cuber*a,cubing2+cuber*b,self.terrain.getElevation(cubing+cuber*a,cubing2+cuber*b)*self.terrain.getRoot().getSz())
                
                h(False,                   0, 0,c=0)
                h(i-1 < 0 or j+1 > bs-1,  -1, 1)
                h(i-1 < 0,                -1, 0)
                h(i-1 < 0 or j-1 < 0,     -1,-1)
                h(j-1 < 0,                 0,-1)
                
                h(i+1 > bs-1 or j-1 < 0,   1,-1)
                h(i+1 > bs-1,              1, 0)
                h(i+1 > bs-1 or j+1 >bs-1, 1, 1)
                h(j+1 > bs-1,              0, 1)
                
                cubing += cuber
            cubing2 = cubing2 + cuber
                 
        #Updates the taskMgr
        taskMgr.add(self.updateTask, "update")

        #this updates the terrain when needed
    def updateTask(self, task): 
        self.terrain.update()
        self.terrain.getRoot().setCollideMask(BitMask32.bit(0)) 
        return task.cont 

w=World()
run()
