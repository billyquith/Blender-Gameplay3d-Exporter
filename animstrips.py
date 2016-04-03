import bpy
from bpy.props import *

class ClipData(bpy.types.PropertyGroup):
    indefinite = BoolProperty(default = False, 
            description = "Set repeatCount to INDEFINITE")
    repeatCount = FloatProperty(default = 1.0, min = 0.1, 
        description = "Repeat count of this clip to loop in Gameplay3D")
    speed = FloatProperty(default = 1.0, min = 1.0, 
            description = "Speed of clip in Gameplay3D")
    loopBlendTime = FloatProperty(default = 0.0, 
            description = "Loop blend time of a clip in Gameplay3D")

def register():
    bpy.utils.register_class(ClipData)
    bpy.types.Action.gp3d_clipdata = PointerProperty(type = ClipData)

def unregister():
    bpy.utils.unregister_class(ClipData)
    del bpy.types.Action.gp3d_clipdata

def get_active_strip(context):
    obj = context.active_object
    if obj:
        anim_data = context.active_object.animation_data
        if anim_data:
            for track in anim_data.nla_tracks:
                for strip in track.strips:
                    if strip.active:
                        return strip.action
    return None

class AnimStripsPanel(bpy.types.Panel):
    bl_idname = "UI_PT_gp3d_animstrips"
    bl_label = "Gameplay3D"
    bl_space_type = 'NLA_EDITOR'
    bl_region_type = 'UI'

    active_strip = None

    @classmethod
    def poll(self, context):
        self.active_strip = get_active_strip(context)
        return self.active_strip is not None

    def draw(self, context):
        layout = self.layout
        if self.active_strip:
            clipdata = self.active_strip.gp3d_clipdata
            layout.prop(clipdata, "indefinite", text = "INDEFINITE")
            if not clipdata.indefinite:
                layout.prop(clipdata, "repeatCount", text = "Repeat Count")
            layout.prop(clipdata, "speed", text = "Speed")
            layout.prop(clipdata, "loopBlendTime", text = "Loop Blend Time")
