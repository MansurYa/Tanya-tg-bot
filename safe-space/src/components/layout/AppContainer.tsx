import React from 'react';

/**
 * AppContainer - главный layout контейнер
 * 
 * Задает:
 * - Полноэкранную разметку (fixed inset-0)
 * - Фон (void color)
 * - Запрет скролла
 * - Шрифты и цвета по умолчанию
 */
export const AppContainer: React.FC<{ children: React.ReactNode }> = ({ 
  children 
}) => {
  return (
    <div 
      className="fixed inset-0 w-full h-full bg-void text-textMain overflow-hidden select-none font-sans"
      style={{
        // Дополнительно гарантируем, что не будет скролла
        height: '100vh',
        width: '100vw',
      }}
    >
      {/* Фоновый паттерн (опционально) */}
      <div 
        className="absolute inset-0 opacity-5"
        style={{
          backgroundImage: `repeating-linear-gradient(
            45deg,
            transparent,
            transparent 10px,
            rgba(139, 233, 253, 0.1) 10px,
            rgba(139, 233, 253, 0.1) 20px
          )`,
        }}
      />

      {/* Основной контент */}
      <div className="relative w-full h-full">
        {children}
      </div>
    </div>
  );
};
