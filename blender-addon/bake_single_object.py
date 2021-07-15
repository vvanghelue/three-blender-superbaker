import bpy
import time
import string
import random
import os


EXPORT_FOLDER = bpy.path.abspath("//") + 'superbaker_lightmaps'
TMP_IMAGE_NAME = 'superbaker_tmp_image.png'
TMP_IMAGE_PATH = bpy.path.abspath("//") + TMP_IMAGE_NAME

initialState = { 'engine': '', 'resolution_x': '', 'resolution_y': '' }

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def findExistingLightmapTextureNode(material):
    for node in material.node_tree.nodes:
        if node.label == "superbaker_lightmap":
            return node
    return False

#object = bpy.context.selected_objects[0]
#print(getOrCreateLightmapTextureNode(object))

def beforeBaking():
    initialState['render_engine'] = bpy.context.scene.render.engine
    initialState['render_resolution_x'] = bpy.context.scene.render.resolution_x
    initialState['render_resolution_y'] = bpy.context.scene.render.resolution_y
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.render.resolution_y = 4
    bpy.context.scene.render.resolution_y = 4

    bpy.context.scene.render.image_settings.file_format = "PNG"
    bpy.context.scene.render.image_settings.color_depth = '8'

    return

def afterBaking():
    return
    bpy.context.scene.render.engine = initialState['render_engine']
    bpy.context.scene.render.resolution_x = initialState['render_resolution_x']
    bpy.context.scene.render.resolution_y = initialState['render_resolution_y']
    return

def doesDenoiseSetupExist():
    if bpy.context.scene.use_nodes == False:
        return False
    for node in bpy.context.scene.node_tree.nodes:
        if node.type == 'DENOISE':
            return True
    return False

def createDenoiseSetup():
    bpy.context.scene.use_nodes = True
    viewerNode = bpy.context.scene.node_tree.nodes.new('CompositorNodeViewer')
    imageNode = bpy.context.scene.node_tree.nodes.new('CompositorNodeImage')
    imageNode.label = "sb_denoizing_image_slot"
    denoiseNode = bpy.context.scene.node_tree.nodes.new('CompositorNodeDenoise')
    
    bpy.context.scene.node_tree.links.new(
    imageNode.outputs['Image'],
        denoiseNode.inputs['Image']
    )
    bpy.context.scene.node_tree.links.new(
        denoiseNode.outputs['Image'],
        viewerNode.inputs['Image']
    )

def secondUVMapExists(object):
    uvLayers = object.data.uv_layers.items()
    return len(uvLayers) > 1

def createSecondUVMap(object):
    print('## Creating lightmap UV map for object :', object)
    object.select_set(True)
    lm = object.data.uv_layers.new(name="sb_lightmap")
    lm.active = True
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project()
    bpy.ops.object.editmode_toggle()
    return False

def findExistingLightmapTextureNode(material):
    for node in material.node_tree.nodes:
        if node.label == "superbaker_lightmap":
            return node
    return False

def getOrCreateLightmapTextureNode(object, material):
    lightmapImageNode = findExistingLightmapTextureNode(material)
    if (lightmapImageNode == False):
        lightmapImageName = 'sb_lightmap_' + id_generator()
        bpy.ops.image.new(name=lightmapImageName, width=32, height=32)
        lightmapImage = bpy.data.images.get(lightmapImageName)
        lightmapImage.alpha_mode = "STRAIGHT"

        lightmapImageNode = material.node_tree.nodes.new('ShaderNodeTexImage')
        lightmapImageNode.image = lightmapImage
        lightmapImageNode.label = 'superbaker_lightmap'
        lightmapImageNode.location = (-600,-100)

    resolution = int(object.SuperBakerObjectProperties.lightmap_resolution)
    lightmapImageNode.image.scale(resolution, resolution)
    return lightmapImageNode

def reloadDenoisedImageSlot(resolution):
    for image in bpy.data.images:
        if image.name == TMP_IMAGE_NAME:
            #image.scale(resolution, resolution)
            image.reload()
            return
    bpy.data.images.load(TMP_IMAGE_PATH)

