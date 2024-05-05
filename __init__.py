# author: 何以千奈的橘子
# bilibili: https://space.bilibili.com/41350412
# license: AGPL 3.0

bl_info = {
    "name": "小橘包",
    "blender": (3, 6, 0),
    "category": "UI",
    "description": "小橘包",
    "author": "何以千奈的橘子",
    "version": (0, 1, 0),
    "honkai_star_rail_version": (0, 1, 0),
    "location": "View3D > Sidebar > XiaoJu Tab"
}

import bpy
from .panel import XiaoJuBaoPanel
from .operator import XJ_OP_HonkaiStarRail, XJ_OP_HonkaiStarRailLightModifier, XJ_OP_HonkaiStarRailLightModifierRemove,XJ_OP_HonkaiStarRailOutline, XJ_OP_HonkaiStarRailOutlineRemove

classes = (XiaoJuBaoPanel, XJ_OP_HonkaiStarRail, XJ_OP_HonkaiStarRailLightModifier, XJ_OP_HonkaiStarRailLightModifierRemove, XJ_OP_HonkaiStarRailOutline, XJ_OP_HonkaiStarRailOutlineRemove)

register, unregister = bpy.utils.register_classes_factory(classes)
