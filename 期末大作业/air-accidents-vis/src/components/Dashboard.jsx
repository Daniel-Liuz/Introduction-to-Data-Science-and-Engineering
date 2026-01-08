import React, { useState, useEffect, useRef } from 'react'
import ReactDatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import { enUS } from "date-fns/locale";

function Dashboard({ searchQuery, onSearchChange, filters, onFiltersChange, filteredData = [] }) {
  const [filterOptions, setFilterOptions] = useState(null)
  const [operatorSearch, setOperatorSearch] = useState('')
  const [aircraftSearch, setAircraftSearch] = useState('')
  const [showOperatorDropdown, setShowOperatorDropdown] = useState(false)
  const [showAircraftDropdown, setShowAircraftDropdown] = useState(false)

  const operatorRef = useRef(null)
  const aircraftRef = useRef(null)
  const activeFilters = filters || {
    startDate: '2025-01-01',
    endDate: '2025-06-30',
    minFatalities: '',
    maxFatalities: '',
    operator: [],
    aircraftType: [],
    category: 'all'
  }

  const API_BASE_URL = '/api'

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (operatorRef.current && !operatorRef.current.contains(event.target)) {
        setShowOperatorDropdown(false)
      }
      if (aircraftRef.current && !aircraftRef.current.contains(event.target)) {
        setShowAircraftDropdown(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [])

  // 获取筛选选项
  const fetchFilterOptions = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/filter-options`)
      if (response.ok) {
        const options = await response.json()
        setFilterOptions(options)
        console.log(' Dashboard筛选选项加载完成:', options)
      }
    } catch (err) {
      console.error('! Dashboard获取筛选选项失败:', err)
    }
  }

  useEffect(() => {
    fetchFilterOptions()
  }, [])

  // 处理筛选变化
  const handleFilterChange = (filterKey, value) => {
    const newFilters = { ...activeFilters, [filterKey]: value }
    if (onFiltersChange) {
      onFiltersChange(newFilters)
    }
  }

  const handleOperatorSelect = (operator) => {
    const currentOperators = Array.isArray(activeFilters.operator) ? activeFilters.operator : []
    let newOperators
    
    if (currentOperators.includes(operator)) {
      // 如果已选中，则移除
      newOperators = currentOperators.filter(op => op !== operator)
    } else {
      // 如果未选中，则添加
      newOperators = [...currentOperators, operator]
    }
    handleFilterChange('operator', newOperators)
  }
  const handleAircraftSelect = (aircraft) => {
    const currentAircraft = Array.isArray(activeFilters.aircraftType) ? activeFilters.aircraftType : []
    let newAircraft
    if (currentAircraft.includes(aircraft)) {
      newAircraft = currentAircraft.filter(ac => ac !== aircraft)
    } else {
      newAircraft = [...currentAircraft, aircraft]
    }
    handleFilterChange('aircraftType', newAircraft)
  }

  const aircraftTypeCountMap = {};
  filteredData.forEach(item => {
    if (item.Type) {
      aircraftTypeCountMap[item.Type] = (aircraftTypeCountMap[item.Type] || 0) + 1;
    }
  })

  const operatorCountMap = {};
  filteredData.forEach(item => {
    if (item['Owner/operator']) {
      operatorCountMap[item['Owner/operator']] = (operatorCountMap[item['Owner/operator']] || 0) + 1;
    }
  })

  const filteredOperators = (filterOptions?.operators || [])
    .filter(op => op['Owner/operator'].toLowerCase().includes(operatorSearch.toLowerCase()))
    .sort((a, b) => (operatorCountMap[b['Owner/operator']] || 0) - (operatorCountMap[a['Owner/operator']] || 0));

  const filteredAircraftTypes = (filterOptions?.aircraftTypes || [])
    .filter(type => type.Type.toLowerCase().includes(aircraftSearch.toLowerCase()))
    .sort((a, b) => (aircraftTypeCountMap[b.Type] || 0) - (aircraftTypeCountMap[a.Type] || 0));

  // 生效按钮（双保险）
  const applyFilters = () => {
    if (onFiltersChange) {
      onFiltersChange({ ...activeFilters })
    }
  }
  // 重置筛选
  const resetFilters = () => {
    const defaultFilters = {
      startDate: '',
      endDate: '',
      minFatalities: '',
      maxFatalities: '',
      operator: [],
      aircraftType: [],
      category: 'all'
    }
    if (onFiltersChange) {
      onFiltersChange(defaultFilters)
    }
    if (onSearchChange) {
      onSearchChange('')
    }
    setOperatorSearch('')
    setAircraftSearch('')
  }


  
  return (
    <div style={{
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      background: '#1a1a1a',
      color: 'white',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      width: '100%' 
    }}>
      {/* Filters Header */}
      <div style={{
        padding: '25px 20px 12px 20px', 
        background: '#2c2c2c',
        borderBottom: '1px solid #333'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <h2 style={{ 
            margin: 0, 
            fontSize: '16px', 
            color: 'white',
            fontWeight: '500'
          }}>
            Filters & Search
          </h2>
          <div style={{
            background: '#0084ff',
            color: 'white',
            fontSize: '10px',
            padding: '2px 6px',
            borderRadius: '3px',
            fontWeight: 'bold',
            letterSpacing: '0.5px'
          }}>
            ACTIVE
          </div>
          <button style={{
            background: 'none',
            border: 'none',
            color: '#999',
            fontSize: '14px',
            cursor: 'pointer',
            marginLeft: 'auto'
          }}>
            ℹ️
          </button>
        </div>
      </div>

      {/* 搜索栏 */}
      <div style={{
        padding: '20px',
        borderBottom: '1px solid #333'
      }}>
        <label style={{
          display: 'block',
          marginBottom: '8px',
          fontSize: '13px',
          color: 'white',
          fontWeight: 'bold'
        }}>
          🔍 Search Flights
        </label>
        <input
          type="text"
          placeholder="Search by flight number, route, or location..."
          value={searchQuery || ''}
          onChange={(e) => onSearchChange && onSearchChange(e.target.value)}
          style={{
            width: '100%',
            padding: '10px',
            borderRadius: '6px',
            border: '1px solid #555',
            background: '#2c2c2c',
            color: 'white',
            fontSize: '14px',
            boxSizing: 'border-box'
          }}
        />
      </div>

      {/* 筛选选项 */}
      <div style={{
        flex: 1,
        padding: '20px', // 调整padding
        overflow: 'auto'
      }}>
        {/* 时间范围筛选 */}
        <div style={{ marginBottom: '20px' }}>
          <label style={{
            display: 'block',
            marginBottom: '8px',
            fontSize: '13px',
            color: 'white',
            fontWeight: 'bold'
          }}>
            📅 Date Range
          </label>
          <div style={{ display: 'flex', gap: '10px', marginBottom: '5px' }}>
            <div>
              <label style={{
                display: 'block',
                marginBottom: '4px',
                fontSize: '11px',
                color: '#999'
              }}>
                From (YYYY-MM-DD)
              </label>
              <ReactDatePicker
                selected={activeFilters.startDate ? new Date(activeFilters.startDate) : null}
                onChange={date => handleFilterChange('startDate', date ? date.toISOString().slice(0, 10) : '')}
                dateFormat="yyyy-MM-dd"
                locale={enUS}
                placeholderText="Select start date"
                className="custom-datepicker"
                popperPlacement="bottom"
                style={{
                  width: '30px',
                  padding: '8px',
                  borderRadius: '4px',
                  border: '1px solid #555',
                  background: '#2c2c2c',
                  color: 'white',
                  fontSize: '14px',
                  boxSizing: 'border-box'
                }}
                calendarClassName="custom-datepicker-calendar"
              />
            </div>
            <div>
              <label style={{
                display: 'block',
                marginBottom: '4px',
                fontSize: '11px',
                color: '#999'
              }}>
                To
              </label>
              <ReactDatePicker
                selected={activeFilters.endDate ? new Date(activeFilters.endDate) : null}
                onChange={date => handleFilterChange('endDate', date ? date.toISOString().slice(0, 10) : '')}
                dateFormat="yyyy-MM-dd"
                locale={enUS}
                placeholderText="Select end date"
                className="custom-datepicker"
                popperPlacement="bottom"
                style={{
                  width: '30px',
                  padding: '8px',
                  borderRadius: '4px',
                  border: '1px solid #555',
                  background: '#2c2c2c',
                  color: 'white',
                  fontSize: '14px',
                  boxSizing: 'border-box'
                }}
                calendarClassName="custom-datepicker-calendar"
              />
            </div>
          </div>
          {/* 快速选择按钮 */}
          <div style={{ display: 'flex', gap: '5px', marginTop: '8px' }}>
            <button
              onClick={() => {
                const now = new Date()
                const oneYearAgo = new Date(now.getFullYear() - 1, now.getMonth(), now.getDate())
                handleFilterChange('startDate', oneYearAgo.toISOString().split('T')[0])
                handleFilterChange('endDate', now.toISOString().split('T')[0])
              }}
              style={{
                padding: '4px 8px',
                fontSize: '10px',
                border: '1px solid #555',
                background: 'transparent',
                color: '#999',
                borderRadius: '3px',
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}
              onMouseEnter={(e) => {
                e.target.style.background = '#333'
                e.target.style.color = 'white'
              }}
              onMouseLeave={(e) => {
                e.target.style.background = 'transparent'
                e.target.style.color = '#999'
              }}
            >
              Last Year
            </button>
                        <button
              onClick={() => {
                if (onFiltersChange) {
                  onFiltersChange({
                    ...activeFilters,
                    startDate: '2025-01-01',
                    endDate: '2025-06-30'
                  });
                }
              }}
              style={{
                padding: '4px 8px',
                fontSize: '10px',
                border: '1px solid #555',
                background: 'transparent',
                color: '#999',
                borderRadius: '3px',
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}
              onMouseEnter={(e) => {
                e.target.style.background = '#333'
                e.target.style.color = 'white'
              }}
              onMouseLeave={(e) => {
                e.target.style.background = 'transparent'
                e.target.style.color = '#999'
              }}
            >
              2025 H1
            </button>
            <button
             onClick={() => {
              if (onFiltersChange) {
                onFiltersChange({
                  ...activeFilters,
                  startDate: '2024-01-01',
                  endDate: '2024-12-31'
                });
              }
            }}
              style={{
                padding: '4px 8px',
                fontSize: '10px',
                border: '1px solid #555',
                background: 'transparent',
                color: '#999',
                borderRadius: '3px',
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}
              onMouseEnter={(e) => {
                e.target.style.background = '#333'
                e.target.style.color = 'white'
              }}
              onMouseLeave={(e) => {
                e.target.style.background = 'transparent'
                e.target.style.color = '#999'
              }}
            >
              2024
            </button>
            <button
             onClick={() => {
              if (onFiltersChange) {
                onFiltersChange({
                  ...activeFilters,
                  startDate: '2023-01-01',
                  endDate: '2023-12-31'
                });
              }
            }}
              style={{
                padding: '4px 8px',
                fontSize: '10px',
                border: '1px solid #555',
                background: 'transparent',
                color: '#999',
                borderRadius: '3px',
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}
              onMouseEnter={(e) => {
                e.target.style.background = '#333'
                e.target.style.color = 'white'
              }}
              onMouseLeave={(e) => {
                e.target.style.background = 'transparent'
                e.target.style.color = '#999'
              }}
            >
              2023
            </button>
            <button
             onClick={() => {
              if (onFiltersChange) {
                onFiltersChange({
                  ...activeFilters,
                  startDate: '2022-01-01',
                  endDate: '2022-12-31'
                });
              }
            }}
              style={{
                padding: '4px 8px',
                fontSize: '10px',
                border: '1px solid #555',
                background: 'transparent',
                color: '#999',
                borderRadius: '3px',
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}
              onMouseEnter={(e) => {
                e.target.style.background = '#333'
                e.target.style.color = 'white'
              }}
              onMouseLeave={(e) => {
                e.target.style.background = 'transparent'
                e.target.style.color = '#999'
              }}
            >
              2022
            </button>
            <button
             onClick={() => {
              if (onFiltersChange) {
                onFiltersChange({
                  ...activeFilters,
                  startDate: '2021-01-01',
                  endDate: '2021-12-31'
                });
              }
            }}
              style={{
                padding: '4px 8px',
                fontSize: '10px',
                border: '1px solid #555',
                background: 'transparent',
                color: '#999',
                borderRadius: '3px',
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}
              onMouseEnter={(e) => {
                e.target.style.background = '#333'
                e.target.style.color = 'white'
              }}
              onMouseLeave={(e) => {
                e.target.style.background = 'transparent'
                e.target.style.color = '#999'
              }}
            >
              2021
            </button>
          </div>
        </div>
        
        {/* 死亡人数范围 */}
        <div style={{ marginBottom: '20px' }}>
          <label style={{
            display: 'block',
            marginBottom: '8px',
            fontSize: '13px',
            color: 'white',
            fontWeight: 'bold'
          }}>
            💀 Fatalities Range
          </label>
          <div style={{ display: 'flex', gap: '10px', marginBottom: '5px' }}>
            <input
              type="number"
              placeholder="Min"
              value={activeFilters.minFatalities}
              onChange={(e) => handleFilterChange('minFatalities', e.target.value)}
              style={{
                flex: 1,
                padding: '8px',
                borderRadius: '4px',
                border: '1px solid #555',
                background: '#333',
                color: 'white',
                fontSize: '14px',
                width: '30px'
              }}
            />
            <input
              type="number"
              placeholder="Max"
              value={activeFilters.maxFatalities}
              onChange={(e) => handleFilterChange('maxFatalities', e.target.value)}
              style={{
                flex: 1,
                padding: '8px',
                borderRadius: '4px',
                border: '1px solid #555',
                background: '#333',
                color: 'white',
                fontSize: '14px',
                width: '30px'
              }}
            />
          </div>
        </div>

        {/* 运营商筛选 */}
        <div style={{ marginBottom: '20px', position: 'relative' }} ref={operatorRef}>
          <label style={{
            display: 'block',
            marginBottom: '8px',
            fontSize: '13px',
            color: 'white',
            fontWeight: 'bold'
          }}>
            🏢 Operator ({Array.isArray(activeFilters.operator) ? activeFilters.operator.length : 0} selected)
          </label>
          
          {/* 已选择的运营商标签 */}
          {Array.isArray(activeFilters.operator) && activeFilters.operator.length > 0 && (
            <div style={{
              marginBottom: '8px',
              display: 'flex',
              flexWrap: 'wrap',
              gap: '4px'
            }}>
              {activeFilters.operator.map(op => (
                <span key={op} style={{
                  background: '#0084ff',
                  color: 'white',
                  padding: '2px 6px',
                  borderRadius: '3px',
                  fontSize: '10px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px'
                }}>
                  {op.length > 15 ? `${op.substring(0, 15)}...` : op}
                  <button
                    onClick={() => handleOperatorSelect(op)}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: 'white',
                      cursor: 'pointer',
                      fontSize: '12px',
                      padding: '0',
                      lineHeight: 1
                    }}
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}

          <input
            type="text"
            placeholder="Search operators..."
            value={operatorSearch}
            onChange={(e) => setOperatorSearch(e.target.value)}
            onFocus={() => setShowOperatorDropdown(true)}
            style={{
              width: '100%',
              padding: '10px',
              borderRadius: '6px',
              border: '1px solid #555',
              background: '#2c2c2c',
              color: 'white',
              fontSize: '14px',
              boxSizing: 'border-box'
            }}
          />
          
          {showOperatorDropdown && (
            <div style={{
              position: 'absolute',
              top: '100%',
              left: 0,
              right: 0,
              background: '#2c2c2c',
              border: '1px solid #555',
              borderTop: 'none',
              borderRadius: '0 0 6px 6px',
              maxHeight: '200px',
              overflow: 'auto',
              zIndex: 1000
            }}>
              {filteredOperators.slice(0, 200).map(op => (
                <div
                  key={op['Owner/operator']}
                  onClick={() => handleOperatorSelect(op['Owner/operator'])}
                  style={{
                    padding: '8px 12px',
                    cursor: 'pointer',
                    background: Array.isArray(activeFilters.operator) && activeFilters.operator.includes(op['Owner/operator']) ? '#0084ff' : 'transparent',
                    color: 'white',
                    fontSize: '13px',
                    borderBottom: '1px solid #555'
                  }}
                  onMouseEnter={(e) => {
                    if (!Array.isArray(activeFilters.operator) || !activeFilters.operator.includes(op['Owner/operator'])) {
                      e.target.style.background = '#333'
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!Array.isArray(activeFilters.operator) || !activeFilters.operator.includes(op['Owner/operator'])) {
                      e.target.style.background = 'transparent'
                    }
                  }}
                >
                  {op['Owner/operator']} ({operatorCountMap[op['Owner/operator']] || 0})
                </div>
              ))}
            </div>
          )}
        </div>
        
        {/* 飞机类型多选筛选 */}
        <div style={{ marginBottom: '20px', position: 'relative' }} ref={aircraftRef}>
          <label style={{
            display: 'block',
            marginBottom: '8px',
            fontSize: '13px',
            color: 'white',
            fontWeight: 'bold'
          }}>
            ✈️ Aircraft Type ({Array.isArray(activeFilters.aircraftType) ? activeFilters.aircraftType.length : 0} selected)
          </label>

          {/* 已选择的飞机类型标签 */}
          {Array.isArray(activeFilters.aircraftType) && activeFilters.aircraftType.length > 0 && (
            <div style={{
              marginBottom: '8px',
              display: 'flex',
              flexWrap: 'wrap',
              gap: '4px'
            }}>
              {activeFilters.aircraftType.map(type => (
                <span key={type} style={{
                  background: '#0084ff',  
                  color: 'white',           
                  border: '1px solid #0084ff',
                  padding: '2px 6px',
                  borderRadius: '3px',
                  fontSize: '10px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px'
                }}>
                  {type.length > 15 ? `${type.substring(0, 15)}...` : type}
                  <button
                    onClick={() => handleAircraftSelect(type)}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: '#bfc6c9ff',
                      cursor: 'pointer',
                      fontSize: '12px',
                      padding: '0',
                      lineHeight: 1
                    }}
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}

          <input
            type="text"
            placeholder="Search aircraft types..."
            value={aircraftSearch}
            onChange={(e) => setAircraftSearch(e.target.value)}
            onFocus={() => setShowAircraftDropdown(true)}
            style={{
              width: '100%',
              padding: '10px',
              borderRadius: '6px',
              border: '1px solid #555',
              background: '#2c2c2c',
              color: 'white',
              fontSize: '14px',
              boxSizing: 'border-box'
            }}
          />
          
          {showAircraftDropdown && (
            <div style={{
              position: 'absolute',
              top: '100%',
              left: 0,
              right: 0,
              background: '#2c2c2c',
              border: '1px solid #555',
              borderTop: 'none',
              borderRadius: '0 0 6px 6px',
              maxHeight: '200px',
              overflow: 'auto',
              zIndex: 1000
            }}>
              {filteredAircraftTypes.slice(0, 200).map(type => (
                <div
                  key={type.Type}
                  onClick={() => handleAircraftSelect(type.Type)}
                  style={{
                    padding: '8px 12px',
                    cursor: 'pointer',
                    background: Array.isArray(activeFilters.aircraftType) && activeFilters.aircraftType.includes(type.Type) ? '#0084ff' : 'transparent',
                    color: 'white',
                    fontSize: '13px',
                    borderBottom: '1px solid #555'
                  }}
                  onMouseEnter={(e) => {
                    if (!Array.isArray(activeFilters.aircraftType) || !activeFilters.aircraftType.includes(type.Type)) {
                      e.target.style.background = '#333'
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!Array.isArray(activeFilters.aircraftType) || !activeFilters.aircraftType.includes(type.Type)) {
                      e.target.style.background = 'transparent'
                    }
                  }}
                >
                  {type.Type} ({aircraftTypeCountMap[type.Type] || 0})
                </div>
              ))}
            </div>
          )}
        </div>

         {/* 事故类型筛选 */}
        <div style={{ marginBottom: '20px' }}>
          <label style={{
            display: 'block',
            marginBottom: '8px',
            fontSize: '13px',
            color: 'white',
            fontWeight: 'bold'
          }}>
            🔧 Accident Category
          </label>
          <select
            value={activeFilters.category}
            onChange={(e) => handleFilterChange('category', e.target.value)}
            style={{
              width: '100%',
              padding: '10px',
              borderRadius: '6px',
              border: '1px solid #555',
              background: '#2c2c2c',
              color: 'white',
              fontSize: '14px'
            }}
          >
            <option value="all">All Categories</option>
            {filterOptions?.categories?.map(cat => (
              <option key={cat.Category} value={cat.Category}>
                {cat.Category} ({cat.count})
              </option>
            ))}
          </select>
        </div>

        {/* 筛选生效按钮 */}
        <button
          onClick={applyFilters}
          style={{
            width: '100%',
            padding: '12px',
            background: '#0084ff',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '14px',
            fontWeight: 'bold',
            transition: 'background 0.2s ease',
            marginBottom: '10px'
          }}
          onMouseEnter={(e) => {
            e.target.style.background = '#0070dd';
          }}
          onMouseLeave={(e) => {
            e.target.style.background = '#0084ff';
          }}
        >
          Apply Filters
        </button>

        {/* 重置按钮 */}
        <button
          onClick={resetFilters}
          style={{
            width: '100%',
            padding: '10px',
            background: 'transparent',
            color: '#999',
            border: '1px solid #555',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '13px',
            transition: 'all 0.2s ease'
          }}
          onMouseEnter={(e) => {
            e.target.style.background = '#333';
            e.target.style.color = 'white';
          }}
          onMouseLeave={(e) => {
            e.target.style.background = 'transparent';
            e.target.style.color = '#999';
          }}
        >
          Reset Filters
        </button>
      </div>

      {/* 当前筛选状态 */}
      <div style={{
        padding: '15px 20px', 
        background: '#2c2c2c',
        borderTop: '1px solid #333'
      }}>
        <div style={{
          fontSize: '12px',
          color: '#999',
          marginBottom: '8px'
        }}>
          Active Filters:
        </div>
        <div style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '5px'
        }}>
          {(activeFilters.startDate || activeFilters.endDate) && (
            <span style={{
              background: '#0084ff',
              color: 'white',
              padding: '2px 6px',
              borderRadius: '3px',
              fontSize: '10px'
            }}>
              {activeFilters.startDate} to {activeFilters.endDate}
            </span>
          )}
          {Array.isArray(activeFilters.operator) && activeFilters.operator.length > 0 && (
            <span style={{
              background: '#333', 
              color: '#ffd700',  
              border: '1px solid #555',   
              padding: '2px 6px',
              borderRadius: '3px',
              fontSize: '10px'
            }}>
              {activeFilters.operator.length} operators
            </span>
          )}
          {Array.isArray(activeFilters.aircraftType) && activeFilters.aircraftType.length > 0 && (
            <span style={{
              background: '#2a2a2a',      
              color: '#edfaffff',           
              border: '1px solid #0084ff',  
              padding: '2px 6px',
              borderRadius: '3px',
              fontSize: '10px'
            }}>
              {activeFilters.aircraftType.length} aircraft
            </span>
          )}
          {activeFilters.category !== 'all' && (
            <span style={{
              background: '#28a745',
              color: 'white',
              padding: '2px 6px',
              borderRadius: '3px',
              fontSize: '10px'
            }}>
              {activeFilters.category}
            </span>
          )}
          {(activeFilters.minFatalities || activeFilters.maxFatalities) && (
            <span style={{
              background: '#6c757d',
              color: 'white',
              padding: '2px 6px',
              borderRadius: '3px',
              fontSize: '10px'
            }}>
              {activeFilters.minFatalities || '0'}-{activeFilters.maxFatalities || '∞'} fatalities
            </span>
          )}
        </div>
      </div>
    </div>
  )
}

export default Dashboard