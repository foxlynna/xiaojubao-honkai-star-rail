# -*- coding: utf-8 -*-
import bpy
from bpy.app.translations import pgettext_iface as _
from .. import bl_info
from ..listener import on_shader_file_path_update, on_honkai_star_rail_material_path_update, on_honkai_star_rail_role_json_file_path_update
from ..cache import CacheParams

cache = CacheParams()
# cache path
default_shader_file_path = cache.get("xj_honkai_star_rail_blend_file_path")
default_xj_honkai_star_rail_material_path = cache.get("xj_honkai_star_rail_material_path")
default_xj_honkai_star_rail_role_json_file_path = cache.get("xj_honkai_star_rail_role_json_file_path")

class XJ_HonkaiStarRail_UI():
    """honkai star rail"""
    # blend file
    bpy.types.Scene.xj_honkai_star_rail_blend_file_path = bpy.props.StringProperty(
        name=_("Shader blend file path"),
        description=_("Input shader blend file path"),
        default=default_shader_file_path if default_shader_file_path else "",
        maxlen=1024,
        subtype='FILE_PATH',
        update=on_shader_file_path_update
    )
    # is preset
    bpy.types.Scene.xj_honkai_star_rail_is_preset = bpy.props.BoolProperty(
        name=_("Is all in configs"),
        description=_("Is all in configs"),
        default=False
    )
    # is join mesh
    bpy.types.Scene.xj_honkai_star_rail_is_join_mesh = bpy.props.BoolProperty(
        name=_("Whether to merge meshes in the same group"),
        description=_("Whether to merge meshes in the same group"),
        default=True
    )
    # texure file
    bpy.types.Scene.xj_honkai_star_rail_material_path = bpy.props.StringProperty(
        name=_("Texture file path"),
        description=_("Input texture file path"),
        default=default_xj_honkai_star_rail_material_path if default_xj_honkai_star_rail_material_path else "",
        maxlen=1024,
        subtype='FILE_PATH',
        update=on_honkai_star_rail_material_path_update
    )
    # role json file
    bpy.types.Scene.xj_honkai_star_rail_role_json_file_path = bpy.props.StringProperty(
        name=_("Character JSON Path"),
        description=_("Input character JSON Path"),
        default=default_xj_honkai_star_rail_role_json_file_path if default_xj_honkai_star_rail_role_json_file_path else "",
        maxlen=1024,
        subtype='FILE_PATH',
        update=on_honkai_star_rail_role_json_file_path_update
    )
    # outline thickness
    bpy.types.Scene.xj_honkai_star_rail_outline_thickness = bpy.props.FloatProperty(
        name=_("Outline thickness"),
        description=_("Input outline thickness"),
        default=0.08
    )
    
    def draw_honkai_star_rail(self, scene, box):
        """honkai star rail ui"""
        version_str = f"version：{bl_info['honkai_star_rail_version'][0]}.{bl_info['honkai_star_rail_version'][1]}.{bl_info['honkai_star_rail_version'][2]}"
        row = box.row()
        row.label(text=version_str)
        
        row = box.row()
        row.prop(scene, "xj_honkai_star_rail_blend_file_path", text=_("Shader blend file path"))
        
        row = box.row()
        row.prop(scene, "xj_honkai_star_rail_is_preset", text=_("Is it to integrate configuration files"))
        
        row = box.row()
        row.prop(scene, "xj_honkai_star_rail_is_join_mesh", text=_("Whether to merge meshes in the same group"))
        
        row = box.row()
        row.enabled = not scene.xj_honkai_star_rail_is_preset
        row.prop(scene, "xj_honkai_star_rail_material_path", text=_("Texture file path"))
        
        row = box.row()
        row.enabled = not scene.xj_honkai_star_rail_is_preset
        row.prop(scene, "xj_honkai_star_rail_role_json_file_path", text=_("Character JSON Path"))
        
        row = box.row()
        row.operator("xj.honkai_star_rail_add", text=_("Batch apply materials"), icon="MATERIAL_DATA")
        
        row = box.row()
        row.operator("xj.honkai_star_rail_add_light_modifier", text=_("Batch apply light vector modifiers"), icon="ADD")
        
        row = box.row()
        row.operator("xj.honkai_star_rail_add_light_modifier_remove", text=_("Batch remove light vector modifiers"), icon="REMOVE")
        
        row = box.row()
        row.prop(scene, "xj_honkai_star_rail_outline_thickness", text=_("Outline thickness"))
        
        row = box.row()
        row.operator("xj.honkai_star_rail_outline_add", text=_("Batch add/modify outlines"), icon="ADD")
        
        row = box.row()
        row.operator("xj.honkai_star_rail_outline_remove", text=_("Batch remove outlines"), icon="REMOVE")
        
