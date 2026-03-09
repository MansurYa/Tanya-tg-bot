import React from 'react';
import { clsx } from 'clsx';

/**
 * CurrencyDisplay - красивый блок отображения валюты
 * 
 * Поддерживает:
 * - Иконку (текст, эмодзи, компонент)
 * - Лейбл (название валюты)
 * - Значение (число в формате)
 * - Цветовую схему (kusi, mint)
 */
interface CurrencyDisplayProps {
  /** Отображаемое значение */
  value: string;

  /** Иконка (эмодзи или Lucide компонент) */
  icon?: React.ReactNode;

  /** Лейбл под иконкой */
  label?: string;

  /** Цветовая схема */
  color?: 'kusi' | 'mint';

  /** Дополнительные классы */
  className?: string;
}

export const CurrencyDisplay: React.FC<CurrencyDisplayProps> = ({
  value,
  icon,
  label,
  color = 'kusi',
  className,
}) => {
  const textColor = color === 'kusi' ? 'text-kusi' : 'text-mint';

  return (
    <div
      className={clsx(
        'flex items-center gap-2 px-3 py-1.5 rounded-full',
        'bg-glass border border-white/5 shadow-lg backdrop-blur-md',
        'transition-transform duration-200 hover:scale-105',
        className
      )}
    >
      {/* Иконка */}
      {icon && (
        <span className="text-lg leading-none">{icon}</span>
      )}

      {/* Текст: лейбл и значение */}
      <div className="flex flex-col gap-0.5">
        {label && (
          <span className="text-[10px] text-textMuted uppercase tracking-wider leading-none">
            {label}
          </span>
        )}
        <span
          className={clsx(
            'font-mono font-bold text-lg leading-none',
            'tabular-nums', // Числа выравниваются по одной ширине
            textColor
          )}
        >
          {value}
        </span>
      </div>
    </div>
  );
};
