# -*- coding: utf-8 -*-
import bpy
from bpy.app.translations import pgettext_iface
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
        name=pgettext_iface("Shader blend file path"),
        description=pgettext_iface("Input shader blend file path"),
        default=default_shader_file_path if default_shader_file_path else "",
        maxlen=1024,
        subtype='FILE_PATH',
        update=on_shader_file_path_update
    )
    # texure file
    bpy.types.Scene.xj_honkai_star_rail_material_path = bpy.props.StringProperty(
        name=pgettext_iface("Texture file path"),
        description=pgettext_iface("Input texture file path"),
        default=default_xj_honkai_star_rail_material_path if default_xj_honkai_star_rail_material_path else "",
        maxlen=1024,
        subtype='FILE_PATH',
        update=on_honkai_star_rail_material_path_update
    )
    # role json file
    bpy.types.Scene.xj_honkai_star_rail_role_json_file_path = bpy.props.StringProperty(
        name=pgettext_iface("Character JSON Path"),
        description=pgettext_iface("Input character JSON Path"),
        default=default_xj_honkai_star_rail_role_json_file_path if default_xj_honkai_star_rail_role_json_file_path else "",
        maxlen=1024,
        subtype='FILE_PATH',
        update=on_honkai_star_rail_role_json_file_path_update
    )
    # outline thickness
    bpy.types.Scene.xj_honkai_star_rail_outline_thickness = bpy.props.FloatProperty(
        name=pgettext_iface("Outline thickness"),
        description=pgettext_iface("Input outline thickness"),
        default=0.08
    )
    
    def draw_honkai_star_rail(self, scene, box):
        """honkai star rail ui"""
        version_str = f"version：{bl_info['honkai_star_rail_version'][0]}.{bl_info['honkai_star_rail_version'][1]}.{bl_info['honkai_star_rail_version'][2]}"
        row = box.row()
        row.label(text=version_str)
        
        row = box.row()
        row.prop(scene, "xj_honkai_star_rail_blend_file_path", text=pgettext_iface("Shader blend file path"))
        
        row = box.row()
        row.prop(scene, "xj_honkai_star_rail_material_path", text=pgettext_iface("Texture file path"))
        
        row = box.row()
        row.prop(scene, "xj_honkai_star_rail_role_json_file_path", text=pgettext_iface("Character JSON Path"))
        
        row = box.row()
        row.operator("xj.honkai_star_rail_add", text=pgettext_iface("Batch apply materials"), icon="MATERIAL_DATA")
        
        row = box.row()
        row.operator("xj.honkai_star_rail_add_light_modifier", text=pgettext_iface("Batch apply light vector modifiers"), icon="ADD")
        
        row = box.row()
        row.operator("xj.honkai_star_rail_add_light_modifier_remove", text=pgettext_iface("Batch remove light vector modifiers"), icon="REMOVE")
        
        row = box.row()
        row.prop(scene, "xj_honkai_star_rail_outline_thickness", text=pgettext_iface("Outline thickness"))
        
        row = box.row()
        row.operator("xj.honkai_star_rail_outline_add", text=pgettext_iface("Batch add/modify outlines"), icon="ADD")
        
        row = box.row()
        row.operator("xj.honkai_star_rail_outline_remove", text=pgettext_iface("Batch remove outlines"), icon="REMOVE")
        
