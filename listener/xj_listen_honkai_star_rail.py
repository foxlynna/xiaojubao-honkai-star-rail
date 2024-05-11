# -*- coding: utf-8 -*-
import bpy
from ..cache import CacheParams
cache = CacheParams()
# listener function expected a function type, not a method        
def on_shader_file_path_update(self, context):
    """when shader file path updated"""
    new_path = context.scene.xj_honkai_star_rail_blend_file_path
    print(f"Blend file path updated to: {new_path}")
    # write to cache
    cache.write("xj_honkai_star_rail_blend_file_path", new_path)

def on_honkai_star_rail_material_path_update(self, context):
    """when honkai star rail material path updated"""
    new_path = context.scene.xj_honkai_star_rail_material_path
    print(f"Material path updated to: {new_path}")
    # write to cache
    cache.write("xj_honkai_star_rail_material_path", new_path)  

def on_honkai_star_rail_role_json_file_path_update(self, context):
    """when honkai star rail role json file path updated"""
    new_path = context.scene.xj_honkai_star_rail_role_json_file_path
    print(f"Role json file path updated to: {new_path}")
    # write to cache
    cache.write("xj_honkai_star_rail_role_json_file_path", new_path)      
