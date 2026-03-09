import React, { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { useGameStore } from '../../../store/useGameStore';
import { formatNumberCompact } from '../../../engine/math';

// ==========================================
// 1. LOOT TABLE (Таблица Эмоций)
// ==========================================
const EMOTES = {
  common: ['❤️', '🩷', '💕', '💖'],        
  uncommon: ['🧸', '🩹', '🫂', '🕯️', '🧶'], 
  rare: ['🐈', '🐈‍⬛', '💾', '🐾'],         
  legendary: ['❤️‍🔥', '💎', '✨', '🪐']      
};

const getRandomEmote = () => {
  const r = Math.random();
  if (r > 0.95) return EMOTES.legendary[Math.floor(Math.random() * EMOTES.legendary.length)];
  if (r > 0.85) return EMOTES.rare[Math.floor(Math.random() * EMOTES.rare.length)];
  if (r > 0.60) return EMOTES.uncommon[Math.floor(Math.random() * EMOTES.uncommon.length)];
  return EMOTES.common[Math.floor(Math.random() * EMOTES.common.length)];
};

interface ClickFxProps {
  children: React.ReactNode;
  className?: string;
}

interface Particle {
  element: HTMLElement;
  x: number;
  y: number;
  velX: number;
  velY: number;
  rotation: number;
  rotSpeed: number;
  scale: number;
  life: number;
  isText: boolean;
}

export const ClickFx: React.FC<ClickFxProps> = ({ children, className }) => {
  const { click, wallet } = useGameStore();
  const containerRef = useRef<HTMLDivElement>(null);
  
  const particlesRef = useRef<Particle[]>([]);
  const frameIdRef = useRef<number>(0);

  // --- PHYSICS ENGINE (FX ANIMATOR TUNING) ---
  const updateParticles = () => {
    const width = window.innerWidth;
    const height = window.innerHeight;
    
    // Гравитация сильнее для ощущения "веса" при высоком взлете
    const gravity = 0.8; 
    const dragEmoji = 0.96; // Эмодзи скользят по воздуху
    const dragText = 0.92;  // Текст тормозит быстрее (эффект зависания)

    for (let i = particlesRef.current.length - 1; i >= 0; i--) {
      const p = particlesRef.current[i];
      
      if (p.life <= 0 || !p.element.parentNode) {
        if (p.element.parentNode) p.element.remove();
        particlesRef.current.splice(i, 1);
        continue;
      }

      // Physics Math
      if (p.isText) {
        p.velX *= dragText;
        p.velY *= dragText;
        // Текст почти не падает вниз, он дрейфует вверх
        p.velY -= 0.1; 
      } else {
        p.velX *= dragEmoji;
        p.velY *= dragEmoji;
        p.velY += gravity;
      }

      p.x += p.velX;
      p.y += p.velY;
      p.rotation += p.rotSpeed;
      p.life--;

      // Bounds (Отскок от стен)
      if (p.x < 0 || p.x > width) {
        p.velX *= -0.7;
        p.x = p.x < 0 ? 0 : width;
      }
      
      // Пол (Только для эмодзи)
      if (!p.isText && p.y > height + 50) {
        // Убиваем частицы, упавшие за экран
        p.life = 0; 
      }

      // Apply styles
      // Плавное исчезновение масштаба для текста в конце
      const currentScale = p.isText 
        ? p.scale * (p.life < 20 ? p.life / 20 : 1) 
        : p.scale;

      p.element.style.transform = `translate(${p.x}px, ${p.y}px) rotate(${p.rotation}deg) scale(${currentScale})`;
      p.element.style.opacity = p.life < 30 ? (p.life / 30).toString() : '1';
    }

    if (particlesRef.current.length > 0) {
      frameIdRef.current = requestAnimationFrame(updateParticles);
    }
  };

  const spawnParticle = (x: number, y: number, type: 'text' | 'emoji', content: string) => {
    if (!containerRef.current) return;

    const el = document.createElement('div');
    el.innerHTML = content;
    el.style.position = 'absolute';
    el.style.pointerEvents = 'none';
    el.style.left = '0';
    el.style.top = '0';
    el.style.zIndex = type === 'text' ? '1000' : '100';
    el.style.willChange = 'transform, opacity';
    
    if (type === 'text') {
      el.className = 'font-mono font-black text-3xl text-white select-none';
      el.style.textShadow = '0 4px 8px rgba(0,0,0,0.6), 0 0 12px rgba(255,121,198,0.6)';
      el.style.webkitTextStroke = '1.5px #FF79C6';
      el.style.textStroke = '1.5px #FF79C6';
    } else {
      el.className = 'text-4xl select-none';
      el.style.filter = 'drop-shadow(0 4px 8px rgba(0,0,0,0.7))';
    }

    containerRef.current.appendChild(el);

    const isText = type === 'text';
    
    // --- JUICY CONFIGURATION (ANIMATOR'S TUNING) ---
    const particle: Particle = {
      element: el,
      x: x - (isText ? 20 : 20),
      y: y - (isText ? 50 : 20),
      
      // ТЕКСТ: Стреляет резко вверх с вариативностью
      // ЭМОДЗИ: Взрываются широким веером
      velX: isText 
        ? (Math.random() - 0.5) * 4 
        : (Math.random() - 0.5) * 30, // Широкий разброс (±15)
      
      // УВЕЛИЧЕНО В 2 РАЗА: Вертикальный импульс
      velY: isText 
        ? -15 - Math.random() * 8     // Текст: от -15 до -23 (очень высоко!)
        : -20 - Math.random() * 15,   // Эмодзи: от -20 до -35 (фейерверк!)
      
      rotation: Math.random() * 360,
      rotSpeed: (Math.random() - 0.5) * 25, // Безумное вращение (±12.5)
      
      scale: isText ? 1 : 0.6 + Math.random() * 0.6, // Вариативный размер
      life: isText ? 50 : 120 + Math.random() * 60,  // Эмодзи живут дольше
      isText
    };

    particlesRef.current.push(particle);
    
    if (particlesRef.current.length === 1) {
      frameIdRef.current = requestAnimationFrame(updateParticles);
    }
  };

  const handleTap = (e: React.PointerEvent) => {
    click();

    // Haptic: Можно сменить на 'medium' для еще большей сочности
    if (window.Telegram?.WebApp?.HapticFeedback) {
      window.Telegram.WebApp.HapticFeedback.impactOccurred('medium');
    }

    // Spawn Text ("+1" максимально сочно)
    const clickPower = 1 + (wallet.mints * 0.5);
    const text = `+${formatNumberCompact(clickPower, 1)}`;
    spawnParticle(e.clientX, e.clientY, 'text', text);

    // Spawn Emojis (Chaos Mode: от 1 до 3 штук)
    const count = Math.floor(Math.random() * 2) + 1; 
    for (let i = 0; i < count; i++) {
      spawnParticle(e.clientX, e.clientY, 'emoji', getRandomEmote());
    }
  };

  useEffect(() => {
    return () => {
      cancelAnimationFrame(frameIdRef.current);
      if (containerRef.current) containerRef.current.innerHTML = '';
      particlesRef.current = [];
    };
  }, []);

  return (
    <div 
      className={`relative ${className || ''}`} 
      onPointerDown={handleTap}
    >
      {/* SQUISH EFFECT: Более резкая пружина для "барабана" */}
      <motion.div
        whileTap={{ scale: 0.97 }}
        transition={{ type: 'spring', stiffness: 800, damping: 15 }}
        className="w-full h-full"
      >
        {children}
      </motion.div>

      {/* Контейнер для физических частиц */}
      <div 
        ref={containerRef}
        className="fixed inset-0 pointer-events-none z-[9999] overflow-hidden"
      />
    </div>
  );
};
