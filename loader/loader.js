import * as THREE from "three"
import jszip from "jszip"
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js"
import { EXRLoader } from "three/examples/jsm/loaders/EXRLoader.js"


function getFileFromZip(zip, name) {
    for (const key of Object.keys(zip.files)) {
      const file = zip.files[key]
  
      if (file.name.includes(name)) {
        return file
      }
    }
    return false
  }

async function loadTextures({ zip, scene }) {
    const file = await getFileFromZip(zip, "_baked_lightmaps/_mapping.json")
    const mappings = JSON.parse(await file.async("text"))
    for (const mapping of mappings) {
      //console.log(mapping)
  
      const object = scene.getObjectByName(
          mapping.objectName.replace(/\./g, "").replace(/ /g, "_"),
          true
      )
  
      if (!object) {
        console.log("loadTextures : mesh not found : " + mapping.objectName)
        continue
      }
  
      let meshes = []
      if (object.type == "Mesh") {
          meshes = [object]
      }
      if (object.type == "Group") {
          meshes = object.children
      }
  
      // console.log(mapping)
      for (let i = 0; i < mapping.materials.length; i++) {
          const file = await getFileFromZip(zip, mapping.materials[i].lightmapFile)
          const u8 = await file.async("uint8array")
          const mesh = meshes[i]
          if (!mesh.material) {
              console.log("loadTextures : no material for mesh : " + mapping.objectName)
              continue
          }
          if (mapping.materials[i].lightmapFile.includes('.exr')) {
              new EXRLoader()
                  .setDataType( THREE.FloatType )
                  .load( 
                      URL.createObjectURL(new Blob([u8.buffer], { type: "image/exr" })), 
                      function ( texture, textureData ) {
                          //texture.anisotropy = renderer.getMaxAnisotropy()
                          //texture.magFilter = THREE.LinearFilter;
                          //texture.encoding = THREE.sRGBEncoding
  
                          mesh.material.lightMap = texture
                          mesh.material.lightMap.flipY = true
                          // mesh.material.lightMapIntensity = 1
                          mesh.material.needsUpdate = true
                      }
                  )
          } else {
              const texture = new THREE.TextureLoader().load(
                  URL.createObjectURL(new Blob([u8.buffer], { type: "image/png" }))
              )
              texture.encoding = THREE.sRGBEncoding
              mesh.material.lightMap = texture
              mesh.material.lightMap.flipY = false
              // mesh.material.lightMapIntensity = 1
              mesh.material.needsUpdate = true
          }
          //mesh.material.lightMap.magFilter = THREE.NearestFilter;
      }
  
      /*
      console.log("Apply lightmap to mesh :");
      console.log(mesh);
      mesh.material.lightMap = new THREE.TextureLoader().load(
        URL.createObjectURL(new Blob([u8.buffer], { type: "image/png" }))
      );
      mesh.material.lightMapIntensity = æ;
      mesh.material.needsUpdate = true;
      */
    }
}

export async function loadLightmaps({lightmaps, scene}) {
    const zip = await jszip.loadAsync(lightmaps)
    await loadTextures({ zip, scene })
}

export function loadHttpFileAsArrayBuffer({ url }) {
    return new Promise((resolve) => {
      var oReq = new XMLHttpRequest();
      oReq.open("GET", url, true);
      oReq.responseType = "arraybuffer";
      oReq.onload = function (e) {
        var arraybuffer = oReq.response
        resolve(arraybuffer)
      }
      oReq.send();
    })
  }