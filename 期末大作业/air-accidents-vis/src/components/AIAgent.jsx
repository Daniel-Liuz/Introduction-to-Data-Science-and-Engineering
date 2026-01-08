import React, { useState, useRef, useEffect } from 'react';

const AIAgent = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([
    { role: 'ai', content: '你好！我是航空事故分析助手，我可以帮你查询数据库中的 3 万多条事故记录。你想了解什么？' }
  ]);
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef(null);

  // 自动滚动到底部
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMsg = input;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setLoading(true);

    try {
      // 这里的地址对应你的 Node.js 后端端口
      const response = await fetch('http://localhost:3001/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg }) // JS 会自动处理 JSON，不会有转义错误
      });

      const data = await response.json();
      
      if (response.ok) {
        setMessages(prev => [...prev, { role: 'ai', content: data.answer }]);
      } else {
        setMessages(prev => [...prev, { role: 'ai', content: `错误: ${data.error || '无法获取 AI 回复'}` }]);
      }
    } catch (error) {
      setMessages(prev => [...prev, { role: 'ai', content: '连接服务器失败，请检查后端是否开启。' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ position: 'fixed', bottom: '20px', right: '20px', zIndex: 9999 }}>
      {/* 聊天窗口 */}
      {isOpen && (
        <div style={{
          width: '380px', height: '500px', background: 'rgba(28, 28, 28, 0.95)',
          borderRadius: '16px', border: '1px solid #444', backdropFilter: 'blur(10px)',
          display: 'flex', flexDirection: 'column', boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
          marginBottom: '15px', overflow: 'hidden', color: '#fff', fontFamily: 'sans-serif'
        }}>
          {/* 头部 */}
          <div style={{ padding: '15px', background: '#2c2c2c', borderBottom: '1px solid #444', display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ fontWeight: 'bold' }}>✈️ 航空 AI 助手 (DeepSeek R1)</span>
            <button onClick={() => setIsOpen(false)} style={{ background: 'none', border: 'none', color: '#888', cursor: 'pointer', fontSize: '20px' }}>×</button>
          </div>

          {/* 消息区域 */}
          <div ref={scrollRef} style={{ flex: 1, padding: '15px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {messages.map((msg, i) => (
              <div key={i} style={{
                alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                background: msg.role === 'user' ? '#0084ff' : '#3d3d3d',
                padding: '10px 14px', borderRadius: '12px', maxWidth: '85%', fontSize: '14px', lineHeight: '1.5'
              }}>
                {msg.content}
              </div>
            ))}
            {loading && <div style={{ color: '#aaa', fontSize: '12px' }}>AI 正在分析数据库...</div>}
          </div>

          {/* 输入区域 */}
          <div style={{ padding: '15px', borderTop: '1px solid #444', display: 'flex', gap: '10px' }}>
            <input 
              value={input} onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
              placeholder="输入你的问题..."
              style={{ flex: 1, background: '#222', border: '1px solid #555', borderRadius: '8px', padding: '8px 12px', color: '#fff', outline: 'none' }}
            />
            <button onClick={handleSendMessage} style={{ background: '#0084ff', border: 'none', borderRadius: '8px', padding: '8px 16px', color: '#fff', cursor: 'pointer' }}>发送</button>
          </div>
        </div>
      )}

      {/* 入口按钮 */}
      <div 
        onClick={() => setIsOpen(!isOpen)}
        style={{
          width: '60px', height: '60px', borderRadius: '30px', background: '#0084ff',
          display: 'flex', justifyContent: 'center', alignItems: 'center', cursor: 'pointer',
          boxShadow: '0 4px 15px rgba(0, 132, 255, 0.4)', transition: 'transform 0.2s'
        }}
        onMouseEnter={(e) => e.currentTarget.style.transform = 'scale(1.1)'}
        onMouseLeave={(e) => e.currentTarget.style.transform = 'scale(1)'}
      >
        <span style={{ fontSize: '30px' }}>🤖</span>
      </div>
    </div>
  );
};

export default AIAgent;