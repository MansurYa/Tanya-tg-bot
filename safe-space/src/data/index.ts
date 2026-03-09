/**
 * src/data/index.ts
 * 
 * Экспортируем данные игры с типизацией.
 * Источники: items.json, upgrades.json, triggers.json
 */

import type { Item, Upgrade } from '../types/index';
import itemsRaw from './items.json';
import upgradesRaw from './upgrades.json';
import triggersRaw from './triggers.json';

// ============================================================
// Данные с типизацией
// ============================================================

/**
 * Массив всех предметов игры
 */
export const ITEMS: Item[] = itemsRaw as unknown as Item[];

/**
 * Массив всех апгрейдов
 */
export const UPGRADES: Upgrade[] = upgradesRaw as unknown as Upgrade[];

/**
 * Словарь реплик бота по триггерам
 * Ключ = ID триггера (например, 'trig_pizza_first')
 * Значение = массив возможных ответов (берется случайный)
 */
export const TRIGGERS: Record<string, string[]> = triggersRaw;

// ============================================================
// Индексы для быстрого поиска
// ============================================================

/**
 * Map для O(1) поиска предмета по ID
 */
export const ITEM_MAP = new Map(ITEMS.map(item => [item.id, item]));

/**
 * Map для O(1) поиска апгрейда по ID
 */
export const UPGRADE_MAP = new Map(UPGRADES.map(upg => [upg.id, upg]));

// ============================================================
// Хелперы
// ============================================================

/**
 * Получить предмет по ID
 */
export const getItem = (id: string): Item | undefined => {
  return ITEM_MAP.get(id);
};

/**
 * Получить апгрейд по ID
 */
export const getUpgrade = (id: string): Upgrade | undefined => {
  return UPGRADE_MAP.get(id);
};

/**
 * Получить случайную реплику по триггеру
 */
export const getTriggerResponse = (triggerId: string): string | undefined => {
  const responses = TRIGGERS[triggerId];
  if (!responses || responses.length === 0) {
    console.warn(`[Triggers] Unknown trigger: ${triggerId}`);
    return undefined;
  }
  return responses[Math.floor(Math.random() * responses.length)];
};

/**
 * Получить все реплики по триггеру
 */
export const getTriggerResponses = (triggerId: string): string[] => {
  return TRIGGERS[triggerId] || [];
};

// ============================================================
// Debug Exports
// ============================================================

if (typeof process !== 'undefined' && process.env?.NODE_ENV === 'development') {
  (globalThis as any).__GAME_DATA__ = {
    ITEMS,
    UPGRADES,
    TRIGGERS,
    ITEM_MAP,
    UPGRADE_MAP,
    getItem,
    getUpgrade,
    getTriggerResponse,
    getTriggerResponses,
  };
}
