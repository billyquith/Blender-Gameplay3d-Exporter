# Author: Mark Lawan
# Email: marklawan@outlook.com
# Date Created: Tue, 08 Dec 2015
# 
# This software can be used for commercial and personal work  
# as long as the following conditions are met:
# 
# 1. This software must not be altered or modified and then redistributed or sold
#    without my consent.
# 2. The author cannot be held liable for any damages caused by using this software.
# 3. This license clause must be left present in all files of this software.

from .utils import HomeTab, make_names_unique

import bpy
from bpy.props import *

class StripGroup(bpy.types.PropertyGroup):
    track = StringProperty(description = "The track where this strip belongs")

    # override equal comparison
    def __eq__(self, other):
        return (isinstance(other, self.__class__) and \
                other.name == self.name)

    # not equal
    def __ne__(self, other):
        return not self.__eq__(other)
    
    # required by __eq__
    def __hash__(self):
        return hash(self.__dict__.values())


class AnimGroup(bpy.types.PropertyGroup):
    def auto_rename(self, context):
        if self.name != self.anim_id:
            animgroups = context.scene.gp3d_animations.groups
            make_names_unique(animgroups, self, "anim_id")

    visible = BoolProperty(default = False)
    boneroot = StringProperty(description="The bone root to use in gmaeplay3d animation")
    anim_id = StringProperty(default="animations",
            description="The animation id for this group in gameplay3d.",
            update=auto_rename)
    strips = CollectionProperty(type = StripGroup)
    strip_index = IntProperty(min=-1, default=-1)


def getStrips(self, context):
    items = []
    obj = context.active_object
    anim_data = obj.animation_data
    if anim_data:
        for track in anim_data.nla_tracks:
            strips = track.strips
            for strip in strips:
                items.append((strip.name, strip.name, "Track: %s" % track.name))
    return items


class Animation(bpy.types.PropertyGroup):
    groups = CollectionProperty(type=AnimGroup)
    index = IntProperty(min=-1, default=-1)
    selected_strip = EnumProperty(items = getStrips, 
            name = "Strips",
            description="Select animation strips to add to selected animation group")


def register():
    bpy.utils.register_class(StripGroup)
    bpy.utils.register_class(AnimGroup)
    bpy.utils.register_class(Animation)
    bpy.types.Scene.gp3d_animations = PointerProperty(type = Animation)
    bpy.types.Bone.gp3d_groupname = StringProperty()


def unregister():
    bpy.utils.unregister_class(StripGroup)
    bpy.utils.unregister_class(AnimGroup)
    bpy.utils.unregister_class(Animation)
    del bpy.types.Scene.gp3d_animations
    del bpy.types.Bone.gp3d_groupname


def display(bone, group, flag):
    bone.select = flag
    for child in bone.children:
        if child.gp3d_groupname == "":
            display(child, group, flag)


def toggleDisplay(context, flag):
    animations = context.scene.gp3d_animations
    group = animations.groups[animations.index]
    bone = context.active_object.data.bones.get(group.boneroot, None)

    bpy.ops.pose.select_all(action='DESELECT')
    group.visible = flag
    display(bone, group.anim_id, flag)

    # set active
    context.active_object.data.bones.active = bone
    

# AnimGroup disowns bone
def disown(armature, animgroup):
    bone = armature.data.bones.get(animgroup.boneroot, None)
    if bone:
        bone.gp3d_groupname = ""
    animgroup.boneroot = ""


# Bone leaves AnimGroup
def orphan(scene, bone):
    animgroup = scene.gp3d_animations.groups.get(bone.gp3d_groupname, None)
    if animgroup:
        animgroup.boneroot = ""
    bone.gp3d_groupname = ""


# get current selected group
def getCurrentGroup(scene):
    animations = scene.gp3d_animations
    index = animations.index
    if index >= 0:
        return animations.groups[index]
    return None


class Add(bpy.types.Operator):
    "Add new animation group"
    bl_label = "Add Animation Group"
    bl_idname = "gp3d.add_animgroup"

    @classmethod
    def poll(self, context):
        return context.mode == 'POSE'

    def execute(self, context):
        scene = context.scene
        animations = scene.gp3d_animations
        animations.index = len(animations.groups) - 1
        newgroup = animations.groups.add()
        animations.index += 1
        newgroup.anim_id = newgroup.anim_id # trigger the update func (auto_rename)

        if len(context.selected_pose_bones) > 0 and\
                context.active_pose_bone.bone.gp3d_groupname == "" and\
                bpy.ops.gp3d.set_animgroup.poll():
            bpy.ops.gp3d.set_animgroup()
        return {'FINISHED'}


