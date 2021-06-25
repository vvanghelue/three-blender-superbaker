
# bl_info = {
#     'name': 'SuperBaker',
#     'description': 'Zero-dependency lightmaps baker',
#     'author': 'Vincent Van Ghelue',
#     'version': (0, 1),
#     'blender': (2, 92, 0),
#     'location': 'View3D',
#     'category': 'Object'
# }


bl_info = {
    'name': 'SuperBaker',
    'description': 'Zero-dependency lightweight lightmaps baker',
    'author': 'Vincent Van Ghelue',
    'version': (0, 0, 0, 0),
    'blender': (2, 90, 0),
    'location': 'View3D',
    'category': '3D View'
}

import bpy
from . bake_single_object import SuperBaker_BakeSingleObject
from . ui import SuperBakerUI

# print(SuperBaker_BakeSingleObject)
# print(Button_BakeSingle)

classes = (
    SuperBaker_BakeSingleObject,
    SuperBakerUI
)

register, unregister  = bpy.utils.register_classes_factory(classes)

if __name__ == "__main__":
    register()