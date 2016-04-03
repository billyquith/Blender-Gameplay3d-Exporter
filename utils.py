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

import bpy
import re
import os

class HomeTab:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = 'Gameplay3D'

# return .00n
def get_suffix(_name):
    _suffix = re.search(r'\.(\d{3})$', _name)
    return _suffix

# return without .00n
def no_suffix(_name):
    return _name[:-4] if get_suffix(_name) else _name

def make_names_unique(collection, item, attribute):
    attrib = getattr(item, attribute) # attribute to make unique

    item.name = "" # empty name to exclude from searching itself
    count = 1
    name = attrib
    basename = no_suffix(name)
    while collection.get(name):
        name = "%s.%03d" % (basename, count)
        count += 1

    item.name = name # set the new unique name
    setattr(item, attribute, name)

def tabs(num):
    return ''.join("\t" for i in range(num))

def deci(n):
    return format(n, '.2f')

def armature_parent_or_none(obj):
    return obj.parent is None or obj.parent.type == 'ARMATURE'

def cross_mkdir(filepath):
    if os.name == 'posix':
        os.system("mkdir -p {0}".format(filepath))
    else:
        filepath = filepath.replace('/','\\')
        os.system("if not exist {0} mkdir {0}".format(filepath))
    return filepath

class SimpleList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, 
            active_propname, index):
        layout.label(text=item.name)
