import React, { useState, useEffect, useRef } from 'react'
import './App.css'
import MapView from './components/MapView'
import Dashboard from './components/Dashboard'
import StatisticsBoard from './components/StatisticsBoard'
import AIAgent from './components/AIAgent';
function App() {
  const [isFiltersOpen, setIsFiltersOpen] = useState(true)
  const [showMenu, setShowMenu] = useState(false)
  const [showStatsBoard, setShowStatsBoard] = useState(false)
  const [isStatsBoardClosing, setIsStatsBoardClosing] = useState(false)  
  const [searchQuery, setSearchQuery] = useState('')
  const [filters, setFilters] = useState({
    startDate: '2025-01-01',
    endDate: '2025-06-30',
    minFatalities: '',
    maxFatalities: '',
    operator: [],
    aircraftType: [],
    category: 'all'
  })
  const [filteredData, setFilteredData] = useState([]);
  const isStatsBoardVisible = showStatsBoard || isStatsBoardClosing;
  
  useEffect(() => {
    console.log('App组件已挂载');
    console.log('MapView组件:', typeof MapView);
    console.log('Dashboard组件:', typeof Dashboard);
    console.log('StatisticsBoard组件:', typeof StatisticsBoard);
  }, []);

  useEffect(() => {
  // 构造查询参数
  const params = new URLSearchParams();
  if (filters.startDate) params.append('startDate', filters.startDate);
  if (filters.endDate) params.append('endDate', filters.endDate);
  if (filters.minFatalities) params.append('minFatalities', filters.minFatalities);
  if (filters.maxFatalities) params.append('maxFatalities', filters.maxFatalities);
  if (filters.operator && filters.operator.length > 0) params.append('operator', filters.operator.join(','));
  if (filters.aircraftType && filters.aircraftType.length > 0) params.append('aircraftType', filters.aircraftType.join(','));
  if (filters.category && filters.category !== 'all') params.append('category', filters.category);
  if (searchQuery) params.append('q', searchQuery);

  fetch(`/api/search?${params.toString()}&limit=1000`)
    .then(res => res.json())
    .then(res => setFilteredData(res.data || []));
}, [filters, searchQuery]);

  const handleSearchChange = (newQuery) => {
    setSearchQuery(newQuery)
    console.log('App收到搜索查询:', newQuery)
  }

  const handleFiltersChange = (newFilters) => {
    setFilters(newFilters)
    console.log('App收到筛选变化:', newFilters)
  }  
  //const statsBoardRef = useRef();
  const handleCloseStatsBoard = () => {
    setIsStatsBoardClosing(true)
    
    setTimeout(() => {
      setShowStatsBoard(false)
      setIsStatsBoardClosing(false)
    }, 350) 
  }
/*
    const handleStatsBoardAnimationEnd = () => {
    if (isStatsBoardClosing) {
      setShowStatsBoard(false);
      setIsStatsBoardClosing(false);
    }
  }
*/
  return (
    <div className="App">
      {/* 顶部导航栏 */}
      <header style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        background: '#1a1a1a',
        color: 'white',
        padding: '8px 20px',
        zIndex: 1000,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        height: '50px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
        borderBottom: '1px solid #333',
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
      }}>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          {/* AAV Logo */}
          <div style={{
            background: 'white',
            color: '#1a1a1a',
            padding: '6px 12px',
            borderRadius: '4px',
            fontWeight: 'bold',
            fontSize: '16px',
            marginRight: '15px',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}>
            <span style={{ display: 'flex', alignItems: 'center', height: '22px' }}>
              <img src="/LOGO.png" alt="logo" style={{ height: '22px', width: '22px', display: 'block' }} />
            </span>
            A&thinsp;A&thinsp;V
          </div>
          <span style={{ 
            fontSize: '11px',
            color: '#999',
            fontWeight: '500',
            letterSpacing: '1px'
          }}>
            AIR ACCIDENTS VISUALIZATION
          </span>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          {(searchQuery || Object.values(filters).some(f => f !== 'all' && f !== '')) && (
            <div style={{
              background: 'rgba(0, 132, 255, 0.2)',
              color: '#0084ff',
              padding: '4px 8px',
              borderRadius: '4px',
              fontSize: '12px',
              fontWeight: 'bold'
            }}>
              FILTERED
            </div>
          )}

          <button 
            onClick={() => setIsFiltersOpen(!isFiltersOpen)}
            style={{
              background: 'transparent',
              color: '#0084ff',
              border: 'none',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: '500',
              padding: '8px 12px',
              borderRadius: '4px',
              transition: 'background 0.2s ease'
            }}
            onMouseEnter={(e) => e.target.style.background = 'rgba(0, 132, 255, 0.1)'}
            onMouseLeave={(e) => e.target.style.background = 'transparent'}
          >
            {isFiltersOpen ? 'HIDE FILTERS' : 'SHOW FILTERS'}
          </button>
          
          <div style={{ position: 'relative' }}>
            <button 
              onClick={() => setShowMenu(!showMenu)}
              style={{
                background: 'transparent',
                color: 'white',
                border: 'none',
                cursor: 'pointer',
                fontSize: '18px',
                padding: '8px',
                borderRadius: '4px',
                transition: 'background 0.2s ease'
              }}
              onMouseEnter={(e) => e.target.style.background = 'rgba(255, 255, 255, 0.1)'}
              onMouseLeave={(e) => e.target.style.background = 'transparent'}
            >
              ☰
            </button>
            
            {/* 下拉菜单 */}
            {showMenu && (
              <div style={{
                position: 'absolute',
                top: '100%',
                right: 0,
                marginTop: '12px',
                background: '#2c2c2c',
                border: '1px solid #333',
                borderRadius: '8px',
                boxShadow: '0 4px 20px rgba(0,0,0,0.5)',
                minWidth: '200px',
                zIndex: 1001
              }}>
                <button style={{
                  width: '100%',
                  padding: '12px 16px',
                  background: 'transparent',
                  color: 'white',
                  border: 'none',
                  textAlign: 'left',
                  cursor: 'pointer',
                  fontSize: '14px',
                  borderRadius: '8px 8px 0 0'
                }}
                onClick={() => {
                  setShowStatsBoard(true);
                  setShowMenu(false);
                }}
                onMouseEnter={(e) => e.target.style.background = '#333'}
                onMouseLeave={(e) => e.target.style.background = 'transparent'}
                >
                  📊 Statistics
                </button>
                <button style={{
                  width: '100%',
                  padding: '12px 16px',
                  background: 'transparent',
                  color: 'white',
                  border: 'none',
                  textAlign: 'left',
                  cursor: 'pointer',
                  fontSize: '14px'
                }}
                onMouseEnter={(e) => e.target.style.background = '#333'}
                onMouseLeave={(e) => e.target.style.background = 'transparent'}
                >
                  🔗 Export <span style={{ fontSize: '11px', color: '#888', marginLeft: 4 }}>(Constructing)</span>
                </button>
                <button style={{
                  width: '100%',
                  padding: '12px 16px',
                  background: 'transparent',
                  color: 'white',
                  border: 'none',
                  textAlign: 'left',
                  cursor: 'pointer',
                  fontSize: '14px'
                }}
                onMouseEnter={(e) => e.target.style.background = '#333'}
                onMouseLeave={(e) => e.target.style.background = 'transparent'}
                >
                  ⚙️ Settings <span style={{ fontSize: '11px', color: '#888', marginLeft: 4 }}>(Constructing)</span>
                </button>
                <button style={{
                  width: '100%',
                  padding: '12px 16px',
                  background: 'transparent',
                  color: 'white',
                  border: 'none',
                  textAlign: 'left',
                  cursor: 'pointer',
                  fontSize: '14px',
                  borderRadius: '0 0 8px 8px'
                }}
                onMouseEnter={(e) => e.target.style.background = '#333'}
                onMouseLeave={(e) => e.target.style.background = 'transparent'}
                >
                  ❓ Help  <span style={{ fontSize: '11px', color: '#888', marginLeft: 4 }}>(Constructing)</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* 主要内容区域 */}
      <main style={{
        position: 'fixed',
        top: '50px',
        left: 0,
        right: 0,
        bottom: 0,
        display: 'flex',
        background: '#000'
      }}>
        {/* 地图容器 */}
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: isFiltersOpen ? '350px' : '0',
          bottom: 0,
          transition: 'right 0.3s ease',
          background: '#000'
        }}>
          <MapView 
            isFiltersOpen={isFiltersOpen} 
            searchQuery={searchQuery}
            filters={filters}
          />
        </div>

        {/* 右侧筛选面板 */}
        {isFiltersOpen && (
          <div style={{
            position: 'absolute',
            top: 0,
            right: 0,
            bottom: 0,
            width: '350px', 
            background: '#1a1a1a',
            borderLeft: '1px solid #333',
            boxShadow: '-4px 0 12px rgba(0,0,0,0.3)',
            overflow: 'hidden',
            transform: 'translateX(0)',
            transition: 'transform 0.3s ease'
          }}>
            <Dashboard 
              searchQuery={searchQuery}
              onSearchChange={handleSearchChange}
              filters={filters}
              onFiltersChange={handleFiltersChange}
              filteredData={filteredData}
            />
          </div>
        )}
      </main>

      {/* 点击外部关闭菜单 */}
      {showMenu && (
        <div 
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            zIndex: 999
          }}
          onClick={() => setShowMenu(false)}
        />
      )}
    

      {/* 底部向上小箭头按钮 */}
      <div
        style={{
          position: 'fixed',
          left: '50%',
          transform: `translateX(${isFiltersOpen ? '-92%' : '-50%'})`, 
          bottom:  '24px',
          zIndex: 2001,
          display: 'flex',
          flexDirection: 'row',
          alignItems: 'center',
          gap: '10px',
          //transition: 'bottom 0.18s cubic-bezier(.4,1.4,.6,1), transform 0.3s ease'
        }}
      >
        <span
          style={{
            fontSize: '16px',
            color: '#0084ff',
            fontWeight: 650,
            letterSpacing: '1px',
            textShadow: '0 1px 4px #000',
            cursor: 'pointer',
            userSelect: 'none'
          }}
          onClick={() => setShowStatsBoard(true)}
          title="Show Dashboard"
        >
          Dashboard
        </span>
        <div
          style={{
            cursor: 'pointer',
            background: '#232323',
            borderRadius: '50%',
            width: '38px',
            height: '38px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
            border: '1px solid #333',
            transition: 'bottom 0.3s'
          }}
          onClick={() => setShowStatsBoard(true)}
          title="Show Dashboard"
        >
          <span style={{ fontSize: '22px', color: '#0084ff', userSelect: 'none' }}>▲</span>
        </div>
      </div>


      {/* 底部弹出数据看板 */}
      {(showStatsBoard || isStatsBoardClosing) && (
        <div
          //ref={statsBoardRef}
          style={{
            position: 'fixed',
            left: 0,
            right: 0,
            bottom: 0,
            zIndex: 2002,
            background: 'rgba(26,26,26,0.98)',
            borderTopLeftRadius: '18px',
            borderTopRightRadius: '18px',
            boxShadow: '0 -4px 24px rgba(0,0,0,0.5)',
            padding: '0 24px 24px 24px',
            minHeight: '340px',
            maxHeight: '92vh',
            overflowY: 'auto',
            animation: `${isStatsBoardClosing ? 'slideDown' : 'slideUp'} 0.35s cubic-bezier(.4,0,.2,1)`
          }}
          //onAnimationEnd={handleStatsBoardAnimationEnd}
        >
          <StatisticsBoard onClose={handleCloseStatsBoard} />
        </div>
      )}

      {/* 弹出动画 */}
      <style>
        {`
        @keyframes slideUp {
          from { transform: translateY(100%); }
          to { transform: translateY(0); }
        }
        `}
      </style>
      <AIAgent />
    </div>
  )
}

export default App