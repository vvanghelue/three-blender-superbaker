import * as THREE from "three"
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js"

let camera, scene, renderer, controls

export default async function () {
  const container = document.createElement("div")
  document.body.appendChild(container)

  scene = window.scene = new THREE.Scene()
  const axesHelper = new THREE.AxesHelper(0.5)
  scene.add(axesHelper)

  camera = new THREE.PerspectiveCamera(70, window.innerWidth / window.innerHeight, 0.01, 20000)
  camera.position.x = 10
  camera.position.y = 10
  camera.position.z = 10

  renderer = window.renderer = new THREE.WebGLRenderer({
    antialias: true,
    //alpha: true
  })
  //renderer.toneMapping = THREE.LinearToneMapping;
  //renderer.toneMappingExposure = 1;
  //renderer.xr.enabled = true;

  //renderer.physicallyCorrectLights = true;
  renderer.outputEncoding = THREE.sRGBEncoding
  renderer.toneMapping=THREE.ACESFilmicToneMapping;
  //renderer.toneMapping=THREE.LinearToneMapping;
  //renderer.toneMapping=THREE.ReinhardToneMapping
  //renderer.toneMapping=THREE.CustomToneMapping
  renderer.toneMappingExposure = 1.1;
  //renderer.gammaOutput = true;
  //renderer.gammaFactor = .2
  renderer.setClearColor(0xabcdef)
  renderer.setPixelRatio(window.devicePixelRatio)
  renderer.setSize(window.innerWidth, window.innerHeight)
  container.appendChild(renderer.domElement)

//   const light = new THREE.AmbientLight(0xffffff);
//   light.intensity = .2;
//   light.position.set(5, 0, 10);
//   scene.add(light);

//   const light2 = new THREE.DirectionalLight(0xabcdef, 1);
//   light2.intensity = .5;
//   light2.position.set(5, 10, 10); // ~60º
//   scene.add(light2);

//   const light = new THREE.HemisphereLight(0xffffbb, 0x080820, .6);
//   scene.add(light);

  controls = new OrbitControls(camera, renderer.domElement)
  controls.minDistance = 1
  controls.maxDistance = 10500

  function onWindowResize() {
    camera.aspect = window.innerWidth / window.innerHeight
    camera.updateProjectionMatrix()

    renderer.setSize(window.innerWidth, window.innerHeight)
  }
  window.addEventListener("resize", onWindowResize)

  function render() {
    renderer.render(scene, camera)
  }
  renderer.setAnimationLoop(render)

  return scene
}
