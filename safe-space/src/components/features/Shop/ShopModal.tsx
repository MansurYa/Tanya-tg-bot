import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Package, Cat, Zap, Move, Settings, RefreshCw, PlusCircle } from 'lucide-react';
import { useGameStore } from '../../../store/useGameStore';
import { ITEMS, UPGRADES } from '../../../data';
import { ItemCard } from './ItemCard';
import clsx from 'clsx';

interface ShopModalProps {
  isOpen: boolean;
  onClose: () => void;
}

type Tab = 'furniture' | 'living' | 'upgrades';

export const ShopModal: React.FC<ShopModalProps> = ({ isOpen, onClose }) => {
  const [activeTab, setActiveTab] = useState<Tab>('furniture');
  const [devClicks, setDevClicks] = useState(0);
  
  const { 
    debugMode,
    calibrationMode,
    timeScale,
    toggleDebugMode,
    toggleCalibrationMode,
    setTimeScale,
    debugAddMoney, 
    hardReset 
  } = useGameStore();

  // Сброс кликов при закрытии
  useEffect(() => {
    if (!isOpen) setDevClicks(0);
  }, [isOpen]);

  useEffect(() => {
    if (devClicks === 5) {
      toggleDebugMode();
      setDevClicks(0);
    }
  }, [devClicks, toggleDebugMode]);

  const handleTitleClick = () => {
    setDevClicks(prev => prev + 1);
  };

  const furnitureItems = ITEMS.filter(i => i.category !== 'living');
  const livingItems = ITEMS.filter(i => i.category === 'living');

  const variants = {
    hidden: { y: '100%', opacity: 0 },
    visible: { y: 0, opacity: 1 },
    exit: { y: '100%', opacity: 0 }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-void/80 backdrop-blur-sm z-40"
          />

          <motion.div
            variants={variants}
            initial="hidden"
            animate="visible"
            exit="exit"
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="fixed bottom-0 left-0 w-full h-[85vh] bg-[#1a1a2e] rounded-t-[32px] z-50 flex flex-col border-t border-white/10 shadow-2xl shadow-kusi/10 overflow-hidden"
          >
            {/* HEADER */}
            <div className="flex justify-between items-center p-6 pb-2">
              <h2 
                onClick={handleTitleClick}
                className="text-2xl font-bold font-mono tracking-tighter select-none active:scale-95 transition-transform cursor-pointer"
              >
                SHOP
                {debugMode && <span className="text-[10px] text-mint ml-2">[GOD MODE]</span>}
              </h2>
              <button 
                onClick={onClose}
                className="p-2 bg-white/5 rounded-full hover:bg-white/10 active:scale-90 transition-all"
              >
                <X size={20} className="text-textMuted" />
              </button>
            </div>

            {/* --- GOD MODE PANEL --- */}
            {debugMode && (
              <div className="mx-6 mb-4 p-4 bg-black/40 border border-mint/20 rounded-2xl flex flex-col gap-3">
                <div className="text-[10px] font-mono text-mint uppercase tracking-widest opacity-50">Developer Tools</div>
                
                <div className="flex gap-2 overflow-x-auto no-scrollbar pb-1 flex-wrap">
                  {/* Деньги */}
                  <button 
                    onClick={debugAddMoney} 
                    className="flex items-center gap-2 px-3 py-2 bg-mint/10 text-mint text-xs font-bold rounded-xl border border-mint/20 whitespace-nowrap active:scale-95 transition-all"
                  >
                    <PlusCircle size={14} /> +1M KUSI
                  </button>

                  {/* Сброс */}
                  <button 
                    onClick={hardReset} 
                    className="flex items-center gap-2 px-3 py-2 bg-red-500/10 text-red-400 text-xs font-bold rounded-xl border border-red-500/20 whitespace-nowrap active:scale-95 transition-all"
                  >
                    <RefreshCw size={14} /> RESET ALL
                  </button>

                  {/* Калибровка */}
                  <button 
                    onClick={toggleCalibrationMode} 
                    className={clsx(
                      "flex items-center gap-2 px-3 py-2 text-xs font-bold rounded-xl border whitespace-nowrap active:scale-95 transition-all",
                      calibrationMode ? "bg-tech text-black border-tech shadow-lg shadow-tech/20" : "bg-white/5 text-textMuted border-white/10"
                    )}
                  >
                    <Move size={14} /> {calibrationMode ? 'EDITING ON' : 'EDIT POSITIONS'}
                  </button>

                  {/* Скорость */}
                  <button 
                    onClick={() => setTimeScale(timeScale === 1 ? 10 : 1)} 
                    className={clsx(
                      "flex items-center gap-2 px-3 py-2 text-xs font-bold rounded-xl border whitespace-nowrap active:scale-95 transition-all",
                      timeScale > 1 ? "bg-yellow-400 text-black border-yellow-400 shadow-lg shadow-yellow-400/30" : "bg-white/5 text-textMuted border-white/10"
                    )}
                  >
                    <Settings size={14} /> {timeScale > 1 ? 'SPEED x10' : 'SPEED x1'}
                  </button>
                </div>
              </div>
            )}

            {/* TABS */}
            <div className="flex px-6 gap-2 mb-4 overflow-x-auto no-scrollbar">
              <TabButton 
                active={activeTab === 'furniture'} 
                onClick={() => setActiveTab('furniture')} 
                icon={<Package size={16} />} 
                label="Decor" 
              />
              <TabButton 
                active={activeTab === 'living'} 
                onClick={() => setActiveTab('living')} 
                icon={<Cat size={16} />} 
                label="Living" 
              />
              <TabButton 
                active={activeTab === 'upgrades'} 
                onClick={() => setActiveTab('upgrades')} 
                icon={<Zap size={16} />} 
                label="Tech" 
              />
            </div>

            {/* CONTENT LIST */}
            <div className="flex-1 overflow-y-auto px-6 pb-safe">
              <div className="space-y-3 pb-20">
                {activeTab === 'furniture' && furnitureItems.map(item => (
                  <ItemCard key={item.id} data={item} type="item" />
                ))}
                {activeTab === 'living' && livingItems.map(item => (
                  <ItemCard key={item.id} data={item} type="item" />
                ))}
                {activeTab === 'upgrades' && UPGRADES.map(upg => (
                  <ItemCard key={upg.id} data={upg} type="upgrade" />
                ))}
                {activeTab === 'upgrades' && UPGRADES.length === 0 && (
                  <div className="text-center py-10 text-textMuted text-sm">
                    No upgrades available yet...
                  </div>
                )}
              </div>
            </div>

          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

const TabButton = ({ active, onClick, icon, label }: any) => (
  <button
    onClick={onClick}
    className={clsx(
      "flex items-center gap-2 px-4 py-2.5 rounded-xl font-bold text-sm transition-all whitespace-nowrap",
      active 
        ? "bg-white text-void shadow-lg shadow-white/10 scale-100" 
        : "bg-white/5 text-textMuted hover:bg-white/10 scale-95"
    )}
  >
    {icon}
    {label}
  </button>
);
