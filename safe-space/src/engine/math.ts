/**
 * src/engine/math.ts
 * 
 * Математический движок игры.
 * Чистые функции для расчетов (без состояния).
 * Работает с Decimal для поддержки больших чисел.
 */

import Decimal from 'break_infinity.js';
import type { Item, Upgrade } from '../types/index';

// ============================================================
// КОНСТАНТЫ
// ============================================================

/** Сколько кусей нужно для 1 Мяты (редкая валюта) */
export const PRESTIGE_K = 100000;

/** Бонус дохода за каждую Мяту */
export const MINT_BONUS = 0.15; // +15%

/** Множитель клика (сила одного тапа на старте) */
export const BASE_CLICK_POWER = 1;

/** Базовая скорость генерации дохода (обновления в сек) */
export const TICK_RATE = 10; // Обновляем каждые 10 миллисекунд = 100 тиков в сек

// ============================================================
// 1. РАСЧЕТ СТОИМОСТИ ПРЕДМЕТА
// ============================================================

/**
 * Рассчитать стоимость N-го предмета в магазине.
 * Formula: BaseCost * (GrowthFactor ^ OwnedCount)
 * 
 * Пример: Пицца стоит 15 кусей. После покупки первой:
 *   15 * 1.15^1 = 17.25 куся
 *   15 * 1.15^2 = 19.8 куся
 *   И т.д.
 * 
 * @param item - Объект предмета из items.json
 * @param ownedCount - Сколько этого предмета уже куплено
 * @returns - Стоимость в кусях (Decimal)
 */
export const calculateItemCost = (item: Item, ownedCount: number): Decimal => {
  const growth = new Decimal(item.growth_factor);
  const count = new Decimal(ownedCount);
  const baseCost = new Decimal(item.base_cost);
  
  // BaseCost * (Growth ^ Owned)
  return baseCost.times(growth.pow(count));
};

// ============================================================
// 2. РАСЧЕТ ДОХОДА ПРЕДМЕТА
// ============================================================

/**
 * Рассчитать доход от одного типа предмета.
 * 
 * Formula: BaseIncome * Count * MultiplierProduct
 * 
 * Пример: Кот генерирует 12 кусей/сек. У Тани 5 котов.
 *   Без апгрейдов: 12 * 5 = 60 кусей/сек
 *   С апгрейдом "Лежанка" (+1.1): 60 * 1.1 = 66 кусей/сек
 * 
 * @param item - Объект предмета
 * @param count - Сколько штук этого предмета куплено
 * @param appliedUpgrades - Апгрейды, которые влияют на этот предмет
 * @returns - Доход в кусях/сек (Decimal)
 */
export const calculateItemIncome = (
  item: Item,
  count: number,
  appliedUpgrades: Upgrade[] = []
): Decimal => {
  if (count === 0) return new Decimal(0);

  let income = new Decimal(item.base_income).times(count);

  // Применяем множители от апгрейдов
  appliedUpgrades.forEach(upg => {
    if (upg.effect === 'multiplier' && upg.target_id === item.id) {
      income = income.times(upg.value);
    }
  });

  return income;
};

// ============================================================
// 3. РАСЧЕТ ОБЩЕГО ДОХОДА
// ============================================================

/**
 * Рассчитать суммарный пассивный доход от всех предметов.
 * 
 * @param items - Все предметы
 * @param inventory - Инвентарь (item_id -> count)
 * @param purchasedUpgrades - Массив купленных апгрейдов
 * @param mintBonus - Количество Мят (редкой валюты) для бонуса
 * @returns - Суммарный доход в кусях/сек (Decimal)
 */
export const calculateTotalIncome = (
  items: Item[],
  inventory: Record<string, number>,
  purchasedUpgrades: Upgrade[] = [],
  mintBonus: number = 0
): Decimal => {
  let totalIncome = new Decimal(0);

  items.forEach(item => {
    const count = inventory[item.id] || 0;
    
    // Получаем апгрейды, влияющие на этот предмет
    const relevantUpgrades = purchasedUpgrades.filter(
      upg => upg.target_id === item.id || upg.target_id === 'global'
    );
    
    const itemIncome = calculateItemIncome(item, count, relevantUpgrades);
    totalIncome = totalIncome.plus(itemIncome);
  });

  // Применяем глобальный бонус от Мят
  const mintMultiplier = new Decimal(1 + mintBonus * MINT_BONUS);
  totalIncome = totalIncome.times(mintMultiplier);

  return totalIncome;
};

// ============================================================
// 4. РАСЧЕТ МЯТНЫХ ПЛИТОК (Престиж)
// ============================================================

/**
 * Рассчитать количество Мят по общему кусейному доходу.
 * Formula: Floor( Sqrt( LifetimeKusi / 100k ) )
 * 
 * Это создает долгосрочную цель (собрать миллионы кусей для бонуса).
 * 
 * Примеры:
 *   100k кусей -> 1 Мята (sqrt(1) = 1)
 *   400k кусей -> 2 Мяты (sqrt(4) = 2)
 *   1M кусей -> 3 Мяты (sqrt(10) ≈ 3)
 * 
 * @param lifetimeKusi - Все когда-либо собранные куси
 * @returns - Целое число Мят
 */
