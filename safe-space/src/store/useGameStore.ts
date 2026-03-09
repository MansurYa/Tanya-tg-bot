import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import Decimal from 'break_infinity.js';
import { ITEMS, UPGRADES, ITEM_MAP } from '../data';
import type { GameState } from '../types';
import { calculateItemCost, calculateItemIncome, calculatePrestigeCurrency, MINT_BONUS } from '../engine/math';

// Chat types
export interface ChatMessage {
  id: string;
  sender: 'mansur' | 'tanya' | 'system';
  text: string;
  timestamp: number;
}

// Расширяем интерфейс стейта методами
interface GameStore extends GameState {
  // Debug flags
  debugMode: boolean;
  calibrationMode: boolean;
  timeScale: number;
  
  // Chat state
  chat: {
    messages: ChatMessage[];
    isTyping: boolean;
    unreadCount: number;
  };
  
  // Actions
  click: () => void;
  buyItem: (itemId: string) => void;
  buyUpgrade: (upgradeId: string) => void;
  tick: (deltaTime: number) => void;
  prestige: () => void;
  resetSave: () => void;
  
  // Chat Actions
  addMessage: (text: string, sender?: 'mansur' | 'tanya' | 'system') => void;
  markChatRead: () => void;
  
  // Debug Actions
  toggleDebugMode: () => void;
  toggleCalibrationMode: () => void;
  setTimeScale: (scale: number) => void;
  debugAddMoney: () => void;
  hardReset: () => void;
  
  // Getters
  getIncomePerSecond: () => Decimal;
  getItemCost: (itemId: string) => Decimal;
  canAfford: (cost: Decimal) => boolean;
}

const INITIAL_STATE = {
  version: '1.4',
  last_login_timestamp: Date.now(),
  debugMode: false,
  calibrationMode: false,
  timeScale: 1,
  wallet: {
    kusi: new Decimal(0),
    mints: 0,
    lifetime_kusi: new Decimal(0),
  },
  inventory: {},
  upgrades: [],
  chat: {
    messages: [
      {
        id: 'init_msg_1',
        sender: 'mansur' as const,
        text: 'Привет, солнце. Я настроил этот сервер специально для тебя. Чувствуй себя как дома ❤️',
        timestamp: Date.now()
      }
    ],
    isTyping: false,
    unreadCount: 1,
  },
  persistent: {
    gallery: [],
    is_shadow_unlocked: false,
  },
  settings: {
    theme: 'auto' as const,
    sound: true,
  },
};

// Хелпер для безопасного превращения чего угодно в Decimal
const safeDecimal = (value: any): Decimal => {
  if (value instanceof Decimal) return value;
  if (typeof value === 'object' && value !== null && 'mantissa' in value) {
    return new Decimal(value);
  }
  return new Decimal(value || 0);
};

