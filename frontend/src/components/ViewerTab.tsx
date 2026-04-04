import { useEffect, useRef, useState } from 'react';
import { Box, Typography, Alert, CircularProgress } from '@mui/material';
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import * as WEBIFC from 'web-ifc';
import { API_BASE } from '../api/client';

interface Props {
  projectId: string;
}

export default function ViewerTab({ projectId }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const container = containerRef.current;
    let disposed = false;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x1a1a2e);

    const camera = new THREE.PerspectiveCamera(
      50,
      container.clientWidth / container.clientHeight,
      0.1,
      1000,
    );
    camera.position.set(30, 30, 30);

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;

    // Lights
    scene.add(new THREE.AmbientLight(0xffffff, 0.6));
    const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
    dirLight.position.set(50, 50, 50);
    scene.add(dirLight);
    const dirLight2 = new THREE.DirectionalLight(0xffffff, 0.3);
    dirLight2.position.set(-50, 20, -50);
    scene.add(dirLight2);

    // Grid
    const grid = new THREE.GridHelper(100, 100, 0x444466, 0x333355);
    scene.add(grid);

    // Animation loop
    const animate = () => {
      if (disposed) return;
      requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    // Resize handler
    const onResize = () => {
      if (!container.clientWidth || !container.clientHeight) return;
      camera.aspect = container.clientWidth / container.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(container.clientWidth, container.clientHeight);
    };
    const resizeObserver = new ResizeObserver(onResize);
    resizeObserver.observe(container);

    // Load IFC
    const loadIFC = async () => {
      try {
        const ifcAPI = new WEBIFC.IfcAPI();
        ifcAPI.SetWasmPath('https://unpkg.com/web-ifc@0.0.77/');
        await ifcAPI.Init();

        const res = await fetch(`${API_BASE}/api/models/${projectId}/file`);
        if (!res.ok) throw new Error('Не удалось загрузить IFC-файл');
        const buffer = await res.arrayBuffer();
        const data = new Uint8Array(buffer);

        if (disposed) return;

        const modelID = ifcAPI.OpenModel(data);
        const modelGroup = new THREE.Group();

        // Get all mesh geometries
        ifcAPI.StreamAllMeshes(modelID, (mesh: WEBIFC.FlatMesh) => {
          const placedGeometries = mesh.geometries;

          for (let i = 0; i < placedGeometries.size(); i++) {
            const pg = placedGeometries.get(i);
            const geomData = ifcAPI.GetGeometry(modelID, pg.geometryExpressID);

            const verts = ifcAPI.GetVertexArray(
              geomData.GetVertexData(),
              geomData.GetVertexDataSize(),
            );
            const indices = ifcAPI.GetIndexArray(
              geomData.GetIndexData(),
              geomData.GetIndexDataSize(),
            );

            const geometry = new THREE.BufferGeometry();
            const posFloats = new Float32Array(verts.length / 2);
            const normFloats = new Float32Array(verts.length / 2);

            for (let j = 0; j < verts.length; j += 6) {
              posFloats[j / 2] = verts[j];
              posFloats[j / 2 + 1] = verts[j + 1];
              posFloats[j / 2 + 2] = verts[j + 2];
              normFloats[j / 2] = verts[j + 3];
              normFloats[j / 2 + 1] = verts[j + 4];
              normFloats[j / 2 + 2] = verts[j + 5];
            }

            geometry.setAttribute('position', new THREE.BufferAttribute(posFloats, 3));
            geometry.setAttribute('normal', new THREE.BufferAttribute(normFloats, 3));
            geometry.setIndex(new THREE.BufferAttribute(indices, 1));

            const color = new THREE.Color(pg.color.x, pg.color.y, pg.color.z);
            const material = new THREE.MeshPhongMaterial({
              color,
              opacity: pg.color.w,
              transparent: pg.color.w < 1,
              side: THREE.DoubleSide,
            });

            const mesh3D = new THREE.Mesh(geometry, material);

            const matrix = new THREE.Matrix4();
            matrix.fromArray(pg.flatTransformation);
            mesh3D.applyMatrix4(matrix);

            modelGroup.add(mesh3D);

            geomData.delete();
          }
        });

        if (disposed) return;

        scene.add(modelGroup);

        // Center camera on model
        const box = new THREE.Box3().setFromObject(modelGroup);
        const center = box.getCenter(new THREE.Vector3());
        const size = box.getSize(new THREE.Vector3());
        const maxDim = Math.max(size.x, size.y, size.z);

        controls.target.copy(center);
        camera.position.set(
          center.x + maxDim,
          center.y + maxDim * 0.7,
          center.z + maxDim,
        );
        camera.lookAt(center);
        controls.update();

        ifcAPI.CloseModel(modelID);

        setLoading(false);
      } catch (e: any) {
        console.error('IFC load error:', e);
        if (!disposed) {
          setError(e.message || 'Ошибка загрузки модели');
          setLoading(false);
        }
      }
    };

    loadIFC();

    return () => {
      disposed = true;
      resizeObserver.disconnect();
      renderer.dispose();
      container.removeChild(renderer.domElement);
    };
  }, [projectId]);

  return (
    <Box>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {loading && (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
          <CircularProgress size={24} />
          <Typography>Загрузка 3D-модели...</Typography>
        </Box>
      )}
      <Box
        ref={containerRef}
        sx={{
          width: '100%',
          height: 'calc(100vh - 240px)',
          minHeight: 400,
          borderRadius: 1,
          border: '1px solid',
          borderColor: 'divider',
          bgcolor: '#1a1a2e',
          position: 'relative',
        }}
      />
    </Box>
  );
}
