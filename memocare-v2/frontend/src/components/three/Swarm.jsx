import { useRef, useMemo, useEffect } from 'react'
import { useFrame, useThree } from '@react-three/fiber'
import * as THREE from 'three'
import { useGLTF } from '@react-three/drei'

// Vertex Shader - All physics calculations happen here on GPU
// Displacement-Based Logic: Orbit is base state, Blast is temporary displacement
const vertexShader = `
  attribute vec3 aHome;
  attribute vec3 aVelocity;
  attribute vec3 aColor;
  
  uniform float uTime;
  uniform bool uBlastActive;
  uniform float uBlastTime;
  uniform float uRotationSpeed;
  uniform float uRepulsionRadius;
  uniform float uLerpRate;
  uniform vec3 uMouseWorld;
  
  varying vec3 vColor;
  
  void main() {
    // 1. BASE STATE: Always calculate the Target Orbit
    float homeAngle = atan(aHome.y, aHome.x);
    float homeR = length(aHome.xy);
    float orbitAngle = homeAngle + uRotationSpeed * uTime;
    vec3 baseOrbitPos = vec3(homeR * cos(orbitAngle), homeR * sin(orbitAngle), aHome.z);

    vec3 finalPos;
    float blastElapsed = uTime - uBlastTime;

    // 2. BLAST LOGIC: Calculate displacement from the orbit
    if (uBlastActive && blastElapsed < 10.0) {
      float dampingFactor = 0.1;
      vec3 blastOffset;

      if (blastElapsed < 5.0) {
        // Phase 1: Outward Explosion
        float damping = 1.0 - exp(-blastElapsed * dampingFactor);
        blastOffset = aVelocity * damping * 15.0;
      } else {
        // Phase 2 & 3: Return to Home
        float returnTime = blastElapsed - 5.0;
        float returnProgress = clamp(returnTime / 3.0, 0.0, 1.0); // Returns by 8s
        float maxDamp = 1.0 - exp(-5.0 * dampingFactor);
        vec3 maxOffset = aVelocity * maxDamp * 15.0;
        
        // Cubic ease-in-out for smooth deceleration
        float smoothProgress = returnProgress * returnProgress * (3.0 - 2.0 * returnProgress);
        blastOffset = mix(maxOffset, vec3(0.0), smoothProgress);
      }

      // 3. SEAMLESS TRANSITION: Blend the blast offset into the orbit
      // We start fading the blast effect into the orbit rotation between 7s and 10s
      float transitionWeight = smoothstep(7.0, 10.0, blastElapsed);
      
      // Calculate where the particle would be if it was JUST orbiting
      // We mix the static blast position with the dynamic orbit position
      finalPos = mix(aHome + blastOffset, baseOrbitPos, transitionWeight);

    } else {
      // 4. NORMAL STATE: Pure orbit
      finalPos = baseOrbitPos;
    }

    // 5. MOUSE INTERACTION (applied as an additive offset)
    float distToMouse = distance(finalPos, uMouseWorld);
    if (distToMouse < uRepulsionRadius) {
      vec3 direction = normalize(finalPos - uMouseWorld);
      float repulsionStrength = pow((uRepulsionRadius - distToMouse) / uRepulsionRadius, 2.0);
      finalPos += direction * repulsionStrength * 2.0;
    }

    // PULSING EFFECT (applied only to Z to avoid radius glitches)
    finalPos.z += sin(uTime * 0.5 + aHome.x * 0.1) * 0.02;

    vColor = aColor;
    vec4 mvPosition = modelViewMatrix * vec4(finalPos, 1.0);
    gl_Position = projectionMatrix * mvPosition;
    
    float pDistance = length(mvPosition.xyz);
    gl_PointSize = 30.0 / pDistance;
  }
`

// Fragment Shader - Simple additive blending
const fragmentShader = `
  varying vec3 vColor;
  
  void main() {
    float distance = length(gl_PointCoord - vec2(0.5));
    float alpha = 1.0 - smoothstep(0.0, 0.5, distance);
    
    gl_FragColor = vec4(vColor, alpha * 0.9);
  }
`

