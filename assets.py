# Author: Mark Lawan
# Email: marklawan@outlook.com
# Date Created: Wed, 10 Feb 2016
# 
# This software can be used for commercial and personal work  
# as long as the following conditions are met:
# 
# 1. This software must not be altered or modified and then redistributed or sold
#    without my consent.
# 2. The author cannot be held liable for any damages caused by using this software.
# 3. This license clause must be left present in all files of this software.

import bpy
from mathutils import *
from bpy.props import *
from bpy.app.handlers import persistent
from .utils import HomeTab, armature_parent_or_none


# name is obj.data.name
class AssetDetail(bpy.types.PropertyGroup):
    objname = StringProperty()
    scene = StringProperty() # where this asset belongs

class Asset(bpy.types.PropertyGroup):
    asset_list = CollectionProperty(type = AssetDetail)
    index = IntProperty(default = -1, min = -1)
    group_list = CollectionProperty(type = AssetDetail)
    group_index = IntProperty(default = -1, min = -1)

# don't call this on load_post handler
# gp3d_assets causes memleak on closing a re-opened saved file
def populate_asset_and_group_list():
    assets = bpy.context.window_manager.gp3d_assets
    assets.asset_list.clear()
    assets.group_list.clear()
    for scene in bpy.data.scenes:
        type_ = scene.gp3d_scenetype
        if type_ == 'ASSETS' or type_ == 'ASSET_GROUP':
            for obj in scene.objects:
                if obj.type == 'MESH':
                    added = None
                    if type_ == 'ASSETS' and armature_parent_or_none(obj):
                        added = assets.asset_list.add()
                        added.name = obj.data.name
                    elif type_ == 'ASSET_GROUP' and obj.parent == None:
                        added = assets.group_list.add()
                        added.name = "{0}".format(obj.as_pointer())
                    if added:
                        added.scene = scene.name
                        added.objname = obj.name

    if len(assets.asset_list) > 0:
        assets.index = 0
    if len(assets.group_list) > 0:
        assets.group_index = 0

@persistent
def assign_refs(x):
    for scene in bpy.data.scenes:
        if scene.gp3d_scenetype == 'GAME_SCENE' or scene.gp3d_scenetype == 'ASSET_GROUP':
            for obj in scene.objects:
                src_name = obj.get('gp3d_name', None)
                if src_name:
                    src = bpy.data.objects.get(src_name, None)
                    if src:
                        obj['gp3d_id'] = "{0}".format(src.as_pointer())

# WORKAROUND because WindowManager custom properties will NOT be saved
@persistent
def on_save(x):
    assets = bpy.context.window_manager.gp3d_assets
    populate_asset_and_group_list()
    for scene in bpy.data.scenes:
        if scene.gp3d_scenetype == 'GAME_SCENE' or scene.gp3d_scenetype == 'ASSET_GROUP':
            for obj in scene.objects:
                src_id = obj.get('gp3d_id', None)
                if src_id:
                    asset = assets.group_list.get(src_id, None)
                    if asset:
                        obj['gp3d_name'] = asset.objname

def register():
    bpy.utils.register_class(AssetDetail)
    bpy.utils.register_class(Asset)
    bpy.types.WindowManager.gp3d_assets = PointerProperty(type = Asset)
    bpy.app.handlers.load_post.append(assign_refs)
    bpy.app.handlers.save_pre.append(on_save)

def unregister():
    bpy.utils.unregister_class(AssetDetail)
    bpy.utils.unregister_class(Asset)
    del bpy.types.WindowManager.gp3d_assets
    bpy.app.handlers.load_post.remove(assign_refs)
    bpy.app.handlers.save_pre.remove(on_save)

def base_poll(context):
    return context.mode == 'OBJECT' and (context.scene.gp3d_scenetype == 'GAME_SCENE'\
            or context.scene.gp3d_scenetype == 'ASSET_GROUP')

class Refresh(bpy.types.Operator):
    "Refresh assets list"
    bl_label = "Refresh"
    bl_idname = "gp3d.assets_refresh"

    @classmethod
    def poll(self, context):
        return base_poll(context)

    def execute(self, context):
        populate_asset_and_group_list()
        return {'FINISHED'}


def show(obj):
    obj.select = True
    for child in obj.children:
        show(child)

def show_instances(context, asset, is_group = False):
    bpy.ops.object.select_all(action='DESELECT')

    for obj in context.scene.objects:
        if is_group:
            if asset.name == obj.get("gp3d_id", None):
                show(obj)
        elif obj.data.name == asset.name:
            obj.select = True
    return {'FINISHED'}

