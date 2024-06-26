# -*- coding: utf-8 -*-
import bpy
from bpy.types import Operator, Image, Object, Mesh, Material, MaterialSlot
from bpy.app.translations import pgettext_iface as _
from bpy.app.handlers import persistent
from bpy.app.timers import register
import bmesh
import os
import json
import time
from typing import Optional, Dict, Any, List
from ..utils import MaterialUtils

# constants
NAME_OF_VERTEX_COLORS_INPUT = 'Input_3'

class XJ_OP_HonkaiStarRail(Operator):
    """add honkai star rail material"""
    bl_label = "Add HonkaiStarRail Material"
    bl_idname = "xj.honkai_star_rail_add"
    bl_description = _("Add HonkaiStarRail Material")
    bl_options = {'REGISTER', 'UNDO'}
    
    LIGHT_VECTOR_NODE_NAME = "Light Vectors"
    STELLAR_TOON_OUTLINE_NODE_NAME = "StellarToon - Outlines GN"
    STELLAR_MATERIAL_NAME = ["StellarToon - Base Outlines", 
                             "StellarToon - Base", 
                             "StellarToon - Hair", 
                             "StellarToon - Hair Outlines",
                             "StellarToon - Weapon",
                             "StellarToon - Weapon Outlines", 
                             "StellarToon - Face", 
                             "StellarToon - Face Outlines"]
    # tex and material map
    TEX_MATERIAL_MAP = {
        "face": "StellarToon - Face",
        "hair": "StellarToon - Hair",
        "body": "StellarToon - Base",
        "body1": "StellarToon - Base",
        "body2": "StellarToon - Base",
    }
    print(f"""TEX_MATERIAL_MAP: {TEX_MATERIAL_MAP}""")

    def execute(self, context):
        blend_file_path = context.scene.xj_honkai_star_rail_blend_file_path
        if blend_file_path:
            self.import_nodes(blend_file_path)
            self.import_material(blend_file_path)
            self.import_light_vector_empty_obj()
            # self.import_light_direction_collection(blend_file_path)
            json_obj : Optional[Dict[str, Any]] = None
            # is preset
            if context.scene.xj_honkai_star_rail_is_preset:
                json_obj = MaterialUtils.load_first_script_as_json(blend_file_path)
                if not json_obj:
                    raise Exception("Failed to load preset json file")    
                self.import_textures_from_blend(blend_file_path)
                self.assign_materials_from_preset(json_obj)
            else:    
                json_obj = MaterialUtils.load_role_json_obj(context.scene.xj_honkai_star_rail_role_json_file_path)
                if not json_obj:
                    raise Exception("Failed to load preset json file")  
                self.assign_materials_from_json(json_obj, context.scene.xj_honkai_star_rail_material_path)
            # emmison material
            self.modify_emission_material(json_obj.get('emmision', []))
            # eyeshadow
            self.modify_eyeshadow_material(json_obj.get('eyeshadow', []))
            # head origin constraint
            self.set_child_of_constraints_to_heads()
            # gooengine_base_render_set
            MaterialUtils.set_gooengine_base_render_set()
            return {'FINISHED'}
        else:
            return {'CANCELLED'}
        

    def import_nodes(self, filepath):
        """import nodes when nodes not exist"""
        with bpy.data.libraries.load(filepath, link=False) as (data_from, data_to):
            node_names = [name for name in data_from.node_groups if self.LIGHT_VECTOR_NODE_NAME in name or self.STELLAR_TOON_OUTLINE_NODE_NAME in name]

            nodes_to_import = []
            for node_name in node_names:
                if self.LIGHT_VECTOR_NODE_NAME in node_name and not MaterialUtils.check_node_group_exist(node_name):
                    nodes_to_import.append(node_name)
                elif self.STELLAR_TOON_OUTLINE_NODE_NAME in node_name and not MaterialUtils.check_node_group_exist(node_name):
                    nodes_to_import.append(node_name)
            data_to.node_groups = nodes_to_import

            if nodes_to_import:
                print("Imported Node Groups:")
                for ng_name in nodes_to_import:
                    print(ng_name)
            else:
                print("No new node groups imported.")
            return nodes_to_import   
        
    def import_material(self, filepath):
        """import material when material not exist"""
        imported_materials = []
        with bpy.data.libraries.load(filepath, link=False) as (data_from, data_to):
            materials_to_import = [name for name in data_from.materials if "StellarToon" in name and name not in bpy.data.materials]
            data_to.materials = materials_to_import

        if data_to.materials:
            imported_materials.extend(data_to.materials)
            print("Imported Materials:")
            for mat_name in data_to.materials:
                print(mat_name)

        return imported_materials
    
    def import_light_direction_collection(self, filepath):
        """
        检查当前活动场景中是否存在 'Light Direction' 集合。
        如果不存在，则从指定的 .blend 文件中追加此集合到当前场景中。
        :param filepath: .blend 文件的路径，其中包含 'Light Direction' 集合。
        """
        # 检查 'Light Direction' 集合是否已链接到当前场景
        if "Light Direction" in bpy.context.scene.collection.children:
            print("'Light Direction' collection already exists in the current scene.")
            return

        # 追加 'Light Direction' 集合
        with bpy.data.libraries.load(filepath, link=False) as (data_from, data_to):
            if "Light Direction" in data_from.collections:
                data_to.collections.append("Light Direction")
            else:
                print("'Light Direction' collection not found in the file.")
                return

        # 获取导入的集合
        imported_collection = bpy.data.collections.get("Light Direction", None)
        if imported_collection:
            # 将导入的集合链接到当前活动场景中
            bpy.context.scene.collection.children.link(imported_collection)
            print("Imported and linked 'Light Direction' collection to the current scene from", filepath)
        else:
            print("Failed to import 'Light Direction' collection.")
    
    def import_light_vector_empty_obj(self):
        """import_light_vector_empty_obj"""
        self.add_object_to_scene_collection("Main Light Direction")
        self.add_object_to_scene_collection("Head Origin")
        self.add_object_to_scene_collection("Head Forward")
        self.add_object_to_scene_collection("Head Up")
    

    
    def import_textures_from_blend(self, blend_filepath: str) -> None:
        """
        from specified .blend file import all existing textures
        If the current project already has a real existing texture with the same name, it will be skipped.

        :param blend_filepath: .blend file full path
        """
        try:
            with bpy.data.libraries.load(blend_filepath, link=False) as (data_from, data_to):
                if not data_from.images:
                    print(f"from {blend_filepath} no images")
                    return
                valid_image_names = []
                # check if image already exists
                for img_name in data_from.images:
                    if "Render Result" in img_name:
                        continue
                    if img_name in bpy.data.images:
                        existing_image = bpy.data.images[img_name]
                        if existing_image.filepath and os.path.isfile(bpy.path.abspath(existing_image.filepath)):
                            print(f"{img_name} exists, skip")
                            continue
                        else:
                            print(f"{img_name} exists, but not a valid file, remove")
                            bpy.data.images.remove(existing_image)
                    valid_image_names.append(img_name)
                data_to.images = valid_image_names
                print(f"import {len(valid_image_names)} images from {blend_filepath}")
        except Exception as e:
            print(f"load blend file error：{e}")
            return
        
    
    def add_object_to_scene_collection(self, obj_name):
        """Adds an object to the active scene's active collection if the object exists."""
        obj = bpy.data.objects.get(obj_name)
        if obj is None:
            print(f"No object found with the name '{obj_name}'.")
            return False
        collection = bpy.context.collection
        if obj.name not in collection.objects:
            collection.objects.link(obj)
            print(f"Object '{obj_name}' has been added to the collection '{collection.name}'.")
        else:
            print(f"Object '{obj_name}' is already in the collection '{collection.name}'.")
        return True
            
    def check_blend_file_exist(self, filepath):
        if os.path.exists(filepath):
            return True
        else:
            return False
    
    def write_role_json(self, role_name, image_map, filepath):
        """write_role_json to json file"""
        full_file_path = os.path.join(filepath, f"{role_name}.json")
        print(full_file_path)
        # data structure
        data_to_write = {
            "role_name": role_name,
            "material_map": {
                
            }
        }
        # image_map add to data
        for key, value in image_map.items():
            data_to_write["material_map"][key] = value
            
        # Ensure the directory exists
        os.makedirs(os.path.dirname(full_file_path), exist_ok=True)
        # Write json
        with open(full_file_path, 'w', encoding='utf-8') as json_file:
            json.dump(data_to_write, json_file, ensure_ascii=False, indent=4)
        print(f"Data successfully written to {full_file_path}")
    
    def collect_image_references(self):
        """read original model material and collect tex image"""
        image_map = {}
        for obj in bpy.context.selected_objects:
            if obj.type == 'MESH':
                if obj.material_slots:
                    for slot in obj.material_slots:
                        if slot.material and slot.material.use_nodes:
                            nodes = slot.material.node_tree.nodes
                            for node in nodes:
                                if node.type == 'TEX_IMAGE' and node.image:
                                    image_name = node.image.name
                                    # remove .png
                                    if image_name.lower().endswith('.png'):
                                        image_name = image_name[:-4]
                                    # get mesh name and split by '_'
                                    mesh_name_parts = obj.name.split('_')
                                    if len(mesh_name_parts) > 1:
                                        mesh_name = mesh_name_parts[1]
                                    else:
                                        mesh_name = mesh_name_parts[0]
                                    if image_name not in image_map:
                                        image_map[image_name] = []
                                    if mesh_name not in image_map[image_name]:
                                        image_map[image_name].append(mesh_name)
        print(image_map)
        return image_map
    
    def material_add_tex(self, mesh: Mesh, adding_material_name, tex_file_path, type, role_name, mesh_material_name, slot: MaterialSlot):
        """replace material

        Args:
            mesh (mesh): mesh
            adding_material_name (str): adding material name
            tex_file_path (str): tex_file_path
            type (str): type
            role_name (str): role_name
            mesh_name_after (str): mesh_material_name
        """
        # find material
        mat = bpy.data.materials.get(adding_material_name)
        if not mat:
            self.report({'ERROR'}, f"No material found with the name '{adding_material_name}'")
            return
        # generate material if not exist
        new_mat_name = role_name + "_" + type
        new_mat = bpy.data.materials.get(new_mat_name)
        if not new_mat:
            # copy material and rename
            new_mat = mat.copy()
            new_mat.name = new_mat_name
            print(f"new_mat: {new_mat}")
        # modify material node
        if type == "face":
            self.get_face_material(new_mat, tex_file_path)
        elif type == "hair":
            self.get_hair_material(new_mat, tex_file_path)
        elif type == "body1":    
            self.get_body1_material(new_mat, tex_file_path)
        elif type == "body2":
            self.get_body2_material(new_mat, tex_file_path)    
        elif type == "body":    
            self.get_body_material(new_mat, tex_file_path)
        # fix face outline, only face material name is {role_name}_face, other face material name is {role_name}_face_{material_name}
        if type == "face" and mesh_material_name not in ["脸", "臉", "顏", "颜"]:
            new_mat = new_mat.copy()
            new_mat.name = role_name + "_" + type + "_" + mesh_material_name
        slot.material = new_mat
    
    def get_texture_image(self, image_name, tex_file_path) -> Image:
        """get_texture_image"""
        image = bpy.data.images.get(image_name)
        if image and (image.packed_file or os.path.isfile(bpy.path.abspath(image.filepath))):
            return image
        else:
            image = bpy.data.images.load(os.path.join(tex_file_path, image_name))
        return image
    
    def get_face_material(self, material, tex_file_path):
        """add and modify face material"""
        if not material.use_nodes:
            material.use_nodes = True

        nodes = material.node_tree.nodes

        # loop tex_file_path and find FaceMap and Face_Color
        face_map_texture = None
        face_color_texture = None
        if tex_file_path:
            for file_name in os.listdir(tex_file_path):
                if "FaceMap" in file_name and file_name.endswith(".png"):
                    face_map_texture = file_name
                elif "Face_Color" in file_name and file_name.endswith(".png"):
                    face_color_texture = file_name
        # tex_file_path is empty, is preset
        if not tex_file_path:
            for image in bpy.data.images:
                file_name = image.name
                if "FaceMap" in file_name and file_name.endswith(".png"):
                    face_map_texture = file_name
                elif "Face_Color" in file_name and file_name.endswith(".png"):
                    face_color_texture = file_name
        # face map texture exists
        if face_map_texture:
            # if face_map_texture exists, use it, else load image
            image = self.get_texture_image(face_map_texture, tex_file_path)
            # to do
            # config Face Lightmap (Non-Color) (Channel Packed) node
            for node in nodes:
                if node.type == 'GROUP' and node.node_tree and node.node_tree.name == "Face Lightmap":
                    group_nodes = node.node_tree.nodes
                    print(f"group_nodes: {group_nodes}")
                    face_lightmap_node = group_nodes.get("FaceMap")
                    print(f"face_lightmap_node: {face_lightmap_node}")
                    if face_lightmap_node:
                        face_lightmap_node.image = image
                        face_lightmap_node.image.alpha_mode = 'CHANNEL_PACKED'
                        face_lightmap_node.image.colorspace_settings.name = 'Non-Color'

            # config Expression Map (Non-Color) (Channel Packed) node
            expression_map_node = nodes.get("ExpressionMap")
            print(f"expression_map_node: {expression_map_node}")
            if expression_map_node:
                expression_map_node.image = image
                expression_map_node.image.alpha_mode = 'CHANNEL_PACKED'
                expression_map_node.image.colorspace_settings.name = 'Non-Color'

        # face color texture exists
        if face_color_texture:
            # if face_color_texture exists, use it, else load image
            image = self.get_texture_image(face_color_texture, tex_file_path)
            # config Face_Color node
            face_color_node = nodes.get("Face_Color")
            print(f"face_color_node: {face_color_node}")
            if face_color_node:
                face_color_node.image = image
                face_color_node.image.alpha_mode = 'CHANNEL_PACKED'
        # default value
        self.set_face_material_default_value(nodes)
        return material
    
    def get_hair_material(self, material, tex_file_path):
        """add and modify hair material"""
        if not material.use_nodes:
            material.use_nodes = True

        nodes = material.node_tree.nodes

        # loop tex_file_path and find Hair_Color and Hair_Cool_Ramp and Hair_Warm_Ramp and Hair_LightMap
        hair_color_texture = None
        hair_cool_ramp_texture = None
        hair_warm_ramp_texture = None
        hair_lightmap_texture = None
        if tex_file_path:
            for file_name in os.listdir(tex_file_path):
                if "Hair_Color" in file_name and file_name.endswith(".png"):
                    hair_color_texture = file_name
                elif "Hair_Cool_Ramp" in file_name and file_name.endswith(".png"):
                    hair_cool_ramp_texture = file_name
                elif "Hair_Warm_Ramp" in file_name and file_name.endswith(".png"):
                    hair_warm_ramp_texture = file_name
                elif "Hair_LightMap" in file_name and file_name.endswith(".png"):
                    hair_lightmap_texture = file_name
        # tex_file_path is empty, is preset
        if not tex_file_path:
            for image in bpy.data.images:
                file_name = image.name
                if "Hair_Color" in file_name and file_name.endswith(".png"):
                    hair_color_texture = file_name
                elif "Hair_Cool_Ramp" in file_name and file_name.endswith(".png"):
                    hair_cool_ramp_texture = file_name
                elif "Hair_Warm_Ramp" in file_name and file_name.endswith(".png"):
                    hair_warm_ramp_texture = file_name
                elif "Hair_LightMap" in file_name and file_name.endswith(".png"):
                    hair_lightmap_texture = file_name
            
        if hair_color_texture:
            # if face_color_texture exists, use it, else load image
            image = self.get_texture_image(hair_color_texture, tex_file_path)
            # config Hair_Color node
            hair_color_node = nodes.get("Hair_Color_UV0")
            print(f"hair_color_node: {hair_color_node}")
            if hair_color_node:
                hair_color_node.image = image
                hair_color_node.image.alpha_mode = 'CHANNEL_PACKED'
                
            hair_color_node1 = nodes.get("Hair_Color_UV1")
            print(f"hair_color_node1: {hair_color_node1}")
            if hair_color_node1:
                hair_color_node1.image = image
                hair_color_node1.image.alpha_mode = 'CHANNEL_PACKED'
        
        if hair_cool_ramp_texture:
            # if hair_cool_ramp_texture exists, use it, else load image
            image = self.get_texture_image(hair_cool_ramp_texture, tex_file_path)
            # config Hair_Cool_Ramp node
            for node in nodes:
                if node.type == 'GROUP' and node.node_tree and node.node_tree.name == "Hair Cool Shadow Ramp":
                    group_nodes = node.node_tree.nodes
                    print(f"group_nodes: {group_nodes}")
                    hair_cool_ramp_node = group_nodes.get("Hair_Cool_Ramp")
                    print(f"hair_cool_ramp_node: {hair_cool_ramp_node}")
                    if hair_cool_ramp_node:
                        hair_cool_ramp_node.image = image
                        hair_cool_ramp_node.image.alpha_mode = 'CHANNEL_PACKED'
        if hair_warm_ramp_texture:
            # if hair_warm_ramp_texture exists, use it, else load image
            image = self.get_texture_image(hair_warm_ramp_texture, tex_file_path)
            # config Hair_Warm_Ramp node
            for node in nodes:
                if node.type == 'GROUP' and node.node_tree and node.node_tree.name == "Hair Warm Shadow Ramp":
                    group_nodes = node.node_tree.nodes
                    print(f"group_nodes: {group_nodes}")
                    hair_warm_ramp_node = group_nodes.get("Hair_Warm_Ramp")
                    print(f"hair_warm_ramp_node: {hair_warm_ramp_node}")
                    if hair_warm_ramp_node:
                        hair_warm_ramp_node.image = image
                        hair_warm_ramp_node.image.alpha_mode = 'CHANNEL_PACKED'                        

        if hair_lightmap_texture:
            # if hair_lightmap_texture exists, use it, else load image
            image = self.get_texture_image(hair_lightmap_texture, tex_file_path)
            # config Hair_LightMap node
            hair_lightmap_node = nodes.get("Hair_Lightmap_UV0")
            print(f"hair_lightmap_node: {hair_lightmap_node}")
            if hair_lightmap_node:
                hair_lightmap_node.image = image
                hair_lightmap_node.image.alpha_mode = 'CHANNEL_PACKED'
                hair_lightmap_node.image.colorspace_settings.name = 'Non-Color'
            
            hair_lightmap_node1 = nodes.get("Hair_Lightmap_UV1")
            print(f"hair_lightmap_node1: {hair_lightmap_node1}")
            if hair_lightmap_node1:
                hair_lightmap_node1.image = image
                hair_lightmap_node1.image.alpha_mode = 'CHANNEL_PACKED'
                hair_lightmap_node1.image.colorspace_settings.name = 'Non-Color'
        
        # uvmap
        uvmap_node = nodes.get("UV Map.001")
        if uvmap_node and uvmap_node.type == 'UVMAP':
            uvmap_node.uv_map = "UVMap"
        # default value
        self.set_hair_material_default_value(nodes)
        
        return material
    
    def get_body_material(self, material, tex_file_path):
        """add and modify body material"""
        if not material.use_nodes:
            material.use_nodes = True

        nodes = material.node_tree.nodes

        # loop tex_file_path and find Body_Color and Body_Cool_Ramp and Body_Warm_Ramp and Body_LightMap
        body_color_texture = None
        body_cool_ramp_texture = None
        body_warm_ramp_texture = None
        body_lightmap_texture = None
        
        if tex_file_path:
            for file_name in os.listdir(tex_file_path):
                if "Body_Color" in file_name and file_name.endswith(".png"):
                    if body_color_texture and ("Eff" in body_color_texture or "_L" in body_color_texture):
                        body_color_texture = file_name
                    else:
                        body_color_texture = file_name
                elif "Body_Cool_Ramp" in file_name and file_name.endswith(".png"):
                    body_cool_ramp_texture = file_name
                elif "Body_Warm_Ramp" in file_name and file_name.endswith(".png"):
                    body_warm_ramp_texture = file_name
                elif "Body_LightMap" in file_name and file_name.endswith(".png"):
                    if body_lightmap_texture and ("Eff" in body_lightmap_texture or "_L" in body_lightmap_texture):
                        body_lightmap_texture = file_name
                    else:
                        body_lightmap_texture = file_name
        # tex_file_path is empty, is preset
        if not tex_file_path:
            for image in bpy.data.images:
                file_name = image.name
                if "Body_Color" in file_name and file_name.endswith(".png"):
                    if body_color_texture and ("Eff" in body_color_texture or "_L" in body_color_texture):
                        body_color_texture = file_name
                    else:
                        body_color_texture = file_name
                elif "Body_Cool_Ramp" in file_name and file_name.endswith(".png"):
                    body_cool_ramp_texture = file_name
                elif "Body_Warm_Ramp" in file_name and file_name.endswith(".png"):
                    body_warm_ramp_texture = file_name
                elif "Body_LightMap" in file_name and file_name.endswith(".png"):
                    if body_lightmap_texture and ("Eff" in body_lightmap_texture or "_L" in body_lightmap_texture):
                        body_lightmap_texture = file_name
                    else:
                        body_lightmap_texture = file_name
                
        if body_color_texture:
            # if body_color_texture exists, use it, else load image
            image = self.get_texture_image(body_color_texture, tex_file_path)
            # config Body_Color node
            body_color_node = nodes.get("Body_Color_UV0")
            print(f"body_color_node: {body_color_node}")
            if body_color_node:
                body_color_node.image = image
                body_color_node.image.alpha_mode = 'CHANNEL_PACKED'
                
            body_color_node1 = nodes.get("Body_Color_UV1")
            print(f"body_color_node1: {body_color_node1}")
            if body_color_node1:
                body_color_node1.image = image
                body_color_node1.image.alpha_mode = 'CHANNEL_PACKED'
        
        if body_cool_ramp_texture:
            # if body_cool_ramp_texture exists, use it, else load image
            image = self.get_texture_image(body_cool_ramp_texture, tex_file_path)
            # config body_cool_ramp node
            for node in nodes:
                if node.type == 'GROUP' and node.node_tree and node.node_tree.name == "Body Cool Shadow Ramp":
                    group_nodes = node.node_tree.nodes
                    print(f"group_nodes: {group_nodes}")
                    body_cool_ramp_node = group_nodes.get("Body_Cool_Ramp")
                    print(f"body_cool_ramp_node: {body_cool_ramp_node}")
                    if body_cool_ramp_node:
                        body_cool_ramp_node.image = image
                        body_cool_ramp_node.image.alpha_mode = 'CHANNEL_PACKED'
        if body_warm_ramp_texture:
            # if body_warm_ramp_texture exists, use it, else load image
            image = self.get_texture_image(body_warm_ramp_texture, tex_file_path)
            # config body_warm_ramp node
            for node in nodes:
                if node.type == 'GROUP' and node.node_tree and node.node_tree.name == "Body Warm Shadow Ramp":
                    group_nodes = node.node_tree.nodes
                    print(f"group_nodes: {group_nodes}")
                    body_warm_ramp_node = group_nodes.get("Body_Warm_Ramp")
                    print(f"body_warm_ramp_node: {body_warm_ramp_node}")
                    if body_warm_ramp_node:
                        body_warm_ramp_node.image = image
                        body_warm_ramp_node.image.alpha_mode = 'CHANNEL_PACKED'                        

        if body_lightmap_texture:
            # if body_lightmap_texture exists, use it, else load image
            image = self.get_texture_image(body_lightmap_texture, tex_file_path)
            # config body_lightmap node
            body_lightmap_node = nodes.get("Body_Lightmap_UV0")
            print(f"body_lightmap_node: {body_lightmap_node}")
            if body_lightmap_node:
                body_lightmap_node.image = image
                body_lightmap_node.image.alpha_mode = 'CHANNEL_PACKED'
                body_lightmap_node.image.colorspace_settings.name = 'Non-Color'
            
            body_lightmap_node1 = nodes.get("Body_Lightmap_UV1")
            print(f"body_lightmap_node1: {body_lightmap_node1}")
            if body_lightmap_node1:
                body_lightmap_node1.image = image
                body_lightmap_node1.image.alpha_mode = 'CHANNEL_PACKED'
                body_lightmap_node1.image.colorspace_settings.name = 'Non-Color'
        
        # stockings ...
        
        # uvmap
        uvmap_node = nodes.get("UV Map.001")
        if uvmap_node and uvmap_node.type == 'UVMAP':
            uvmap_node.uv_map = "UVMap"
        
        # default value
        self.set_body_material_default_value(nodes)
        return material
    
    
    def get_body1_material(self, material, tex_file_path):
        """add and modify body material"""
        if not material.use_nodes:
            material.use_nodes = True

        nodes = material.node_tree.nodes

        # loop tex_file_path and find Body1_Color and Body_Cool_Ramp and Body_Warm_Ramp and Body1_LightMap
        body1_color_texture = None
        body_cool_ramp_texture = None
        body_warm_ramp_texture = None
        body1_lightmap_texture = None
        
        if tex_file_path:
            for file_name in os.listdir(tex_file_path):
                if "Body1_Color" in file_name and file_name.endswith(".png"):
                    body1_color_texture = file_name
                elif "Body_Cool_Ramp" in file_name and file_name.endswith(".png"):
                    body_cool_ramp_texture = file_name
                elif "Body_Warm_Ramp" in file_name and file_name.endswith(".png"):
                    body_warm_ramp_texture = file_name
                elif "Body1_LightMap" in file_name and file_name.endswith(".png"):
                    body1_lightmap_texture = file_name
        # tex_file_path is empty, is preset
        if not tex_file_path:
            for image in bpy.data.images:
                file_name = image.name
                if "Body1_Color" in file_name and file_name.endswith(".png"):
                    body1_color_texture = file_name
                elif "Body_Cool_Ramp" in file_name and file_name.endswith(".png"):
                    body_cool_ramp_texture = file_name
                elif "Body_Warm_Ramp" in file_name and file_name.endswith(".png"):
                    body_warm_ramp_texture = file_name
                elif "Body1_LightMap" in file_name and file_name.endswith(".png"):
                    body1_lightmap_texture = file_name
        
        if body1_color_texture:
            # if body1_color_texture exists, use it, else load image
            image = self.get_texture_image(body1_color_texture, tex_file_path)
            # config Body1_Color node
            body1_color_node = nodes.get("Body_Color_UV0")
            print(f"body1_color_node: {body1_color_node}")
            if body1_color_node:
                body1_color_node.image = image
                body1_color_node.image.alpha_mode = 'CHANNEL_PACKED'
                
            body1_color_node1 = nodes.get("Body_Color_UV1")
            print(f"body1_color_node1: {body1_color_node1}")
            if body1_color_node1:
                body1_color_node1.image = image
                body1_color_node1.image.alpha_mode = 'CHANNEL_PACKED'
        
        if body_cool_ramp_texture:
            # if body_cool_ramp_texture exists, use it, else load image
            image = self.get_texture_image(body_cool_ramp_texture, tex_file_path)
            # config body_cool_ramp node
            for node in nodes:
                if node.type == 'GROUP' and node.node_tree and node.node_tree.name == "Body Cool Shadow Ramp":
                    group_nodes = node.node_tree.nodes
                    print(f"group_nodes: {group_nodes}")
                    body_cool_ramp_node = group_nodes.get("Body_Cool_Ramp")
                    print(f"body_cool_ramp_node: {body_cool_ramp_node}")
                    if body_cool_ramp_node:
                        body_cool_ramp_node.image = image
                        body_cool_ramp_node.image.alpha_mode = 'CHANNEL_PACKED'
        if body_warm_ramp_texture:
            # if body_warm_ramp_texture exists, use it, else load image
            image = self.get_texture_image(body_warm_ramp_texture, tex_file_path)
            # config body_warm_ramp node
            for node in nodes:
                if node.type == 'GROUP' and node.node_tree and node.node_tree.name == "Body Warm Shadow Ramp":
                    group_nodes = node.node_tree.nodes
                    print(f"group_nodes: {group_nodes}")
                    body_warm_ramp_node = group_nodes.get("Body_Warm_Ramp")
                    print(f"body_warm_ramp_node: {body_warm_ramp_node}")
                    if body_warm_ramp_node:
                        body_warm_ramp_node.image = image
                        body_warm_ramp_node.image.alpha_mode = 'CHANNEL_PACKED'                        

        if body1_lightmap_texture:
            # if body1_lightmap_texture exists, use it, else load image
            image = self.get_texture_image(body1_lightmap_texture, tex_file_path)
            # config body1_lightmap node
            body1_lightmap_node = nodes.get("Body_Lightmap_UV0")
            print(f"body1_lightmap_node: {body1_lightmap_node}")
            if body1_lightmap_node:
                body1_lightmap_node.image = image
                body1_lightmap_node.image.alpha_mode = 'CHANNEL_PACKED'
                body1_lightmap_node.image.colorspace_settings.name = 'Non-Color'
            
            body1_lightmap_node1 = nodes.get("Body_Lightmap_UV1")
            print(f"body1_lightmap_node1: {body1_lightmap_node1}")
            if body1_lightmap_node1:
                body1_lightmap_node1.image = image
                body1_lightmap_node1.image.alpha_mode = 'CHANNEL_PACKED'
                body1_lightmap_node1.image.colorspace_settings.name = 'Non-Color'
        
        # stockings ...
        
        # uvmap
        uvmap_node = nodes.get("UV Map.001")
        if uvmap_node and uvmap_node.type == 'UVMAP':
            uvmap_node.uv_map = "UVMap"
        
        # default value
        self.set_body_material_default_value(nodes)
        return material
    
    def get_body2_material(self, material, tex_file_path):
        """add and modify body material"""
        if not material.use_nodes:
            material.use_nodes = True

        nodes = material.node_tree.nodes

        # loop tex_file_path and find Body2_Color and Body_Cool_Ramp and Body_Warm_Ramp and Body2_LightMap
        body2_color_texture = None
        body_cool_ramp_texture = None
        body_warm_ramp_texture = None
        body2_lightmap_texture = None
        
        if tex_file_path:
            for file_name in os.listdir(tex_file_path):
                if "Body2_Color" in file_name and file_name.endswith(".png"):
                    body2_color_texture = file_name
                elif "Body_Cool_Ramp" in file_name and file_name.endswith(".png"):
                    body_cool_ramp_texture = file_name
                elif "Body_Warm_Ramp" in file_name and file_name.endswith(".png"):
                    body_warm_ramp_texture = file_name
                elif "Body2_LightMap" in file_name and file_name.endswith(".png"):
                    body2_lightmap_texture = file_name
        # tex_file_path is empty, is preset
        if not tex_file_path:
            for image in bpy.data.images:
                file_name = image.name
                if "Body2_Color" in file_name and file_name.endswith(".png"):
                    body2_color_texture = file_name
                elif "Body_Cool_Ramp" in file_name and file_name.endswith(".png"):
                    body_cool_ramp_texture = file_name
                elif "Body_Warm_Ramp" in file_name and file_name.endswith(".png"):
                    body_warm_ramp_texture = file_name
                elif "Body2_LightMap" in file_name and file_name.endswith(".png"):
                    body2_lightmap_texture = file_name
        
        if body2_color_texture:
            # if body2_color_texture exists, use it, else load image
            image = self.get_texture_image(body2_color_texture, tex_file_path)
            # config Body2_Color node
            body2_color_node = nodes.get("Body_Color_UV0")
            print(f"body2_color_node: {body2_color_node}")
            if body2_color_node:
                body2_color_node.image = image
                body2_color_node.image.alpha_mode = 'CHANNEL_PACKED'
                
            body2_color_node1 = nodes.get("Body_Color_UV1")
            print(f"body2_color_node1: {body2_color_node1}")
            if body2_color_node1:
                body2_color_node1.image = image
                body2_color_node1.image.alpha_mode = 'CHANNEL_PACKED'
        
        if body_cool_ramp_texture:
            # if body_cool_ramp_texture exists, use it, else load image
            image = self.get_texture_image(body_cool_ramp_texture, tex_file_path)
            # config body_cool_ramp node
            for node in nodes:
                if node.type == 'GROUP' and node.node_tree and node.node_tree.name == "Body Cool Shadow Ramp":
                    group_nodes = node.node_tree.nodes
                    print(f"group_nodes: {group_nodes}")
                    body_cool_ramp_node = group_nodes.get("Body_Cool_Ramp")
                    print(f"body_cool_ramp_node: {body_cool_ramp_node}")
                    if body_cool_ramp_node:
                        body_cool_ramp_node.image = image
                        body_cool_ramp_node.image.alpha_mode = 'CHANNEL_PACKED'
        if body_warm_ramp_texture:
            # if body_warm_ramp_texture exists, use it, else load image
            image = self.get_texture_image(body_warm_ramp_texture, tex_file_path)
            # config body_warm_ramp node
            for node in nodes:
                if node.type == 'GROUP' and node.node_tree and node.node_tree.name == "Body Warm Shadow Ramp":
                    group_nodes = node.node_tree.nodes
                    print(f"group_nodes: {group_nodes}")
                    body_warm_ramp_node = group_nodes.get("Body_Warm_Ramp")
                    print(f"body_warm_ramp_node: {body_warm_ramp_node}")
                    if body_warm_ramp_node:
                        body_warm_ramp_node.image = image
                        body_warm_ramp_node.image.alpha_mode = 'CHANNEL_PACKED'                        

        if body2_lightmap_texture:
            # if body2_lightmap_texture exists, use it, else load image
            image = self.get_texture_image(body2_lightmap_texture, tex_file_path)
            # config body2_lightmap node
            body2_lightmap_node = nodes.get("Body_Lightmap_UV0")
            print(f"body2_lightmap_node: {body2_lightmap_node}")
            if body2_lightmap_node:
                body2_lightmap_node.image = image
                body2_lightmap_node.image.alpha_mode = 'CHANNEL_PACKED'
                body2_lightmap_node.image.colorspace_settings.name = 'Non-Color'
            
            body2_lightmap_node1 = nodes.get("Body_Lightmap_UV1")
            print(f"body2_lightmap_node1: {body2_lightmap_node1}")
            if body2_lightmap_node1:
                body2_lightmap_node1.image = image
                body2_lightmap_node1.image.alpha_mode = 'CHANNEL_PACKED'
                body2_lightmap_node1.image.colorspace_settings.name = 'Non-Color'
        
        # stockings ...
        
        # uvmap
        uvmap_node = nodes.get("UV Map.001")
        if uvmap_node and uvmap_node.type == 'UVMAP':
            uvmap_node.uv_map = "UVMap"
        
        # default value
        self.set_body_material_default_value(nodes)
        return material
    
    def set_body_material_default_value(self, nodes):
        """set group input param default value"""
        node = nodes.get("Group.006")
        if node and node.type == 'GROUP' and node.node_tree and node.node_tree.name == "StellarToon - Base":
            # set rim light thinkness
            node.inputs[61].default_value = 0.6
            print(f"node.inputs[63].default_value: {node.inputs[63].default_value}")
    
    def set_face_material_default_value(self, nodes):
        """set group input param default value"""
        node = nodes.get("Group.006")
        print(f"node: {node}")
        if node and node.type == 'GROUP' and node.node_tree and node.node_tree.name == "StellarToon - Face":
            # set warm shadow color 
            node.inputs[7].default_value = (0.947566, 0.713151, 0.713151, 1.0)
            print(f"node.inputs[7].default_value: {node.inputs[7].default_value}")
    
    def set_hair_material_default_value(self, nodes):
        """set group input param default value"""
        node = nodes.get("Group.006")
        if node and node.type == 'GROUP' and node.node_tree and node.node_tree.name == "StellarToon - Hair":
            # set rim light thinkness
            node.inputs[25].default_value = 1
            print(f"node.inputs[25].default_value: {node.inputs[25].default_value}")
    
    def assign_materials_from_preset(self, json_obj: dict) -> None:
        material_map = json_obj['material_map']
        role_name = json_obj["role_name"]
        # loop selected objects
        for obj in bpy.context.selected_objects:
            if obj.type == 'MESH':
                # Loop through all material slots
                for slot in obj.material_slots:
                    mesh_material = slot.material
                    if mesh_material:
                        mesh_material_name = mesh_material.name
                        print(f"Object: {obj.name}, Material Slot: {slot.name}, Material: {mesh_material_name}")                
                        # find mesh_material_name type in material_map
                        for key, items in material_map.items():
                            if mesh_material_name in items:
                                # get adding material name
                                adding_material_name = self.TEX_MATERIAL_MAP.get(key)
                                if adding_material_name:
                                    self.material_add_tex(obj, adding_material_name, None, key, role_name, mesh_material_name, slot)
                                    break
                # set mesh object slot default index
                obj.active_material_index = 0
    
    def assign_materials_from_json(self, json_obj: Dict[str, Any], tex_file_path: str) -> None:
        material_map = json_obj['material_map']
        role_name = json_obj["role_name"]
        # loop selected objects
        for obj in bpy.context.selected_objects:
            if obj.type == 'MESH':
                # Loop through all material slots
                for slot in obj.material_slots:
                    mesh_material = slot.material
                    if mesh_material:
                        mesh_material_name = mesh_material.name
                        print(f"Object: {obj.name}, Material Slot: {slot.name}, Material: {mesh_material_name}")                
                        # find mesh_material_name type in material_map
                        for key, items in material_map.items():
                            if mesh_material_name in items:
                                # get material name
                                adding_material_name = self.TEX_MATERIAL_MAP.get(key)
                                if adding_material_name:
                                    self.material_add_tex(obj, adding_material_name, tex_file_path, key, role_name, mesh_material_name, slot)
                                break
                        
    def join_group_mesh(self, json_obj: Dict[str, Any]) -> None:
        """join same group mesh"""
        selected_meshes = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']
        mesh_groups = {}
        # loop material_map
        for material_key, mesh_names in json_obj['material_map'].items():
            matched_meshes = []
            if len(mesh_names) > 1:
                for mesh in selected_meshes:
                    parts = mesh.name.split('_')
                    if(len(parts) > 1):
                        mesh_name_after = parts[1]
                        if any(name == mesh_name_after for name in mesh_names):
                            matched_meshes.append(mesh)
                # join meshes
                if matched_meshes:
                    mesh_groups[material_key] = matched_meshes
        # After collecting all groups, merge them
        for name, meshes in mesh_groups.items():
            self.merge_meshes(meshes, name)
        
    def merge_meshes(self, meshes: List[bpy.types.Object], name: str):
        """join meshes"""
        # clear selection
        bpy.ops.object.select_all(action='DESELECT')
        # reselect meshes
        for mesh in meshes:
            mesh.select_set(True)        
        
        bpy.context.view_layer.objects.active = meshes[0]  
        for mesh in meshes[1:]:  
            mesh.select_set(True)
        bpy.ops.object.join()
        bpy.context.object.name = name
    
    def set_child_of_constraints_to_heads(self, head_origin_name: str = 'Head Origin') -> None:
        """set child of constraints to heads"""
        # Find the 'Head Origin' empty object in the scene
        head_origin = bpy.data.objects.get(head_origin_name)
        if not head_origin:
            print("Error: No object named 'Head Origin' found.")
            return

        # calculate the number of armatures in the scene
        armatures = [obj for obj in bpy.data.objects if obj.type == 'ARMATURE']
        if len(armatures) > 1:
            print("Error: More than one armature found in the scene. Exiting without setting constraints.")
            return

        # if there's only one armature in the scene, continue
        if armatures:
            armature = armatures[0]
            # 约束 find or add 'Child Of' constraint
            child_of_constraint = next((c for c in head_origin.constraints if c.type == 'CHILD_OF' and not c.target), None)
            if not child_of_constraint:
                child_of_constraint = head_origin.constraints.new(type='CHILD_OF')
            # set
            child_of_constraint.target = armature
            
            if '頭' in armature.data.bones:
                child_of_constraint.subtarget = '頭'
                # set inverse
                bpy.context.view_layer.objects.active = head_origin
                head_origin.select_set(True)
                bpy.ops.constraint.childof_set_inverse(constraint="Child Of", owner='OBJECT')
                # move head origin to 頭 location
                head_bone = armature.data.bones['頭']
                head_origin.location = armature.matrix_world @ head_bone.head_local
                print(f"Constraint set successfully for armature {armature.name}.")
            else:
                print(f"No bone named '頭' found in armature {armature.name}.")
    
    def modify_emission_material(self, material_names: List[str]) -> None:
        """
        Modifies specified materials to connect a texture node's color output to the Principled BSDF's emission input.
        Args:
        material_names (List[str]): List of material names to be modified.
        """
        # Iterate over the list of material names provided
        for mat_name in material_names:
            # Attempt to retrieve the material by name
            material = bpy.data.materials.get(mat_name)
            
            # Check if the material exists and uses nodes
            if material and material.use_nodes:
                nodes = material.node_tree.nodes
                links = material.node_tree.links

                # Try to find the 'Mmd Base Tex' texture node and the 'Principled BSDF' node
                texture_node = next((node for node in nodes if node.type == 'TEX_IMAGE'), None)
                bsdf_node = next((node for node in nodes if node.type == 'BSDF_PRINCIPLED'), None)

                # Ensure both nodes were found
                if texture_node and bsdf_node:
                    # Check if the connection already exists
                    already_connected = any(link.to_node == bsdf_node and link.from_node == texture_node and link.from_socket == texture_node.outputs['Color'] and link.to_socket == bsdf_node.inputs['Emission'] for link in links)

                    # If not already connected, create a new link
                    if not already_connected:
                        color_output = texture_node.outputs['Color']  # Assuming the texture node has an output named 'Color'
                        emission_input = bsdf_node.inputs['Emission']  # Assuming BSDF has an input named 'Emission'
                        links.new(color_output, emission_input)
                        print(f"Connected texture color from '{texture_node.name}' to emission of '{bsdf_node.name}' in material '{mat_name}'")
                else:
                    print(f"Texture node or Principled BSDF node not found in material '{mat_name}'")
            else:
                print(f"Material '{mat_name}' not found or does not use nodes.")
    
    def modify_eyeshadow_material(self, material_names: List[str]) -> None:
        """
        Modifies eyeshadow materials to ensure they have a Transparency BSDF node set to a specific color and connected to the material output.
        
        Args:
            material_names (List[str]): List of material names to be modified.
        """
        # Iterate over the provided material names
        for mat_name in material_names:
            # Attempt to retrieve the material by name
            material = bpy.data.materials.get(mat_name)
            
            # Check if the material exists and uses nodes
            if material and material.use_nodes:
                nodes = material.node_tree.nodes
                links = material.node_tree.links

                # Try to find a Transparent BSDF node by type
                trans_bsdf_node = next((node for node in nodes if node.type == 'BSDF_TRANSPARENT'), None)

                # If no Transparent BSDF node exists, create one
                if not trans_bsdf_node:
                    trans_bsdf_node = nodes.new(type='ShaderNodeBsdfTransparent')
                    trans_bsdf_node.location = (300, 300)  # Position the new node slightly apart

                # Set the color and alpha of the Transparent BSDF node
                trans_bsdf_node.inputs['Color'].default_value = (0.031, 0.031, 0.031, 1)  # RGB and Alpha

                # Find the material output node
                material_output_node = next((node for node in nodes if node.type == 'OUTPUT_MATERIAL'), None)
                if material_output_node:
                    # Connect the Transparent BSDF node to the Surface input of the Material Output node
                    links.new(trans_bsdf_node.outputs['BSDF'], material_output_node.inputs['Surface'])
                    print(f"Modified material '{mat_name}' with a Transparent BSDF node.")
            else:
                print(f"Material '{mat_name}' not found or does not use nodes.")
        

