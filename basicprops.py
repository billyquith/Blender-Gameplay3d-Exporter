# Author: Mark Lawan
# Email: marklawan@outlook.com
# Date Created: Tue, 02 Feb 2016
# 
# This software can be used for commercial and personal work  
# as long as the following conditions are met:
# 
# 1. This software must not be altered or modified and then redistributed or sold
#    without my consent.
# 2. The author cannot be held liable for any damages caused by using this software.
# 3. This license clause must be left present in all files of this software.

import bpy
from bpy.props import *

def register():
    bpy.types.Object.gp3d_tags = StringProperty()
    items = (
            ('GAME_SCENE', 'Game Scene', "This scene is equivalent to \
                    a game scene in Gameplay3D or .scene file"),
            ('ASSETS', 'Assets', "This scene is for assets which will \
                    be exported to Gameplay3D bundle file"),
            ('ASSET_GROUP', 'Asset Group', "This is for constructing asset heirarchies"),
            ('NONE', 'None', "This scene will not be processed by gameplay3d exporter"),
        )
    bpy.types.Scene.gp3d_scenetype = EnumProperty(items = items, 
        description = "Whether this blender scene is for assets or a game scene")

def unregister():
    del bpy.types.Object.gp3d_tags
    del bpy.types.Scene.gp3d_scenetype

class GamePlayObjPanel(bpy.types.Panel):
    bl_idname = "OBJECT_PT_gp3d_basicprops"
    bl_label = "GamePlay3D"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"  # put panel under object properties

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and (obj.type == 'MESH' or obj.type == 'CAMERA' or\
                obj.type == 'LAMP')

    def draw(self, context):
        obj = context.active_object
        self.layout.prop(obj, "gp3d_tags", text = "Tags")

class GamePlayScenePanel(bpy.types.Panel):
    bl_idname = "SCENE_PT_gp3d_sceneprops"
    bl_label = "GamePlay3D"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"    # put panel under scene properties

    def draw(self, context):
        self.layout.prop(context.scene, "gp3d_scenetype", text = "Type", expand=True)
