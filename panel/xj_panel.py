# -*- coding: utf-8 -*-
import bpy
from bpy.app.translations import pgettext_iface as _
from .. import bl_info
from ..ui import XJ_HonkaiStarRail_UI

class XiaoJuBaoPanel(bpy.types.Panel):
    """Panel"""
    bl_label = _("XiaoJuBao-HonkaiStarRail@何以千奈的橘子")
    bl_idname = "XIAOJUBAO_PT_XiaoJu"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'XiaoJu'

    xj_honkai_star_rail_ui = XJ_HonkaiStarRail_UI()

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        box = layout.box()
        self.xj_honkai_star_rail_ui.draw_honkai_star_rail(scene, box)