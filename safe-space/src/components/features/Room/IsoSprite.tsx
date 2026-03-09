import React from 'react';
import { motion } from 'framer-motion';
import type { AssetId } from '../../../assets/assetMap';
import { getAssetUrl } from '../../../assets/assetMap';
import clsx from 'clsx';

interface IsoSpriteProps {
  id: AssetId;
  x: number;
  y: number;
  zIndex: number;
  scale?: number;
  className?: string;
  onClick?: () => void;
  animate?: boolean;
  
  /** Включить анимацию дыхания (для живых существ) */
  breathing?: boolean;
}

export const IsoSprite: React.FC<IsoSpriteProps> = ({
  id,
  x,
  y,
  zIndex,
  scale = 1,
  className,
  onClick,
  animate = true,
  breathing = false,
}) => {
  const src = getAssetUrl(id);

  if (!src) return null;

  // Варианты анимации дыхания
  const breathingVariants = {
    idle: {
      scale: [1, 1.02, 1], // Легкое увеличение
      y: [0, -2, 0],       // Легкое всплытие
      transition: {
        duration: 4,      // Медленно (4 секунды цикл)
        repeat: Infinity,
        ease: "easeInOut",
        times: [0, 0.5, 1] // Пик в середине
      }
    }
  };

  return (
    <div
      className={clsx('absolute pointer-events-auto cursor-pointer', className)}
      style={{
        left: `${x}%`,
        top: `${y}%`,
        zIndex,
        width: `${100 * scale}%`,
        height: 'auto',
        transform: 'translate(-50%, -50%)', // Центрирование контейнера
      }}
      onClick={(e) => {
        if (onClick) {
          e.stopPropagation(); // Чтобы клик по предмету не триггерил клик по комнате дважды
          onClick();
        }
      }}
    >
      <motion.img
        src={src}
        alt={id}
        className="w-full h-full object-contain select-none"
        draggable={false}
        
        // Входная анимация (появление)
        initial={animate ? { opacity: 0, scale: 0.8 } : { opacity: 1, scale: 1 }}
        animate={animate ? { opacity: 1, scale: 1 } : undefined}
        transition={{ type: 'spring', stiffness: 200, damping: 15 }}
        
        // Анимация нажатия (Squish)
        whileTap={{ scale: 0.95 }}

        // Анимация дыхания (запускается, если breathing=true)
        variants={breathing ? breathingVariants : undefined}
        whileInView={breathing ? "idle" : undefined}
      />
    </div>
  );
};