class Remove(bpy.types.Operator):
    "Remove selected animation group"
    bl_label = "Remove Animation Group"
    bl_idname = "gp3d.remove_animgroup"

    @classmethod
    def poll(self, context):
        return context.mode == 'POSE' and context.scene.gp3d_animations.index >= 0 

    def execute(self, context):
        scene = context.scene

        # unset before removing
        if bpy.ops.gp3d.unset_animgroup.poll():
            bpy.ops.gp3d.unset_animgroup()

        animations = scene.gp3d_animations
        animations.groups.remove(animations.index)
        animations.index -= 1
        if animations.index < 0 and len(animations.groups) > 0:
            animations.index = 0
        return {'FINISHED'}


class ToggleDisplay(bpy.types.Operator):
    "Toggle displaying of bone members for this animation group"
    bl_label = "Show/Hide Members of Animation Group"
    bl_idname = "gp3d.display_animgroup"

    mode = BoolProperty()

    @classmethod
    def poll(self, context):
        group = getCurrentGroup(context.scene)
        if group and context.mode == 'POSE':
            return group.boneroot != ""
        return False

    def execute(self, context):
        toggleDisplay(context, self.mode)
        return {'FINISHED'}


class Set(bpy.types.Operator):
    "Set selected bone as root for this animation group"
    bl_label = "Set Bone as Root to Animation Group"
    bl_idname = "gp3d.set_animgroup"

    @classmethod
    def poll(self, context):
        return context.mode == 'POSE' and context.active_pose_bone is not None and\
            context.scene.gp3d_animations.index >= 0 

    def execute(self, context):
        scene = context.scene
        bone = context.active_pose_bone.bone
        animgroup = getCurrentGroup(scene)

        orphan(scene, bone)
        disown(context.active_object, animgroup)

        animgroup.boneroot = bone.name
        bone.gp3d_groupname = animgroup.name
        toggleDisplay(context, True)
        return {'FINISHED'}


class Unset(bpy.types.Operator):
    "Unset this animation group"
    bl_label = "Unset Animation Group"
    bl_idname = "gp3d.unset_animgroup"

    @classmethod
    def poll(self, context):
        group = getCurrentGroup(context.scene)
        if group:
            return group.boneroot != ""
        return False

    def execute(self, context):
        scene = context.scene
        bone = context.active_pose_bone.bone
        animgroup = getCurrentGroup(scene)

        toggleDisplay(context, False)

        orphan(scene, bone)
        disown(context.active_object, animgroup)
        return {'FINISHED'}


class MoveAnimGroup(bpy.types.Operator):
    "Move group one step upwards/downwards in animation groups list"
    bl_label = "Move AnimGroup"
    bl_idname = "gp3d.move_animgroup"

    direction = EnumProperty(items = [('UP', 'Up', ''), ('DOWN', 'Down', '')])

    @classmethod
    def poll(self, context):
        return len(context.scene.gp3d_animations.groups) > 1

    def execute(self, context):
        scene = context.scene
        animations = scene.gp3d_animations

        index = animations.index
        groups = animations.groups
        if self.direction == 'UP' and index > 0:
            groups.move(index, index - 1)
            animations.index -= 1
        elif self.direction == 'DOWN' and index < len(groups) - 1:
            groups.move(index, index + 1)
            animations.index += 1
        return {'FINISHED'}

# Strips
class StripAdd(bpy.types.Operator):
    "Add strip to selected animation group. The group must have a bone root set."
    bl_label = "Add Strip to Animation Group"
    bl_idname = "gp3d.add_strip"

    @classmethod
    def poll(self, context):
        scene = context.scene
        group = getCurrentGroup(scene)
        return scene.gp3d_animations.selected_strip is not None and \
                group.boneroot != ""

    def execute(self, context):
        scene = context.scene
        obj = context.active_object
        tracks = obj.animation_data.nla_tracks
        group = getCurrentGroup(scene)

        for track in tracks:
            strip = track.strips.get(scene.gp3d_animations.selected_strip, None)
            if strip:
                if group.strips.get(strip.name, None):
                    self.report({'INFO'}, "This strip is already on the list")
                    return {'CANCELLED'}
                else:
                    addedstrip = group.strips.add()
                    addedstrip.track = track.name
                    addedstrip.name = strip.name
                    group.strip_index += 1
                    break
        return {'FINISHED'}
    