export const calculatePrestigeCurrency = (lifetimeKusi: Decimal): number => {
  const lifeDecimal = new Decimal(lifetimeKusi);
  
  if (lifeDecimal.lt(PRESTIGE_K)) {
    return 0;
  }
  
  // (Total / 100k) ^ 0.5
  const ratio = lifeDecimal.div(PRESTIGE_K);
  const sqrtRatio = ratio.sqrt();
  
  return Math.floor(sqrtRatio.toNumber());
};

// ============================================================
// 5. ФОРМАТИРОВАНИЕ ЧИСЕЛ
// ============================================================

/**
 * Преобразовать число в читаемый формат.
 * Примеры:
 *   15 -> "15"
 *   1500 -> "1.5k"
 *   1500000 -> "1.50M"
 *   1500000000 -> "1.50B"
 *   1.5e15 -> "1.50e+15"
 * 
 * @param num - Число (обычное или Decimal)
 * @returns - Строка в читаемом формате
 */
export const formatNumber = (num: Decimal | number): string => {
  const d = new Decimal(num);
  
  // До 1000
  if (d.lt(1000)) {
    return d.toFixed(0);
  }
  
  // До 1 миллиона (тысячи)
  if (d.lt(1000000)) {
    return d.div(1000).toFixed(1) + 'k';
  }
  
  // До 1 миллиарда (миллионы)
  if (d.lt(1e9)) {
    return d.div(1e6).toFixed(2) + 'M';
  }
  
  // До 1 триллиона (миллиарды)
  if (d.lt(1e12)) {
    return d.div(1e9).toFixed(2) + 'B';
  }
  
  // Очень большие числа (триллионы+)
  return d.toExponential(2);
};

/**
 * Форматировать число с максимальным количеством знаков.
 * Полезно для компактного отображения (например, в UI).
 * 
 * @param num - Число
 * @param precision - Количество знаков (по умолчанию 3)
 * @returns - Строка вида "1.23k" или "456"
 */
export const formatNumberCompact = (num: Decimal | number, precision: number = 3): string => {
  const d = new Decimal(num);
  
  if (d.lt(1000)) {
    return d.toFixed(0);
  }
  
  const suffixes = ['', 'k', 'M', 'B', 'T'];
  const absNum = d.abs();
  
  for (let i = suffixes.length - 1; i >= 0; i--) {
    const divisor = new Decimal(10).pow(i * 3);
    if (absNum.gte(divisor)) {
      return d.div(divisor).toFixed(precision - 1) + suffixes[i];
    }
  }
  
  return d.toFixed(0);
};

// ============================================================
// 6. ПРОВЕРКА ДОСТУПНОСТИ ПОКУПКИ
// ============================================================

/**
 * Может ли игрок купить предмет?
 * Проверяет: достаточно ли денег + требуемые предметы куплены.
 * 
 * @param item - Объект предмета
 * @param currentKusi - Текущий баланс кусей
 * @param inventory - Инвентарь игрока
 * @returns - true если можно купить
 */
export const canAffordItem = (
  item: Item,
  currentKusi: Decimal,
  inventory: Record<string, number>
): boolean => {
  // Проверяем, достаточно ли денег
  const ownedCount = inventory[item.id] || 0;
  const cost = calculateItemCost(item, ownedCount);
  
  if (currentKusi.lt(cost)) {
    return false;
  }
  
  // Проверяем требуемые предметы
  if (item.req_item_id && (!inventory[item.req_item_id] || inventory[item.req_item_id] === 0)) {
    return false;
  }
  
  return true;
};

/**
 * Может ли игрок купить апгрейд?
 * 
 * @param upgrade - Объект апгрейда
 * @param wallet - Баланс кусей или мят
 * @param inventory - Инвентарь игрока
 * @returns - true если можно купить
 */
export const canAffordUpgrade = (
  upgrade: Upgrade,
  wallet: { kusi: Decimal; mints: number },
  inventory: Record<string, number>
): boolean => {
  // Проверяем баланс нужной валюты
  const balance = upgrade.currency === 'kusi' ? wallet.kusi : wallet.mints;
  const cost = new Decimal(upgrade.cost);
  
  if (new Decimal(balance).lt(cost)) {
    return false;
  }
  
  // Проверяем требуемые предметы
  if (upgrade.req_item_id && (!inventory[upgrade.req_item_id] || inventory[upgrade.req_item_id] === 0)) {
    return false;
  }
  
  return true;
};

// ============================================================
// 7. DEBUG EXPORTS
// ============================================================

if (typeof process !== 'undefined' && process.env?.NODE_ENV === 'development') {
  (globalThis as any).__MATH_ENGINE__ = {
    calculateItemCost,
    calculateItemIncome,
    calculateTotalIncome,
    calculatePrestigeCurrency,
    formatNumber,
    formatNumberCompact,
    canAffordItem,
    canAffordUpgrade,
    PRESTIGE_K,
    MINT_BONUS,
    BASE_CLICK_POWER,
    TICK_RATE,
  };
}