class XJ_OP_HonkaiStarRailLightModifier(Operator):
    """add light vector modifier"""
    bl_idname = "xj.honkai_star_rail_add_light_modifier"
    bl_label = "add light vector modifier"
    bl_description = _("Add HonkaiStarRail light vector modifier")
    bl_options = {'REGISTER', 'UNDO'}
    
    light_modifier_name = "XJ-Light-Vector"
    light_vector_node_group_name = "Light Vectors"

    def execute(self, context):
        selected_meshes = [obj for obj in context.selected_objects if obj.type == 'MESH']
        
        if not selected_meshes:
            self.report({'WARNING'}, "No mesh objects selected.")
            return {'CANCELLED'}
        
        for mesh in selected_meshes:
            modifier = mesh.modifiers.get(self.light_modifier_name)
            if not modifier:
                modifier = mesh.modifiers.new(name=self.light_modifier_name, type='NODES')
                # control light vector modifier order
                if len(mesh.modifiers) > 2:
                    current_index = mesh.modifiers.find(self.light_modifier_name)
                    target_index = 1
                    while current_index > target_index:
                        bpy.ops.object.modifier_move_up(modifier=self.light_modifier_name)
                        current_index -= 1
            
            node_group = bpy.data.node_groups.get(self.light_vector_node_group_name)
            if not node_group:
                self.report({'WARNING'}, "Node group 'Light Vectors' not found.")
                return {'CANCELLED'}
            
            modifier.node_group = node_group
            # modifier["Input_3"] = "Main Light Direction"
            # modifier["Input_4"] = "Head Origin"
            # modifier["Input_5"] = "Head Forward"
            # modifier["Input_6"] = "Head Up"
            
            modifier["Output_7_attribute_name"] = "lightDir"
            modifier["Output_8_attribute_name"] = "headForward"
            modifier["Output_9_attribute_name"] = "headUp"

        self.report({'INFO'}, "Light vector modifiers added or updated.")
        return {'FINISHED'}