export default function Swarm() {
  const meshRef = useRef()
  const blastStateRef = useRef({ active: false, startTime: 0 })
  const { camera } = useThree()

  // Load the brain model
  const { scene } = useGLTF('/human-brain.glb')

  // Initialize points using the brain's vertices
  const { homes, velocities, colors } = useMemo(() => {
    // 1. Extract all vertices from the GLTF meshes
    const brainVertices = []
    scene.traverse((child) => {
      if (child.isMesh && child.geometry) {
        const pos = child.geometry.attributes.position
        if (pos) {
          child.updateMatrixWorld()
          for (let i = 0; i < pos.count; i++) {
            const v = new THREE.Vector3().fromBufferAttribute(pos, i)
            v.applyMatrix4(child.matrixWorld)
            brainVertices.push(v)
          }
        }
      }
    })

    // Fallback to a single point if the model has no vertices (shouldn't happen)
    if (brainVertices.length === 0) {
      brainVertices.push(new THREE.Vector3(0, 0, 0))
    }

    // 2. Calculate bounding box to center and scale the brain
    const box = new THREE.Box3()
    brainVertices.forEach(p => box.expandByPoint(p))
    
    const center = new THREE.Vector3()
    box.getCenter(center)
    
    const size = new THREE.Vector3()
    box.getSize(size)
    const maxDim = Math.max(size.x, size.y, size.z)
    
    // Scale the brain to fit inside a radius of roughly 5 units
    // (maxDim is the full diameter, so we divide 10 by maxDim)
    const scale = maxDim > 0 ? (10 / maxDim) : 1

    const count = 50000
    const homes = new Float32Array(count * 3)
    const velocities = new Float32Array(count * 3)
    const colors = new Float32Array(count * 3)

    for (let i = 0; i < count; i++) {
      // Pick a random vertex from the brain model
      const randomVertex = brainVertices[Math.floor(Math.random() * brainVertices.length)]
      
      // Center, scale, and add a tiny jitter to avoid exact overlapping
      const jitter = 0.05
      const x = (randomVertex.x - center.x) * scale + (Math.random() - 0.5) * jitter
      const y = (randomVertex.y - center.y) * scale + (Math.random() - 0.5) * jitter
      const z = (randomVertex.z - center.z) * scale + (Math.random() - 0.5) * jitter

      const i3 = i * 3
      homes[i3] = x
      homes[i3 + 1] = y
      homes[i3 + 2] = z

      // Pre-calculate velocities for blast (direction from center + randomness)
      const dist = Math.sqrt(x * x + y * y + z * z)
      if (dist > 0) {
        const baseForce = 4.0 + Math.random() * 3.0 // Random force between 4.0 and 7.0
        const directionX = x / dist
        const directionY = y / dist
        const directionZ = z / dist
        
        const randomOffset = (Math.random() - 0.5) * 0.8
        velocities[i3] = directionX * baseForce + randomOffset
        velocities[i3 + 1] = directionY * baseForce + randomOffset
        velocities[i3 + 2] = directionZ * baseForce + randomOffset
      } else {
        // If particle is at center, give it random direction
        const theta = Math.random() * Math.PI * 2
        const phi = Math.acos(Math.random() * 2 - 1)
        const force = 4.0 + Math.random() * 3.0
        velocities[i3] = Math.sin(phi) * Math.cos(theta) * force
        velocities[i3 + 1] = Math.sin(phi) * Math.sin(theta) * force
        velocities[i3 + 2] = Math.cos(phi) * force
      }

      // Color gradient from white to cyan based on position from center
      const normalizedR = Math.min(dist / 5.0, 1.0)
      colors[i3] = 0.5 + normalizedR * 0.5 // R: 0.5 to 1.0
      colors[i3 + 1] = 0.8 + normalizedR * 0.2 // G: 0.8 to 1.0
      colors[i3 + 2] = 1.0 // B: always 1.0 (white to cyan)
    }

    return { homes, velocities, colors }
  }, [scene])



  // Center click detection for blast effect
  useEffect(() => {
    const handleClick = (e) => {
      const centerX = window.innerWidth / 2
      const centerY = window.innerHeight / 2
      const clickX = e.clientX
      const clickY = e.clientY
      const distance = Math.sqrt(
        Math.pow(clickX - centerX, 2) + Math.pow(clickY - centerY, 2)
      )

      if (distance < 50 && !blastStateRef.current.active) {
        blastStateRef.current.active = true
        // Store the current time from the clock (will be set in useFrame)
        blastStateRef.current.startTime = 0 // Will be set to current time in useFrame
      }
    }

    window.addEventListener('click', handleClick)
    return () => window.removeEventListener('click', handleClick)
  }, [])

  // GPU-accelerated update - only updates uniforms, no CPU loops!
  useFrame((state) => {
    if (!meshRef.current) return

    const material = meshRef.current.material
    const mouse = state.pointer
    const blastState = blastStateRef.current
    const time = state.clock.elapsedTime

    // Project mouse to 3D space
    const mouse3D = new THREE.Vector3(mouse.x, mouse.y, 0.5)
    mouse3D.unproject(camera)
    const dir = mouse3D.sub(camera.position).normalize()
    const distance = 10
    const mouseWorld = camera.position.clone().add(dir.multiplyScalar(distance))

    // Initialize blast start time on first frame after click
    if (blastState.active && blastState.startTime === 0) {
      blastState.startTime = time
    }

    // Calculate time since blast (in seconds)
    const timeSinceBlast = blastState.active ? time - blastState.startTime : 0

    // Auto-disable blast after 10 seconds (complete cycle: 5s blast + 5s return)
    if (blastState.active && timeSinceBlast > 10) {
      blastState.active = false
      blastState.startTime = 0 // Reset for next blast
    }

    // Update uniforms - this is the ONLY thing happening in useFrame!
    material.uniforms.uTime.value = time
    material.uniforms.uMouse.value = [mouse.x, mouse.y]
    material.uniforms.uBlastActive.value = blastState.active
    material.uniforms.uBlastTime.value = blastState.startTime
    material.uniforms.uMouseWorld.value = [mouseWorld.x, mouseWorld.y, mouseWorld.z]
  })

  const geometry = useMemo(() => {
    const geom = new THREE.BufferGeometry()
    
    // Set initial positions (will be overridden by shader)
    const positions = new Float32Array(homes.length)
    geom.setAttribute('position', new THREE.BufferAttribute(positions, 3))
    
    // Set attributes for shader
    geom.setAttribute('aHome', new THREE.BufferAttribute(homes, 3))
    geom.setAttribute('aVelocity', new THREE.BufferAttribute(velocities, 3))
    geom.setAttribute('aColor', new THREE.BufferAttribute(colors, 3))
    
    return geom
  }, [homes, velocities, colors])

  const material = useMemo(() => {
    return new THREE.ShaderMaterial({
      vertexShader,
      fragmentShader,
      uniforms: {
        uTime: { value: 0 },
        uMouse: { value: [0, 0] },
        uBlastActive: { value: false },
        uBlastTime: { value: 0 },
        uRotationSpeed: { value: 0.0 },
        uRepulsionRadius: { value: 3.5 },
        uLerpRate: { value: 0.08 },
        uMouseWorld: { value: [0, 0, 0] },
      },
      transparent: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
      vertexColors: true,
    })
  }, [])

  return (
    <points ref={meshRef} geometry={geometry} material={material} />
  )
}
