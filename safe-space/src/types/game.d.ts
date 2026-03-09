import Decimal from 'break_infinity.js';

// 1. Предмет (Мебель, Кот, Декор)
export interface Item {
  id: string;
  name: string;
  tier: 1 | 2 | 2.5 | 3 | 4; // 2.5 для промежуточных этапов
  base_cost: Decimal;
  base_income: Decimal;
  growth_factor: number; // Обычно 1.15
  category: 'living' | 'tech' | 'food' | 'secret';
  image_id: string; // Ссылка на assetMap
  req_item_id?: string; // Если нужно скрыть до покупки чего-то
  on_buy_trigger?: string; // ID фразы для чата
  description: string;
}

// 2. Состояние Игры (Сейв)
export interface GameState {
  version: string;
  last_login_timestamp: number;
  
  wallet: {
    kusi: Decimal;
    mints: number;
    lifetime_kusi: Decimal;
  };

  inventory: Record<string, number>; // item_id -> quantity
  upgrades: string[]; // array of upgrade_ids
  
  persistent: {
    gallery: string[];
    is_shadow_unlocked: boolean;
  };
  
  settings: {
    theme: 'auto';
    sound: boolean;
  };
}

// 3. Апгрейд
export interface Upgrade {
  id: string;
  name: string;
  cost: Decimal;
  currency: 'kusi' | 'mints';
  effect: 'multiplier' | 'click_power' | 'synergy';
  value: number;
  target_id: string | 'global'; // ID предмета или 'global'
  req_item_id?: string;
  description: string;
}

// 4. Реплика чата
export interface ChatTrigger {
  id: string;
  category: 'item_buy' | 'time' | 'afk' | 'achievement';
  trigger_value: string; // Например 'item_pizza' или 'night'
  responses: string[];
}
