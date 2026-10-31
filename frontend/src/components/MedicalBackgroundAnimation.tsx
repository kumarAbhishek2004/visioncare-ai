"use client";

import React, { useEffect, useRef } from "react";

interface BokehSphere {
  x: number;
  y: number;
  radius: number;
  baseAlpha: number;
  speedY: number;
  oscSpeed: number;
  oscAmp: number;
  phase: number;
  hue: "cyan" | "blue" | "sky" | "deep";
  blur: number;
}

interface StarSparkle {
  xPct: number;
  yPct: number;
  size: number;
  phase: number;
  speed: number;
}

export const MedicalBackgroundAnimation: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationFrameId: number;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    // Parallax tracking
    let targetMouseX = 0;
    let targetMouseY = 0;
    let mouseX = 0;
    let mouseY = 0;

    const handleMouseMove = (e: MouseEvent) => {
      targetMouseX = (e.clientX - width / 2) / (width / 2);
      targetMouseY = (e.clientY - height / 2) / (height / 2);
    };

    window.addEventListener("mousemove", handleMouseMove, { passive: true });

    // Handle high-DPI resize
    const handleResize = () => {
      if (!canvas) return;
      const dpr = window.devicePixelRatio || 1;
      width = window.innerWidth;
      height = window.innerHeight;
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      ctx.scale(dpr, dpr);
    };

    handleResize();
    window.addEventListener("resize", handleResize);

    // 1. Initialize Bokeh Spheres (Matching the floating soft-focus spheres in reference image)
    const NUM_SPHERES = 24;
    const spheres: BokehSphere[] = [];

    const hues: BokehSphere["hue"][] = ["cyan", "blue", "sky", "deep"];

    for (let i = 0; i < NUM_SPHERES; i++) {
      spheres.push({
        x: Math.random() * width,
        y: Math.random() * height,
        radius: 8 + Math.random() * 32, // Some small, some large depth-of-field orbs
        baseAlpha: 0.18 + Math.random() * 0.35,
        speedY: -(0.2 + Math.random() * 0.4), // Gentle upward buoyancy
        oscSpeed: 0.01 + Math.random() * 0.02,
        oscAmp: 10 + Math.random() * 30,
        phase: Math.random() * Math.PI * 2,
        hue: hues[Math.floor(Math.random() * hues.length)],
        blur: Math.random() > 0.4 ? 12 : 3,
      });
    }

    // 2. Fixed Star Sparkles (Focal points like on the reference image)
    const sparkles: StarSparkle[] = [
      { xPct: 0.18, yPct: 0.28, size: 14, phase: 0, speed: 0.025 },
      { xPct: 0.26, yPct: 0.38, size: 18, phase: 1.5, speed: 0.03 },
      { xPct: 0.42, yPct: 0.62, size: 12, phase: 3.0, speed: 0.02 },
      { xPct: 0.68, yPct: 0.48, size: 15, phase: 4.2, speed: 0.035 },
      { xPct: 0.86, yPct: 0.22, size: 16, phase: 2.1, speed: 0.028 },
      { xPct: 0.82, yPct: 0.72, size: 13, phase: 0.8, speed: 0.032 },
    ];

    let time = 0;

    // Helper: Draw 4-point medical sparkle
    const drawStarSparkle = (
      cx: number,
      cy: number,
      size: number,
      alpha: number
    ) => {
      ctx.save();
      ctx.translate(cx, cy);
      ctx.globalAlpha = Math.max(0, Math.min(1, alpha));

      // Glow center
      const radGrad = ctx.createRadialGradient(0, 0, 0, 0, 0, size * 1.5);
      radGrad.addColorStop(0, "rgba(255, 255, 255, 0.95)");
      radGrad.addColorStop(0.35, "rgba(56, 189, 248, 0.65)");
      radGrad.addColorStop(1, "rgba(56, 189, 248, 0)");
      ctx.fillStyle = radGrad;
      ctx.beginPath();
      ctx.arc(0, 0, size * 1.5, 0, Math.PI * 2);
      ctx.fill();

      // 4-point sharp star flare
      ctx.fillStyle = "rgba(255, 255, 255, 0.9)";
      ctx.beginPath();
      ctx.moveTo(0, -size);
      ctx.quadraticCurveTo(0, 0, size, 0);
      ctx.quadraticCurveTo(0, 0, 0, size);
      ctx.quadraticCurveTo(0, 0, -size, 0);
      ctx.quadraticCurveTo(0, 0, 0, -size);
      ctx.closePath();
      ctx.fill();

      ctx.restore();
    };

    // Helper: Draw Sinuous Wave Ribbons (matching the flow lines in user image)
    const drawFlowingRibbons = (parallaxOffsetX: number, parallaxOffsetY: number) => {
      ctx.save();
      const waveCount = 5;
      const baseFreq = 0.0018;

      for (let w = 0; w < waveCount; w++) {
        ctx.beginPath();
        const strandOffset = w * 18;
        const phaseShift = time * 0.0012 + w * 0.25;

        // Gradient for wave ribbons (soft cyan to sky-blue to transparent)
        const waveGrad = ctx.createLinearGradient(0, 0, width, height);
        waveGrad.addColorStop(0, "rgba(56, 189, 248, 0.05)");
        waveGrad.addColorStop(0.25, `rgba(56, 189, 248, ${0.28 - w * 0.04})`);
        waveGrad.addColorStop(0.65, `rgba(96, 165, 250, ${0.32 - w * 0.04})`);
        waveGrad.addColorStop(1, "rgba(147, 197, 253, 0.05)");

        ctx.strokeStyle = waveGrad;
        ctx.lineWidth = 1.2 + (waveCount - w) * 0.3;

        for (let x = 0; x <= width; x += 12) {
          // Double harmonic wave equation creating smooth biological fluid ribbon
          const waveY =
            height * 0.62 +
            strandOffset +
            parallaxOffsetY * 15 +
            Math.sin(x * baseFreq + phaseShift) * (65 + w * 6) +
            Math.cos(x * (baseFreq * 1.7) - phaseShift * 0.8) * 35;

          if (x === 0) {
            ctx.moveTo(x + parallaxOffsetX * 10, waveY);
          } else {
            ctx.lineTo(x + parallaxOffsetX * 10, waveY);
          }
        }
        ctx.stroke();
      }
      ctx.restore();
    };

    // Main 60fps render loop
    const render = () => {
      time += 1;

      // Smooth mouse parallax lerp
      mouseX += (targetMouseX - mouseX) * 0.05;
      mouseY += (targetMouseY - mouseY) * 0.05;

      ctx.clearRect(0, 0, width, height);

      const parallaxX = mouseX * 18;
      const parallaxY = mouseY * 12;

      // 1. Draw Flowing Sinuous Wave Ribbons
      drawFlowingRibbons(parallaxX, parallaxY);

      // 2. Draw Orbiting Light Halo around the Pulmonary Lungs (Left Side)
      const lungCenterX = width * 0.17 + parallaxX * 0.8;
      const lungCenterY = height * 0.34 + parallaxY * 0.8;
      const orbitRadiusX = 140;
      const orbitRadiusY = 85;
      const orbitAngle = time * 0.014;

      ctx.save();
      ctx.translate(lungCenterX, lungCenterY);
      ctx.rotate(-0.35); // Ellipse tilt matching the lung contour in image

      // Faint orbital path ellipse
      ctx.strokeStyle = "rgba(56, 189, 248, 0.22)";
      ctx.lineWidth = 1;
      ctx.setLineDash([4, 6]);
      ctx.beginPath();
      ctx.ellipse(0, 0, orbitRadiusX, orbitRadiusY, 0, 0, Math.PI * 2);
      ctx.stroke();
      ctx.setLineDash([]);

      // Orbiting light photon
      const photonX = Math.cos(orbitAngle) * orbitRadiusX;
      const photonY = Math.sin(orbitAngle) * orbitRadiusY;

      // Glow behind photon
      const photonGrad = ctx.createRadialGradient(
        photonX,
        photonY,
        0,
        photonX,
        photonY,
        22
      );
      photonGrad.addColorStop(0, "rgba(255, 255, 255, 0.9)");
      photonGrad.addColorStop(0.3, "rgba(56, 189, 248, 0.8)");
      photonGrad.addColorStop(1, "rgba(56, 189, 248, 0)");
      ctx.fillStyle = photonGrad;
      ctx.beginPath();
      ctx.arc(photonX, photonY, 22, 0, Math.PI * 2);
      ctx.fill();

      ctx.restore();

      // 3. Draw Floating Bokeh Spheres (Exact feel from reference image)
      for (const sphere of spheres) {
        sphere.y += sphere.speedY;
        sphere.phase += sphere.oscSpeed;

        // Wrap around vertically
        if (sphere.y + sphere.radius < -20) {
          sphere.y = height + sphere.radius + 10;
          sphere.x = Math.random() * width;
        }

        const oscX = Math.sin(sphere.phase) * sphere.oscAmp;
        const drawX = sphere.x + oscX + parallaxX * (sphere.radius / 18);
        const drawY = sphere.y + parallaxY * (sphere.radius / 18);

        ctx.save();
        const radGrad = ctx.createRadialGradient(
          drawX - sphere.radius * 0.25,
          drawY - sphere.radius * 0.25,
          0,
          drawX,
          drawY,
          sphere.radius
        );

        if (sphere.hue === "cyan") {
          radGrad.addColorStop(0, `rgba(186, 230, 253, ${sphere.baseAlpha * 1.2})`);
          radGrad.addColorStop(0.55, `rgba(56, 189, 248, ${sphere.baseAlpha})`);
          radGrad.addColorStop(1, "rgba(56, 189, 248, 0)");
        } else if (sphere.hue === "blue") {
          radGrad.addColorStop(0, `rgba(191, 219, 254, ${sphere.baseAlpha * 1.1})`);
          radGrad.addColorStop(0.5, `rgba(96, 165, 250, ${sphere.baseAlpha})`);
          radGrad.addColorStop(1, "rgba(59, 130, 246, 0)");
        } else if (sphere.hue === "sky") {
          radGrad.addColorStop(0, `rgba(224, 242, 254, ${sphere.baseAlpha * 1.3})`);
          radGrad.addColorStop(0.6, `rgba(125, 211, 252, ${sphere.baseAlpha * 0.8})`);
          radGrad.addColorStop(1, "rgba(14, 165, 233, 0)");
        } else {
          radGrad.addColorStop(0, `rgba(165, 180, 252, ${sphere.baseAlpha})`);
          radGrad.addColorStop(0.6, `rgba(99, 102, 241, ${sphere.baseAlpha * 0.7})`);
          radGrad.addColorStop(1, "rgba(99, 102, 241, 0)");
        }

        ctx.fillStyle = radGrad;
        ctx.beginPath();
        ctx.arc(drawX, drawY, sphere.radius, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      }

      // 4. Draw Twinkling Medical Sparkles
      for (const sp of sparkles) {
        sp.phase += sp.speed;
        const currentAlpha = 0.25 + 0.7 * Math.sin(sp.phase) ** 2;
        const sx = width * sp.xPct + parallaxX * 1.2;
        const sy = height * sp.yPct + parallaxY * 1.2;
        drawStarSparkle(sx, sy, sp.size, currentAlpha);
      }

      // 5. Draw Molecular Hexagon Nodes (Top-right & bottom-left subtle chemistry lattice)
      ctx.save();
      const nodePulse = (Math.sin(time * 0.03) + 1) / 2;
      ctx.fillStyle = `rgba(56, 189, 248, ${0.4 + nodePulse * 0.4})`;
      ctx.strokeStyle = `rgba(147, 197, 253, ${0.25 + nodePulse * 0.25})`;
      ctx.lineWidth = 1;

      const hexBaseX = width * 0.88 + parallaxX * 0.5;
      const hexBaseY = height * 0.16 + parallaxY * 0.5;

      // Small molecular cluster
      const clusterPoints = [
        [hexBaseX, hexBaseY],
        [hexBaseX + 35, hexBaseY - 20],
        [hexBaseX + 70, hexBaseY],
        [hexBaseX + 70, hexBaseY + 40],
        [hexBaseX + 35, hexBaseY + 60],
        [hexBaseX, hexBaseY + 40],
      ];

      ctx.beginPath();
      clusterPoints.forEach(([px, py], idx) => {
        if (idx === 0) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
      });
      ctx.closePath();
      ctx.stroke();

      clusterPoints.forEach(([px, py]) => {
        ctx.beginPath();
        ctx.arc(px, py, 2.5, 0, Math.PI * 2);
        ctx.fill();
      });

      ctx.restore();

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener("resize", handleResize);
      window.removeEventListener("mousemove", handleMouseMove);
    };
  }, []);

  return (
    <div className="fixed inset-0 pointer-events-none overflow-hidden z-0 select-none">
      {/* 1. High-Resolution Photographic Base Layer (User's Exact Pulmonary Medical Artwork) */}
      <div className="absolute inset-0 w-full h-full">
        <img
          src="/images/medical-ambient-bg-2x.png"
          alt="Pulmonary Ambient Medical Artwork"
          className="w-full h-full object-cover object-left-top sm:object-center opacity-85 transition-opacity duration-1000 animate-lung-breathe"
        />
      </div>

      {/* 2. Soft Ambient Lighting Gradients (Ensuring pristine readability while accentuating blue hues) */}
      <div className="absolute inset-0 bg-gradient-to-b from-white/35 via-transparent to-white/40 pointer-events-none"></div>
      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-white/30 pointer-events-none"></div>

      {/* 3. 60FPS Live Animated Canvas Layer (Moving Ribbons, Bokeh Spheres, Orbiting Light, Twinkling Stars) */}
      <canvas
        ref={canvasRef}
        className="absolute inset-0 w-full h-full pointer-events-none"
      />
    </div>
  );
};
