import bpy

class Button_BakeSingle(bpy.types.Panel):
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

        row = layout.row()
        row.label(text="Hello world!", icon='WORLD_DATA')

        row = layout.row()
        row.label(text="Active object is: " + obj.name)
        row = layout.row()
        row.prop(obj, "name")

        row = layout.row()
        row.operator("superbaker.bake_single_object")