class XJ_OP_HonkaiStarRailLightModifierRemove(Operator):
    """remove light vector modifier"""
    bl_idname = "xj.honkai_star_rail_add_light_modifier_remove"
    bl_label = "remove light vector modifier"
    bl_description = _("Remove HonkaiStarRail light vector modifier")
    bl_options = {'REGISTER', 'UNDO'}
    
    light_modifier_name = "XJ-Light-Vector"
    
    def execute(self, context):
        selected_meshes = [obj for obj in context.selected_objects if obj.type == 'MESH']
        if not selected_meshes:
            self.report({'WARNING'}, "No mesh objects selected.")
            return {'CANCELLED'}
        
        for mesh in selected_meshes:
            modifier = mesh.modifiers.get(self.light_modifier_name)
            if modifier:
                mesh.modifiers.remove(modifier)
        
        self.report({'INFO'}, "Light vector modifiers removed.")
        return {'FINISHED'}
    
class XJ_OP_HonkaiStarRailOutline(Operator):
    """add outline"""
    bl_idname = "xj.honkai_star_rail_outline_add"
    bl_label = "Add StellarToon Outline"
    bl_description = _("Add Outline")
    bl_options = {'REGISTER', 'UNDO'}
    # outline node group
    node_group_name = "StellarToon - Outlines GN"
    # outline modifier name
    outline_modifier_name = "XJ-StellarToon - Outlines GN"
    # outline material
    OUTLINE_MATERIAL = [
        "StellarToon - Face Outlines",
        "StellarToon - Hair Outlines",
        "StellarToon - Base Outlines"
    ]
    # tex and outline material map
    TEX_OUTLINE_MATERIAL_MAP = {
        "face": "StellarToon - Face Outlines",
        "hair": "StellarToon - Hair Outlines",
        "body": "StellarToon - Base Outlines",
        "body1": "StellarToon - Base Outlines",
        "body2": "StellarToon - Base Outlines",
    }
    OUTLINE_COLOR = {
        "StellarToon - Face Outlines": {
            "_OutlineColor": {
                "r": 0.4528302,
                "g": 0.3268067,
                "b": 0.33669087,
                "a": 1.0
            }
        },
        "StellarToon - Hair Outlines": {
            "_OutlineColor0": {
                "r": 0,
                "g": 0,
                "b": 0,
                "a": 1.0
            }
        },
        "StellarToon - Base Outlines": {
            "_OutlineColor0": {
                "r": 0.4509804,
                "g": 0.3254902,
                "b": 0.3372549,
                "a": 1.0
            },
            "_OutlineColor1": {
                "r": 0.3033755,
                "g": 0.28511038,
                "b": 0.4056604,
                "a": 1.0
            },
            "_OutlineColor2": {
                "r": 0.2264151,
                "g": 0.15699537,
                "b": 0.15699537,
                "a": 1.0
            },
            "_OutlineColor3": {
                "r": 0.22365607,
                "g": 0.21555711,
                "b": 0.26415092,
                "a": 1.0
            },
            "_OutlineColor4": {
                "r": 0.3301887,
                "g": 0.2289516,
                "b": 0.23495466,
                "a": 1.0
            },
            "_OutlineColor5": {
                "r": 0.27358484,
                "g": 0.17163578,
                "b": 0.20986667,
                "a": 1.0
            },
            "_OutlineColor6": {
                "r": 0.23673905,
                "g": 0.26965,
                "b": 0.3773585,
                "a": 1.0
            },
            "_OutlineColor7": {
                "r": 0.0,
                "g": 0.0,
                "b": 0.0,
                "a": 1.0
            }
        }
    }
    

    def execute(self, context):
        blend_file_path = context.scene.xj_honkai_star_rail_blend_file_path
        # get all selected mesh objects
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        json_obj = None
        # is preset
        if context.scene.xj_honkai_star_rail_is_preset:
            json_obj = MaterialUtils.load_first_script_as_json(blend_file_path)
        else:
            json_obj = MaterialUtils.load_role_json_obj(context.scene.xj_honkai_star_rail_role_json_file_path)
        
        # iterate over selected mesh objects
        for obj in selected_objects:
            if obj.type == 'MESH':
                # self.paint_vertex_color(obj.data)
                self.material_add_outline(obj, json_obj["role_name"])
                # append outline material
                self.set_outline_mat_default_value(obj)
        return {'FINISHED'}
    
    def material_add_outline(self, obj: Mesh, role_name: str):
        geo_node_mod = None
        # loop modifiers
        for mod in obj.modifiers:
            if mod.type == 'NODES' and mod.node_group and mod.node_group.name == self.node_group_name:
                geo_node_mod = mod
                break
                    
        # add geometry node modifier
        if(geo_node_mod == None):
            geo_node_mod = obj.modifiers.new(name=self.outline_modifier_name, type='NODES')
        
        node_group = bpy.data.node_groups[self.node_group_name]
        if not node_group:
            self.report({'WARNING'}, f"Node group '{self.node_group_name}' not found.")
            return {'CANCELLED'}
        
        geo_node_mod.node_group = node_group
        # vertex color
        # input_color = node_group.inputs.get("Vertex Colors")
        # if input_color:
        #     self.set_up_modifier_vertex_color(geo_node_mod, obj)
        
        # set inputs
        input_thickness = node_group.inputs.get("Outline Thickness")
        # set outline thickness
        if input_thickness:
            geo_node_mod[input_thickness.identifier] = bpy.context.scene.xj_honkai_star_rail_outline_thickness
            
        for index, key in enumerate(self.TEX_OUTLINE_MATERIAL_MAP.keys()):
            mask_material_name = role_name + "_" + key
            mask_material = bpy.data.materials.get(mask_material_name)
            if not mask_material:
                self.report({'WARNING'}, f"Material '{mask_material_name}' not found.")
                continue
            
            outline_material_name = self.TEX_OUTLINE_MATERIAL_MAP[key]
            outline_material = bpy.data.materials.get(outline_material_name)
            
            if outline_material:
                # Set Outline Mask and Material
                input_mask_material = node_group.inputs.get(f"Outline {index + 1} Mask")
                input_outline_material = node_group.inputs.get(f"Outline {index + 1} Material")
                if input_mask_material:
                    geo_node_mod[input_mask_material.identifier] = mask_material
                if input_outline_material:
                    geo_node_mod[input_outline_material.identifier] = outline_material
    
    def set_up_modifier_vertex_color(self, modifier, mesh):
        if modifier[f'{NAME_OF_VERTEX_COLORS_INPUT}_use_attribute'] == 0:
            with bpy.context.temp_override(active_object=bpy.data.objects[mesh.name]):
                bpy.context.view_layer.objects.active = bpy.context.active_object

                if bpy.app.version >= (4,0,0):
                    bpy.ops.object.geometry_nodes_input_attribute_toggle(
                        input_name=NAME_OF_VERTEX_COLORS_INPUT, 
                        modifier_name=modifier.name
                    )
                else:
                    bpy.ops.object.geometry_nodes_input_attribute_toggle(
                        prop_path=f"[\"{NAME_OF_VERTEX_COLORS_INPUT}_use_attribute\"]", 
                        modifier_name=modifier.name
                    )

        modifier[f'{NAME_OF_VERTEX_COLORS_INPUT}_attribute_name'] = 'Col'
        
    def paint_vertex_color(self, mesh: Mesh):
        if not isinstance(mesh, Mesh):
            print("Provided object is not a Mesh")
            return
        # check if vertex color layer exists
        color_layer = mesh.vertex_colors.get('Col')
        if not color_layer:
            # if not, create it
            color_layer = mesh.vertex_colors.new(name='Col')
            print("Created new vertex color layer 'Col'")
        else:
            print("Using existing vertex color layer 'Col'")

        # set color value
        color_value = (1, 0.502, 0.502, 0.5)
        
        color_layer_index = 0
        for poly in mesh.polygons:
            for indice in poly.loop_indices:
                color_layer.data[color_layer_index].color = (1, 0.502, 0.502, 0.5)
                color_layer_index += 1
        print(f"Set vertex colors to {color_value} in layer 'Col'")
        
    def set_outline_mat_default_value(self, obj: Object):
        """Add outline materials to the object's material slots"""
        for mat_name in self.OUTLINE_MATERIAL:
            if not any(slot.material and slot.material.name == mat_name for slot in obj.material_slots):
                if bpy.data.materials.get(mat_name):
                    obj.data.materials.append(bpy.data.materials[mat_name])
        
        # Set the values for the node groups
        for mat_name in self.OUTLINE_MATERIAL:
            mat = bpy.data.materials.get(mat_name)
            if mat and mat.node_tree:
                nodes = mat.node_tree.nodes
                for node in nodes:
                    if node.type == 'GROUP' and node.name.startswith("Group.006"):
                        if mat_name == "StellarToon - Face Outlines":
                            outline_color = self.OUTLINE_COLOR[mat_name]["_OutlineColor"]
                            node.inputs[5].default_value = (outline_color["r"], outline_color["g"], outline_color["b"], outline_color["a"])
                        elif mat_name == "StellarToon - Hair Outlines":
                            outline_color = self.OUTLINE_COLOR[mat_name]["_OutlineColor0"]
                            node.inputs[5].default_value = (outline_color["r"], outline_color["g"], outline_color["b"], outline_color["a"])
                        elif mat_name == "StellarToon - Base Outlines":
                            for i in range(8):
                                outline_color_key = f"_OutlineColor{i}"
                                outline_color = self.OUTLINE_COLOR[mat_name][outline_color_key]
                                node.inputs[5 + i].default_value = (outline_color["r"], outline_color["g"], outline_color["b"], outline_color["a"])
        

