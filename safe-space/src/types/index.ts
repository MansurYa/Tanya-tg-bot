import Decimal from 'break_infinity.js';

// Интерфейс для визуальных настроек
export interface VisualPos {
  x: number;
  y: number;
  scale: number;
  zIndexOffset?: number; // Если нужно принудительно поднять/опустить слой
}

export interface Item {
  id: string;
  name: string;
  tier: 1 | 2 | 2.5 | 3 | 4;
  base_cost: Decimal;
  base_income: Decimal;
  growth_factor: number;
  category: 'living' | 'tech' | 'food' | 'secret';
  image_id: string;
  req_item_id?: string;
  on_buy_trigger?: string;
  description: string;
  visual_replaces?: string[];
  
  // НОВОЕ ПОЛЕ: Теперь координаты живут здесь
  visual_pos?: VisualPos; 
}

export interface Upgrade {
  id: string;
  name: string;
  cost: Decimal;
  currency: 'kusi' | 'mints';
  effect: 'multiplier' | 'click_power' | 'synergy';
  value: number;
  target_id: string | 'global';
  req_item_id?: string;
  description: string;
  image_id?: string;
  visual_replaces?: string[];
  
  // НОВОЕ ПОЛЕ: И у апгрейдов тоже
  visual_pos?: VisualPos;
}

// ... Остальные типы без изменений ...
export interface GameState {
  version: string;
  last_login_timestamp: number;
  wallet: {
    kusi: Decimal;
    mints: number;
    lifetime_kusi: Decimal;
  };
  inventory: Record<string, number>;
  upgrades: string[];
  persistent: {
    gallery: string[];
    is_shadow_unlocked: boolean;
  };
  settings: {
    theme: 'auto';
    sound: boolean;
  };
}

export type TriggerMap = Record<string, string[]>;