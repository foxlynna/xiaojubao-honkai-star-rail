# -*- coding: utf-8 -*-
import bpy
import json
import os

class CacheParams:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    param_json_file = os.path.join(current_dir, "param.json")
    
    """cache"""
    def __init__(self):
        self.cache = {}
        self.load_cache()
    
    def load_cache(self):
        """from json read cache data"""
        if os.path.exists(self.param_json_file):
            try:
                with open(self.param_json_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error reading {self.param_json_file}：{e}")
                self.cache = {}        

    def get(self, key, default=None):
        return self.cache.get(key, default)

    def set(self, name, value):
        self.cache[name] = value
        
    def write(self, key, value):
        if not value:
            return
        self.cache[key] = value
        try:
            with open(self.param_json_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=4)
                print(f"Write {self.param_json_file} successfully.")
        except IOError as e:
            print(f"Error writing {self.param_json_file}：{e}")     