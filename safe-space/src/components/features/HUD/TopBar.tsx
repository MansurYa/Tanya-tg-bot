import React from 'react';
import { useGameStore } from '../../../store/useGameStore';
import { CurrencyDisplay } from './CurrencyDisplay';
import { formatNumber } from '../../../engine/math';
import { Settings, Zap } from 'lucide-react';

export const TopBar: React.FC = () => {
  // ИСПРАВЛЕНИЕ:
  // Мы не берем весь Decimal объект. Мы берем только .mantissa и .exponent (примитивы)
  // или сразу форматируем в строку, если стейт меняется часто.
  
  // Вариант A: Подписка на изменение конкретных полей кошелька
  const kusi = useGameStore(state => state.wallet.kusi);
  const mints = useGameStore(state => state.wallet.mints);
  
  // Вариант B: Доход пересчитываем, но приводим к числу для рендера.
  // Внимание: getIncomePerSecond() создает новый объект.
  // Чтобы избежать цикла, мы будем вызывать его внутри useEffect или использовать useShallow.
  // Но проще всего — брать значение из store.tick() или вычислять локально,
  // если оно зависит только от инвентаря.
  
  // ХАК: Чтобы разорвать цикл, мы будем использовать useStore с кастомным сравнением
  // или просто брать inventory и считать доход (но это дублирование).
  
  // ЛУЧШЕЕ РЕШЕНИЕ:
  // Мы просто вызовем функцию получения дохода, но обернем результат.
  // ТАК КАК getIncomePerSecond() - это getter, а не поле state,
  // его нельзя использовать в селекторе напрямую, если он возвращает сложный объект.
  
  const income = useGameStore(state => state.getIncomePerSecond().toNumber()); 
  // .toNumber() вернет примитив. Если доход не меняется, ререндера не будет.

  return (
    <div className="fixed top-0 left-0 w-full z-50 pointer-events-none">
      <div className="w-full px-4 pt-[calc(env(safe-area-inset-top)+12px)] pb-2 flex justify-between items-start">
        
        {/* ЛЕВАЯ ЧАСТЬ */}
        <div className="flex flex-col gap-2 pointer-events-auto">
          <CurrencyDisplay 
            value={formatNumber(kusi)} 
            icon="💖" 
            label="Kusi"
            color="kusi"
          />
          <div className="flex items-center gap-1 px-2 opacity-80">
            <Zap size={12} className="text-tech" />
            <span className="text-xs font-mono text-textMain">
              {formatNumber(income)}/s
            </span>
          </div>
        </div>

        {/* ПРАВАЯ ЧАСТЬ */}
        <div className="flex gap-2 pointer-events-auto">
          {mints > 0 && (
            <CurrencyDisplay 
              value={mints.toString()} 
              icon="🍫" 
              color="mint"
              className="scale-90 origin-top-right"
            />
          )}
          
          <button className="p-2 bg-glass rounded-full border border-white/10 active:scale-95 transition-transform text-tech">
            <Settings size={20} />
          </button>
        </div>

      </div>
    </div>
  );
};