import bpy
from .. import bl_info
from ..listener import on_shader_file_path_update, on_honkai_star_rail_material_path_update, on_honkai_star_rail_role_json_file_path_update
from ..cache import CacheParams

cache = CacheParams()
default_shader_file_path = cache.get("xj_honkai_star_rail_blend_file_path")
default_xj_honkai_star_rail_material_path = cache.get("xj_honkai_star_rail_material_path")
default_xj_honkai_star_rail_role_json_file_path = cache.get("xj_honkai_star_rail_role_json_file_path")

class XJ_HonkaiStarRail_UI():
    """honkai star rail"""
    # blend file
    bpy.types.Scene.xj_honkai_star_rail_blend_file_path = bpy.props.StringProperty(
        name="shader blend file path",
        description="shader blend文件路径",
        default=default_shader_file_path if default_shader_file_path else "",
        maxlen=1024,
        subtype='FILE_PATH',
        update=on_shader_file_path_update
    )
    # texure file
    bpy.types.Scene.xj_honkai_star_rail_material_path = bpy.props.StringProperty(
        name="texture file path",
        description="贴图路径",
        default=default_xj_honkai_star_rail_material_path if default_xj_honkai_star_rail_material_path else "",
        maxlen=1024,
        subtype='FILE_PATH',
        update=on_honkai_star_rail_material_path_update
    )
    # role json file
    bpy.types.Scene.xj_honkai_star_rail_role_json_file_path = bpy.props.StringProperty(
        name="role json Path",
        description="角色配置文件",
        default=default_xj_honkai_star_rail_role_json_file_path if default_xj_honkai_star_rail_role_json_file_path else "",
        maxlen=1024,
        subtype='FILE_PATH',
        update=on_honkai_star_rail_role_json_file_path_update
    )
    # outline thickness
    bpy.types.Scene.xj_honkai_star_rail_outline_thickness = bpy.props.FloatProperty(
        name="描边厚度",
        description="描边厚度",
        default=0.08
    )
    
    def draw_honkai_star_rail(self, scene, box):
        """honkai star rail ui"""
        version_str = f"version：{bl_info['honkai_star_rail_version'][0]}.{bl_info['honkai_star_rail_version'][1]}.{bl_info['honkai_star_rail_version'][2]}"
        row = box.row()
        row.label(text=version_str)
        
        row = box.row()
        row.prop(scene, "xj_honkai_star_rail_blend_file_path", text="shader blend文件路径")
        
        row = box.row()
        row.prop(scene, "xj_honkai_star_rail_material_path", text="贴图路径")
        
        row = box.row()
        row.prop(scene, "xj_honkai_star_rail_role_json_file_path", text="角色配置文件")
        
        row = box.row()
        row.operator("xj.honkai_star_rail_add", text="批量添加材质", icon="MATERIAL_DATA")
        
        row = box.row()
        row.operator("xj.honkai_star_rail_add_light_modifier", text="批量添加灯光矢量修改器", icon="ADD")
        
        row = box.row()
        row.operator("xj.honkai_star_rail_add_light_modifier_remove", text="批量移除灯光矢量修改器", icon="REMOVE")
        
        row = box.row()
        row.prop(scene, "xj_honkai_star_rail_outline_thickness", text="描边厚度")
        
        row = box.row()
        row.operator("xj.honkai_star_rail_outline_add", text="批量添加/修改描边", icon="ADD")
        
        row = box.row()
        row.operator("xj.honkai_star_rail_outline_remove", text="批量移除描边", icon="REMOVE")
        
