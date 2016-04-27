# Author: Mark Lawan
# Email: marklawan@outlook.com
# Date Created: Sun, 07 Feb 2016
# 
# This software can be used for commercial and personal work  
# as long as the following conditions are met:
# 
# 1. This software must not be altered or modified and then redistributed or sold
#    without my consent.
# 2. The author cannot be held liable for any damages caused by using this software.
# 3. This license clause must be left present in all files of this software.

from .utils import *
import os
import bpy 
from mathutils import *
from math import *

class SceneGen:
    filepath = None
    str_scene = None
    lights = None
    cameras = None

    def __init__(self, filepath):
        self.filepath = cross_mkdir(os.path.join(filepath, "scenes"))

    def export(self, scene):
        self.str_scene = "scene {0} {{\n".format(scene.name)
        if scene.world:
            ambient = scene.world.ambient_color
            self.str_scene += "\tambientColor = {0}, {1}, {2}\n"\
                    .format(deci(ambient.r), deci(ambient.g), deci(ambient.b))
        if scene.camera:
            self.str_scene += "\tactiveCamera = {0}\n".format(scene.camera.name)

        self.lights = {} # {light.name: str_light}
        self.cameras = {} # {camera.name: str_camera}

        for obj in scene.objects:
            if obj.parent is None:
                temp = self.to_prop(scene, 1, obj) 
                if temp is not None:
                    self.str_scene += temp

        self.str_scene += "}\n"
        scenefile = os.path.join(self.filepath, scene.name + ".scene")
        self.write(self.str_scene, scenefile)

    def to_prop(self, scene, tab_num, node):
        tabs_lvl1 = tabs(tab_num)
        tabs_lvl2 = tabs(tab_num + 1)
        tabs_lvl3 = tabs(tab_num + 2)

        suffix = get_suffix(node.name)
        name = no_suffix(node.name) if suffix and suffix.group(0) == ".001"\
                else node.name
        str_node = "{1}node {0}{{\n".format(name, tabs_lvl1)
        if node.type == 'MESH':
            # url
            source = bpy.context.window_manager.gp3d_assets.asset_list[node.data.name]
            str_node += "{2}url = res/gpb/{0}.gpb#{1}\n"\
                    .format(source.scene, source.objname, tabs_lvl2)

            # material - use the first in list
            mat = node.material_slots[0]
            if mat is not None:
                str_node += "{2}material = res/materials/{0}.material#{1}\n"\
                        .format(source.scene, mat.name.replace('.', '_'), tabs_lvl2)

        # light
        if node.type == 'LAMP':
            data = node.data
            if data.name not in self.lights:
                str_light = "light {0} {{\n".format(data.name)
                _type = data.type
                if _type == 'SUN':
                    _type = 'DIRECTIONAL'
                str_light += "\ttype = {0}\n".format(_type)
                color = data.color
                str_light += "\tcolor = {0}, {1}, {2}\n".format(deci(color.r), 
                        deci(color.g), deci(color.b))

                if data.type == 'SPOT' or data.type == 'POINT':
                    str_light += "\trange = {0}\n".format(data.distance)
                    if data.type == 'SPOT':
                        str_light += "\tinnerAngle = 1.0\n"
                        str_light += "\touterAngle = {0}\n".format(deci(data.spot_size))
                str_light += "}\n"
                self.lights[data.name] = str_light
            str_node += "{2}light = res/scenes/{0}.scene#{1}\n"\
                    .format(scene.name, data.name, tabs_lvl2)

        # camera
        if node.type == 'CAMERA':
            data = node.data
            if data.name not in self.cameras:
                str_camera = "camera {0} {{\n".format(data.name)
                if data.type == 'PERSP':
                    str_camera += "\ttype = PERSPECTIVE\n"
                    render = scene.render
                    aspect_ratio = (render.resolution_x * render.pixel_aspect_x) \
                            / (render.resolution_y * render.pixel_aspect_y)
                    data.lens_unit = 'FOV'
                    str_camera += "\tfieldOfView = {0}\n"\
                            .format(deci(degrees(atan(tan(data.angle / 2) \
                                / aspect_ratio) * 2)))
                elif data.type == 'ORTHO':
                    str_camera += "\ttype = ORTHOGRAPHIC\n"
                    str_camera += "\tzoomX = {0}\n".format(deci(data.ortho_scale))
                    str_camera += "\tzoomY = {0}\n"\
                            .format(deci(scene.render.resolution_y * 
                                    data.ortho_scale / scene.render.resolution_x))

                str_camera += "\tnearPlane = {0}\n".format(deci(data.clip_start))
                str_camera += "\tfarPlane = {0}\n".format(deci(data.clip_end))
                str_camera += "}\n"
                self.cameras[data.name] = str_camera

            str_node += "{2}camera = res/scenes/{0}.scene#{1}\n"\
                    .format(scene.name, data.name, tabs_lvl2)

        # transformation
        if armature_parent_or_none(node):
            # rotate to match gameplay3d's orientation
            if node.type == 'CAMERA' or node.type == 'LAMP':
                trans = node.matrix_world.copy() * Matrix.Rotation(radians(-90), 4, 'X')
            else:
                trans = node.matrix_world
            dec = trans.decompose()
        else:
            dec = node.matrix_local.decompose()
            
        # locate
        loc = dec[0]
        str_node += "{3}translate = {0}, {1}, {2}\n"\
                .format(deci(loc.x), deci(loc.z), deci(loc.y * -1), tabs_lvl2)

        # rotate
        pair = dec[1].to_axis_angle()
        axis = pair[0]
        angle = degrees(pair[1])
        str_node += "{4}rotate = {0}, {1}, {2}, {3}\n"\
                .format(deci(axis.x), deci(axis.z), deci(axis.y * -1) , deci(angle),
                        tabs_lvl2)
        # scale
        scale = dec[2]
        str_node += "{3}scale = {0}, {1}, {2}\n".format(deci(scale.x), 
                deci(scale.z), deci(scale.y), tabs_lvl2)

        # enable
        if not node.hide:
            temp = "{1}enabled = {0}\n".format(not node.hide, tabs_lvl2)
            str_node += temp.lower()

        # tags
        if len(node.gp3d_tags) > 0:
            tags = node.gp3d_tags.split()
            str_tags = "{0}tags {{\n".format(tabs_lvl2)
            for tag in tags:
                str_tags += "{1}{0}\n".format(tag, tabs_lvl3)
            str_tags += "{0}}}\n".format(tabs_lvl2)
            str_node += str_tags

        for child in node.children:
            str_node += self.to_prop(scene, tab_num + 1, child)
        str_node += "{0}}}\n".format(tabs_lvl1)
        return str_node

    # write files
    def write(self, data, scenefile):
        for light in self.lights.values():
            data += light
        for camera in self.cameras.values():
            data += camera

        f = open(scenefile, 'w', encoding = 'utf-8')
        f.write(data)
        f.close()
