import bpy
import sys
import string
import random
import json
import os, glob
import zipfile

# scale down resolution, for update hack
bpy.context.scene.render.engine = 'CYCLES'
bpy.context.scene.render.resolution_x = 4
bpy.context.scene.render.resolution_y = 4
 
BAKE_OUTPUT_FOLDER = bpy.path.abspath("//") + '_baked_lightmaps'
OUTPUT_FORMAT = 'png' # 'exr'

DEFAULT_RESOLUTION = 128

if OUTPUT_FORMAT == 'exr':
    bpy.context.scene.render.image_settings.file_format = "OPEN_EXR"
    bpy.context.scene.render.image_settings.color_depth = '32'

if OUTPUT_FORMAT == 'png':
    bpy.context.scene.render.image_settings.file_format = "PNG"
    bpy.context.scene.render.image_settings.color_depth = '8'

# create folder if not exists
if not os.path.exists(BAKE_OUTPUT_FOLDER):
    os.makedirs(BAKE_OUTPUT_FOLDER)

# remove all files inside folder
for file in os.scandir(BAKE_OUTPUT_FOLDER):
    os.remove(file.path)

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def lightmapExists(object):
    uvLayers = object.data.uv_layers.items()
    return len(uvLayers) > 1

def createLightmap(object):
    print('Creating lightmap for object :', object)
    object.select_set(True)
    lm = object.data.uv_layers.new(name="LightMap")
    lm.active = True
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project()
    bpy.ops.object.editmode_toggle()
    return False

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
    denoiseNode = bpy.context.scene.node_tree.nodes.new('CompositorNodeDenoise')
    
    bpy.context.scene.node_tree.links.new(
    imageNode.outputs['Image'],
        denoiseNode.inputs['Image']
    )
    bpy.context.scene.node_tree.links.new(
        denoiseNode.outputs['Image'],
        viewerNode.inputs['Image']
    )
        
if doesDenoiseSetupExist() == False:
    print("No denoise setup found, creating one...")
    createDenoiseSetup()


jsonMappings = []

for object in bpy.data.objects:
    bpy.ops.object.mode_set(mode='OBJECT')

    if object.type == 'MESH':
        #if object.name != "murs salle de bain":
        #if object.name != "murs salon cuisine":
        #    continue

        print("")
        print("Try object : " + object.name)

        if object.hide_get():
            print("  object not visible, continue")
            continue
            
        dontBake = object.get("dont_bake", 0)
        if dontBake != 0:
            print("  dont_bake = 1, continue")
            continue

        print("  Baking : " + object.name)

        if lightmapExists(object) is False:
            print('Object has no lightmap, creating it...')
            createLightmap(object)

        bpy.ops.object.select_all(action='DESELECT')
        #activeObject = bpy.data.objects.get('Plane')
        object.select_set(True)

        if len(object.data.materials) == 0:
            print('  no material found, continue')
            continue

        # select object
        bpy.context.view_layer.objects.active = object

        jsonMapping = {
            "objectName": object.name
        }
        jsonMapping['materials'] = []

        baseColorNodesToReconnect = []

        # find image nodes to disconnect
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

        #for material in [object.data.materials[0]]:
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

            # add new image texture
            bakedImageName = "Baked_Texture_" + id_generator() + "." + OUTPUT_FORMAT
            bakedImagePath = BAKE_OUTPUT_FOLDER + "/" + bakedImageName
            resolution = object.get("lightmap_resolution", DEFAULT_RESOLUTION)
            resolution = max(DEFAULT_RESOLUTION, resolution)
            resolution = DEFAULT_RESOLUTION
            print('  creating image with RESOLUTION : ' + str(resolution))
            bpy.ops.image.new(name=bakedImageName, width=resolution, height=resolution)
            bakedImage = bpy.data.images.get(bakedImageName)
            bakedImage.alpha_mode = "STRAIGHT"
            bakedImage.filepath = bakedImagePath
            bakedImage.save()
            print('  Create image ' + bakedImageName)
            
            # create image node
            bakedImageNode = material.node_tree.nodes.new('ShaderNodeTexImage')
            bakedImageNode.image = bakedImage
            
            # unselect all nodes
            for node in material.node_tree.nodes:
                node.select = False

            # select image node
            bakedImageNode.select = True
            material.node_tree.nodes.active = bakedImageNode

            # select proper UV
            uvLayers = object.data.uv_layers.items()
            if len(uvLayers) > 1:
                name, layer = uvLayers[1]
                layer.active = True
                layer.active_render = True

            # bake lightmap
            print("  Bake...")
            bpy.ops.object.bake(type='COMBINED', pass_filter={'DIFFUSE', 'DIRECT', 'INDIRECT'}, target='IMAGE_TEXTURES')

            # denoising
            for node in bpy.context.scene.node_tree.nodes:
                if node.name == 'Image':
                    node.image = bakedImage
                    # hack to force update
                    bpy.ops.render.render(animation=False, write_still=False, use_viewport=False, layer="", scene="")
                    bpy.data.images['Viewer Node'].save_render(bakedImagePath)
                    bakedImage.reload()

                    jsonMapping['materials'].append({ "lightmapFile": bakedImageName })

            # make uv1 active back
            if len(uvLayers) > 1:
                name, layer = uvLayers[0]
                layer.active = True
                layer.active_render = True

            # remove temp node
            material.node_tree.nodes.remove(bakedImageNode)

            # remove images 
            bpy.data.images.remove(bakedImage)


        # reconnect Base Color nodes
        for nodeToReconnect in baseColorNodesToReconnect:
            #continue
            print('')
            print('')
            print('  Reconnect base color image node', nodeToReconnect)
            material.node_tree.nodes.active = nodeToReconnect['node']
            nodeToReconnect['material'].node_tree.links.new(
                nodeToReconnect['node'].outputs['Color'],
                nodeToReconnect['shader'].inputs['Base Color']
            )
        
        # reloading images to prevent bugs...
        for image in bpy.data.images:
            image.reload()

        jsonMappings.append(jsonMapping)

with open(BAKE_OUTPUT_FOLDER + '/_mapping.json', 'w', encoding='utf-8') as f:
    json.dump(jsonMappings, f, ensure_ascii=False, indent=4)


# zip folder
def zipdir(path, ziph):
    print('')
    print('Exporting to ' + BAKE_OUTPUT_FOLDER + '.zip')
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file), 
                       os.path.relpath(os.path.join(root, file), 
                                       os.path.join(path, '..')))
      
zipf = zipfile.ZipFile( BAKE_OUTPUT_FOLDER + '.zip', 'w', zipfile.ZIP_DEFLATED)
zipdir(BAKE_OUTPUT_FOLDER, zipf)
zipf.close()

# scale render res back
bpy.context.scene.render.resolution_x = 1080
bpy.context.scene.render.resolution_y = 1920

print('Baking DONE')

print('Exporting scene to _export.glb')
bpy.ops.export_scene.gltf(filepath=bpy.path.abspath("//") + "_export.glb", use_custom_props=True)