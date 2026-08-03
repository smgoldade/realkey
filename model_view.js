import * as THREE from "three"
import WebGL from "three/addons/capabilities/WebGL.js"
import { OrbitControls } from "three/addons/controls/OrbitControls.js"
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js"
import { STLLoader } from "three/addons/loaders/STLLoader.js"

// Constants used for lighting and look
const ENVIRONMENT_INTENSITY = 0.6
const MAX_PIXEL_RATIO = 2
const MIN_OBJECT_RADIUS = 0.001
const FIT_PADDING = 1.2
const MATERIAL_ENVIRONMENT_INTENSITY = 0.65
const MATERIAL_SPECULAR_INTENSITY = 0.5
const TONE_MAPPING_EXPOSURE = 0.72

// WebGL2 check for Chumi
if (!WebGL.isWebGL2Available()) {
    window.realkeyBoot?.fail(
        "WebGL 2 is unavailable",
        "realkey requires WebGL 2 to display generated models. Please use a compatible browser.",
        "The browser did not provide a WebGL 2 rendering context.",
    )
    throw new Error("WebGL 2 is not available")
}

// Canvas and viewport verification
const canvas = document.querySelector("#canvas")
const viewport = document.querySelector("#model-view")
if (!(canvas instanceof HTMLCanvasElement)) {
    throw new Error("Model canvas was not found")
}
if (!(viewport instanceof HTMLElement)) {
    throw new Error("Model viewport was not found")
}

// Camera setup
const camera = new THREE.PerspectiveCamera(75, 1, 0.01, 10000)
const scene = new THREE.Scene()
const renderGroup = new THREE.Group()

const renderer = new THREE.WebGLRenderer({ canvas, antialias: true })
renderer.setPixelRatio(Math.min(window.devicePixelRatio, MAX_PIXEL_RATIO))
renderer.setAnimationLoop(animate)
renderer.setClearColor(0x101314, 0)
renderer.toneMapping = THREE.ACESFilmicToneMapping
renderer.toneMappingExposure = TONE_MAPPING_EXPOSURE
renderer.shadowMap.enabled = true
renderer.shadowMap.autoUpdate = false
renderer.shadowMap.type = THREE.PCFSoftShadowMap

const roomEnvironment = new RoomEnvironment()
const pmremGenerator = new THREE.PMREMGenerator(renderer)
const environmentRenderTarget = pmremGenerator.fromScene(roomEnvironment)
scene.environment = environmentRenderTarget.texture
scene.environmentIntensity = ENVIRONMENT_INTENSITY
roomEnvironment.dispose()
pmremGenerator.dispose()

const controls = new OrbitControls(camera, renderer.domElement)
controls.autoRotate = true
controls.cursorStyle = "grab"
controls.enableDamping = true
controls.saveState()

let currentObject = new THREE.Object3D()
let objectRadius = null
let lastFitDistance = null
renderGroup.add(currentObject)

function getFitDistance() {
    if (objectRadius === null) {
        return null
    }

    const radius = Math.max(objectRadius, MIN_OBJECT_RADIUS)
    const verticalFov = THREE.MathUtils.degToRad(camera.fov)
    const horizontalFov = 2 * Math.atan(Math.tan(verticalFov / 2) * camera.aspect)
    const limitingHalfFov = Math.min(verticalFov, horizontalFov) / 2
    return radius * FIT_PADDING / Math.sin(limitingHalfFov)
}

function frameObject(preserveZoom = false) {
    const fitDistance = getFitDistance()
    if (fitDistance === null) {
        return
    }

    const viewDirection = camera.position.clone().sub(controls.target)
    const currentDistance = viewDirection.length()
    if (viewDirection.lengthSq() === 0) {
        viewDirection.set(0, 0, 1)
    }
    viewDirection.normalize()

    // Preserve the user's zoom relative to the fitted model across resizes.
    const distance = preserveZoom && lastFitDistance !== null && currentDistance > 0
        ? currentDistance * fitDistance / lastFitDistance
        : fitDistance
    lastFitDistance = fitDistance

    const radius = Math.max(objectRadius, MIN_OBJECT_RADIUS)
    controls.target.set(0, 0, 0)
    camera.position.copy(viewDirection.multiplyScalar(distance))
    camera.near = Math.max(0.01, distance - radius * 1.5)
    camera.far = distance + radius * 4
    camera.updateProjectionMatrix()
    controls.update()
}

function resizeViewport() {
    const width = Math.max(1, viewport.clientWidth)
    const height = Math.max(1, viewport.clientHeight)

    renderer.setPixelRatio(Math.min(window.devicePixelRatio, MAX_PIXEL_RATIO))
    renderer.setSize(width, height, false)
    camera.aspect = width / height
    camera.updateProjectionMatrix()
    frameObject(true)
}

let pendingResizeFrame = null
function scheduleResize() {
    if (pendingResizeFrame !== null) {
        cancelAnimationFrame(pendingResizeFrame)
    }

    pendingResizeFrame = requestAnimationFrame(() => {
        pendingResizeFrame = null
        resizeViewport()
    })
}

