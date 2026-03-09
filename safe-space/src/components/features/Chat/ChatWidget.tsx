import React, { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Send } from 'lucide-react';
import { useGameStore } from '../../../store/useGameStore';
import { ASSETS } from '../../../assets/assetMap';
import clsx from 'clsx';

interface ChatWidgetProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ChatWidget: React.FC<ChatWidgetProps> = ({ isOpen, onClose }) => {
  const { chat, addMessage, markChatRead } = useGameStore();
  const [inputText, setInputText] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Автоскролл вниз при открытии и новых сообщениях
  useEffect(() => {
    if (isOpen) {
      markChatRead();
      setTimeout(scrollToBottom, 100);
    }
  }, [isOpen, chat.messages.length, markChatRead]);

  useEffect(() => {
    scrollToBottom();
  }, [chat.messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSend = () => {
    if (!inputText.trim()) return;
    
    // Добавляем сообщение Тани
    addMessage(inputText, 'tanya');
    setInputText('');

    // Эмуляция ответа Мансура (пока заглушка, позже подключим AI)
    setTimeout(() => {
      const responses = [
        "Я работаю над этим, солнце )",
        "Звучит как план.",
        "Ты лучшая!",
        "Скоро допишу код и освобожусь.",
        "❤️",
        "Хихи )",
        "Согласен)"
      ];
      const randomResponse = responses[Math.floor(Math.random() * responses.length)];
      addMessage(randomResponse, 'mansur');
    }, 1000 + Math.random() * 2000);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const variants = {
    hidden: { opacity: 0, y: '100%' },
    visible: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: '100%' }
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
            className="fixed bottom-0 left-0 w-full h-[90vh] bg-[#1a1a2e] rounded-t-[32px] z-50 flex flex-col border-t border-white/10 shadow-2xl shadow-kusi/10 overflow-hidden"
          >
            {/* HEADER */}
            <div className="flex items-center justify-between p-6 pb-3 border-b border-white/10 bg-glass backdrop-blur-md">
              <div className="flex items-center gap-3">
                <div className="relative">
                  <div className="w-12 h-12 rounded-full overflow-hidden border border-white/10 bg-black/20 flex items-center justify-center">
                    <span className="text-xl">👨‍💻</span>
                  </div>
                  <div className="absolute bottom-0 right-0 w-3 h-3 bg-mint rounded-full border-2 border-[#1a1a2e]"></div>
                </div>
                <div>
                  <h3 className="font-bold text-white text-sm">Mansur</h3>
                  <p className="text-xs text-mint">Online • Coding</p>
                </div>
              </div>
              <button 
                onClick={onClose}
                className="p-2 bg-white/5 rounded-full hover:bg-white/10 active:scale-90 transition-all"
              >
                <X size={20} className="text-textMuted" />
              </button>
            </div>

            {/* MESSAGES AREA */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-gradient-to-b from-void to-[#161622] scroll-smooth">
              {chat.messages.map((msg) => {
                const isMe = msg.sender === 'tanya';
                const isSystem = msg.sender === 'system';

                if (isSystem) {
                  return (
                    <div key={msg.id} className="flex justify-center py-2">
                      <span className="text-[10px] text-textMuted bg-white/5 px-3 py-1 rounded-full">
                        {msg.text}
                      </span>
                    </div>
                  );
                }

                return (
                  <motion.div 
                    key={msg.id} 
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.2 }}
                    className={clsx(
                      "flex w-full",
                      isMe ? "justify-end" : "justify-start"
                    )}
                  >
                    <div 
                      className={clsx(
                        "max-w-[80%] p-3 rounded-2xl text-sm leading-relaxed shadow-sm",
                        isMe 
                          ? "bg-kusi text-void rounded-tr-sm" 
                          : "bg-white/10 text-textMain rounded-tl-sm border border-white/5"
                      )}
                    >
                      {msg.text}
                      <div 
                        className={clsx(
                          "text-[9px] mt-1 text-right opacity-60",
                          isMe ? "text-void" : "text-textMuted"
                        )}
                      >
                        {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </div>
                    </div>
                  </motion.div>
                );
              })}
              <div ref={messagesEndRef} />
            </div>

            {/* INPUT AREA */}
            <div className="p-4 bg-glass border-t border-white/10 pb-safe-bottom">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Write a message..."
                  className="flex-1 bg-white/5 border border-white/10 rounded-full px-4 py-3 text-sm text-white placeholder-textMuted focus:outline-none focus:border-kusi/50 transition-colors"
                />
                <button 
                  onClick={handleSend}
                  disabled={!inputText.trim()}
                  className="p-3 bg-kusi rounded-full text-void shadow-lg shadow-kusi/20 disabled:opacity-50 disabled:shadow-none active:scale-95 transition-all"
                >
                  <Send size={20} />
                </button>
              </div>
            </div>

          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};
