import React, { useMemo } from 'react';
import clsx from 'clsx';
import { Lock, Check } from 'lucide-react';
import Decimal from 'break_infinity.js';
import { useGameStore } from '../../../store/useGameStore';
import { getAssetUrl } from '../../../assets/assetMap';
import type { Item, Upgrade } from '../../../types';

interface ItemCardProps {
  data: Item | Upgrade;
  type: 'item' | 'upgrade';
}

export const ItemCard: React.FC<ItemCardProps> = ({ data, type }) => {
  const { 
    wallet, 
    inventory, 
    upgrades, 
    getItemCost, 
    buyItem, 
    buyUpgrade 
  } = useGameStore();

  // 1. ВЫЧИСЛЕНИЕ СОСТОЯНИЯ (Memoized для производительности)
  const state = useMemo(() => {
    // --- ЛОГИКА ДЛЯ ПРЕДМЕТОВ ---
    if (type === 'item') {
      const item = data as Item;
      const count = inventory[item.id] || 0;
      const cost = getItemCost(item.id);
      const isAffordable = wallet.kusi.gte(cost);
      
      // Проверка зависимостей (например, Кофемашина требует Пиццу)
      const isLocked = item.req_item_id ? (inventory[item.req_item_id] || 0) === 0 : false;

      return { count, cost, isAffordable, isLocked, isOwned: false };
    } 
    // --- ЛОГИКА ДЛЯ АПГРЕЙДОВ ---
    else {
      const upg = data as Upgrade;
      const isOwned = upgrades.includes(upg.id);
      const cost = new Decimal(upg.cost);
      const isAffordable = wallet.kusi.gte(cost);
      
      // Апгрейд заблокирован, если нет предмета, который он улучшает
      const isLocked = upg.req_item_id ? (inventory[upg.req_item_id] || 0) === 0 : false;

      return { count: 0, cost, isAffordable, isLocked, isOwned };
    }
  }, [wallet.kusi, inventory, upgrades, data, type, getItemCost]); // Зависимость от валюты вызовет ререндер при смене статуса доступности

  // 2. ОБРАБОТЧИК ПОКУПКИ
  const handleBuy = () => {
    if (state.isLocked || !state.isAffordable || state.isOwned) return;

    // Haptic feedback (вибрация)
    if (window.Telegram?.WebApp?.HapticFeedback) {
      window.Telegram.WebApp.HapticFeedback.impactOccurred('light');
    }

    if (type === 'item') {
      buyItem(data.id);
    } else {
      buyUpgrade(data.id);
    }
  };

  // 3. ВИЗУАЛ (Рендер)
  // Если заблокировано - показываем заглушку или серую карточку
  if (state.isLocked) {
    return (
      <div className="p-4 bg-white/5 rounded-2xl border border-white/5 flex items-center gap-4 opacity-50 grayscale">
        <div className="w-12 h-12 rounded-xl bg-black/20 flex items-center justify-center">
          <Lock size={16} className="text-white/40" />
        </div>
        <div className="flex-1">
          <div className="font-bold text-sm text-textMuted">Locked</div>
          <div className="text-xs text-textMuted/50">Requires previous items</div>
        </div>
      </div>
    );
  }

  // URL картинки (если это предмет) или иконка (если апгрейд)
  // Для апгрейдов пока используем generic иконку, либо картинку целевого предмета
  const imageUrl = type === 'item' 
    ? getAssetUrl((data as Item).image_id) 
    : getAssetUrl((data as Upgrade).target_id === 'global' ? 'mansur_coding' : (data as Upgrade).target_id);

  return (
    <div className={clsx(
      "relative p-3 rounded-2xl border transition-all duration-200",
      state.isOwned 
        ? "bg-mint/10 border-mint/20" // Купленный апгрейд
        : "bg-glass border-white/5 active:scale-[0.98]" // Обычное состояние
    )}>
      
      <div className="flex gap-3">
        {/* КАРТИНКА */}
        <div className={clsx(
          "w-16 h-16 rounded-xl flex items-center justify-center shrink-0 overflow-hidden",
          "bg-gradient-to-br from-white/5 to-white/0"
        )}>
          {imageUrl ? (
            <img src={imageUrl} alt={data.name} className="w-full h-full object-contain p-1" />
          ) : (
            <div className="text-xs text-textMuted">No IMG</div>
          )}
        </div>

        {/* ИНФО */}
        <div className="flex-1 flex flex-col justify-between py-0.5">
          <div>
            <div className="flex justify-between items-start">
              <h3 className="font-bold text-sm text-textMain leading-tight">{data.name}</h3>
              {type === 'item' && state.count > 0 && (
                <span className="text-[10px] font-mono bg-white/10 px-1.5 py-0.5 rounded text-textMuted">
                  Lvl {state.count}
                </span>
              )}
            </div>
            <p className="text-[10px] text-textMuted leading-tight mt-1 line-clamp-2">
              {data.description}
            </p>
          </div>

          {/* ЦЕНА / КНОПКА */}
          <div className="mt-2">
            {state.isOwned ? (
              <div className="flex items-center gap-1 text-mint text-xs font-bold">
                <Check size={12} /> Purchased
              </div>
            ) : (
              <button
                onClick={handleBuy}
                disabled={!state.isAffordable}
                className={clsx(
                  "w-full flex items-center justify-between px-3 py-1.5 rounded-lg text-xs font-bold font-mono transition-colors",
                  state.isAffordable 
                    ? "bg-kusi text-void shadow-lg shadow-kusi/20 hover:bg-white" 
                    : "bg-white/5 text-textMuted/50 cursor-not-allowed"
                )}
              >
                <span>Buy</span>
                <span className="flex items-center gap-1">
                  {Math.floor(state.cost.toNumber()).toLocaleString()} 
                  {/* Иконка валюты */}
                  {((data as Upgrade).currency === 'mints') ? '🍫' : '💖'}
                </span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