const resizeObserver = new ResizeObserver(scheduleResize)
resizeObserver.observe(viewport)
window.addEventListener("resize", scheduleResize)
window.addEventListener("pagehide", () => environmentRenderTarget.dispose(), { once: true })
scheduleResize()

const AMBIENT_LIGHT_INTENSITY = 0.16
const LIGHT_COUNT = 10
const LIGHT_RADIUS = 250
const LIGHT_STRENGTH = 0.75
const SHADOW_CASTING_LIGHT_COUNT = 10
const SHADOW_INTENSITY = 0.4
const SHADOW_RADIUS = 4

const ambientLight = new THREE.AmbientLight(0xFFFFFF, AMBIENT_LIGHT_INTENSITY)
scene.add(ambientLight)

for (let index = 0; index < LIGHT_COUNT; index += 1) {
    // construct a spherical lattice for lights using Fibonacci lattice method
    // Square lattice
    const sx = ((2 * index) / (1 + Math.sqrt(5))) % 1
    const sy = index / (LIGHT_COUNT - 1)
    // lat, lon lattice
    const theta = 2 * Math.PI * sx
    const phi = Math.acos(1 - 2 * sy)
    // convert to x,y,z coords
    const x = LIGHT_RADIUS * Math.cos(theta) * Math.sin(phi)
    const y = LIGHT_RADIUS * Math.sin(theta) * Math.sin(phi)
    const z = LIGHT_RADIUS * Math.cos(phi)

    const light = new THREE.DirectionalLight(0xFFFFFF, LIGHT_STRENGTH / LIGHT_COUNT)
    light.position.set(x, y, z)
    light.castShadow = index < SHADOW_CASTING_LIGHT_COUNT
    if (light.castShadow) {
        light.shadow.bias = -0.0005
        light.shadow.intensity = SHADOW_INTENSITY
        light.shadow.radius = SHADOW_RADIUS
        light.shadow.camera.top = LIGHT_RADIUS
        light.shadow.camera.bottom = -LIGHT_RADIUS
        light.shadow.camera.left = -LIGHT_RADIUS
        light.shadow.camera.right = LIGHT_RADIUS
        light.shadow.camera.near = 1
        light.shadow.camera.far = 1000
        light.shadow.mapSize.width = 1024
        light.shadow.mapSize.height = 1024
    }

    renderGroup.add(light)
}

renderGroup.add(camera)
scene.add(renderGroup)

let lastAnimationTime = null
function animate(time) {
    const deltaSeconds = lastAnimationTime === null ? 0 : (time - lastAnimationTime) / 1000
    lastAnimationTime = time

    controls.update(deltaSeconds)
    renderer.render(scene, camera)
}

async function loadStl(file, roughness = 0.5, metalness = 0.5, color = 0xE3BD7A) {
    const loader = new STLLoader()
    const geometry = await loader.loadAsync(file)
    const material = new THREE.MeshPhysicalMaterial({
        color,
        envMapIntensity: MATERIAL_ENVIRONMENT_INTENSITY,
        metalness,
        roughness,
        specularIntensity: MATERIAL_SPECULAR_INTENSITY,
    })
    return new THREE.Mesh(geometry, material)
}

function disposeObject(target) {
    target.geometry?.dispose()

    if (Array.isArray(target.material)) {
        for (const material of target.material) {
            material.dispose()
        }
    } else {
        target.material?.dispose()
    }
}

function prepareObject(target) {
    target.geometry.computeBoundingBox()
    const boundingBox = target.geometry.boundingBox
    if (boundingBox === null) {
        throw new Error("Unable to calculate the model bounds")
    }

    const center = new THREE.Vector3()
    boundingBox.getCenter(center)

    // Center all axes so asymmetric models orbit around their true center.
    target.geometry.translate(-center.x, -center.y, -center.z)
    target.geometry.computeBoundingSphere()
    const boundingSphere = target.geometry.boundingSphere
    if (boundingSphere === null || !Number.isFinite(boundingSphere.radius)) {
        throw new Error("Unable to calculate the model radius")
    }

    target.position.set(0, 0, 0)
    target.rotation.z = -Math.PI / 2
    target.castShadow = true
    target.receiveShadow = true
    return boundingSphere.radius
}

export async function loadObject(file, roughness = 0.5, metalness = 0.5, color = 0xE3BD7A) {
    const newObject = await loadStl(file, roughness, metalness, color)

    let newObjectRadius
    try {
        newObjectRadius = prepareObject(newObject)
    } catch (error) {
        disposeObject(newObject)
        throw error
    }

    const previousObject = currentObject
    currentObject = newObject
    objectRadius = newObjectRadius
    lastFitDistance = null

    renderGroup.add(newObject)
    renderGroup.remove(previousObject)
    disposeObject(previousObject)
    frameObject()
    renderer.shadowMap.needsUpdate = true
}