class XJ_OP_HonkaiStarRailOutlineRemove(Operator):
    """remove outline"""
    bl_idname = "xj.honkai_star_rail_outline_remove"
    bl_label = "Remove StellarToon Outline"
    bl_description = _("Remove Outline")
    bl_options = {'REGISTER', 'UNDO'}

    # outline node group
    node_group_name = "StellarToon - Outlines GN"
    # outline modifier name
    outline_modifier_name = "XJ-StellarToon - Outlines GN"
    
    def execute(self, context):
        # get all selected objs
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']

        # loop objs mesh
        for obj in selected_objects:
            if obj.type == 'MESH':
                # remove outline modifier
                for mod in obj.modifiers:
                    if mod.type == 'NODES' and mod.name == self.outline_modifier_name:
                        obj.modifiers.remove(mod)
                        break

        return {'FINISHED'}


class XJ_OP_HonkaiStarRailRunEntireSetup(Operator):
    """run entire setup"""
    bl_idname = "xj.honkai_star_rail_run_entire_setup"
    bl_label = "Run Entire Setup"
    bl_description = _("Run Entire Setup for MMD Model")
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # Step 1: Start importing the MMD model
        bpy.ops.mmd_tools.import_model('INVOKE_DEFAULT')
        
        # Step 2: Set up a timer to check for the model import completion
        register(self.check_import_completion)
       
        return {'FINISHED'}
    
    def check_import_completion(self):
        # Check if the model has been imported by looking for specific objects
        if self.is_model_imported():
            for obj in bpy.context.selected_objects:
                if obj.type == 'EMPTY':
                    # active mesh object
                    self.select_mesh_children(obj)
            if bpy.context.view_layer.objects.active.type != 'MESH':
                self.report({'ERROR'}, "No mesh object selected.")
                return {'CANCELLED'}
            
            # Step 3: Convert the materials
            bpy.ops.mmd_tools.convert_materials()
            
            # Step 4: all processes
            bpy.ops.xj.honkai_star_rail_add()
            bpy.ops.xj.honkai_star_rail_add_light_modifier()
            bpy.ops.xj.honkai_star_rail_outline_add()
            
            # Import completed and operations finished
            return None  # Returning None stops the timer
            
        # If the model is not imported yet, check again after 0.5 seconds
        return 0.5
    
    def is_model_imported(self):
        # Check for specific objects that indicate the model has been imported
        for obj in bpy.context.selected_objects:
            if obj.type == 'EMPTY':
                return True
        return False
    
    def select_mesh_children(self, obj: Object) -> bool:
        """empty select mesh children
        Args:
            obj (Object): empty
        """
        # Iterate through the children of the object
        for child in obj.children:
            # Check if the child is a mesh
            if child.type == 'MESH' and hasattr(obj, 'mmd_root'):
                # Select the mesh
                child.select_set(True)
                bpy.context.view_layer.objects.active = child
                return True
            # Recursively check the child's children
            self.select_mesh_children(child)