def bakeObjects(objects):
    beforeBaking()

    if doesDenoiseSetupExist() == False:
        print("No denoise setup found, creating one...")
        createDenoiseSetup()

    for object in objects:
        if object.type == "MESH":
            if object.SuperBakerObjectProperties.baking_enabled == False:
                continue

            if len(object.data.materials) == 0:
                continue

            print('# baking object', object)

            if secondUVMapExists(object) is False:
                print('## Object has no lightmap, creating it...')
                createSecondUVMap(object)

            
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            object.select_set(True)
            bpy.context.view_layer.objects.active = object

            baseColorNodesToReconnect = []
            for material in object.data.materials:
                if material == None:
                    continue
            
                if material.use_nodes:
                    nodeToDisconnect = None
                    shader = None
                    for node in material.node_tree.nodes:
                        if node.name == "Principled BSDF":
                            shader = node
                            baseColorLinks = shader.inputs["Base Color"].links
                            if len(baseColorLinks) > 0:
                                nodeToDisconnect = baseColorLinks[0].from_node
                
                    if nodeToDisconnect != None:
                        material.node_tree.nodes.active = nodeToDisconnect
                        print('  Disconnect base color')
                        for link in material.node_tree.links:
                            if link.from_node == nodeToDisconnect and link.to_node == shader:
                                print('  Remove link')
                                material.node_tree.links.remove(link)
                        print('  Add node to reconnect list')
                        baseColorNodesToReconnect.append({
                            "node": nodeToDisconnect,
                            "shader": shader,
                            "material": material
                        })

            for material in object.data.materials:
                
                print('  Preparing material ', material)

                baseColorNode = None
                principledShaderNode = None
                
                if material == None:
                    print('  no material found, continue')
                    continue
                
                if material.use_nodes:
                    for node in material.node_tree.nodes:
                        if node.name == "Principled BSDF":
                            print('  found a Principled material')
                            principledShaderNode = node
                            baseColorLinks = principledShaderNode.inputs["Base Color"].links
                            if len(baseColorLinks) > 0:
                                print('  found Base Color material')
                                baseColorNode = baseColorLinks[0].from_node

                if principledShaderNode == None:
                    print("  No principledShader found, continue")
                    continue

                lightmapImageNode = getOrCreateLightmapTextureNode(object, material)

                # unselect all nodes
                for node in material.node_tree.nodes:
                    node.select = False

                # select image node
                lightmapImageNode.select = True
                material.node_tree.nodes.active = lightmapImageNode

                # select proper UV
                uvLayers = object.data.uv_layers.items()
                if len(uvLayers) > 1:
                    name, layer = uvLayers[1]
                    layer.active = True
                    layer.active_render = True
                
                bpy.ops.object.bake(type='COMBINED', pass_filter={'DIFFUSE', 'DIRECT', 'INDIRECT'}, target='IMAGE_TEXTURES')

                #print('####### DENOISING')
                # denoising
                if True:
                    for node in bpy.context.scene.node_tree.nodes:
                        #continue
                        #print(node, node.label)
                        if node.label == 'sb_denoizing_image_slot':
                            #denoisingImageNode = node
                            #print(node, node.label)
                            print('## APPLY DENOISING')
                            node.image = lightmapImageNode.image
                            # hack to force update
                            bpy.ops.render.render(animation=False, write_still=False, use_viewport=False, layer="", scene="")
                            bpy.data.images['Viewer Node'].save_render(TMP_IMAGE_PATH)
                            # bpy.data.images['Viewer Node'].save_render()
                            time.sleep(1)

                            resolution = int(object.SuperBakerObjectProperties.lightmap_resolution)
                            reloadDenoisedImageSlot(resolution)

                            # lightmapImageNode.image.replace(filepath=TMP_IMAGE_PATH, relative_path=False)
                            # lightmapImageNode.image.filepath = TMP_IMAGE_PATH
                            # lightmapImageNode.image.reload()
                            lightmapImageNode.image.pixels = bpy.data.images[TMP_IMAGE_NAME].pixels[:]
                            
                            #lightmapImageNode.image.reload()
                            # lightmapImageNode.image.file_format = bpy.data.images['Viewer Node'].file_format
                            # lightmapImageNode.image.depth = bpy.data.images['Viewer Node'].depth
                            # lightmapImageNode.image.pixels = bpy.data.images['Viewer Node'].pixels[:]
                            # lightmapImageNode.image.update()
                            #lightmapImageNode.image.reload()
                            #jsonMapping['materials'].append({ "lightmapFile": bakedImageName })

                # make uv1 active back
                if len(uvLayers) > 1:
                    name, layer = uvLayers[0]
                    layer.active = True
                    layer.active_render = True
                
            print('')
    afterBaking()
    return

