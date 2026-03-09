import React, { useEffect, useState } from 'react';
import { AppContainer } from './components/layout/AppContainer';
import { Room } from './components/features/Room/Room';
import { TopBar } from './components/features/HUD/TopBar';
import { ShopModal } from './components/features/Shop/ShopModal';
import { ChatWidget } from './components/features/Chat/ChatWidget';
import { useGameStore } from './store/useGameStore';
import { ShoppingBag, MessageCircle, Star } from 'lucide-react';

function App() {
  const initStore = useGameStore(state => state.tick);
  
  // Локальный стейт для управления модальными окнами
  const [isShopOpen, setIsShopOpen] = useState(false);
  const [isChatOpen, setIsChatOpen] = useState(false);
  
  // Берём счётчик непрочитанных сообщений из стора
  const unreadCount = useGameStore(state => state.chat.unreadCount);

  useEffect(() => {
    if (typeof window !== 'undefined' && window.Telegram?.WebApp) {
      window.Telegram.WebApp.ready();
      window.Telegram.WebApp.expand();
      try { window.Telegram.WebApp.requestFullscreen(); } catch (e) {}
    }
    const interval = setInterval(() => initStore(0.1), 100);
    return () => clearInterval(interval);
  }, [initStore]);

  return (
    <AppContainer>
      {/* LAYER 1: THE STAGE (Геометрический центр экрана) */}
      <div className="absolute inset-0 flex items-center justify-center z-0 overflow-hidden pointer-events-none">
        <div className="relative w-[90vw] max-w-[400px] aspect-square pointer-events-auto">
           <Room />
        </div>
      </div>

      {/* LAYER 2: HUD (Верх) */}
      <TopBar />

      {/* LAYER 3: BOTTOM NAVIGATION (Низ) */}
      <div className="fixed bottom-0 left-0 w-full pb-[calc(env(safe-area-inset-bottom)+20px)] pt-12 z-50 pointer-events-none bg-gradient-to-t from-void via-void/90 to-transparent">
        <div className="flex justify-between items-end px-8 max-w-md mx-auto pointer-events-auto">
          
          {/* Кнопка SHOP */}
          <button 
            onClick={() => setIsShopOpen(true)}
            className="flex flex-col items-center gap-1 group"
          >
            <div className="p-3 bg-glass rounded-2xl border border-white/10 group-active:scale-95 transition-all shadow-lg shadow-kusi/20">
              <ShoppingBag size={24} className="text-kusi" />
            </div>
            <span className="text-[10px] font-bold tracking-wider text-textMuted group-hover:text-white">Shop</span>
          </button>

          {/* Кнопка CHAT */}
          <button 
            onClick={() => setIsChatOpen(true)}
            className="flex flex-col items-center gap-1 group relative"
          >
             <div className="p-3 bg-glass rounded-2xl border border-white/10 group-active:scale-95 transition-all">
                <MessageCircle size={24} className="text-tech" />
                {unreadCount > 0 && (
                  <div className="absolute -top-1 -right-1 bg-kusi text-void text-[10px] font-bold rounded-full w-5 h-5 flex items-center justify-center shadow-lg">
                    {unreadCount}
                  </div>
                )}
             </div>
             <span className="text-[10px] font-bold tracking-wider text-textMuted group-hover:text-white">Chat</span>
          </button>

          {/* Кнопка PRESTIGE (Пока заглушка) */}
          <button className="flex flex-col items-center gap-1 group">
             <div className="p-3 bg-glass rounded-2xl border border-white/10 group-active:scale-95 transition-all">
                <Star size={24} className="text-mint" />
             </div>
             <span className="text-[10px] font-bold tracking-wider text-textMuted group-hover:text-white">Prestige</span>
          </button>

        </div>
      </div>

      {/* MODALS LAYER */}
      <ShopModal isOpen={isShopOpen} onClose={() => setIsShopOpen(false)} />
      <ChatWidget isOpen={isChatOpen} onClose={() => setIsChatOpen(false)} />

    </AppContainer>
  );
}

export default App;
