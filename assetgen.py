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
import subprocess
import shutil
import glob
from mathutils import Vector
from math import radians, degrees
from .utils import cross_mkdir

class AssetGen:
    filepath = None
    temp = None
    matpath = None

    def __init__(self, filepath):
        self.filepath = cross_mkdir(os.path.join(filepath, 'gpb'))
        self.temp = cross_mkdir(os.path.join(filepath, 'temp'))
        self.matpath = cross_mkdir(os.path.join(filepath, 'materials'))

    def clean_up(self):
        shutil.rmtree(self.temp)

    def write(self, overrides, scene):
        try:
            bpy.ops.export_scene.fbx(overrides, filepath = self.temp + '/',
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
            self.report({'ERROR'},
                "FBX exporter version it not compatible. Aborting exporting of assets.")
            return

        fbxfile = os.path.join(self.temp, scene.name + '.fbx')
        gpbfile = os.path.join(self.filepath, scene.name)

        # command to run encoder
        cmd = [ 'gameplay-encoder', '-v', '0', '-m' ]
        
        if len(scene.gp3d_animations.groups) > 0:
            for group in scene.gp3d_animations.groups:
                cmd += [ "-g", group.boneroot, group.anim_id ]
        else:
            cmd.append("-g:auto")

        cmd += [ fbxfile, gpbfile ]
            
        try:
            ret = subprocess.run(cmd, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)        
            ret.check_returncode()
            print(ret.stdout)
        except FileNotFoundError as err:
            print('Error: ', err)
            print(ret.stdout)
            print('Is the Gameplay encoder in your path?')
        except subprocess.CalledProcessError as err:
            print('There was a problem running the Gameplay encoder.')
            print(err)
        else:
            # move material files            
            for f in glob.glob(os.path.join(self.filepath, "*.material")):
                targmat = os.path.join(self.matpath, os.path.basename(f))
                if os.path.exists(targmat):
                    os.remove(targmat)
                shutil.move(f, self.matpath)
                
