import { Canvas } from "@react-three/fiber";
import { Float, OrbitControls } from "@react-three/drei";
import { Suspense } from "react";
import * as THREE from "three";

function Crop({ position, scale = 1 }: { position: [number, number, number]; scale?: number }) {
  return (
    <group position={position} scale={scale}>
      <mesh position={[0, 0.35, 0]} castShadow>
        <cylinderGeometry args={[0.018, 0.027, 0.72, 7]} />
        <meshStandardMaterial color="#55734b" roughness={0.9} />
      </mesh>
      {[-1, 1].map((side, index) => (
        <mesh
          key={side}
          position={[side * 0.12, 0.47 + index * 0.12, 0]}
          rotation={[0, 0, side * -0.55]}
          castShadow
        >
          <sphereGeometry args={[0.16, 10, 8]} />
          <meshStandardMaterial color={index === 0 ? "#789759" : "#92a968"} roughness={0.8} />
        </mesh>
      ))}
      <mesh position={[0.025, 0.73, 0]} rotation={[0.2, 0, -0.25]}>
        <sphereGeometry args={[0.13, 9, 7]} />
        <meshStandardMaterial color="#a6b96e" roughness={0.8} />
      </mesh>
    </group>
  );
}

function FieldRows() {
  const crops: Array<[number, number, number]> = [];
  for (let row = 0; row < 8; row += 1) {
    for (let plant = 0; plant < 9; plant += 1) {
      const x = (plant - 4) * 0.64 + (row % 2) * 0.26;
      const z = (row - 3.5) * 0.7;
      crops.push([x, 0, z]);
    }
  }

  return (
    <group rotation={[-0.15, 0.25, 0]}>
      <mesh receiveShadow position={[0, -0.09, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <planeGeometry args={[9, 7]} />
        <meshStandardMaterial color="#b7a77b" roughness={1} />
      </mesh>
      {crops.map((position, index) => (
        <Crop key={index} position={position} scale={0.72 + ((index * 17) % 5) * 0.07} />
      ))}
      {[-1.8, 0, 1.8].map((x, index) => (
        <mesh key={x} position={[x, 0.012, 0]} rotation={[-Math.PI / 2, 0, 0]}>
          <planeGeometry args={[0.09, 6.6]} />
          <meshBasicMaterial color={index === 1 ? "#d9c99d" : "#a99667"} />
        </mesh>
      ))}
    </group>
  );
}

function SceneContent() {
  return (
    <>
      <color attach="background" args={["#edf1e6"]} />
      <fog attach="fog" args={["#edf1e6", 7, 15]} />
      <ambientLight intensity={1.8} />
      <directionalLight
        position={[4, 7, 5]}
        intensity={2.2}
        castShadow
        shadow-mapSize-width={1024}
        shadow-mapSize-height={1024}
      />
      <Float speed={1.1} rotationIntensity={0.03} floatIntensity={0.12}>
        <FieldRows />
        <mesh position={[2.1, 1.15, 0.3]} rotation={[0, 0, 0]}>
          <torusGeometry args={[0.7, 0.012, 5, 48]} />
          <meshBasicMaterial color="#6f9a69" transparent opacity={0.75} />
        </mesh>
      </Float>
      <OrbitControls
        enablePan={false}
        enableZoom={false}
        minPolarAngle={Math.PI / 3.2}
        maxPolarAngle={Math.PI / 2.05}
        autoRotate
        autoRotateSpeed={0.2}
        target={new THREE.Vector3(0, 0.2, 0)}
      />
    </>
  );
}

export default function FieldScene() {
  return (
    <div className="field-scene" aria-label="Interactive 3D crop field">
      <Canvas
        shadows
        dpr={[1, 1.5]}
        camera={{ position: [5.4, 4.1, 6.6], fov: 39 }}
        gl={{ antialias: true, alpha: true }}
      >
        <Suspense fallback={null}>
          <SceneContent />
        </Suspense>
      </Canvas>
      <div className="scene-caption">
        <span className="scene-caption-dot" />
        FIELD HEALTH · LIVE VIEW
      </div>
    </div>
  );
}
