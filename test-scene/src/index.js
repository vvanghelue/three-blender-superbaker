import { loadLightmaps } from "../../loader/loader"

import * as THREE from "three"
import jszip from "jszip"
import initScene from "./init-scene"
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js"
import { EXRLoader } from "three/examples/jsm/loaders/EXRLoader.js"


let scene
  ; (async () => {
    scene = await initScene()
  })()

function getFileFromZip(zip, name) {
  for (const key of Object.keys(zip.files)) {
    const file = zip.files[key]

    if (file.name.includes(name)) {
      return file
    }
  }
  return false
}

// async function loadGLTF(zip) {
//   return new Promise(async (resolve) => {
//     for (const key of Object.keys(zip.files)) {
//       const file = zip.files[key]

//       if (file.name.includes(".glb")) {
//         //console.log(file);
//         const data = await file.async("uint8array")
//         //console.log(data);
//         new GLTFLoader().parse(
//           data.buffer,
//           "",
//           function onLoad(gltf) {
//             //console.log("onLoad", gltf);
//             resolve(gltf)
//           },
//           function onError(err) {
//             console.log("onError loadGLTF", err)
//           }
//         )
//       }
//     }
//   })
// }

/*
async function loadGLTF(zip) {
  return new Promise((resolve) => {
    const loader = new GLTFLoader().setPath(
      "https://vvg-dump.s3.eu-west-3.amazonaws.com/"
    );
    loader.load("bake-test.glb", function (gltf) {
      resolve(gltf);
    });
  });
}
*/

async function loadTextures(zip, scene) {
  const file = await getFileFromZip(zip, "_baked_lightmaps/_mapping.json")
  const mappings = JSON.parse(await file.async("text"))
  for (const mapping of mappings) {
    console.log(mapping)

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
          .setDataType(THREE.FloatType)
          .load(
            URL.createObjectURL(new Blob([u8.buffer], { type: "image/exr" })),
            function (texture, textureData) {
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

function loadScene({ gltfData }) {
  return new Promise((resolve) => {
    new GLTFLoader().parse(
      gltfData,
      "",
      function onLoad(gltfObject) {
        console.log("onLoad", gltfObject)
        gltf = gltfObject

        // gltf.scene.scale.set(100, 100, 100)
        gltf.scene.traverse((child) => {
          return
          //console.log(child)
          if (child.isMesh) {

            const color = child.material.color
            const map = child.material.map
            const normalMap = child.material.normalMap
            const roughnessMap = child.material.roughnessMap
            const emissiveMap = child.material.emissiveMap
            //console.log(emissiveMap)
            child.material = new THREE.MeshBasicMaterial({ color, map, normalMap, roughnessMap, emissiveMap })
            child.material.emissiveIntensity = 2
            // if (map) {
            //   child.material.map = map
            // }
          }
        })

        scene.add(gltf.scene)
        resolve()
      },
      function onError() {
        console.log("onError")
      }
    )
  })
}

let gltf
document.querySelector("input.load-gltf").addEventListener("change", async (e) => {
  const gltfData = await getArrayBufferFromInputFile({ file: e.target.files[0] })

  //var array = new Int8Array(data);
  //console.log(array);

  // console.log(data)

  loadScene({ gltfData })
})

document.querySelector("input.load-textures").addEventListener("change", async (e) => {
  //console.log(e.target.files[0])
  await loadLightmaps({
    lightmaps: e.target.files[0],
    scene
  })
  // jszip
  //   .loadAsync(e.target.files[0]) // 1) read the Blob
  //   .then(async function (zip) {
  //     //console.log("unzip gltf...");
  //     //const gltf = await loadGLTF(zip);
  //     console.log("load textures...")
  //     await loadTextures(zip, gltf.scene)

  //     scene.add(gltf.scene)
  //   })
})

/*
document.querySelector("input").addEventListener("change", (e) => {
  var fr = new FileReader();
  fr.onload = function () {
    var data = fr.result;
    //var array = new Int8Array(data);
    //console.log(array);

    console.log(data);

    new GLTFLoader().parse(
      data,
      "",
      function onLoad(gltf) {
        console.log("onLoad", gltf);
      },
      function onError() {
        console.log("onError");
      }
    );
  };
  fr.readAsArrayBuffer(e.target.files[0]);
});
const loader = new GLTFLoader().setPath(
  "https://vvg-dump.s3.eu-west-3.amazonaws.com/"
);
*/

function getArrayBufferFromInputFile({ file }) {
  return new Promise((resolve) => {
    var fr = new FileReader()
    fr.readAsArrayBuffer(file)
    fr.onload = function () {
      resolve(fr.result)
    }
  })
}

function loadFile({ url }) {
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

; (async () => {

  await loadScene({ gltfData: await loadFile({ url: '/_export.glb' }) })

  await loadLightmaps({
    lightmaps: await loadFile({ url: '/_baked_lightmaps.zip' }),
    scene
  })

  // console.log(await loadFile({ url: '/_export.glb' }))
})()