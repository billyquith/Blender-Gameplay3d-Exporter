# Author: Mark Lawan
# Email: marklawan@outlook.com
# Date Created: Sun, 31 Jan 2016
# 
# This software can be used for commercial and personal work  
# as long as the following conditions are met:
# 
# 1. This software must not be altered or modified and then redistributed or sold
#    without my consent.
# 2. The author cannot be held liable for any damages caused by using this software.
# 3. This license clause must be left present in all files of this software.

import bpy
import os

from .scenegen import SceneGen
from .animgen import AnimGen
from .assetgen import AssetGen

# ExportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty
from bpy.types import Operator

from mathutils import Matrix, Vector

class ExportToGameplay3D(Operator, ExportHelper):
    """Export scenes to Gameplay3d files"""
    bl_idname = "export_scene.gameplay3d"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Export to Gameplay3D files"

    # ExportHelper mixin class uses this
    filename_ext = ""#.scene"

    filter_glob = StringProperty(
            default="",#*.scene",
            options={'HIDDEN'},
            )

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.
    gen_scenes = BoolProperty(
            name="Generate scene files",
            description="Generate Gameplay3D scene files",
            default=True,
            ) 
    gen_animations = BoolProperty(
            name="Generate animation files",
            description="Generate Gameplay3D animation files",
            default=True,
            ) 
    gen_assets = BoolProperty(
            name="Generate gpb and material files",
            description="Generate Gameplay3D bundle files",
            default=True,
            ) 
            
    def execute(self, context):
        if self.gen_assets:
            assetgen = AssetGen(self.filepath)
        if self.gen_scenes:
            scenegen = SceneGen(self.filepath)
        if self.gen_animations:
            animgen = AnimGen(self.filepath)
            
        overrides = self.initOverrides(context)
        space = overrides.get('space_data')
        user_settings = self.prepSetttings(space)

        # progress info
        wm = context.window_manager
        total = len(bpy.data.scenes)
        wm.progress_begin(0, total)
        for scene, progress in zip(bpy.data.scenes, range(total)):
            # update progress
            wm.progress_update(progress)
            overrides['scene'] = scene
            scene.cursor_location = Vector((0, 0, 0))

            if scene.gp3d_scenetype == 'GAME_SCENE' and self.gen_scenes:
                scenegen.export(scene)
                    
            elif scene.gp3d_scenetype == 'ASSETS':
                bases_ = list()
                objs_ = list()
                apply_objs = list()
                apply_bases = list()
                dups = list()

                # ready objects to match gameplay3d orientation
                # iterate copy to exclude  duplicates
                for obj, base in zip(list(scene.objects), list(scene.object_bases)):
                    if obj.parent is None:
                        dup = Dup()
                        copy = dup.create_copy(scene, obj)
                        objs_.append(copy)
                        if obj.type == 'MESH':
                            scene.objects.link(copy)
                            apply_objs.append(copy)
                            copy_base = super(bpy.types.Object, copy)
                            bases_.append(copy_base)
                            apply_bases.append(copy_base)
                        elif obj.type == 'ARMATURE':
                            # write animation
                            if self.gen_animations:
                                animgen.write(scene, obj)
                            bases_.append(base)
                        dups.append(dup)

                overrides['selected_objects'] = objs_
                overrides['selected_bases'] = bases_
                overrides['selected_editable_objects'] = objs_
                bpy.ops.object.location_clear(overrides) 
                bpy.ops.object.mode_set(overrides, mode='OBJECT', toggle=False)

                overrides['selected_objects'] = apply_objs
                overrides['selected_bases'] = apply_bases
                overrides['selected_editable_objects'] = apply_objs
                bpy.ops.object.transform_apply(overrides, rotation=True)

                # write assets
                if self.gen_assets:
                    assetgen.write(overrides, scene)

                # restore
                for dup in dups:
                    dup.restore(scene)

        if self.gen_assets:
            assetgen.clean_up()
        self.applyUserSettings(space, user_settings)
        wm.progress_end()
        return {'FINISHED'}

    def initOverrides(self, context):
        screen = bpy.data.screens['Default']
        overrides = dict({
            'window': context.window, 
            'screen': screen,
            'blend_data': context.blend_data})
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                overrides.setdefault('area', area)
                overrides.setdefault('space_data', area.spaces.active)
                for region in area.regions:
                    if region.type == 'WINDOW':
                        overrides.setdefault('region', region)
                        return overrides
        return None

    def prepSetttings(self, space):
        user_settings = dict()
        user_settings['trans_orient'] = space.transform_orientation
        user_settings['pivot_point'] = space.pivot_point
        space.transform_orientation = 'GLOBAL'
        space.pivot_point = 'INDIVIDUAL_ORIGINS' 
        return user_settings

    def applyUserSettings(self, space, settings):
        space.transform_orientation = settings['trans_orient']
        space.pivot_point = settings['pivot_point']

class Dup:
    trans = None
    obj = None
    copy = None

    def __init__(self):
        trans = None
        obj = None
        copy = None

    def create_copy(self, scene, obj):
        self.obj = obj
        self.trans = obj.matrix_world.copy()
        if obj.type == 'MESH':
            real_name = obj.name
            obj.name = "gp3d__{0}".format(real_name)
            mesh = bpy.data.meshes.new_from_object(scene, obj, True, 'PREVIEW')
            self.copy = bpy.data.objects.new(name = real_name, object_data=mesh)
            self.copy.matrix_world *= Matrix.Rotation(-1.5708, 4, 'X') 
            return self.copy
        elif obj.type == 'ARMATURE':
            self.obj.matrix_world *= Matrix.Rotation(-1.5708, 4, 'X') 
            return self.obj

    def restore(self, scene):
        self.obj.matrix_world = self.trans
        if self.copy is not None:
            real_name = self.copy.name
            self.copy.name = "gp3d__temp"
            self.obj.name = real_name
            scene.objects.unlink(self.copy)
            self.copy.user_clear()
            bpy.data.objects.remove(self.copy)

# Only needed if you want to add into a dynamic menu
def menu_func_export(self, context):
    self.layout.operator(ExportToGameplay3D.bl_idname, text="Export Gameplay3D")

def register():
    bpy.utils.register_class(ExportToGameplay3D)
    bpy.types.INFO_MT_file_export.append(menu_func_export)

def unregister():
    bpy.utils.unregister_class(ExportToGameplay3D)
    bpy.types.INFO_MT_file_export.remove(menu_func_export)
