import bpy

class SuperBaker_BakeSingleObject(bpy.types.Operator):
    bl_idname = "superbaker.bake_single_object"
    bl_label = "Bake Single Object (SuperBaker)"
    bl_description = "Bake Single Object"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        print("Test")
        return {'RUNNING_MODAL'}