class ShowInstances(bpy.types.Operator):
    "Show instances of selected asset"
    bl_label = "Show Instances"
    bl_idname = "gp3d.assets_toggle"

    @classmethod
    def poll(self, context):
        return base_poll(context) and context.window_manager.gp3d_assets.index >= 0

    def execute(self, context):
        assets = context.window_manager.gp3d_assets
        asset = assets.asset_list[assets.index]
        return show_instances(context, asset, False)

class ShowAssetGroupInstances(bpy.types.Operator):
    "Show group instances of selected asset group"
    bl_label = "Show Asset Group Instances"
    bl_idname = "gp3d.asset_group_select"

    @classmethod
    def poll(self, context):
        return base_poll(context) and context.window_manager.gp3d_assets.group_index >= 0

    def execute(self, context):
        wm = context.window_manager
        assets = context.window_manager.gp3d_assets
        asset = assets.group_list[assets.group_index]
        return show_instances(context, asset, True)


def link_instance(context, source, is_group = False):
    # duplicate source
    bpy.ops.object.add_named(linked = True, name = source.name)
    instance = context.active_object

    instance.parent = None
    for mod in instance.modifiers:
        if mod.type == 'ARMATURE':
            mod.show_viewport = False
            mod.show_render = False

    for slot in instance.material_slots:
        slot.link = 'OBJECT'
    if len(source.material_slots) > 0:
        instance.material_slots[0].material = source.material_slots[0].material
        instance.active_material_index = 0

    if is_group:
        # create children
        for child in source.children:
            child_instance = link_instance(context, child, is_group)
            child_instance.location = Vector((0, 0, 0))
            child_instance.parent = instance
            child_instance.location = child.location
    return instance

def add_instance(context, asset, is_group = False):
    bpy.ops.object.select_all(action='DESELECT')
    
    source = None
    try:
        source = bpy.data.objects[asset.objname]
    except:
        return ({'ERROR'}, "Object ({0}) from scene ({1}) is not found. \
Try refreshing the list and make sure the asset doest exist. \
in the scene".format(asset.name, asset.scene))

    instance = link_instance(context, source, is_group)
    instance.location = context.scene.cursor_location
    if is_group:
        instance['gp3d_id'] = asset.name
    return None

class AddInstance(bpy.types.Operator):
    "Create an instance of the selected asset to cursor position"
    bl_label = "Create instance"
    bl_idname = "gp3d.assets_add"

    @classmethod
    def poll(self, context):
        return base_poll(context) and context.window_manager.gp3d_assets.index >= 0

    def execute(self, context):
        assets = context.window_manager.gp3d_assets
        asset = assets.asset_list[assets.index]
        ret = add_instance(context, asset)
        if ret is not None:
            self.report(ret[0], ret[1])
            return {'CANCELLED'}
        return {'FINISHED'}

class AddAssetGrouPInstance(bpy.types.Operator):
    "Create a group instance of the selected asset group to cursor position"
    bl_label = "Create group instance"
    bl_idname = "gp3d.asset_group_add"

    @classmethod
    def poll(self, context):
        return base_poll(context) and context.window_manager.gp3d_assets.group_index >= 0

    def execute(self, context):
        assets = context.window_manager.gp3d_assets
        asset = assets.group_list[assets.group_index]
        ret = add_instance(context, asset, True)
        if ret is not None:
            self.report(ret[0], ret[1])
            return {'CANCELLED'}
        return {'FINISHED'}


class AssetList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, 
            active_propname, index):
        layout.label(text=item.objname)
class AssetGroupList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, 
            active_propname, index):
        layout.label(text=item.objname)

class AssetsPanel(HomeTab, bpy.types.Panel):
    bl_idname = "VIEW3D_PT_gp3d_assetss_panel"
    bl_label = "Assets"

    @classmethod
    def poll(cls, context):
        return base_poll(context)

    def draw(self, context):
        assets = context.window_manager.gp3d_assets
        layout = self.layout
        layout.operator("gp3d.assets_refresh", icon='FILE_REFRESH', text= "Refresh Lists")
        layout.template_list("AssetList", "", assets, "asset_list",
                assets, "index", rows = 5)
        layout.operator("gp3d.assets_add", icon='ZOOMIN', text="New Instance")
        layout.operator("gp3d.assets_toggle", icon='VISIBLE_IPO_ON', text="Show intances")

        layout.separator()
        layout.label(text = "Asset Groups:")
        layout.template_list("AssetGroupList", "", assets, "group_list",
                assets, "group_index", rows = 5)
        layout.operator("gp3d.asset_group_add", icon='ZOOMIN', text="New Group Instance")
        layout.operator("gp3d.asset_group_select", icon='VISIBLE_IPO_ON', 
                text="Show Group Instances")
