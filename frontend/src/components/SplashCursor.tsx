import { useEffect, useRef } from 'react';

// Fluid splash cursor — lightweight canvas-based ripple cursor
export function SplashCursor() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    interface Particle {
      x: number; y: number;
      vx: number; vy: number;
      life: number; maxLife: number;
      r: number; g: number; b: number; size: number;
    }

    const particles: Particle[] = [];
    let mouseX = -999, mouseY = -999;

    const COLORS = [
      { r: 6,   g: 182, b: 212 },
      { r: 139, g: 92,  b: 246 },
      { r: 16,  g: 185, b: 129 },
      { r: 99,  g: 102, b: 241 },
    ];

    function spawnParticle(x: number, y: number) {
      const color = COLORS[Math.floor(Math.random() * COLORS.length)];
      const angle = Math.random() * Math.PI * 2;
      const speed = 0.5 + Math.random() * 2;
      particles.push({
        x, y,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed,
        life: 0,
        maxLife: 40 + Math.random() * 40,
        r: color.r, g: color.g, b: color.b,
        size: 2 + Math.random() * 4,
      });
    }

    let frameId: number;
    let lastX = -1, lastY = -1;
    let spawnAcc = 0;

    function animate() {
      ctx!.clearRect(0, 0, width, height);
      const dx = mouseX - lastX, dy = mouseY - lastY;
      const dist = Math.sqrt(dx * dx + dy * dy);
      spawnAcc += dist;
      const step = 8;
      const steps = Math.floor(spawnAcc / step);
      for (let i = 0; i < steps; i++) {
        const t = (i + 1) / Math.max(steps, 1);
        spawnParticle(lastX + dx * t, lastY + dy * t);
      }
      spawnAcc -= steps * step;
      if (steps > 0) { lastX = mouseX; lastY = mouseY; }

      for (let i = particles.length - 1; i >= 0; i--) {
        const p = particles[i];
        p.life++;
        p.x += p.vx;
        p.y += p.vy;
        p.vx *= 0.97;
        p.vy *= 0.97;
        const progress = p.life / p.maxLife;
        const alpha = (1 - progress) * 0.7;
        const size = p.size * (1 - progress * 0.5);
        ctx!.beginPath();
        const grad = ctx!.createRadialGradient(p.x, p.y, 0, p.x, p.y, size * 2);
        grad.addColorStop(0, `rgba(${p.r},${p.g},${p.b},${alpha})`);
        grad.addColorStop(1, `rgba(${p.r},${p.g},${p.b},0)`);
        ctx!.fillStyle = grad;
        ctx!.arc(p.x, p.y, size * 2, 0, Math.PI * 2);
        ctx!.fill();
        if (p.life >= p.maxLife) particles.splice(i, 1);
      }
      frameId = requestAnimationFrame(animate);
    }

    const onMove = (e: MouseEvent) => {
      if (lastX === -1) { lastX = e.clientX; lastY = e.clientY; }
      mouseX = e.clientX; mouseY = e.clientY;
    };
    const onResize = () => {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };

    window.addEventListener('mousemove', onMove);
    window.addEventListener('resize', onResize);
    animate();

    return () => {
      cancelAnimationFrame(frameId);
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('resize', onResize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'fixed', inset: 0, pointerEvents: 'none',
        zIndex: 9999, mixBlendMode: 'screen',
      }}
    />
  );
}
