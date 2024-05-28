# -*- coding: utf-8 -*-
import bpy
import json
from typing import Optional, Dict, Any

class MaterialUtils:
    @staticmethod
    def get_base_texture_image(mesh):
        """从mesh对象的材质节点中获取纹理图片"""
        images = []
        # 确保mesh对象有材质，并且使用节点
        for slot in mesh.material_slots:
            if slot.material and slot.material.use_nodes:
                nodes = slot.material.node_tree.nodes
                for node in nodes:
                    if node.type == 'TEX_IMAGE':
                        if hasattr(node, 'image') and node.image is not None:
                            images.append(node.image)
        
        # 根据收集到的图像数量处理返回值
        if not images:
            return None
        elif len(images) > 1:
            print(f"{mesh.name} image size > 1")
            return images[0]
        else:
            return images[0]
    
    @staticmethod
    def create_toon_material_with_nodes(mesh):
        # 创建新材质
        mat = bpy.data.materials.new(name=mesh.name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes

        # 清除默认节点
        nodes.clear()

        # 添加所需的节点
        tex_node = nodes.new(type='ShaderNodeTexImage')
        tex_node.image = MaterialUtils.get_base_texture_image(mesh)
        tex_node.image.alpha_mode = 'STRAIGHT'
        tex_node.extension = 'EXTEND'

        mix_node = nodes.new(type='ShaderNodeMixRGB')
        mix_node.blend_type = 'MULTIPLY'
        mix_node.inputs['Fac'].default_value = 1.0
        mix_node.inputs['Color2'].default_value = (1.0, 1.0, 1.0, 1.0)
    
        goo_node = nodes.new(type='ShaderNodeGroup')
        goo_node.node_tree = bpy.data.node_groups.get('GooEngineToon')

        output_node = nodes.new(type='ShaderNodeOutputMaterial')

        # 连接节点
        links = mat.node_tree.links
        links.new(tex_node.outputs['Color'], mix_node.inputs['Color1'])
        links.new(tex_node.outputs['Color'], goo_node.inputs['LitColor'])
        links.new(mix_node.outputs['Color'], goo_node.inputs['ShadowColor'])
        links.new(goo_node.outputs['Color'], output_node.inputs['Surface'])

        tex_node.location = (-300, 200)
        mix_node.location = (100, 200)
        goo_node.location = (500, 200)
        output_node.location = (700, 200)
        return mat
    
    @staticmethod
    def apply_material_to_mesh(mesh, mat):
        """
        将给定的材质应用到指定的网格对象上
        """
        # 检查网格对象是否已经有材质插槽，如果没有则添加
        if len(mesh.data.materials) == 0:
            mesh.data.materials.append(mat)
        else:
            mesh.data.materials[0] = mat
    
    @staticmethod
    def print_selected_material_node_info(mesh):
        # 确保传入的对象是一个mesh，并且有材质
        if not mesh or not mesh.active_material:
            print("No active material found or invalid mesh object.")
            return
        mat = mesh.active_material
        # 确保材质使用节点
        if not mat.use_nodes:
            print("Active material does not use nodes.")
            return
        nodes = mat.node_tree.nodes
        active_node = None
        # 查找用户当前选中的节点
        for node in nodes:
            if node.select:
                active_node = node
                break
        if not active_node:
            print("No node is selected.")
            return
        # 打印选中节点的信息
        print(f"Selected Node: {active_node.name} (Type: {active_node.type})")
        print("Modifiable Properties:")
        # 打印所有可修改的属性
        for prop_name, prop in active_node.bl_rna.properties.items():
            if not prop.is_readonly:
                print(f"  - {prop_name}: {getattr(active_node, prop_name)}")    

    @staticmethod
    def check_node_group_exist(node_group_name):
        """检查是否存在包含特定名称的节点组"""
        for node_group in bpy.data.node_groups:
            if node_group_name in node_group.name:
                print(f"Found node group: {node_group.name}")
                return True
        print(f"No node group found containing {node_group_name}.")
        return False
    
    @staticmethod
    def print_geometry_node_group_inputs(node_group_name):
        """
        打印指定几何节点组的所有组输入参数信息。
        :param node_group_name: 要查找的几何节点组的名称。
        """
        # 遍历所有节点组
        for node_group in bpy.data.node_groups:
            # 检查节点组名称是否匹配
            if node_group.name == node_group_name:
                print(f"输入参数信息 for {node_group_name}:")
                # 检查该节点组是否是几何节点组
                if node_group.type == 'GEOMETRY':
                    # 遍历节点组中的所有节点，寻找组输入节点
                    for node in node_group.nodes:
                        if node.type == 'GROUP_INPUT':
                            # 遍历组输入节点的所有输出，这些输出代表节点组的输入参数
                            for output in node.outputs:
                                # 检查输出是否有 default_value 属性
                                if hasattr(output, 'default_value'):
                                    print(f"  输入参数 {output.name}: 类型 {output.type}, 默认值 {output.default_value}")
                                else:
                                    print(f"  输入参数 {output.name}: 类型 {output.type}, 无默认值")
                        if node.type == 'GROUP_OUTPUT':
                            for inputs in node.inputs:
                                if hasattr(inputs, 'default_value'):
                                    print(f"  输出参数 {inputs.name}: 类型 {inputs.type}, 默认值 {inputs.default_value}")
                                else:
                                    print(f"  输出参数 {inputs.name}: 类型 {inputs.type}, 无默认值")            
                else:
                    print("指定的节点组不是几何节点组。")
                break
        else:
            print(f"没有找到名称为 '{node_group_name}' 的节点组。")
            
    @staticmethod        
    def print_node_tree_details(node_tree_name):
        """Print details of all nodes in a given node tree."""
        # 获取指定的节点树
        node_tree = bpy.data.node_groups.get(node_tree_name)
        
        if not node_tree:
            print(f"No node tree found with the name '{node_tree_name}'.")
            return
        
        print(f"Details of Node Tree: {node_tree_name}")
        
        # 遍历节点树中的所有节点
        for node in node_tree.nodes:
            print(f"\nNode Name: {node.name}")
            print(f"Node Type: {node.type}")
            
            # 打印节点的内部属性
            for prop_name, prop_value in node.bl_rna.properties.items():
                if prop_name not in ['rna_type', 'input_template', 'output_template']:
                    print(f"{prop_name}: {getattr(node, prop_name, 'N/A')}")          

    @staticmethod
    def load_role_json_obj(filepath):
        """get json file"""
        with open(filepath, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data

    @staticmethod
    def load_first_script_as_json(blend_filepath: str) -> Optional[Dict[str, Any]]:
        """
        from specified .blend file load first script as json
        :param blend_filepath: .blend file full path
        :return: json object/None
        """
        first_json_text_name = None
        # check json config exists
        json_texts_exists = [text.name for text in bpy.data.texts if text.name.endswith(".json")]
        try:
            with bpy.data.libraries.load(blend_filepath, link=False) as (data_from, data_to):
                if data_from.texts:
                    json_texts = [text for text in data_from.texts if text.endswith(".json")]
                    if not json_texts:
                        print(f"json text not found in {blend_filepath}")
                        return None
                    first_json_text_name = json_texts[0]
                    if first_json_text_name not in json_texts_exists:
                        data_to.texts = [first_json_text_name]
                else:
                    print("blend file has no text data")
                    return None
        except Exception as e:
            print(f"load blend file error：{e}")
            return None
        
        # get first text data
        imported_text = bpy.data.texts[first_json_text_name]
        # parse json
        try:
            json_object = json.loads(imported_text.as_string())
            return json_object
        except json.JSONDecodeError as e:
            print(f"parse json error：{e}")
            return None
    
    @staticmethod
    def set_gooengine_base_render_set():
        """gooengine_base_render_set"""
        # view_transform: Standard
        bpy.context.scene.view_settings.view_transform = 'Standard'
        # Screen Space Refraction: On
        bpy.context.scene.eevee.use_ssr = True
        bpy.context.scene.eevee.use_ssr_refraction = True