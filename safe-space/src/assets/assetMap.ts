// src/assets/assetMap.ts
/**
 * Asset Registry для Safe House 404
 * 
 * Этот файл связывает строковые ID ассетов с реальными файлами.
 * React/Vite нужны реальные импорты для обработки статических файлов.
 * 
 * Использование:
 *   - Получить URL: getAssetUrl('item_pizza')
 *   - Получить все: ASSETS
 *   - Типизация: AssetId
 */

// ============================================================
// 1. ИМПОРТ СПРАЙТОВ (Vite обработает пути)
// ============================================================

import roomShell from './sprites/room_shell.png';
import mansurCoding from './sprites/mansur_coding.png';
import itemPizza from './sprites/item_pizza.png';
import itemCatCream from './sprites/item_cat_cream.png';
import itemCoffee from './sprites/item_coffee_machine.png';
import itemCatBed from './sprites/item_cat_cream_in_cat_bed.png';

// ============================================================
// 2. СЛОВАРЬ АССЕТОВ
// ============================================================

export const ASSETS = {
  // Environment (Окружение)
  'room_shell': roomShell,
  
  // Characters (Персонажи)
  'mansur_coding': mansurCoding,
  
  // Tier 1 Items (Начало игры)
  'item_pizza': itemPizza,
  
  // Tier 2 Items (Ранняя игра)
  'item_cat_cream': itemCatCream,
  
  // Tier 2.5 Items (Переходные)
  'item_coffee_machine': itemCoffee,
  
  // Tier 2 Variants (Эволюции предметов)
  'item_cat_bed': itemCatBed,
} as const;

// ============================================================
// 3. ТИПИЗАЦИЯ АССЕТОВ (для TypeScript)
// ============================================================

/**
 * AssetId - тип, который подсказывает доступные ID ассетов.
 * IDE будет автодополнять и проверять существование.
 */
export type AssetId = keyof typeof ASSETS;

// ============================================================
// 4. ВАЛИДАЦИЯ И ХЕЛПЕРЫ
// ============================================================

/**
 * Получить URL ассета по ID.
 * Безопасно: вернет пустую строку если ассет не найден.
 * 
 * @param id - ID ассета (например, 'item_pizza')
 * @returns - URL для использования в <img src={...}>
 */
export const getAssetUrl = (id: string): string => {
  const asset = ASSETS[id as AssetId];
  if (!asset) {
    console.warn(`[AssetMap] Missing asset: "${id}". Available: ${Object.keys(ASSETS).join(', ')}`);
    return '';
  }
  return asset;
};

/**
 * Проверить существование ассета.
 * 
 * @param id - ID ассета
 * @returns - true если ассет существует
 */
export const hasAsset = (id: string): id is AssetId => {
  return id in ASSETS;
};

/**
 * Получить список всех доступных ID ассетов.
 * Полезно для отладки и тестирования.
 * 
 * @returns - Массив ID ассетов
 */
export const getAssetIds = (): AssetId[] => {
  return Object.keys(ASSETS) as AssetId[];
};

// ============================================================
// 5. DEBUG EXPORTS (для консоли браузера)
// ============================================================

// В development режиме можно вызвать window.__ASSETS__ для отладки
if (typeof process !== 'undefined' && process.env?.NODE_ENV === 'development') {
  (globalThis as any).__ASSETS__ = {
    ASSETS,
    getAssetUrl,
    hasAsset,
    getAssetIds,
  };
}
