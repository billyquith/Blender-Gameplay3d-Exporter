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

bl_info = {
    "name": "Gameplay3D Files Exporter",
    "author": "Mark Lawan",
    "description": "Tools to export blender scenes to gameplay3d files.",
    "version": (1, 0),
    "blender": (2, 75, 0),
    "location": "Tool Shelf (ctrl + T), Scene Properties, Object Properties,\
            and NlaStrip Properties",
    "wiki_url": "makujin-lawan.rhcloud.com/posts/BlenderGameplay3DExporterAddonv10",
    "category": "Import-Export"
}

if "bpy" in locals():
    import imp
    imp.reload(utils)
    imp.reload(basicprops)
    imp.reload(assets)
    imp.reload(animgroups)
    imp.reload(animstrips)
    imp.reload(export)
else:
    from . import (
            utils, 
            basicprops,
            assets,
            animgroups, 
            animstrips,
            export
            )

import bpy

def register():
    basicprops.register()
    assets.register()
    animgroups.register()
    animstrips.register()
    export.register()
    bpy.utils.register_module(__name__)
 
def unregister():
    basicprops.unregister()
    assets.unregister()
    animgroups.unregister()
    animstrips.unregister()
    export.unregister()
    bpy.utils.unregister_module(__name__)
    
if __name__ == "__main__":
    register()
