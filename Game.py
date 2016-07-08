# -*- coding: UTF-8 -*-

# Author: CJT
# Date: 2016/6/16

# A simple skybox.

from panda3d.core import loadPrcFileData
loadPrcFileData('', 'window-title CJT Skybox Demo')
loadPrcFileData('', 'win-size 1280 720')
loadPrcFileData('', 'sync-video true')
loadPrcFileData('', 'show-frame-rate-meter true')
loadPrcFileData('', 'texture-minfilter linear-mipmap-linear')
loadPrcFileData('', 'cursor-hidden true')

from pandac.PandaModules import *
from direct.showbase.ShowBase import ShowBase
from panda3d.core import *
from direct.task.Task import Task
from direct.actor.Actor import Actor
from direct.gui.OnscreenText import OnscreenText
from direct.showbase.DirectObject import DirectObject
from direct.showbase.BufferViewer import BufferViewer
from direct.showbase.InputStateGlobal import inputState
from direct.interval.IntervalGlobal import Sequence
import sys
import os
from math import *

from panda3d.bullet import *

from threading import Timer
import time

MouseSensitivity = 100
cameraSpeed = 25
zoomRate = 5


class Skybox(ShowBase):

    def __init__(self):
        ShowBase.__init__(self)
        # base.setBackgroundColor(0.0, 0.0, 0.0, 1)
        # base.setFrameRateMeter(True)

        # 渲染天空盒，添加光照
        sha = Shader.load(
            Shader.SLGLSL, "shaders/skybox_vert.glsl", "shaders/skybox_frag.glsl")

        self.skyTex = loader.loadCubeMap("textures/skybox/Highnoon_#.jpg")

        self.ambientLight = render.attachNewNode(AmbientLight("ambientLight"))
        self.ambientLight.node().setColor((0.2, 0.2, 0.2, 1.0))

        self.sun = render.attachNewNode(DirectionalLight("sun"))
        self.sun.node().setColor((0.8, 0.8, 1.0, 1.0))
        self.sun.node().setDirection(LVector3(1, -1, -3))

        render.setLight(self.ambientLight)
        render.setLight(self.sun)

        self.skybox = self.loader.loadModel("models/skybox")
        self.skybox.reparentTo(self.render)
        self.skybox.setShader(sha)
        self.skybox.setShaderInput("skybox", self.skyTex)
        self.skybox.setAttrib(DepthTestAttrib.make(RenderAttrib.MLessEqual))

        # 处理输入
        self.accept('escape', self.doExit)
        self.accept('r', self.doReset)
        self.accept('f1', self.toggleWireframe)
        self.accept('f2', self.toggleTexture)
        self.accept('f3', self.toggleDebug)

        self.tagOfForward = 0
        self.tagOfReverse = 0
        self.tagOfLeft = 0
        self.tagOfRight = 0
        self.count = 0

        #### 各种tag参数 ####

        # 是否在零摩擦区域内
        self.tagOfZeroRub = 0
        # 用来判断零摩擦运动是否结束
        self.countForCheck = 0  # 用于判断停止的时间间隔（mod 5）
        self.posXBefore = 0
        self.posYBefore = 0
        self.posXNow = 0
        self.posYNow = 0
        #
        self.tagOfSlabStone = 1
        self.tagOfOut = 1
        #### 各种tag参数 ####

        # 接受输入
        inputState.watchWithModifiers('forward', 'w')
        inputState.watchWithModifiers('left', 'a')
        inputState.watchWithModifiers('reverse', 's')
        inputState.watchWithModifiers('right', 'd')
        inputState.watchWithModifiers('transfer', 'e')
        inputState.watchWithModifiers('slabstone', 'z')

        # Task
        taskMgr.add(self.update, 'updateWorld')

        # 初始化
        self.setup()

    #### 函数 ####

    # 退出
    def doExit(self):
        self.cleanup()
        sys.exit(1)

    # 重置
    def doReset(self):
        #### 各种tag参数 ####

        # 是否在零摩擦区域内
        self.tagOfZeroRub = 0
        # 用来判断零摩擦运动是否结束
        self.countForCheck = 0  # 用于判断停止的时间间隔（mod 5）
        self.posXBefore = 0
        self.posYBefore = 0
        self.posXNow = 0
        self.posYNow = 0
        #
        self.tagOfSlabStone = 1
        self.tagOfOut = 1
        #### 各种tag参数 ####

        self.cleanup()
        self.setup()

    # 暂时不可用，会出错，希望谁能够实现这两个函数
    # def toggleWireframe(self):
    #     base.toggleWireframe()

    # def toggleTexture(self):
    #     base.toggleTexture()
    def goZ(self):
        for i in range(100):
            speed = Vec3(0, 0, 0)
            speed.setY(1.0)
            speed *= 6.0
            self.characterNP.node().setLinearMovement(speed, True)

    # 显示框框
    def toggleDebug(self):
        if self.debugNP.isHidden():
            self.debugNP.show()
        else:
            self.debugNP.hide()

    # 处理输入(在零摩擦区域之外)
    def processInputOutZero(self, dt):
        speed = Vec3(0, 0, 0)
        # torque = Vec3(0, 0, 0)

        if inputState.isSet('forward'):
            speed.setX(1.0)
        if inputState.isSet('reverse'):
            speed.setX(-1.0)
        if inputState.isSet('left'):
            speed.setY(1.0)
        if inputState.isSet('right'):
            speed.setY(-1.0)

        speed *= 6.0
        # torque *= 10.0

        # speed = render.getRelativeVector(self.boxNP, speed)
        # torque = render.getRelativeVector(self.boxNP, torque)
        for i in range(100):
            # #print "a"
            self.characterNP.node().setLinearMovement(speed, True)

        # self.boxNP.node().setActive(True)
        # self.boxNP.node().applyCentralspeed(speed)
        # self.boxNP.node().applyTorque(torque)

    # 处理输入(在零摩擦区域之内)
    def processInputInZero(self, dt):
        if self.tagOfForward == 0 and self.tagOfReverse == 0 and self.tagOfLeft == 0 and self.tagOfRight == 0:
            if inputState.isSet('forward'):
                self.tagOfForward = 1
            if inputState.isSet('reverse'):
                self.tagOfReverse = 1
            if inputState.isSet('left'):
                self.tagOfLeft = 1
            if inputState.isSet('right'):
                self.tagOfRight = 1

    # 在零摩擦区域内的移动
    def MoveInZero(self):
        self.posXBefore = self.characterNP.getX()
        self.posYBefore = self.characterNP.getY()
        self.speed = Vec3(0, 0, 0)
        if self.tagOfForward == 1:
            if self.world.contactTest(self.characterNP.node()).getNumContacts() != 0:
                speed = Vec3(0, 0, 0)
                speed.setX(1.0)
                speed *= 6.0
                self.speed = speed
            if self.world.contactTest(self.characterNP.node()).getNumContacts() == 0:
                self.speed = Vec3(0, 0, 0)
            self.characterNP.node().setLinearMovement(self.speed, True)
        if self.tagOfReverse == 1:
            if self.world.contactTest(self.characterNP.node()).getNumContacts() != 0:
                speed = Vec3(0, 0, 0)
                speed.setX(-1.0)
                speed *= 6.0
                self.speed = speed
            if self.world.contactTest(self.characterNP.node()).getNumContacts() == 0:
                self.speed = Vec3(0, 0, 0)
            self.characterNP.node().setLinearMovement(self.speed, True)
        if self.tagOfLeft == 1:
            if self.world.contactTest(self.characterNP.node()).getNumContacts() != 0:
                speed = Vec3(0, 0, 0)
                speed.setY(1.0)
                speed *= 6.0
                self.speed = speed
            if self.world.contactTest(self.characterNP.node()).getNumContacts() == 0:
                self.speed = Vec3(0, 0, 0)
            self.characterNP.node().setLinearMovement(self.speed, True)
        if self.tagOfRight == 1:
            if self.world.contactTest(self.characterNP.node()).getNumContacts() != 0:
                speed = Vec3(0, 0, 0)
                speed.setY(-1.0)
                speed *= 6.0
                self.speed = speed
            if self.world.contactTest(self.characterNP.node()).getNumContacts() == 0:
                self.speed = Vec3(0, 0, 0)
            self.characterNP.node().setLinearMovement(self.speed, True)

    def check(self):
        self.posXNow = self.characterNP.getX()
        self.posYNow = self.characterNP.getY()

        if self.posXBefore == self.posXNow and self.posYBefore == self.posYNow:
            self.tagOfForward = 0
            self.tagOfReverse = 0
            self.tagOfLeft = 0
            self.tagOfRight = 0

        # #print self.characterNP.getPos()
        if self.characterNP.getPos() == Vec3(15, 31, 0.96):
            if self.tagOfOut == 1:
                self.tagOfZeroRub = 1
            self.tagOfSlabStone -= 1
            self.tagOfOut -= 1

        # #print self.tagOfOut
        # print self.characterNP.getPos()
        # #print self.tagOfOut
        if self.characterNP.getX() > 16 and self.characterNP.getY() < 4:
            # print self.tagOfOut
            if self.tagOfOut < 0:
                # #print "yes"
                self.tagOfOut += 1
                self.tagOfZeroRub = 0
                characterPosInterval = self.characterNP.posInterval(
                    2, Point3(20, 19, 2), startPos=Point3(16, 2, 1))
                characterPosInterval.start()

        if self.characterNP.getPos() == Vec3(20, 19, 0.96):
            # #print "yesA"
            # print self.tagOfOut
            if self.tagOfOut == 0:
                # #print "yesB"
                self.characterNP.node().removeChild(self.visualNPOfCharacter.node())
                self.visualNPOfSlabstone.reparentTo(self.slabstoneNP)
                self.tagOfOut += 1

    # 碰撞事件
    def contact(self):
        result = self.world.contactTest(self.characterNP.node())
        # #print result.getNumContacts()

        for contact in result.getContacts():
            # #print contact.getNode0()
            # #print contact.getNode1()
            for i in range(2):
                if inputState.isSet('slabstone'):
                    if self.tagOfSlabStone == 1:
                        if contact.getNode1() == self.slabstoneNP.node():
                            # self.characterNP.node().setGravity(0)
                            # characterPosInterval = self.characterNP.posInterval(
                            # 2, Point3(15, 31, 2), startPos=Point3(20, 19, 1))
                            self.visualNPOfCharacter = loader.loadModel(
                                'models/Slabstone.egg')
                            self.visualNPOfCharacter.clearModelNodes()
                            self.visualNPOfCharacter.setScale(0.5)
                            self.visualNPOfCharacter.reparentTo(
                                self.characterNP)
                            self.visualNPOfCharacter.setPos(0, 0, -1)
                            # self.characterNP.node().setGravity(0)
                            # characterPosInterval.start()
                            self.takeoff(-5)
                            self.tagOfSlabStone -= 1
                            # #print self.characterNP.getPos()
                            self.slabstoneNP.node().removeChild(self.visualNPOfSlabstone.node())
                            # if self.characterNP.getPos == Point3(15,31,0):
                            # self.characterNP.node().setGravity(9.81)

                if inputState.isSet('transfer'):
                    if contact.getNode1() == self.transList[1].node():
                        self.speed = Vec3(0, 0, 0)
                        self.characterNP.node().setLinearMovement(self.speed, True)
                        self.nowX = 14.00
                        self.nowY = 12.00
                        self.nowZ = 0.96

                        self.characterNP.setPos(
                            self.transList[4].getPos() + (0, 0, 0.1))
                        self.takeoff(4)

                    if contact.getNode1() == self.transList[5].node():
                        self.speed = Vec3(0, 0, 0)
                        self.characterNP.node().setLinearMovement(self.speed, True)
                        self.nowX = 14.00
                        self.nowY = 35.00
                        self.nowZ = 20.96

                        self.characterNP.setPos(
                            self.transList[7].getPos() + (0, 0, 0.1))
                        self.takeoff(7)

                    if contact.getNode1() == self.transList[6].node():
                        self.speed = Vec3(0, 0, 0)
                        self.characterNP.node().setLinearMovement(self.speed, True)
                        self.nowX = 6.00
                        self.nowY = 36.00
                        self.nowZ = 40.96

                        self.characterNP.setPos(
                            self.transList[3].getPos() + (0, 0, 0.5))
                        self.takeoff(3)

                    if contact.getNode1() == self.transList[2].node():
                        self.speed = Vec3(0, 0, 0)
                        self.characterNP.node().setLinearMovement(self.speed, True)
                        self.nowX = 6.00
                        self.nowY = 32.00
                        self.nowZ = 20.96

                        self.characterNP.setPos(
                            self.transList[0].getPos() + (0, 0, 0.1))
                        self.takeoff(0)

    def takeoff(self, tag):
        self.taskMgr.remove("updateWorld")

        if tag < 0:
            self.taskMgr.add(self.fly, "Fly")

        if tag >= 0:
            self.speedX = float(
                self.transList[tag].getX() - self.nowX) / float(200)
            self.speedY = float(
                self.transList[tag].getY() - self.nowY) / float(200)
            self.speedZ = float(
                self.transList[tag].getZ() - self.nowZ) / float(200)
            # print self.transList[tag].getPos(),self.characterNP.getPos(),self.nowX,self.nowY,self.nowZ
            # print self.speedX,self.speedY,self.speedZ
            self.taskMgr.add(self.flycam, "Flycam")

    def fly(self, task):
        self.characterNP.setPos(self.characterNP.getX(
        ) - 0.025, self.characterNP.getY() + 0.06, self.characterNP.getZ())
        self.updatecam()
        self.count += 1

        if self.count == 199:
            self.count = 0
            self.land(-5)

        return Task.cont

    def flycam(self, task):
        # print "x",self.cam.getX()
        self.cam.setPos(self.cam.getX() + self.speedX, self.cam.getY() +
                        self.speedY, self.cam.getZ() + self.speedZ)

        # print "flying",self.cam.getPos()
        self.skybox.setPos(self.cam.getPos())
        self.count += 1

        if self.count == 199:
            self.count = 0
            self.land(1)

        return Task.cont

    def land(self, tag):
        # self.characterNP.setPos(15, 31, 0.97)
        self.tagOfZeroRub = 1
        if tag < 0:
            self.taskMgr.remove("Fly")
        if tag >= 0:
            self.nowX = 0.00
            self.nowY = 0.00
            self.nowZ = 0.00
            self.taskMgr.remove("Flycam")
            # print self.transList[tag].getPos(),self.characterNP.getPos()

        self.taskMgr.add(self.update, "updateWorld")

    # Task函数
    def update(self, task):

        self.countForCheck += 1
        dt = globalClock.getDt()

        if self.tagOfZeroRub == 0:
            self.processInputOutZero(dt)
        if self.tagOfZeroRub == 1:
            self.processInputInZero(dt)

        if self.countForCheck % 5 != 0:
            self.MoveInZero()
        # self.world.doPhysics(dt)
        self.world.doPhysics(dt, 5, 1.0 / 45.0)
        if self.countForCheck % 5 == 0:
            self.check()

        self.contact()
        # #print "out"
        self.updatecam()

        return task.cont

    # 重置
    def cleanup(self):
        self.world.removeCharacter(self.characterNP.node())
        self.world.removeRigidBody(self.groundNP.node())
        self.world.removeRigidBody(self.wallNP.node())
        self.world.removeRigidBody(self.transNP.node())

        self.world = None

        self.boxNP = None
        self.debugNP = None
        self.groundNP = None
        self.wallNP = None
        self.transNP = None

        self.worldNP.removeNode()

    # 设置地面方块
    def initGroundBoxes(self, posx, posy, posz):
        shape = BulletBoxShape(Vec3(0.5, 0.5, 0.5))
        # #print 'GroundBox_(%d,%d)_' % (posx, posy)
        groundBoxNP = self.worldNP.attachNewNode(
            BulletRigidBodyNode('GroundBox_(%d,%d,%d)_' % (posx, posy, posz)))
        groundBoxNP.node().addShape(shape)
        groundBoxNP.setPos(posx, posy, posz)
        groundBoxNP.setCollideMask(BitMask32.allOn())
        self.world.attachRigidBody(groundBoxNP.node())
        # visualNP = loader.loadModel('models/cube.egg')
        # visualNP.clearModelNodes()
        # visualNP.setScale(0.5)
        # visualNP.reparentTo(groundBoxNP)

        self.groundNP = groundBoxNP

    # 设置墙面方块
    def initWallBoxes(self, posx, posy, posz):
        shape = BulletBoxShape(Vec3(0.5, 0.5, 0.5))
        # #print 'WallBox_(%d,%d)_' % (posx, posy)
        wallBoxNP = self.worldNP.attachNewNode(
            BulletRigidBodyNode('WallBox_(%d,%d,%d)_' % (posx, posy, posz)))
        wallBoxNP.node().addShape(shape)
        wallBoxNP.setPos(posx, posy, posz + 1)
        wallBoxNP.setCollideMask(BitMask32.allOn())
        self.world.attachRigidBody(wallBoxNP.node())
        visualNP = loader.loadModel('models/Stair.egg')
        visualNP.clearModelNodes()
        visualNP.setScale(0.5)
        visualNP.reparentTo(wallBoxNP)

        self.wallNP = wallBoxNP

    # 设置传送方块
    def initTransBoxes(self, posx, posy, posz):
        shape = BulletBoxShape(Vec3(0.5, 0.5, 0.5))
        # #print 'TransBox_(%d,%d)_' % (posx, posy)
        transBoxNP = self.worldNP.attachNewNode(
            BulletRigidBodyNode('TransBox_(%d,%d,%d)_' % (posx, posy, posz)))
        transBoxNP.node().addShape(shape)
        transBoxNP.setPos(posx, posy, posz)
        transBoxNP.setCollideMask(BitMask32.allOn())
        self.world.attachRigidBody(transBoxNP.node())
        visualNP = loader.loadModel('models/Cloudcube.egg')
        visualNP.clearModelNodes()
        visualNP.setScale(0.5)
        visualNP.reparentTo(transBoxNP)

        self.transNP = transBoxNP

    # 游戏角色
    def initCharacter(self):
        characterMaterial = Material()
        characterMaterial.setShininess(4.0)
        characterMaterial.setSpecular(VBase4(1, 1, 1, 1))

        shape = BulletBoxShape(Vec3(0.5, 0.5, 0.5))

        characterBoxNP = self.worldNP.attachNewNode(
            BulletCharacterControllerNode(shape, 0.5, 'character'))
        # characterBoxNP.node().setGravity(0)
        # characterBoxNP.node().setMass(1.0)
        # characterBoxNP.node().addShape(shape)
        # characterBoxNP.setPos(15, 32, 4) #落在零摩擦初始地点
        characterBoxNP.setPos(20, 20, 4)
        characterBoxNP.setCollideMask(BitMask32.allOn())

        self.world.attachCharacter(characterBoxNP.node())

        self.characterNP = characterBoxNP

        # 角色模型
        visualNP = loader.loadModel('models/BlueCube.egg')
        visualNP.setMaterial(characterMaterial)
        visualNP.clearModelNodes()
        visualNP.setScale(0.5)
        visualNP.reparentTo(self.characterNP)

        self.characterNP.setAntialias(AntialiasAttrib.MMultisample)

    # 开始点
    def initStart(self):
        start = [[2, 2, 2, 2, 2, 2, 2],
                 [2, 2, 2, 2, 2, 2, 2],
                 [2, 2, 2, 2, 2, 2, 2],
                 [2, 2, 2, 2, 2, 2, 2],
                 [2, 2, 2, 2, 2, 2, 2],
                 [2, 2, 2, 2, 2, 2, 2],
                 [2, 2, 2, 2, 2, 2, 2]]

        startCountX = 0
        for i in start:
            startCountY = -1
            for j in i:
                if j == 0:
                    startCountY += 1
                    # continue
                if j == 1:
                    startCountY += 1
                    self.initWallBoxes(startCountX + 20, startCountY + 20, 0)
                    # continue
                if j == 2:
                    startCountY += 1
                    self.initGroundBoxes(startCountX + 20, startCountY + 20, 0)
                    # continue
                if j == 3:
                    self.countTransTag += 1
                    startCountY += 1
                    self.initTransBoxes(startCountX + 20, startCountY + 20, 0)
                    self.transList.append(self.transNP)
                    # continue
            startCountX += 1

    # 浮板
    def initSlabstone(self):
        shape = BulletBoxShape(Vec3(0.5, 0.5, 0.5))
        slabstoneBoxNP = self.worldNP.attachNewNode(
            BulletRigidBodyNode('SlabstoneBox'))
        slabstoneBoxNP.node().addShape(shape)
        slabstoneBoxNP.setPos(20, 19, 0)
        slabstoneBoxNP.setCollideMask(BitMask32.allOn())
        self.world.attachRigidBody(slabstoneBoxNP.node())
        self.visualNPOfSlabstone = loader.loadModel('models/Slabstone.egg')
        self.visualNPOfSlabstone.clearModelNodes()
        self.visualNPOfSlabstone.setScale(0.5)
        self.visualNPOfSlabstone.reparentTo(slabstoneBoxNP)

        self.slabstoneNP = slabstoneBoxNP

    # 零摩擦地图
    def initZero(self):
        # 零摩擦第一层（2个传送）
        L1 = [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                  0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                  0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
               0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
               0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
              [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
               1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
              [0, 0, 1, 1, 1, 1, 1, 2, 2, 2, 2, 1, 2, 2, 2, 1, 2, 2, 2,
               1, 2, 2, 2, 1, 2, 2, 2, 1, 2, 2, 2, 3, 1, 0, 0, 0],
              [0, 1, 2, 2, 2, 2, 2, 2, 2, 1, 2, 1, 2, 1, 2, 2, 2, 1, 2,
               2, 2, 1, 2, 2, 2, 1, 2, 1, 2, 1, 1, 1, 1, 0, 0, 0],
              [0, 1, 2, 2, 1, 1, 1, 1, 1, 1, 2, 2, 2, 1, 1, 1, 1, 1, 1,
               1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 1, 1, 1, 1, 0, 0, 0],
              [1, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 1,
               2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0],
              [1, 2, 2, 2, 1, 1, 1, 1, 1, 2, 1, 2, 2, 2, 2, 2, 1, 2, 2,
               2, 1, 2, 2, 2, 2, 1, 2, 2, 2, 1, 1, 1, 1, 0, 0, 0],
              [1, 2, 1, 2, 1, 1, 1, 1, 1, 2, 1, 2, 2, 1, 2, 2, 2, 1, 1,
               1, 1, 2, 2, 1, 2, 2, 2, 1, 2, 2, 1, 2, 1, 0, 0, 0],
              [1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 2, 2, 2, 2, 1, 1, 1, 1,
               1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 1, 0, 0],
              [1, 2, 2, 1, 2, 1, 1, 1, 1, 2, 1, 2, 2, 2, 1, 1, 1, 1, 2,
               2, 2, 2, 2, 1, 1, 1, 2, 2, 2, 2, 1, 1, 2, 1, 0, 0],
              [1, 2, 2, 1, 2, 2, 2, 2, 1, 2, 1, 3, 2, 1, 1, 2, 2, 2, 2,
               2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 1, 0, 0],
              [1, 2, 2, 1, 1, 1, 2, 2, 2, 2, 1, 1, 1, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 1, 0, 0]]

        L1CountX = 0
        for i in L1:
            L1CountY = -1
            for j in i:
                if j == 0:
                    L1CountY += 1
                    # continue
                if j == 1:
                    L1CountY += 1
                    self.initWallBoxes(L1CountX, L1CountY, 0)
                    # continue
                if j == 2:
                    L1CountY += 1
                    self.initGroundBoxes(L1CountX, L1CountY, 0)
                    # continue
                if j == 3:
                    self.countTransTag += 1
                    L1CountY += 1
                    self.initTransBoxes(L1CountX, L1CountY, 0)
                    self.transList.append(self.transNP)
                    # continue
            L1CountX += 1

        # 零摩擦第二层（4个传送）
        L2 = [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 1, 0,
                  0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 1, 0,
                  0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 1, 0,
               0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 2, 1, 1,
               1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 1, 2, 1, 1],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 2, 2, 2, 2, 2, 1, 2,
               1, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 2, 1, 2, 1, 2, 2, 1],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 2, 2, 2, 1, 2, 2, 2,
               1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 2, 3, 2, 1, 2, 3, 1],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 2, 2, 2, 1, 2, 2, 2, 2,
               1, 2, 1, 1, 1, 2, 2, 2, 2, 2, 1, 1, 2, 2, 2, 2, 2, 1],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 2, 1, 2, 1, 2, 2, 1, 2,
               2, 2, 1, 1, 1, 2, 2, 2, 2, 1, 1, 1, 1, 1, 2, 1, 2, 1],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 1, 1, 1, 1, 2, 1, 1, 2,
               2, 2, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 1, 1, 2, 2, 2, 1],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 1, 2, 2, 1, 2, 2, 1, 2,
               1, 2, 1, 2, 2, 1, 1, 1, 1, 1, 2, 2, 2, 1, 1, 2, 2, 1],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 1, 1, 2, 2, 2, 2, 1, 2,
               2, 2, 1, 2, 2, 2, 2, 2, 2, 1, 2, 2, 2, 1, 1, 1, 1, 1],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 2, 1, 2, 2, 1, 2, 1, 1,
               2, 2, 1, 2, 2, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 0],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 2, 1, 2, 1, 1, 2, 1, 1,
               2, 2, 1, 2, 2, 2, 2, 2, 1, 2, 2, 1, 2, 2, 2, 2, 1, 0],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 3, 1, 2, 2, 2, 2, 1, 1,
               1, 2, 2, 2, 1, 1, 2, 2, 2, 2, 2, 1, 1, 2, 2, 3, 1, 0],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0]]

        L2CountX = 0
        for i in L2:
            L2CountY = 0
            for j in i:
                if j == 0:
                    L2CountY += 1
                    # continue
                if j == 1:
                    L2CountY += 1
                    self.initWallBoxes(L2CountX, L2CountY, 20)
                    # continue
                if j == 2:
                    L2CountY += 1
                    self.initGroundBoxes(L2CountX, L2CountY, 20)
                    # continue
                if j == 3:
                    self.countTransTag += 1
                    L2CountY += 1
                    self.initTransBoxes(L2CountX, L2CountY, 20)
                    self.transList.append(self.transNP)
                    # continue
            L2CountX += 1

        # 零摩擦第三层（2个传送）
        L3 = [[0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 2, 2, 1, 2, 2, 2, 2, 2,
                  2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2,
                  2, 2, 2, 2, 1, 2, 2, 2, 2, 2, 2, 2, 2, 1, 2, 2, 2, 1],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 2, 2, 2, 2, 2, 1, 2, 2,
               2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 2, 2, 2, 2, 1, 1],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2,
               2, 2, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 1, 2, 2, 2, 2, 2, 2, 2,
               2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 2, 2, 2, 2, 2, 2, 0, 0],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2,
               2, 2, 2, 2, 2, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 1],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2,
               2, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 2, 0, 0],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2,
               2, 2, 2, 1, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 2, 2, 2, 2, 2, 1, 1, 1,
               1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 1],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 2, 2, 2, 2, 2, 1, 1, 1,
               1, 1, 2, 2, 2, 1, 2, 2, 2, 1, 2, 2, 2, 1, 2, 1, 2, 1],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 2, 1, 1, 1, 1, 1, 2, 2,
               2, 1, 2, 1, 2, 1, 2, 1, 2, 2, 2, 1, 2, 2, 2, 1, 2, 1],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 2, 1, 1, 1, 1, 2, 2, 1,
               2, 1, 2, 1, 2, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 0],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 2, 2, 2, 2, 1, 2, 1, 1,
               2, 1, 2, 1, 2, 2, 2, 1, 2, 1, 2, 2, 2, 2, 2, 2, 2, 1],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 2, 1, 2, 2, 2, 2, 1,
               2, 2, 2, 1, 1, 1, 1, 1, 2, 2, 2, 1, 1, 1, 2, 2, 3, 1],
              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1]]

        L3CountX = 0
        for i in L3:
            L3CountY = 0
            for j in i:
                if j == 0:
                    L3CountY += 1
                    # continue
                if j == 1:
                    L3CountY += 1
                    self.initWallBoxes(L3CountX, L3CountY, 40)
                    # continue
                if j == 2:
                    L3CountY += 1
                    self.initGroundBoxes(L3CountX, L3CountY, 40)
                    # continue
                if j == 3:
                    self.countTransTag += 1
                    L3CountY += 1
                    self.initTransBoxes(L3CountX, L3CountY, 40)
                    self.transList.append(self.transNP)
                    # continue
            L3CountX += 1

    # 初始化
    def setup(self):
        self.worldNP = render.attachNewNode('World')

        # World
        self.debugNP = self.worldNP.attachNewNode(BulletDebugNode('Debug'))
        self.debugNP.show()
        self.debugNP.node().showWireframe(True)
        self.debugNP.node().showConstraints(True)
        self.debugNP.node().showBoundingBoxes(False)
        self.debugNP.node().showNormals(True)

        self.world = BulletWorld()
        self.world.setGravity(Vec3(0, 0, -9.81))
        self.world.setDebugNode(self.debugNP.node())

        # 传送阵标识
        self.countTransTag = -1
        self.transList = []

        self.initZero()
        self.initStart()
        self.initSlabstone()
        self.initCharacter()

    # 摄像机更新函数
    def updatecam(self):
        self.cam.setPos(self.characterNP.getX(
        ) - 12, self.characterNP.getY() - 12, self.characterNP.getZ() + 12)
        self.skybox.setPos(self.cam.getPos())
        self.cam.lookAt(self.characterNP)
        # print self.cam.getPos()


game = Skybox()
game.run()
