"""
components/three_scene.py
=========================
Streamlit-compatible interactive 3D plant and crop field visualizer using Three.js.
Preserves the exact crop geometry, leaf structure, colors, soil base, and OrbitControls
from the original AgriVision React 3D FieldScene.
"""

from __future__ import annotations

import streamlit.components.v1 as components


def render_3d_plant_scene(
    height: int = 420,
    view_mode: str = "field",
    auto_rotate: bool = True,
) -> None:
    """
    Render the interactive 3D plant model or crop field using Three.js and OrbitControls.
    - view_mode: "field" (crop rows with furrow ground) or "plant" (single plant close-up)
    - auto_rotate: enables gentle rotation (pauses when user drags to inspect)
    """
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body, html {{
          margin: 0;
          padding: 0;
          overflow: hidden;
          width: 100%;
          height: 100%;
          background: #edf1e6;
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }}
        #canvas-container {{
          width: 100%;
          height: 100%;
          position: relative;
        }}
        #badge {{
          position: absolute;
          top: 12px;
          left: 14px;
          background: rgba(255, 255, 255, 0.88);
          backdrop-filter: blur(6px);
          border: 1px solid rgba(27, 61, 38, 0.15);
          border-radius: 999px;
          padding: 4px 12px;
          font-size: 11px;
          font-weight: 600;
          color: #1b3d26;
          pointer-events: none;
          box-shadow: 0 2px 8px rgba(0,0,0,0.05);
          display: flex;
          align-items: center;
          gap: 5px;
        }}
        #instructions {{
          position: absolute;
          bottom: 10px;
          right: 14px;
          background: rgba(255, 255, 255, 0.85);
          border-radius: 6px;
          padding: 3px 8px;
          font-size: 10px;
          color: #5e6057;
          pointer-events: none;
        }}
        #loader {{
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          font-size: 12px;
          color: #5e6057;
          font-weight: 500;
          transition: opacity 0.3s ease;
        }}
      </style>
      <!-- Three.js and OrbitControls via reliable CDN -->
      <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
      <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    </head>
    <body>
      <div id="canvas-container">
        <div id="badge">🌱 AgriVision 3D Foliage Visualizer ({view_mode.title()} Mode)</div>
        <div id="instructions">Drag to rotate · Scroll to zoom</div>
        <div id="loader">Initializing 3D geometry...</div>
      </div>

      <script>
        const container = document.getElementById('canvas-container');
        const loader = document.getElementById('loader');
        const isField = "{view_mode}" === "field";
        const autoRotateInitial = {str(auto_rotate).lower()};
        const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

        // Scene, Camera, Renderer
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0xedf1e6);
        scene.fog = new THREE.Fog(0xedf1e6, 7, 18);

        const width = container.clientWidth || 600;
        const height = container.clientHeight || {height};
        const camera = new THREE.PerspectiveCamera(38, width / height, 0.1, 50);
        
        if (isField) {{
          camera.position.set(5.2, 3.8, 6.2);
        }} else {{
          camera.position.set(0.2, 0.8, 2.2);
        }}

        const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true }});
        renderer.setSize(width, height);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        container.appendChild(renderer.domElement);

        // Lighting
        const ambientLight = new THREE.AmbientLight(0xffffff, 1.6);
        scene.add(ambientLight);

        const dirLight = new THREE.DirectionalLight(0xfffaed, 2.0);
        dirLight.position.set(5, 8, 5);
        dirLight.castShadow = true;
        dirLight.shadow.mapSize.width = 1024;
        dirLight.shadow.mapSize.height = 1024;
        scene.add(dirLight);

        // Controls
        const controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;
        controls.enablePan = false;
        controls.autoRotate = autoRotateInitial && !prefersReducedMotion;
        controls.autoRotateSpeed = 0.5;
        controls.minDistance = 1.2;
        controls.maxDistance = 14;
        controls.maxPolarAngle = Math.PI / 2.05;
        controls.minPolarAngle = Math.PI / 4;
        controls.target.set(0, isField ? 0.3 : 0.45, 0);

        // Build Single Plant Hierarchy
        function createPlant(scale = 1.0) {{
          const plant = new THREE.Group();
          plant.scale.set(scale, scale, scale);

          // Stem
          const stemGeo = new THREE.CylinderGeometry(0.018, 0.027, 0.72, 8);
          const stemMat = new THREE.MeshStandardMaterial({{ color: 0x55734b, roughness: 0.9 }});
          const stem = new THREE.Mesh(stemGeo, stemMat);
          stem.position.y = 0.36;
          stem.castShadow = true;
          plant.add(stem);

          // Lateral Leaves
          const leaf1Geo = new THREE.SphereGeometry(0.16, 12, 10);
          leaf1Geo.scale(1.2, 0.4, 0.8);
          const leaf1Mat = new THREE.MeshStandardMaterial({{ color: 0x789759, roughness: 0.75 }});
          
          const leafL = new THREE.Mesh(leaf1Geo, leaf1Mat);
          leafL.position.set(-0.14, 0.46, 0);
          leafL.rotation.set(0, 0, 0.5);
          leafL.castShadow = true;
          plant.add(leafL);

          const leaf2Mat = new THREE.MeshStandardMaterial({{ color: 0x92a968, roughness: 0.75 }});
          const leafR = new THREE.Mesh(leaf1Geo, leaf2Mat);
          leafR.position.set(0.14, 0.58, 0);
          leafR.rotation.set(0, 0, -0.5);
          leafR.castShadow = true;
          plant.add(leafR);

          // Crown Foliage
          const crownGeo = new THREE.SphereGeometry(0.13, 10, 8);
          crownGeo.scale(1.1, 0.5, 0.9);
          const crownMat = new THREE.MeshStandardMaterial({{ color: 0xa6b96e, roughness: 0.7 }});
          const crown = new THREE.Mesh(crownGeo, crownMat);
          crown.position.set(0.02, 0.74, 0);
          crown.rotation.set(0.15, 0, -0.2);
          crown.castShadow = true;
          plant.add(crown);

          return plant;
        }}

        // Scene Content Assembly
        if (isField) {{
          const fieldGroup = new THREE.Group();
          fieldGroup.rotation.x = -0.12;
          fieldGroup.rotation.y = 0.22;

          // Soil Base
          const groundGeo = new THREE.PlaneGeometry(9.5, 7.5);
          const groundMat = new THREE.MeshStandardMaterial({{ color: 0xb7a77b, roughness: 1.0 }});
          const ground = new THREE.Mesh(groundGeo, groundMat);
          ground.rotation.x = -Math.PI / 2;
          ground.position.y = -0.06;
          ground.receiveShadow = true;
          fieldGroup.add(ground);

          // Furrows
          [-1.8, 0, 1.8].forEach((fx, idx) => {{
            const furrowGeo = new THREE.PlaneGeometry(0.11, 7.2);
            const furrowMat = new THREE.MeshBasicMaterial({{ color: idx === 1 ? 0xd9c99d : 0xa99667 }});
            const furrow = new THREE.Mesh(furrowGeo, furrowMat);
            furrow.rotation.x = -Math.PI / 2;
            furrow.position.set(fx, 0.01, 0);
            fieldGroup.add(furrow);
          }});

          // 8 Rows x 9 Plants
          for (let r = 0; r < 7; r++) {{
            for (let p = 0; p < 8; p++) {{
              const px = (p - 3.5) * 0.68 + (r % 2) * 0.25;
              const pz = (r - 3) * 0.72;
              const plantScale = 0.75 + ((r * 7 + p * 3) % 4) * 0.06;
              const crop = createPlant(plantScale);
              crop.position.set(px, 0, pz);
              fieldGroup.add(crop);
            }}
          }}

          // Botanical Atmospheric Halo
          const torusGeo = new THREE.TorusGeometry(0.75, 0.014, 6, 48);
          const torusMat = new THREE.MeshBasicMaterial({{ color: 0x6f9a69, transparent: true, opacity: 0.65 }});
          const halo = new THREE.Mesh(torusGeo, torusMat);
          halo.position.set(1.9, 1.2, 0.2);
          halo.rotation.x = 0.3;
          fieldGroup.add(halo);

          scene.add(fieldGroup);
        }} else {{
          // Single Plant Close-up
          const plantRoot = new THREE.Group();
          
          // Pot / Soil Mound
          const potGeo = new THREE.CylinderGeometry(0.42, 0.32, 0.35, 24);
          const potMat = new THREE.MeshStandardMaterial({{ color: 0x7c6957, roughness: 0.95 }});
          const pot = new THREE.Mesh(potGeo, potMat);
          pot.position.y = 0.17;
          pot.receiveShadow = true;
          plantRoot.add(pot);

          const soilGeo = new THREE.CircleGeometry(0.40, 24);
          const soilMat = new THREE.MeshStandardMaterial({{ color: 0x4a3d31, roughness: 1.0 }});
          const soil = new THREE.Mesh(soilGeo, soilMat);
          soil.rotation.x = -Math.PI / 2;
          soil.position.y = 0.345;
          plantRoot.add(soil);

          const specimen = createPlant(1.35);
          specimen.position.y = 0.34;
          plantRoot.add(specimen);

          scene.add(plantRoot);
        }}

        // Hide Loader
        loader.style.opacity = '0';
        setTimeout(() => loader.remove(), 350);

        // Animation Loop
        let frameId;
        function animate() {{
          frameId = requestAnimationFrame(animate);
          controls.update();
          renderer.render(scene, camera);
        }}
        animate();

        // Responsive Resizing
        window.addEventListener('resize', () => {{
          const nw = container.clientWidth || 600;
          const nh = container.clientHeight || {height};
          camera.aspect = nw / nh;
          camera.updateProjectionMatrix();
          renderer.setSize(nw, nh);
        }});
      </script>
    </body>
    </html>
    """
    components.html(html_code, height=height, scrolling=False)
