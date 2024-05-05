import bpy
from .. import bl_info
from ..ui import XJ_HonkaiStarRail_UI

class XiaoJuBaoPanel(bpy.types.Panel):
    """Panel"""
    bl_label = "小橘包-星穹铁道"
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