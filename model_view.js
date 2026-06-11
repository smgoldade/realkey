import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { STLLoader } from 'three/addons/loaders/STLLoader.js';
import WebGL from 'three/addons/capabilities/WebGL.js';

// WebGL checks for Chumi
if (!WebGL.isWebGL2Available()) {
    const status = document.querySelector("#status")
    status.innerHTML = "WebGL issue detected."
    status.appendChild(WebGL.getWebGL2ErrorMessage())
    throw new Error()
}

// Create all Three rendering objects
const canvas = document.querySelector("#canvas")
const camera = new THREE.PerspectiveCamera(75, canvas.clientWidth / canvas.clientHeight, 0.1, 1000)

const scene = new THREE.Scene()
const renderGroup = new THREE.Group()

const renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true })
renderer.setSize(canvas.clientWidth, canvas.clientHeight)
renderer.setPixelRatio(window.devicePixelRatio)
renderer.setAnimationLoop(animate)
renderer.setClearColor(0x222222)
renderer.shadowMap.enabled = true
renderer.shadowMap.autoUpdate = true
renderer.shadowMap.type = THREE.PCFSoftShadowMap

const controls = new OrbitControls(camera, renderer.domElement)
controls.autoRotate = true
controls.cursorStyle = "grab"
controls.enableDamping = true
controls.saveState()

window.addEventListener("resize", () => {
    let w = canvas.clientWidth
    let h = canvas.clientHeight
    let dpr = window.devicePixelRatio

    camera.aspect = w / h
    camera.updateProjectionMatrix()

    renderer.setSize(w, h)
    renderer.setPixelRatio(dpr)

    canvas.width = w * dpr;
    canvas.height = h * dpr;
})

var object = new THREE.Object3D()
renderGroup.add(object)

const ambient = new THREE.AmbientLight(0x404040)
scene.add(ambient)

const LIGHT_COUNT = 10
const LIGHT_RADIUS = 250
const LIGHT_STRENGTH = 10

for (var i = 0; i < LIGHT_COUNT; ++i) {
    // square lattice
    var x = ((2 * i) / (1 + Math.sqrt(5))) % 1
    var y = i / (LIGHT_COUNT - 1)
    // disc lattice
    var theta = 2 * Math.PI * x
    var phi = Math.acos(1 - 2 * y)
    // spherical lattice
    x = LIGHT_RADIUS * Math.cos(theta) * Math.sin(phi)
    y = LIGHT_RADIUS * Math.sin(theta) * Math.sin(phi)
    var z = LIGHT_RADIUS * Math.cos(phi)

    const l1 = new THREE.DirectionalLight(0xFFFFFF, LIGHT_STRENGTH / LIGHT_COUNT)
    l1.position.set(x, y, z)
    l1.castShadow = true
    l1.shadow.bias = -0.0005
    l1.shadow.camera.top = LIGHT_RADIUS
    l1.shadow.camera.bottom = -LIGHT_RADIUS
    l1.shadow.camera.left = -LIGHT_RADIUS
    l1.shadow.camera.right = LIGHT_RADIUS
    l1.shadow.camera.near = 1
    l1.shadow.camera.far = 1000
    l1.shadow.mapSize.width = 1024
    l1.shadow.mapSize.height = 1024

    renderGroup.add(l1)
}

renderGroup.add(camera)
scene.add(renderGroup)

var lastTime = 0;
function animate(time) {
    var deltaTime = (time - lastTime) / 1000
    lastTime = time

    controls.update(deltaTime)
    renderer.render(scene, camera)
}

async function loadStl(file, roughness = 0.5, metalness = 0.5, color = 0xE3BD7A) {
    const stlLoader = new STLLoader()
    var geometry = await stlLoader.loadAsync(file)
    var brassMaterial = new THREE.MeshPhysicalMaterial({
        color: color,
        roughness: roughness,
        metalness: metalness
    })
    return new THREE.Mesh(geometry, brassMaterial)
}

export async function loadObject(file, roughness = 0.5, metalness = 0.5, color = 0xE3BD7A) {
    renderGroup.remove(object)
    if ("geometry" in object)
        object.geometry.dispose()
    if ("material" in object)
        object.material.dispose()
    object = await loadStl(file, roughness, metalness, color)

    object.geometry.computeBoundingBox()
    var boundingBox = object.geometry.boundingBox
    var center = new THREE.Vector3()
    boundingBox.getCenter(center)
    var boundedSize = boundingBox.max.sub(boundingBox.min)
    var size = boundedSize.length()

    object.translateX(-center.x)
    object.translateY(-center.y)
    object.pivot = center
    object.rotation.z = -Math.PI / 2
    object.castShadow = true
    object.receiveShadow = true

    camera.position.z = size * 0.75
    renderGroup.add(object)
}