class StripRemove(bpy.types.Operator):
    "Remove strip from selected animation group"
    bl_label = "Remoe Strip from Animation Group"
    bl_idname = "gp3d.remove_strip"

    @classmethod
    def poll(self, context):
        group = getCurrentGroup(context.scene)
        return group.strip_index >= 0

    def execute(self, context):
        group = getCurrentGroup(context.scene)
        group.strips.remove(group.strip_index)
        group.strip_index -= 1
        if group.strip_index < 0 and len(group.strips) > 0:
            group.strip_index = 0
        return {'FINISHED'}

class StripMoveStrip(bpy.types.Operator):
    "Move strip one step upwards/downwards in strips list"
    bl_label = "Move Strip"
    bl_idname = "gp3d.move_strip"

    direction = EnumProperty(items = [('UP', 'Up', ''), ('DOWN', 'Down', '')])

    @classmethod
    def poll(self, context):
        group = getCurrentGroup(context.scene)
        return len(group.strips) > 1

    def execute(self, context):
        scene = context.scene
        group = getCurrentGroup(scene)

        index = group.strip_index
        if self.direction == 'UP' and index > 0:
            group.strips.move(index, index - 1)
            group.strip_index -= 1
        elif self.direction == 'DOWN' and index < len(group.strips) - 1:
            group.strips.move(index, index + 1)
            group.strip_index += 1
        return {'FINISHED'}


class AnimGroupList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, 
            active_propname, index):
        col = layout.column(align=True)
        col.prop(item, "anim_id", text="", emboss=False)

        # show icon to warn if group is not yet set 
        col = layout.column(align=True)
        if item.boneroot == "":
            col.label(text="", icon='ERROR')


class AnimGroupPanel(HomeTab, bpy.types.Panel):
    bl_idname = "VIEW3D_PT_gp3d_animation_groups"
    bl_label = "Animation Groups"
    
    @classmethod
    def poll(cls, context):
        obj = context.active_object 
        if obj:
            return context.scene.gp3d_scenetype == 'ASSETS' and obj.type == 'ARMATURE'
        return False

    def draw(self, context):
        animgroup = getCurrentGroup(context.scene)
        animations = context.scene.gp3d_animations

        layout = self.layout
        row = layout.row()
        col = row.column(align=True)
        col.template_list("AnimGroupList", "", animations, "groups", animations,
                "index", rows=5)

        col = row.column(align=True)
        col.operator("gp3d.add_animgroup", text="", icon="ZOOMIN")
        col.operator("gp3d.remove_animgroup", text="", icon="ZOOMOUT")
        col.separator()
        col.operator("gp3d.move_animgroup", text="", icon="TRIA_UP").direction = 'UP'
        col.operator("gp3d.move_animgroup", text="", icon="TRIA_DOWN").direction = 'DOWN'
        col.separator()
        if animgroup:
            col.operator("gp3d.display_animgroup", text="", 
                    icon='VISIBLE_IPO_ON').mode = not animgroup.visible 

        layout.separator()
        row = layout.row(align=True)
        row.operator("gp3d.set_animgroup", text="Set")
        row.operator("gp3d.unset_animgroup", text="Unset")
        layout.separator()

        # Strips
        if animgroup:
            layout.prop(animations, "selected_strip")
            row = layout.row()
            col = row.column(align=True)
            col.template_list("SimpleList", "", animgroup, "strips", animgroup,
                    "strip_index", rows=5)

            col = row.column(align=True)
            col.operator("gp3d.add_strip", text="", icon="ZOOMIN")
            col.operator("gp3d.remove_strip", text="", icon="ZOOMOUT")
            col.separator()
            col.operator("gp3d.move_strip", text="", icon="TRIA_UP").direction = 'UP'
            col.operator("gp3d.move_strip", text="", icon="TRIA_DOWN").direction = 'DOWN'
            layout.separator()
