# Author: Mark Lawan
# Email: marklawan@outlook.com
# Date Created: Fri, 12 Feb 2016
# 
# This software can be used for commercial and personal work  
# as long as the following conditions are met:
# 
# 1. This software must not be altered or modified and then redistributed or sold
#    without my consent.
# 2. The author cannot be held liable for any damages caused by using this software.
# 3. This license clause must be left present in all files of this software.

import os
import bpy
from mathutils import Vector
from math import radians, degrees
from .utils import cross_mkdir

class AssetGen:
    filepath = None
    temp = None
    matpath = None

    def __init__(self, filepath):
        self.filepath = cross_mkdir(filepath + "/gpb/")
        self.temp = cross_mkdir(filepath + "/temp/")
        self.matpath = cross_mkdir(filepath + "/materials/")

    def clean_up(self):
        flag = "rm -rf"
        if os.name != 'posix':
            flag = "rd /s /q"
        os.system("{0} {1}".format(flag, self.temp))

    def write(self, overrides, scene):
        try:
            bpy.ops.export_scene.fbx(overrides, filepath=self.temp,
                    axis_forward='Y',
                    axis_up='Z',
                    apply_unit_scale=False,
                    use_mesh_modifiers=True,
                    add_leaf_bones=False,
                    use_armature_deform_only=True,
                    bake_anim=True,
                    bake_anim_use_all_bones=True,
                    bake_anim_use_nla_strips=False,
                    bake_anim_use_all_actions=False,
                    batch_mode='SCENE',
                    use_batch_own_dir=False)
        except:
            self.report({'ERROR'}, "FBX exporter version it not compatible. Aborting exporting of assets.")
            return


        fbxfile = "{0}{1}.fbx".format(self.temp, scene.name)
        gpbfile = "{0}{1}".format(self.filepath, scene.name)

        flag_animations = ""
        if len(scene.gp3d_animations.groups) > 0:
            for group in scene.gp3d_animations.groups:
                flag_animations += "-g {0} {1} ".format(group.boneroot, group.anim_id)
        else:
            flag_animations += "-g:auto"
        cmd = "gameplay-encoder -v 0 -m {0} {1} {2}".format(flag_animations, 
                fbxfile, gpbfile)
        os.system(cmd)

        # move material files
        flag = "mv"
        if os.name != "posix":
            flag = "move /Y"
        cmd = "{0} {1}*.material {2}".format(flag, self.filepath, self.matpath)
        os.system(cmd)
