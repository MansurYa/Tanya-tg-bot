import React, { useState, useMemo, useEffect } from 'react';
import { IsoSprite } from './IsoSprite';
import { useGameStore } from '../../../store/useGameStore';
import { Copy, Check } from 'lucide-react';
import { ITEMS, UPGRADES } from '../../../data';
import { ClickFx } from '../Effects/ClickFx';
import type { VisualPos } from '../../../types';

export const Room: React.FC = () => {
  const { inventory, upgrades, calibrationMode } = useGameStore(); 
  const [copied, setCopied] = useState(false);

  // 1. Статичные объекты сцены (они всегда есть)
  // Мансур теперь тоже часть статики, но с возможностью калибровки
  const [staticOffsets, setStaticOffsets] = useState({
    'room_shell': { x: 50.0, y: 50.0, scale: 1.0 },
    'mansur_coding': { x: 28.5, y: 39.0, scale: 0.34 }
  });

  // 2. Динамические объекты (читаются из JSON при старте)
  const [dynamicOffsets, setDynamicOffsets] = useState<Record<string, VisualPos>>({});

  // Инициализация координат из JSON (один раз при маунте)
  useEffect(() => {
    const initialOffsets: Record<string, VisualPos> = {};
    
    ITEMS.forEach(item => {
      if (item.visual_pos) initialOffsets[item.id] = item.visual_pos;
    });
    
    UPGRADES.forEach(upg => {
      if (upg.visual_pos) initialOffsets[upg.id] = upg.visual_pos;
    });

    setDynamicOffsets(initialOffsets);
  }, []);

  const [activeItemId, setActiveItemId] = useState<string>('room_shell');

  // --- ENGINE LOGIC ---
  const visibleItems = useMemo(() => {
    // Единый список для рендера. Сюда попадет ВСЁ, что куплено и имеет визуализацию.
    const renderList: Array<{
      id: string; 
      assetId: string; 
      pos: VisualPos; 
      breathing: boolean;
      zIndex: number;
    }> = [];

    const itemsToHide = new Set<string>();

    // A. Обработка ITEMS
    ITEMS.forEach(item => {
      const isOwned = (inventory[item.id] || 0) > 0;
      if (isOwned || calibrationMode) {
        // Логика замены (Visual Replaces)
        if (isOwned && item.visual_replaces) {
          item.visual_replaces.forEach(hiddenId => {
            // В режиме калибровки не скрываем объект, если мы редактируем именно ЕГО
            if (!calibrationMode || activeItemId !== hiddenId) itemsToHide.add(hiddenId);
          });
        }
        
        // Берем координаты (приоритет у локального стейта калибровки)
        const pos = dynamicOffsets[item.id] || item.visual_pos;
        if (pos) {
          renderList.push({
            id: item.id,
            assetId: item.image_id,
            pos,
            breathing: item.category === 'living', // Только живое дышит
            // AUTO Z-INDEX: Чем ниже Y, тем выше Z
            zIndex: Math.floor(pos.y) + (pos.zIndexOffset || 0) 
          });
        }
      }
    });

    // B. Обработка UPGRADES
    UPGRADES.forEach(upg => {
      if (!upg.image_id) return;
      const isOwned = upgrades.includes(upg.id);
      
      if (isOwned || calibrationMode) {
        if (isOwned && upg.visual_replaces) {
          upg.visual_replaces.forEach(hiddenId => {
            if (!calibrationMode || activeItemId !== hiddenId) itemsToHide.add(hiddenId);
          });
        }

        const pos = dynamicOffsets[upg.id] || upg.visual_pos;
        if (pos) {
          renderList.push({
            id: upg.id,
            assetId: upg.image_id,
            pos,
            breathing: false, // Мебель не дышит
            zIndex: Math.floor(pos.y) + (pos.zIndexOffset || 0)
          });
        }
      }
    });

    // Фильтруем скрытые объекты
    return renderList.filter(item => !itemsToHide.has(item.id));
  }, [inventory, upgrades, calibrationMode, activeItemId, dynamicOffsets]);

  // --- CALIBRATION HANDLERS ---
  const updateItemVal = (key: keyof VisualPos, val: number) => {
    // Если правим статику
    if (activeItemId in staticOffsets) {
       setStaticOffsets(prev => ({
         ...prev,
         [activeItemId]: { ...prev[activeItemId as keyof typeof staticOffsets], [key]: val }
       }));
    } else {
       // Если правим динамику
       setDynamicOffsets(prev => ({
         ...prev,
         [activeItemId]: { ...prev[activeItemId], [key]: val }
       }));
    }
  };

  const handleCopy = () => {
    // Копируем JSON фрагмент для быстрой вставки в items.json
    let dataToCopy = {};
    if (activeItemId in staticOffsets) {
       dataToCopy = staticOffsets[activeItemId as keyof typeof staticOffsets];
    } else {
       dataToCopy = dynamicOffsets[activeItemId];
    }
    
    // Форматируем в строку, готовую для вставки в JSON файл
    navigator.clipboard.writeText(`"visual_pos": ${JSON.stringify(dataToCopy)}`);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getCurrentPos = () => {
    if (activeItemId in staticOffsets) return staticOffsets[activeItemId as keyof typeof staticOffsets];
    return dynamicOffsets[activeItemId] || { x: 0, y: 0, scale: 1 };
  };
  const current = getCurrentPos();

  // Объединяем все оффсеты для системы частиц (ClickFx)
  const allOffsets = { ...staticOffsets, ...dynamicOffsets };

  return (
    <ClickFx className="w-full h-full" itemOffsets={allOffsets}>
      <div className="relative w-full h-full">
        
        {/* 1. СТАТИКА (Фон) */}
        <IsoSprite 
            id="room_shell" 
            {...staticOffsets['room_shell']} 
            zIndex={10} 
            className={calibrationMode && activeItemId === 'room_shell' ? 'brightness-125' : ''}
        />

        {/* 2. СТАТИКА (Мансур) */}
        {/* zIndex 30 - база для Мансура. Предметы ниже него (ковер) будут <30, предметы выше (стол, монитор) >30 */}
        <IsoSprite 
            id="mansur_coding" 
            {...staticOffsets['mansur_coding']} 
            zIndex={30} 
            breathing={false}
            className={calibrationMode && activeItemId === 'mansur_coding' ? 'brightness-150 drop-shadow-lg' : ''}
        />

        {/* 3. ДИНАМИКА (Всё остальное) */}
        {visibleItems.map(item => (
          <IsoSprite
            key={item.id}
            id={item.assetId as any}
            x={item.pos.x}
            y={item.pos.y}
            scale={item.pos.scale}
            zIndex={item.zIndex} // Auto-calculated Z
            breathing={item.breathing}
            className={calibrationMode && activeItemId === item.id ? 'brightness-150 drop-shadow-lg' : ''}
          />
        ))}

        {/* 4. CALIBRATION UI (Architect v2) */}
        {calibrationMode && (
          <div 
            className="fixed top-24 right-4 bg-black/90 p-3 rounded-xl z-[100] text-white text-[10px] font-mono flex flex-col gap-3 pointer-events-auto border border-kusi/50 shadow-2xl w-44"
            onPointerDown={(e) => e.stopPropagation()} 
          >
            <div className="flex justify-between items-center border-b border-white/20 pb-1 mb-1">
              <span className="font-bold text-kusi">ARCHITECT v2</span>
              <button onClick={handleCopy} className={`p-1 rounded flex items-center gap-1 ${copied ? 'bg-mint text-black' : 'bg-white/10 hover:bg-white/20'}`}>
                {copied ? <Check size={12} /> : <><Copy size={12} /> JSON</>}
              </button>
            </div>

            {/* Selector Grid */}
            <div className="grid grid-cols-4 gap-1 mb-2 max-h-32 overflow-y-auto no-scrollbar">
              <button onClick={() => setActiveItemId('room_shell')} className={`py-1 rounded ${activeItemId === 'room_shell' ? 'bg-kusi text-black' : 'bg-white/10 hover:bg-white/5'}`}>🏠</button>
              <button onClick={() => setActiveItemId('mansur_coding')} className={`py-1 rounded ${activeItemId === 'mansur_coding' ? 'bg-kusi text-black' : 'bg-white/10 hover:bg-white/5'}`}>👨‍💻</button>
              
              {visibleItems.map(item => (
                <button 
                  key={item.id} 
                  onClick={() => setActiveItemId(item.id)} 
                  className={`py-1 rounded text-xs overflow-hidden ${activeItemId === item.id ? 'bg-kusi text-black' : 'bg-white/10 hover:bg-white/5'}`}
                  title={item.id}
                >
                  {item.assetId.includes('pizza') ? '🍕' : 
                   item.assetId.includes('cat') ? '🐈' : 
                   item.assetId.includes('coffee') ? '☕' : '📦'}
                </button>
              ))}
            </div>
            
            {/* Sliders */}
            <div className="space-y-2">
              <div className="text-center font-bold text-white text-[11px] truncate px-2 mb-1 border-b border-white/10 pb-1">
                {activeItemId}
              </div>
              <label className="block"><span className="text-[9px]">X: {current.x.toFixed(1)}%</span><input type="range" min="0" max="100" step="0.5" value={current.x} onChange={(e) => updateItemVal('x', Number(e.target.value))} className="w-full accent-kusi h-1 mt-1" /></label>
              <label className="block"><span className="text-[9px]">Y: {current.y.toFixed(1)}%</span><input type="range" min="0" max="100" step="0.5" value={current.y} onChange={(e) => updateItemVal('y', Number(e.target.value))} className="w-full accent-kusi h-1 mt-1" /></label>
              <label className="block"><span className="text-[9px]">S: {current.scale.toFixed(2)}</span><input type="range" min="0.05" max="2.0" step="0.01" value={current.scale} onChange={(e) => updateItemVal('scale', Number(e.target.value))} className="w-full accent-kusi h-1 mt-1" /></label>
            </div>
          </div>
        )}
      </div>
    </ClickFx>
  );
};