export const useGameStore = create<GameStore>()(
  persist(
    (set, get) => ({
      ...INITIAL_STATE,

      // --- GETTERS ---
      
      getItemCost: (itemId) => {
        const item = ITEM_MAP.get(itemId);
        if (!item) return new Decimal(0);
        const count = get().inventory[itemId] || 0;
        return calculateItemCost(item, count);
      },

      getIncomePerSecond: () => {
        const { inventory, upgrades, wallet } = get();
        let total = new Decimal(0);
        
        ITEMS.forEach(item => {
          const count = inventory[item.id] || 0;
          if (count > 0) {
            const itemUpgrades = UPGRADES.filter(u => 
              upgrades.includes(u.id) && u.target_id === item.id
            );
            total = total.plus(calculateItemIncome(item, count, itemUpgrades));
          }
        });

        if (wallet.mints > 0) {
          const prestigeMultiplier = 1 + (wallet.mints * MINT_BONUS);
          total = total.times(prestigeMultiplier);
        }

        return total;
      },

      canAfford: (cost: Decimal) => {
        // Защита от краша: убедимся, что kusi это Decimal перед вызовом .gte
        const currentKusi = safeDecimal(get().wallet.kusi);
        return currentKusi.gte(cost);
      },

      // --- ACTIONS ---

      click: () => {
        const state = get();
        const kusi = safeDecimal(state.wallet.kusi);
        const lifetime = safeDecimal(state.wallet.lifetime_kusi);
        const clickPower = new Decimal(1).plus(state.wallet.mints * 0.5); 

        set({
          wallet: { 
            ...state.wallet, 
            kusi: kusi.plus(clickPower),
            lifetime_kusi: lifetime.plus(clickPower) 
          }
        });
      },

      buyItem: (itemId) => {
        const state = get();
        const cost = state.getItemCost(itemId);
        const kusi = safeDecimal(state.wallet.kusi);
        
        if (kusi.gte(cost)) {
          set((state) => {
            const currentCount = state.inventory[itemId] || 0;
            const kusiBefore = safeDecimal(state.wallet.kusi);
            return {
              wallet: { 
                ...state.wallet, 
                kusi: kusiBefore.minus(cost) 
              },
              inventory: {
                ...state.inventory,
                [itemId]: currentCount + 1
              }
            };
          });
        }
      },

      buyUpgrade: (upgradeId) => {
        const upgrade = UPGRADES.find(u => u.id === upgradeId);
        if (!upgrade) return;
        
        const state = get();
        const cost = new Decimal(upgrade.cost);
        const kusi = safeDecimal(state.wallet.kusi);

        if (kusi.gte(cost) && !state.upgrades.includes(upgradeId)) {
          set((state) => {
            const kusiBefore = safeDecimal(state.wallet.kusi);
            return {
              wallet: { ...state.wallet, kusi: kusiBefore.minus(cost) },
              upgrades: [...state.upgrades, upgradeId]
            };
          });
        }
      },

      tick: (deltaTime) => {
        const state = get();
        // Применяем Time Scale для ускорения
        const adjustedDelta = deltaTime * state.timeScale;
        const incomePerSec = state.getIncomePerSecond();
        const income = incomePerSec.times(adjustedDelta);
        
        if (income.gt(0)) {
          const kusi = safeDecimal(state.wallet.kusi);
          const lifetime = safeDecimal(state.wallet.lifetime_kusi);
          
          set({
            wallet: {
              ...state.wallet,
              kusi: kusi.plus(income),
              lifetime_kusi: lifetime.plus(income)
            }
          });
        }
      },

      prestige: () => {
        const state = get();
        const lifetime = safeDecimal(state.wallet.lifetime_kusi);
        const earnedMints = calculatePrestigeCurrency(lifetime);
        
        if (earnedMints > 0) {
          set((oldState) => ({
            ...INITIAL_STATE,
            debugMode: oldState.debugMode,
            calibrationMode: oldState.calibrationMode,
            wallet: {
              ...INITIAL_STATE.wallet,
              mints: oldState.wallet.mints + earnedMints,
            },
            persistent: {
              ...oldState.persistent,
              gallery: [...oldState.persistent.gallery, `Run ${new Date().toLocaleDateString()}`]
            },
          }));
        }
      },

      resetSave: () => {
        localStorage.removeItem('safe-house-404-storage');
        window.location.reload();
      },

      // --- DEBUG ACTIONS ---

      toggleDebugMode: () => {
        set((state) => ({
          debugMode: !state.debugMode
        }));
      },

      toggleCalibrationMode: () => {
        set((state) => ({
          calibrationMode: !state.calibrationMode
        }));
      },

      setTimeScale: (scale) => {
        set({ timeScale: scale });
      },

      addMessage: (text, sender = 'mansur') => {
        set(state => ({
          chat: {
            ...state.chat,
            messages: [
              ...state.chat.messages,
              {
                id: Math.random().toString(36).substr(2, 9),
                sender,
                text,
                timestamp: Date.now()
              }
            ],
            unreadCount: state.chat.unreadCount + 1
          }
        }));
      },

      markChatRead: () => {
        set(state => ({
          chat: { ...state.chat, unreadCount: 0 }
        }));
      },

      debugAddMoney: () => {
        const state = get();
        const kusi = safeDecimal(state.wallet.kusi);
        
        set({
          wallet: {
            ...state.wallet,
            kusi: kusi.plus(1000000),
            lifetime_kusi: safeDecimal(state.wallet.lifetime_kusi).plus(1000000)
          }
        });
      },

      hardReset: () => {
        if (!get().debugMode) return;
        localStorage.removeItem('safe-house-404-storage');
        set(INITIAL_STATE);
      }
    }),
    {
      name: 'safe-house-404-storage',
      storage: createJSONStorage(() => localStorage, {
        reviver: (key, value: any) => {
          if (value && typeof value === 'object' && 'mantissa' in value) {
            return new Decimal(value);
          }
          return value;
        },
      }),
      // Функция, которая запускается после восстановления данных из localStorage
      onRehydrateStorage: () => (state) => {
        if (state) {
          // ПРИНУДИТЕЛЬНОЕ ВОССТАНОВЛЕНИЕ DECIMAL
          // Если после загрузки данные оказались числами или объектами без методов
          state.wallet.kusi = safeDecimal(state.wallet.kusi);
          state.wallet.lifetime_kusi = safeDecimal(state.wallet.lifetime_kusi);
          // Инициализация чата, если его нет в старом сейве
          if (!state.chat) {
            state.chat = INITIAL_STATE.chat;
          }
          console.log('[Store] Rehydration complete. Wallet fixed. ✅');
        }
      },
    }
  )
);