import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { FiSend, FiMic, FiX, FiMessageCircle, FiRotateCcw } from "react-icons/fi";
import "./App.css";

const QUICK_ACTIONS = [
  { label: "Refund", icon: "↩" },
  { label: "Payment Failed", icon: "⚡" },
  { label: "API Integration", icon: "🔗" },
  { label: "Chargebacks", icon: "🛡" },
];

function MsgAvatar() {
  return (
    <div className="mavatar">
      <img src="/sezzle_logo.jpg" alt="Sezzle" style={{ width: "100%", height: "100%", objectFit: "cover", borderRadius: "50%" }} />
    </div>
  );
}

function TypingDots() {
  return (
    <div className="typing-wrap">
      <MsgAvatar />
      <div className="typing">
        <span /><span /><span />
      </div>
    </div>
  );
}

function VoiceScreen({ onClose }) {
  return (
    <div className="voice-screen">
      <div className="rings">
        <div className="ring ring1" />
        <div className="ring ring2" />
        <div className="ring ring3" />
      </div>

      <div className="globe-container" onClick={onClose}>
        <iframe
          src="https://my.spline.design/09a1967a051f4493b2149a87e7e53aec/"
          className="spline-iframe"
          title="Voice Globe"
          frameBorder="0"
        />
      </div>

      <p className="voice-label">Listening...</p>
      <p className="voice-sub">Tap globe to stop</p>

      <div className="voice-controls">
        <button className="vc-btn" onClick={onClose}>
          <FiRotateCcw size={16} />
        </button>
        <button className="vc-mic" onClick={onClose}>
          <FiMic size={20} />
        </button>
        <button className="vc-btn" onClick={onClose}>
          <FiX size={16} />
        </button>
      </div>
    </div>
  );
}

export default function App() {
  const [open, setOpen] = useState(false);
  const [voice, setVoice] = useState(false);
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([
    { sender: "bot", text: "Hey there 👋 I'm your Sezzle AI assistant. Ask me anything about payments, integrations, refunds, or your account." },
  ]);
  const [loading, setLoading] = useState(false);
  const [quickVisible, setQuickVisible] = useState(true);
  const chatRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    chatRef.current?.scrollTo({ top: chatRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    if (open) setTimeout(() => inputRef.current?.focus(), 300);
  }, [open]);

  const handleSend = async (customText = null) => {
    const text = (customText || message).trim();
    if (!text) return;

    setQuickVisible(false);
    setMessages((prev) => [...prev, { sender: "user", text }]);
    setMessage("");
    setLoading(true);

    try {
      const response = await fetch("http://localhost:8000/get", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ msg: text }),
      });
      const data = await response.json();
      setMessages((prev) => [...prev, { sender: "bot", text: data.answer }]);
    } catch (error) {
      setMessages((prev) => [...prev, { sender: "bot", text: "Failed to connect to backend. Make sure your Flask server is running on port 8000." }]);
    }

    setLoading(false);
  };

  return (
    <>
      {/* Toggle Button */}
      <motion.button
        className="chat-toggle"
        onClick={() => setOpen((o) => !o)}
        whileHover={{ scale: 1.08 }}
        whileTap={{ scale: 0.93 }}
      >
        <div className="toggle-online-dot" />
        <AnimatePresence mode="wait">
          <motion.div
            key={open ? "x" : "msg"}
            initial={{ rotate: -80, opacity: 0 }}
            animate={{ rotate: 0, opacity: 1 }}
            exit={{ rotate: 80, opacity: 0 }}
            transition={{ duration: 0.18 }}
          >
            {open ? <FiX size={22} /> : <FiMessageCircle size={22} />}
          </motion.div>
        </AnimatePresence>
      </motion.button>

      {/* Widget */}
      <AnimatePresence>
        {open && (
          <motion.div
            className="widget"
            initial={{ opacity: 0, y: 32, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 32, scale: 0.95 }}
            transition={{ type: "spring", stiffness: 320, damping: 28 }}
          >
            {/* Header */}
            <div className="widget-header">
              <div className="header-avatar">
                <img src="/sezzle_logo.jpg" alt="Sezzle" style={{ width: "100%", height: "100%", objectFit: "cover", borderRadius: "50%" }} />
              </div>
              <div className="header-info">
                <p className="header-name">Sezzle AI Assistant</p>
                <div className="header-status">
                  <div className="status-dot" />
                  <span>Online · Customer Support Agent</span>
                </div>
              </div>
              <button className="header-close" onClick={() => setOpen(false)}>
                <FiX size={14} />
              </button>
            </div>

            {/* Voice screen overlay */}
            <AnimatePresence>
              {voice && (
                <motion.div
                  className="voice-overlay"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.2 }}
                >
                  <VoiceScreen onClose={() => setVoice(false)} />
                </motion.div>
              )}
            </AnimatePresence>

            {/* Messages */}
            <div className="chat-messages" ref={chatRef}>
              {messages.map((msg, i) => (
                <motion.div
                  key={i}
                  className={`msg-row ${msg.sender}`}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.22 }}
                >
                  {msg.sender === "bot" && <MsgAvatar />}
                  <div className={`bubble ${msg.sender}`}>{msg.text}</div>
                </motion.div>
              ))}
              {loading && <TypingDots />}
            </div>

            {/* Quick Actions — bottom, above input */}
            <AnimatePresence>
              {quickVisible && (
                <motion.div
                  className="quick-actions"
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, height: 0, padding: 0 }}
                  transition={{ duration: 0.2 }}
                >
                  {QUICK_ACTIONS.map((a) => (
                    <button key={a.label} className="quick-btn" onClick={() => handleSend(a.label)}>
                      <span>{a.icon}</span> {a.label}
                    </button>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>

            {/* Separator */}
            <div className="sep" />

            {/* Input Area */}
            <div className="input-area">
              <button
                className={`mic-btn ${voice ? "active" : ""}`}
                onClick={() => setVoice(true)}
              >
                <FiMic size={16} />
              </button>

              <input
                ref={inputRef}
                className="chat-input"
                type="text"
                placeholder="Ask a question..."
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSend()}
              />

              <button
                className={`send-btn ${message.trim() ? "active" : ""}`}
                onClick={() => handleSend()}
              >
                <FiSend size={15} />
              </button>
            </div>

            <p className="widget-footer">Powered by Unofficial Sezzle AI · Enter to send</p>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}