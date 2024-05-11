# -*- coding: utf-8 -*-
# author: 何以千奈的橘子
# bilibili: https://space.bilibili.com/41350412
# license: AGPL 3.0

bl_info = {
    "name": "小橘包-星穹铁道",
    "blender": (3, 6, 0),
    "category": "UI",
    "description": "小橘包-星穹铁道",
    "author": "何以千奈的橘子",
    "version": (0, 2, 0),
    "honkai_star_rail_version": (0, 2, 0),
    "location": "View3D > Sidebar > XiaoJu Tab"
}

import bpy
from .panel import XiaoJuBaoPanel
from .operator import XJ_OP_HonkaiStarRail, XJ_OP_HonkaiStarRailLightModifier, XJ_OP_HonkaiStarRailLightModifierRemove,XJ_OP_HonkaiStarRailOutline, XJ_OP_HonkaiStarRailOutlineRemove

classes = (XiaoJuBaoPanel, XJ_OP_HonkaiStarRail, XJ_OP_HonkaiStarRailLightModifier, XJ_OP_HonkaiStarRailLightModifierRemove, XJ_OP_HonkaiStarRailOutline, XJ_OP_HonkaiStarRailOutlineRemove)

register_class, unregister_class = bpy.utils.register_classes_factory(classes)
def register():
    register_class()
    from .i18n import translation_dict
    bpy.app.translations.register(bl_info['name'], translation_dict)
    
def unregister():
    bpy.app.translations.unregister(bl_info['name'])
    unregister_class()
    
    
if __name__ == "__main__":
    register()
    