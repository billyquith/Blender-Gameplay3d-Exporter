# Author: Mark Lawan
# Email: marklawan@outlook.com
# Date Created: Mon, 08 Feb 2016
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
from .utils import deci, cross_mkdir
from collections import Counter

class AnimGen:
    filepath = None

    def __init__(self, filepath):
        self.filepath = cross_mkdir(filepath + "/animations/")

    def write(self, scene, node):
        if node.type == 'ARMATURE' and len(scene.gp3d_animations.groups) > 0:
            temp_props = list()
            ctr_items = list()
            ctr_lists = list()
            for grp in scene.gp3d_animations.groups:
                temp = Aggregator.AnimProp()
                temp.name = grp.name
                temp_props.append(temp)
                ctr_items += list(grp.strips)
                ctr_lists.append(list(grp.strips))
                
            ctr = Counter(ctr_items)
            common = ctr.most_common()
            common_strips = [s[0] for s in common]
            for lst, temp in zip(ctr_lists, temp_props):
                temp.strips = [s for s in common_strips if s in lst]
                
            animfile = "{0}{1}.animation".format(self.filepath, scene.name)
            agg = Aggregator()
            agg.process(temp_props)
            agg.write(scene.frame_end, node.animation_data.nla_tracks, animfile)


class Aggregator:
    class AnimProp:
        name = None
        strips = None
        parent = None

        def __init__(self):
            self.name = None
            self.strips = list()
            self.parent = None

        def copy(self):
            new = Aggregator.AnimProp()
            new.name = self.name
            new.strips = self.strips.copy()
            new.parent = self.parent
            return new

    finalprops = None

    def __init__(self):
        self.finalprops = list()

    def process(self, temp_props):
        base = Aggregator.AnimProp()
        index = 0
        while True:
            strip = None
            diff = False

            for prop in list(temp_props): #iterate copy to freely remove while iterating
                if index >= len(prop.strips):
                    copy = base.copy()
                    copy.name = prop.name
                    self.finalprops.append(copy)
                    base.strips.clear()
                    base.parent = prop.name
                    temp_props.remove(prop)
                elif strip is None:
                    strip = prop.strips[index]
                elif strip.name != prop.strips[index].name:
                    copy = base.copy()
                    copy.name = prop.name
                    copy.strips += prop.strips[index:]
                    self.finalprops.append(copy)
                    temp_props.remove(prop)

            if len(temp_props) == 0:
                break
            if diff is False and strip is not None:
                base.strips.append(strip)
            index += 1

    def write(self, frm_count, tracks, animfile):
        str_result = ""
        for prop in self.finalprops:
            if prop.parent:
                str_anim = "animation {0} : {1}{{\n".format(prop.name, prop.parent)
            else:
                str_anim = "animation {0} {{\n".format(prop.name)
            if prop.parent is None:
                str_anim += "\tframeCount = {0}\n".format(frm_count)
            str_anim += self.write_props(prop, tracks)
            str_anim += "}\n"
            str_result += str_anim
        # write 
        f = open(animfile, 'w', encoding = 'utf-8')
        f.write(str_result)
        f.close()

    def write_props(self, prop, tracks):
        str_clip = ""
        for strip in prop.strips:
            real_strip = tracks[strip.track].strips[strip.name]
            clipdata = real_strip.action.gp3d_clipdata
            str_clip += "\tclip {0} {{\n".format(strip.name)
            str_clip += "\t\tbegin = {0}\n".format(real_strip.frame_start)
            str_clip += "\t\tend = {0}\n".format(real_strip.frame_end)

            rpt = "INDEFINITE" if clipdata.indefinite else deci(clipdata.repeatCount)
            str_clip += "\t\trepeatCount = {0}\n".format(rpt)
            str_clip += "\t\tspeed = {0}\n".format(deci(clipdata.speed))
            str_clip += "\t\tloopBlendTime = {0}\n"\
                    .format(deci(clipdata.loopBlendTime))
            str_clip += "\t}\n"
        return str_clip
