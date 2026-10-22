/**
 * AutoNexa 3D Interactive Automotive Canvas & Visual Engine
 * ==========================================================
 * Renders a silky-smooth, hardware-accelerated 3D wireframe vehicle chassis,
 * exploded assembly components, rotating telemetry HUD nodes, and particle streams.
 * Guarantees zero blank/black video states on Home and Login pages.
 */

(function() {
  function init3DHeroCanvas() {
    const canvas = document.getElementById('canvas3dHero');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    let width = (canvas.width = canvas.parentElement.clientWidth || 1100);
    let height = (canvas.height = canvas.parentElement.clientHeight || 560);

    window.addEventListener('resize', () => {
      if (!canvas.parentElement) return;
      width = canvas.width = canvas.parentElement.clientWidth || 1100;
      height = canvas.height = canvas.parentElement.clientHeight || 560;
    });

    let mouseX = 0;
    let mouseY = 0;
    let targetRotY = 0;
    let currentRotY = 0;

    const stage = canvas.parentElement;
    if (stage) {
      stage.addEventListener('mousemove', (e) => {
        const rect = stage.getBoundingClientRect();
        mouseX = ((e.clientX - rect.left) / width - 0.5) * 2;
        mouseY = ((e.clientY - rect.top) / height - 0.5) * 2;
        targetRotY = mouseX * 0.45;
      });
      stage.addEventListener('mouseleave', () => {
        targetRotY = 0;
      });
    }

    // 3D Exploded Automotive Assembly Nodes (Engine, Gearbox, 4 Struts, 4 Discs, Exhaust, Chassis)
    const assemblyNodes = [
      // Chassis Spine & Rails
      { x: -140, y: -20, z: -80, label: "Front Subframe", color: "#38bdf8" },
      { x: 140, y: -20, z: -80, label: "Front Subframe RH", color: "#38bdf8" },
      { x: -130, y: -20, z: 200, label: "Rear Axle LH", color: "#38bdf8" },
      { x: 130, y: -20, z: 200, label: "Rear Axle RH", color: "#38bdf8" },

      // Engine Block (Exploded View upward)
      { x: 0, y: -75, z: -90, label: "2.0L Turbo Engine Core", color: "#f59e0b", size: 6, pulse: true },
      { x: 0, y: -130, z: -90, label: "Intake Manifold & Rail", color: "#fbbf24", size: 4 },
      { x: -45, y: -45, z: -60, label: "Intercooler & Turbo", color: "#f97316", size: 5 },

      // Transmission & Clutch
      { x: 0, y: -30, z: -10, label: "Dual-Clutch Transmission", color: "#a855f7", size: 6, pulse: true },
      { x: 0, y: -10, z: 70, label: "Propshaft Assembly", color: "#c084fc", size: 4 },
      { x: 0, y: -15, z: 190, label: "Rear Differential", color: "#a855f7", size: 5 },

      // Suspension & Brake Corners (Exploded Outward)
      { x: -210, y: -50, z: -80, label: "FL Strut & Coil Spring", color: "#10b981", size: 5 },
      { x: -230, y: 15, z: -80, label: "FL Ventilated Brake Disc", color: "#34d399", size: 6, pulse: true },
      { x: 210, y: -50, z: -80, label: "FR Strut & Coil Spring", color: "#10b981", size: 5 },
      { x: 230, y: 15, z: -80, label: "FR Ventilated Brake Disc", color: "#34d399", size: 6, pulse: true },

      { x: -200, y: -40, z: 200, label: "RL Multi-Link Shock", color: "#10b981", size: 5 },
      { x: -220, y: 15, z: 200, label: "RL Brake Disc & Caliper", color: "#34d399", size: 5 },
      { x: 200, y: -40, z: 200, label: "RR Multi-Link Shock", color: "#10b981", size: 5 },
      { x: 220, y: 15, z: 200, label: "RR Brake Disc & Caliper", color: "#34d399", size: 5 }
    ];

    // Connection Links (Laser Lines)
    const links = [
      [0, 1], [0, 2], [1, 3], [2, 3], // Chassis box
      [4, 5], [4, 6], [4, 7], // Engine & turbo to transmission
      [7, 8], [8, 9], // Driveshaft
      [0, 10], [10, 11], // Front Left Corner
      [1, 12], [12, 13], // Front Right Corner
      [2, 14], [14, 15], // Rear Left Corner
      [3, 16], [16, 17]  // Rear Right Corner
    ];

    // Floating Ambient Particles
    const particles = [];
    for (let i = 0; i < 45; i++) {
      particles.push({
        x: (Math.random() - 0.5) * 600,
        y: (Math.random() - 0.5) * 350,
        z: (Math.random() - 0.5) * 500,
        vy: -0.35 - Math.random() * 0.45,
        color: Math.random() > 0.5 ? "rgba(56, 189, 248, 0.4)" : "rgba(168, 85, 247, 0.4)",
        size: 1.5 + Math.random() * 2
      });
    }

    let angle = 0;

    function render() {
      ctx.clearRect(0, 0, width, height);

      angle += 0.007;
      currentRotY += (targetRotY - currentRotY) * 0.05;
      const effectiveRotY = angle * 0.5 + currentRotY;

      const fov = 420;
      const centerX = width * 0.5;
      const centerY = height * 0.52;

      // Project function
      function project(x, y, z) {
        // Rotate around Y
        const cosY = Math.cos(effectiveRotY);
        const sinY = Math.sin(effectiveRotY);
        const rx = x * cosY - z * sinY;
        const rz = x * sinY + z * cosY + 440;

        // Subtle pitch angle
        const pitch = 0.22 + mouseY * 0.12;
        const cosP = Math.cos(pitch);
        const sinP = Math.sin(pitch);
        const ry = y * cosP - rz * sinP;
        const finalZ = y * sinP + rz * cosP;

        const scale = fov / Math.max(finalZ, 120);
        return {
          px: centerX + rx * scale,
          py: centerY + ry * scale,
          scale: scale,
          z: finalZ
        };
      }

      // Draw Laser Wireframe Links
      ctx.lineWidth = 1.4;
      links.forEach(([i, j]) => {
        const p1 = project(assemblyNodes[i].x, assemblyNodes[i].y, assemblyNodes[i].z);
        const p2 = project(assemblyNodes[j].x, assemblyNodes[j].y, assemblyNodes[j].z);

        const grad = ctx.createLinearGradient(p1.px, p1.py, p2.px, p2.py);
        grad.addColorStop(0, "rgba(56, 189, 248, 0.45)");
        grad.addColorStop(1, "rgba(168, 85, 247, 0.45)");

        ctx.strokeStyle = grad;
        ctx.beginPath();
        ctx.moveTo(p1.px, p1.py);
        ctx.lineTo(p2.px, p2.py);
        ctx.stroke();
      });

      // Draw Exploded Assembly Nodes
      assemblyNodes.forEach((node, idx) => {
        const p = project(node.x, node.y, node.z);
        const r = (node.size || 4.5) * p.scale;

        // Glowing outer pulse ring
        if (node.pulse) {
          const pulseR = r + Math.sin(angle * 4 + idx) * (r * 0.7);
          ctx.beginPath();
          ctx.arc(p.px, p.py, Math.max(pulseR, 2), 0, Math.PI * 2);
          ctx.strokeStyle = node.color;
          ctx.globalAlpha = 0.35;
          ctx.stroke();
          ctx.globalAlpha = 1.0;
        }

        // Inner solid core
        ctx.beginPath();
        ctx.arc(p.px, p.py, Math.max(r, 2.5), 0, Math.PI * 2);
        ctx.fillStyle = node.color;
        ctx.shadowColor = node.color;
        ctx.shadowBlur = 10;
        ctx.fill();
        ctx.shadowBlur = 0;

        // Label on larger nodes
        if (node.size && node.size >= 5.5 && p.scale > 0.7) {
          ctx.font = "800 10px 'Outfit', sans-serif";
          ctx.fillStyle = "#ffffff";
          ctx.fillText(node.label, p.px + r + 6, p.py + 3);
        }
      });

      // Draw Particles
      particles.forEach((pt) => {
        pt.y += pt.vy;
        if (pt.y < -220) pt.y = 220;

        const p = project(pt.x, pt.y, pt.z);
        ctx.beginPath();
        ctx.arc(p.px, p.py, Math.max(pt.size * p.scale * 0.8, 1), 0, Math.PI * 2);
        ctx.fillStyle = pt.color;
        ctx.fill();
      });

      // HUD Coordinate Overlay in bottom-right corner
      ctx.font = "700 11px monospace";
      ctx.fillStyle = "rgba(56, 189, 248, 0.75)";
      ctx.fillText(`3D EXPLODED TELEMETRY • ROT_Y: ${(effectiveRotY % (Math.PI * 2)).toFixed(2)} rad • 18 NODES ACTIVE`, 28, height - 24);

      requestAnimationFrame(render);
    }

    render();
  }

  // Auto-init when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init3DHeroCanvas);
  } else {
    init3DHeroCanvas();
  }

  window.init3DHeroCanvas = init3DHeroCanvas;
})();