class SetResolutionToAll(bpy.types.Operator):
    bl_idname = "superbaker.apply_res_to_selected"
    bl_label = "SetResolutionToAll"
    bl_description = "SetResolutionToAll"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        defaultResolution = context.scene.SuperBakerSceneProperties.default_lightmap_resolution
        print("[SuperBaker] Set default resolution to all objects")
        # for object in bpy.data.objects:
        for object in bpy.context.selected_objects:
            object.SuperBakerObjectProperties.lightmap_resolution = defaultResolution
        return {'RUNNING_MODAL'}

class BakeAllSceneObjects(bpy.types.Operator):
    bl_idname = "superbaker.bake_all_scene_objects"
    bl_label = "Bake All Scene Objects"
    bl_description = "Bake All Scene Objects"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        print("BakeAllSceneObjects")
        bakeObjects(bpy.data.objects)
        return {'RUNNING_MODAL'}


class BakeSelectedObjects(bpy.types.Operator):
    bl_idname = "superbaker.bake_selected_objects"
    bl_label = "Bake Selected Objects"
    bl_description = "Bake Selected Objects"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        print("BakeSelectedObjects")
        bakeObjects(bpy.context.selected_objects)
        # print(
        #     int(context.object.SuperBakerObjectProperties.lightmap_resolution)
        # )
        # print(
        #     int(context.scene.SuperBakerSceneProperties.default_lightmap_resolution)
        # )
        # time.sleep(15)
        return {'RUNNING_MODAL'}


class ToggleLightmapsPreview(bpy.types.Operator):
    bl_idname = "superbaker.toggle_lightmaps_preview"
    bl_label = "Toggle Preview"
    bl_description = "Toggle Preview"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        print("ToggleLightmapsPreview")
        # bpy.context.space_data.shading.use_scene_world = True
        # bpy.context.space_data.shading.type = 'MATERIAL'

        # set material shading
        for area in bpy.context.screen.areas: 
            if area.type == 'VIEW_3D':
                for space in area.spaces: 
                    if space.type == 'VIEW_3D':
                        space.shading.type = 'MATERIAL'
                        
        # Set nodes
        for object in bpy.data.objects:
            if object.type == "MESH":
                for material in object.data.materials:
                    if material.use_nodes:
                        nodeToDisconnect = None
                        shader = None
                        for node in material.node_tree.nodes:
                            if node.type == 'OUTPUT_MATERIAL':


        return {'RUNNING_MODAL'}


class ExportLightmaps(bpy.types.Operator):
    bl_idname = "superbaker.export_lightmaps"
    bl_label = "Export lightmaps"
    bl_description = "Export lightmaps"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        print("ExportLightmaps")
        
        # create folder if not exists
        if not os.path.exists(EXPORT_FOLDER):
            os.makedirs(EXPORT_FOLDER)

        # remove all files inside folder
        for file in os.scandir(EXPORT_FOLDER):
            os.remove(file.path)

        jsonMappings = []

        for object in bpy.data.objects:
            if object.type == 'MESH':
                jsonMapping = {
                    "objectName": object.name
                }
                jsonMapping['materials'] = []

                for material in object.data.materials:
                    if material == None:
                        continue
                    if material.use_nodes:
                        nodeToDisconnect = None
                        shader = None
                        for node in material.node_tree.nodes:
                            if (node.label == "superbaker_lightmap"):
                                print(node)
                                print(material.name)

        return {'RUNNING_MODAL'}

# register, unregister  = bpy.utils.register_classes_factory([SuperBaker_BakeSingleObject])

# if __name__ == "__main__":
#     register()

def register():
    bpy.utils.register_class(BakeSelectedObjects)
    bpy.utils.register_class(BakeAllSceneObjects)
    bpy.utils.register_class(ToggleLightmapsPreview)
    bpy.utils.register_class(ExportLightmaps)
    bpy.utils.register_class(SetResolutionToAll)
    
    

def unregister():
    bpy.utils.unregister_class(BakeSelectedObjects)
    bpy.utils.unregister_class(BakeAllSceneObjects)
    bpy.utils.unregister_class(ToggleLightmapsPreview)
    bpy.utils.unregister_class(ExportLightmaps)
    bpy.utils.unregister_class(SetResolutionToAll)

if __name__ == "__main__":
    register()