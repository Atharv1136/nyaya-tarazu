import { useRef, useMemo } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import * as THREE from 'three'

// ---------------------------------------------------------------------------
// Scale geometry — parametric construction
// ---------------------------------------------------------------------------
function ScaleModel({ scrollY = 0 }: { scrollY?: number }) {
  const groupRef = useRef<THREE.Group>(null!)
  const beamRef = useRef<THREE.Mesh>(null!)
  const leftPanRef = useRef<THREE.Group>(null!)
  const rightPanRef = useRef<THREE.Group>(null!)

  const saffronMat = useMemo(() => new THREE.MeshStandardMaterial({
    color: new THREE.Color('#C1440E'),
    roughness: 0.6,
    metalness: 0.7,
  }), [])

  const brassMat = useMemo(() => new THREE.MeshStandardMaterial({
    color: new THREE.Color('#D4A24C'),
    roughness: 0.5,
    metalness: 0.8,
  }), [])

  // Idle sway + scroll tilt
  const time = useRef(0)
  useFrame((_state, delta) => {
    time.current += delta
    if (groupRef.current) {
      // Gentle idle bob
      groupRef.current.position.y = Math.sin(time.current * 0.4) * 0.04
    }
    if (beamRef.current) {
      // Scroll-reactive tilt: at scrollY=0 balanced, at scrollY=1 tilt toward prosecution
      const idleTilt = Math.sin(time.current * 0.3) * 0.04
      const scrollTilt = scrollY * 0.25
      beamRef.current.rotation.z = idleTilt + scrollTilt
    }
    // Pan heights follow beam tilt
    if (leftPanRef.current && rightPanRef.current) {
      const beamAngle = beamRef.current?.rotation.z || 0
      leftPanRef.current.position.y = -0.8 + Math.sin(beamAngle) * 1.1
      rightPanRef.current.position.y = -0.8 - Math.sin(beamAngle) * 1.1
    }
  })

  return (
    <group ref={groupRef} position={[0, 0.2, 0]}>
      {/* === Pillar === */}
      <mesh position={[0, -1.2, 0]} material={brassMat}>
        <cylinderGeometry args={[0.06, 0.1, 2.4, 12]} />
      </mesh>

      {/* Base */}
      <mesh position={[0, -2.5, 0]} material={brassMat}>
        <cylinderGeometry args={[0.5, 0.6, 0.2, 16]} />
      </mesh>
      <mesh position={[0, -2.35, 0]} material={brassMat}>
        <cylinderGeometry args={[0.2, 0.3, 0.15, 12]} />
      </mesh>

      {/* Top finial */}
      <mesh position={[0, 0.1, 0]} material={brassMat}>
        <sphereGeometry args={[0.1, 12, 12]} />
      </mesh>

      {/* === Beam === */}
      <mesh ref={beamRef} position={[0, 0, 0]} material={brassMat}>
        <boxGeometry args={[2.2, 0.07, 0.07]} />
      </mesh>

      {/* Pivot knob */}
      <mesh position={[0, 0, 0]} material={brassMat}>
        <sphereGeometry args={[0.12, 12, 12]} />
      </mesh>

      {/* === Left chain + pan (saffron / prosecution) === */}
      <group ref={leftPanRef} position={[-1.0, -0.8, 0]}>
        {/* Chain segments */}
        {[-0.2, -0.4, -0.6].map((y, i) => (
          <mesh key={i} position={[0, y + 0.8, 0]} material={brassMat}>
            <cylinderGeometry args={[0.015, 0.015, 0.18, 6]} />
          </mesh>
        ))}
        {/* Pan ring */}
        <mesh position={[0, 0.1, 0]} material={brassMat}>
          <torusGeometry args={[0.28, 0.02, 8, 20]} />
        </mesh>
        {/* Pan dish — saffron */}
        <mesh rotation={[Math.PI / 2, 0, 0]} material={saffronMat}>
          <cylinderGeometry args={[0.25, 0.2, 0.08, 16]} />
        </mesh>
      </group>

      {/* === Right chain + pan (brass / defense) === */}
      <group ref={rightPanRef} position={[1.0, -0.8, 0]}>
        {[-0.2, -0.4, -0.6].map((y, i) => (
          <mesh key={i} position={[0, y + 0.8, 0]} material={brassMat}>
            <cylinderGeometry args={[0.015, 0.015, 0.18, 6]} />
          </mesh>
        ))}
        <mesh position={[0, 0.1, 0]} material={brassMat}>
          <torusGeometry args={[0.28, 0.02, 8, 20]} />
        </mesh>
        {/* Pan dish — brass */}
        <mesh rotation={[Math.PI / 2, 0, 0]} material={brassMat}>
          <cylinderGeometry args={[0.25, 0.2, 0.08, 16]} />
        </mesh>
      </group>
    </group>
  )
}

// ---------------------------------------------------------------------------
// Scene wrapper with lighting
// ---------------------------------------------------------------------------
interface ScaleSceneProps {
  scrollY?: number
}

export default function ScaleScene({ scrollY = 0 }: ScaleSceneProps) {
  return (
    <Canvas
      camera={{ position: [0, 0, 5], fov: 40 }}
      style={{ background: 'transparent' }}
    >
      {/* Courtroom spotlight from upper-right */}
      <directionalLight
        position={[3, 5, 2]}
        intensity={2.5}
        color="#FFF5E0"
        castShadow
      />
      {/* Very dim ambient fill */}
      <ambientLight intensity={0.15} color="#14161F" />
      {/* Saffron rim light from left */}
      <pointLight position={[-3, 2, 1]} intensity={0.6} color="#C1440E" />
      {/* Brass fill from below */}
      <pointLight position={[1, -2, 2]} intensity={0.3} color="#D4A24C" />

      <ScaleModel scrollY={scrollY} />
    </Canvas>
  )
}
