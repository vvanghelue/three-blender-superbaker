import bpy

from bpy.props import *

DEFAULT_LIGHTMAP_RESOLUTION = '256'

class SuperBakerSceneProperties(bpy.types.PropertyGroup):
    default_lightmap_resolution : bpy.props.EnumProperty(
        items = [   
            ('64', '64', ''),
            ('256', '256', ''),
            ('512', '512', ''),
            ('1024', '1024', ''),
            ('2048', '2048', ''),
        ],
        name = "Default Lightmap Resolution", 
        description="For all objects", 
        default=DEFAULT_LIGHTMAP_RESOLUTION
    )
                
class SuperBakerObjectProperties(bpy.types.PropertyGroup):
    baking_enabled : bpy.props.BoolProperty(
        name="Baking enabled", 
        description="Enable baking for object", 
        default=True)

    lightmap_resolution : bpy.props.EnumProperty(
        items = [   
            ('64', '64', ''),
            ('256', '256', ''),
            ('512', '512', ''),
            ('1024', '1024', ''),
            ('2048', '2048', ''),
        ],
        name = "Lightmap Resolution", 
        description="Select the lightmap resolution", 
        default=DEFAULT_LIGHTMAP_RESOLUTION
    )

class SuperBakerUI(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "SuperBakser"
    bl_idname = "OBJECT_PT_superbaker"
    
    #bl_space_type = 'PROPERTIES'
    #bl_region_type = 'WINDOW'
    #bl_context = "object"
    
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Tool"
    bl_label = "SuperBaker"

    def draw(self, context):
        layout = self.layout
        obj = context.object
        # box = layout.box()
        # col = box.column()

        # row = layout.row()
        # row.label(text='Active Object : ' + obj.name)
        # row.label(text=obj.name, icon='TEXTURE')

        # little separator
        row = layout.row()
        row.scale_y = 0.3
        row.label(text="")


        if obj.type == "MESH":
            row = layout.row(align=True)
            # row.label(text="For active object (" + obj.name + ")", icon='MESH_CUBE')
            row.label(text=obj.name, icon='SETTINGS')

            if len(obj.data.materials) == 0:
                row = layout.row(align=True)
                row.label(text="Not bakable (no material found)")
            else:
                # row = layout.row()
                # row.prop(obj, "name")

                # row = layout.row(align=True)
                # row = col.split(factor=0.6, align=True)
                row = layout.row(align=True)
                # row.label(text='Baking Enabled')
                row.prop(obj.SuperBakerObjectProperties, "baking_enabled")

                row = layout.row(align=True)
                row.prop(obj.SuperBakerObjectProperties, "lightmap_resolution", expand=False)

                row = layout.row()
                row.operator("superbaker.bake_selected_objects", text="Bake selected objects : (" + str(len(bpy.context.selected_objects)) + ")")

        row = layout.row()
        row.scale_y = 2
        row.operator("superbaker.bake_all_scene_objects", text="Bake all", icon='SHADERFX')

        row = layout.row()
        row.scale_y = 2
        row.operator("superbaker.toggle_lightmaps_preview", text="Show preview", icon='HIDE_OFF')

        # little separator
        row = layout.row()
        row.scale_y = 0.3
        row.label(text="")

        row = layout.row(align=True)
        row.label(text="For all scene :" , icon='WORLD')
        
        row = layout.row(align=True)
        row.prop(context.scene.SuperBakerSceneProperties, "default_lightmap_resolution", expand=False)
        
        row = layout.row()
        selectedCount = str(len(bpy.context.selected_objects))
        row.operator("superbaker.apply_res_to_selected", text="Apply default to selected (" + selectedCount + ")")

        row = layout.row()
        row.scale_y = 2
        row.operator("superbaker.export_lightmaps", icon='EXPORT')


# register, unregister  = bpy.utils.register_classes_factory([Button_BakeSingle])

def register():
    bpy.utils.register_class(SuperBakerObjectProperties)
    bpy.types.Object.SuperBakerObjectProperties = bpy.props.PointerProperty(type=SuperBakerObjectProperties)
    bpy.utils.register_class(SuperBakerSceneProperties)
    bpy.types.Scene.SuperBakerSceneProperties = bpy.props.PointerProperty(type=SuperBakerSceneProperties)
    bpy.utils.register_class(SuperBakerUI)

def unregister():
    del bpy.types.Object.SuperBakerObjectProperties
    bpy.utils.unregister_class(SuperBakerObjectProperties)
    del bpy.types.Scene.SuperBakerSceneProperties
    bpy.utils.unregister_class(SuperBakerSceneProperties)
    bpy.utils.unregister_class(SuperBakerUI)


if __name__ == "__main__":
    register()