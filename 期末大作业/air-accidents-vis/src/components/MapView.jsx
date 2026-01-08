import React, { useState, useEffect, useMemo } from 'react'
import { MapContainer, TileLayer, Polyline, Marker, Popup } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

// 修复Leaflet图标问题
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

function MapView({ isFiltersOpen, searchQuery, filters }) {
  const [selectedFlight, setSelectedFlight] = useState(null)
  const [mapLoaded, setMapLoaded] = useState(false)
  const [showRecentAccidents, setShowRecentAccidents] = useState(false)
  const [flightRoutes, setFlightRoutes] = useState([])
  const [recentIncidents, setRecentIncidents] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [statistics, setStatistics] = useState(null)

  const [unmappedAccidents, setUnmappedAccidents] = useState([]);
  const [showUnmapped, setShowUnmapped] = useState(false);
  
  const [searchResults, setSearchResults] = useState([])
  const [allSearchResults, setAllSearchResults] = useState([]) // 搜索分页
  const [isSearching, setIsSearching] = useState(false)
  const [showSearchResults, setShowSearchResults] = useState(false)
  const [mapSearchQuery, setMapSearchQuery] = useState('')
  const [searchPagination, setSearchPagination] = useState(null) // 分页信息
  const [isLoadingMore, setIsLoadingMore] = useState(false)

  const API_BASE_URL = '/api'


  const performSearch = async (query = '', currentFilters = {}, page = 1, append = false) => {
    if ((!query.trim()) &&(!currentFilters || Object.values(currentFilters).every(v => v === 'all' || v === '' || (Array.isArray(v) && v.length === 0)))) {
      setShowSearchResults(false)
      setAllSearchResults([])
      setUnmappedAccidents([])
      return
    }

    try {
      if (page === 1) {
        setIsSearching(true)
      } else {
        setIsLoadingMore(true)
      }
      
      const params = new URLSearchParams()
      if (query.trim()) params.append('q', query.trim())
      if (currentFilters.startDate) params.append('startDate', currentFilters.startDate)
      if (currentFilters.endDate) params.append('endDate', currentFilters.endDate)
      if (currentFilters.minFatalities) params.append('minFatalities', currentFilters.minFatalities)
      if (currentFilters.maxFatalities) params.append('maxFatalities', currentFilters.maxFatalities)
      if (currentFilters.operator !== 'all') params.append('operator', currentFilters.operator)
      if (currentFilters.aircraftType !== 'all') params.append('aircraftType', currentFilters.aircraftType)
      if (currentFilters.category !== 'all') params.append('category', currentFilters.category)
      
      params.append('page', page.toString())
      params.append('limit', '500')

      const response = await fetch(`${API_BASE_URL}/search?${params}`)
      
      if (response.ok) {
        const result = await response.json()
        const results = result.data || result
        
        const mapped = []
        const unmapped = []
        results.forEach(item => {
          if (
            item.dep_lat && item.dep_lon && item.arr_lat && item.arr_lon &&
            !isNaN(parseFloat(item.dep_lat)) && !isNaN(parseFloat(item.dep_lon)) &&
            !isNaN(parseFloat(item.arr_lat)) && !isNaN(parseFloat(item.arr_lon))
          ) {
            mapped.push(item)
          } else {
            unmapped.push(item)
          }
        })

        const startIndex = append ? allSearchResults.length : 0
        const formattedResults = transformAccidentData(results, startIndex)

        if (append && page > 1) {
          setAllSearchResults(prev => [...prev, ...formattedResults])
          setSearchResults(prev => [...prev, ...formattedResults])
          setUnmappedAccidents(prev => [...prev, ...unmapped])
        } else {
          setAllSearchResults(formattedResults)
          setSearchResults(formattedResults)
          setUnmappedAccidents(unmapped)
        }

        //setUnmappedAccidents(unmapped)
        setSearchPagination(result.pagination || null)
        setShowSearchResults(true)
        
        console.log(` 搜索完成 (第${page}页): 找到 ${formattedResults.length} 条结果, 总计 ${result.pagination?.totalRecords || formattedResults.length} 条`)
      }
    } catch (err) {
      console.error(' 搜索失败:', err)
    } finally {
      setIsSearching(false)
      setIsLoadingMore(false)
    }
  }

  const loadMoreResults = async () => {
    if (!searchPagination || !searchPagination.hasNextPage || isLoadingMore) return
    
    const nextPage = searchPagination.currentPage + 1
    await performSearch(
      mapSearchQuery, 
      filters || {
        year: 'all',
        minFatalities: '',
        maxFatalities: '',
        operator: 'all',
        aircraftType: 'all',
        category: 'all'
      }, 
      nextPage, 
      true // append = true
    )
  }

  const clearSearchAndFilters = () => {
    setMapSearchQuery('')
    setShowSearchResults(false)
    setSearchResults([])
    setAllSearchResults([])
    setSearchPagination(null)
    fetchUnmappedAccidents()
  }

  useEffect(() => {
    if (searchQuery !== undefined || filters !== undefined) {
      performSearch(searchQuery || mapSearchQuery || '', filters || {
        year: 'all',
        minFatalities: '',
        maxFatalities: '',
        operator: 'all',
        aircraftType: 'all',
        category: 'all',
        hasRoute: 'all'
      })
    }
  }, [searchQuery, filters, mapSearchQuery])
  
  useEffect(() => {
    if (searchQuery !== mapSearchQuery) {
      setMapSearchQuery(searchQuery || '')
    }
  }, [searchQuery])

  const handleSearchInputChange = (e) => {
      const value = e.target.value
      setMapSearchQuery(value)
      
      // 实时搜索
      performSearch(value, filters ||{
        year: 'all',
        minFatalities: '',
        maxFatalities: '',
        operator: 'all',
        aircraftType: 'all',
        category: 'all',
        hasRoute: 'all'
      })
  }
  
  const fetchUnmappedAccidents = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/unmapped-accidents`);
      if (res.ok) {
        const data = await res.json();
        setUnmappedAccidents(data);
      }
    } catch (err) {
      console.error('获取unmapped事故失败:', err);
    }
  };

  useEffect(() => {
    fetchUnmappedAccidents();
  }, []);


  const transformAccidentData = (rawData, startIndex = 0) => {
    return rawData
      .filter(accident => 
        accident.dep_lat && accident.dep_lon && 
        accident.arr_lat && accident.arr_lon &&
        !isNaN(parseFloat(accident.dep_lat)) &&
        !isNaN(parseFloat(accident.dep_lon)) &&
        !isNaN(parseFloat(accident.arr_lat)) &&
        !isNaN(parseFloat(accident.arr_lon))
      )
      .map((accident, index) => ({
        id: startIndex + index + 1,
        flightNumber: accident.Registration || `Unknown-${index}`,
        from: accident['Departure airport'] || 'Unknown',
        to: accident['Destination airport'] || 'Unknown',
        fromCode: accident.dep_IATA || accident.dep_ICAO || '',
        toCode: accident.arr_IATA || accident.arr_ICAO || '',
        status: 'accident',
        date: accident.Date ? new Date(accident.Date).toISOString().split('T')[0] : 'Unknown',
        location: accident.Location || 'Unknown',
        fatalities: accident.Fatalities ? accident.Fatalities.toString() : '0',
        otherFatalities: accident['Other fatalities'] ? accident['Other fatalities'].toString() : '0',
        occupants: accident.Occupants ? accident.Occupants.toString() : 'Unknown',
        cause: accident.Nature || 'Unknown cause',
        phase: accident.Phase || 'Unknown',
        operator: accident['Owner/operator'] || 'Unknown',
        aircraftType: accident.Type || 'Unknown',
        damage: accident['Aircraft damage'] || 'Unknown',
        category: accident.Category || 'Unknown',
        narrative: accident.Narrative || '',
        sourceUrl: accident.DetailURL || '', 
        origin: { 
          lat: parseFloat(accident.dep_lat), 
          lng: parseFloat(accident.dep_lon) 
        },
        destination: { 
          lat: parseFloat(accident.arr_lat), 
          lng: parseFloat(accident.arr_lon) 
        }
      }))
  }

  const transformRecentData = (rawData) => {
    return rawData.map((accident, index) => ({
      num: `${index + 1}.`,
      flight: accident.Registration || `Flight-${index + 1}`,
      route: `${accident['Departure airport'] || 'Unknown'} → ${accident['Destination airport'] || 'Unknown'}`,
      code: `${accident.dep_IATA || '???'} → ${accident.arr_IATA || '???'}`,
      date: accident.Date ? new Date(accident.Date).toISOString().split('T')[0] : 'Unknown',
      fatalities: accident.Fatalities ? accident.Fatalities.toString() : '0',
      cause: accident.Nature || 'Unknown cause',
      operator: accident['Owner/operator'] || 'Unknown',
      type: accident.Type || 'Unknown',
      sourceUrl: accident.DetailURL || '', 
      // 添加原始数据用于匹配
      originalData: accident
    }))
  }

  // 获取航空事故数据
  const fetchAccidentData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      console.log(' 开始获取数据...')
      
      const [accidentsResponse, recentResponse, statsResponse] = await Promise.all([
        fetch(`${API_BASE_URL}/accidents`),
        fetch(`${API_BASE_URL}/recent-accidents`),
        fetch(`${API_BASE_URL}/statistics`)
      ])
      
      if (!accidentsResponse.ok) {
        throw new Error(`事故数据请求失败: ${accidentsResponse.status}`)
      }
      if (!recentResponse.ok) {
        throw new Error(`最近事故请求失败: ${recentResponse.status}`)
      }
      if (!statsResponse.ok) {
        throw new Error(`统计数据请求失败: ${statsResponse.status}`)
      }
      
      const accidentsData = await accidentsResponse.json()
      const recentData = await recentResponse.json()
      const statsData = await statsResponse.json()
      
      console.log(' 原始数据获取成功:', {
        accidents: accidentsData.length,
        recent: recentData.length,
        stats: statsData
      })
      
      // 转换数据格式
      const formattedRoutes = transformAccidentData(accidentsData, 0)
      const formattedRecent = transformRecentData(recentData)
      
      console.log(' 数据转换完成:', {
        routes: formattedRoutes.length,
        recent: formattedRecent.length
      })
      
      setFlightRoutes(formattedRoutes)
      setRecentIncidents(formattedRecent)
      setStatistics(statsData)
      
    } catch (err) {
      console.error('! 获取数据失败:', err)
      setError(`! 数据加载失败: ${err.message}`)
      
      // 如果API失败，使用空数据
      setFlightRoutes([])
      setRecentIncidents([])
      setStatistics(null)
    } finally {
      setLoading(false)
    }
  }
  useEffect(() => {
    fetchAccidentData()
  }, [])

  // 处理航班选择
  const handleFlightSelect = (flight) => {
    if (selectedFlight && selectedFlight.id === flight.id) {
      setSelectedFlight(null)
    } else {
      setSelectedFlight(flight)
    }
  }

  // 大圆航线路径生成
  const generateGreatCircleRoutes = (start, end) => {
    const routes = [];
    const steps = 60;
    
    // 计算最短路径的经度差
    let deltaLng = end.lng - start.lng;
    if (deltaLng > 180) deltaLng -= 360;
    if (deltaLng < -180) deltaLng += 360;
    
    if (Math.abs(deltaLng) > 180) {
      return routes; // 返回空数组，不显示这条航线
    }
    
    const deltaLat = end.lat - start.lat;
    const distance = Math.sqrt(deltaLat * deltaLat + deltaLng * deltaLng);
    
    // 生成弧线路径
    const points = [];
    const curvatureHeight = Math.min(distance * 0.12, 10);
    const curveDirection = (start.lat + end.lat) / 2 > 0 ? 1 : -1;
    
    for (let i = 0; i <= steps; i++) {
      const t = i / steps;
      
      const baseLat = start.lat + (deltaLat * t);
      const baseLng = start.lng + (deltaLng * t);
      
      // 添加弧度
      const curvature = Math.sin(t * Math.PI) * curvatureHeight * curveDirection;
      const curvedLat = Math.max(-85, Math.min(85, baseLat + curvature));
      
      points.push([curvedLat, baseLng]);
    }
    
    // 创建世界副本
    routes.push(points); // 主路径
    routes.push(points.map(([lat, lng]) => [lat, lng - 360])); // 左副本
    routes.push(points.map(([lat, lng]) => [lat, lng + 360])); // 右副本
    
    return routes;
  };
  
  // 缓存已经渲染的航线
  /* 
  const visibleFlights = showSearchResults ? searchResults : flightRoutes;

  const polylines = useMemo(() => {
    return visibleFlights.map(flight => {
      const routeVariants = flight.origin && flight.destination
        ? generateGreatCircleRoutes(flight.origin, flight.destination)
        : [];
      const isSelected = selectedFlight?.id === flight.id;
      return routeVariants.map((routePoints, variantIndex) => ({
        key: `${flight.id}-${variantIndex}`,
        routePoints,
        isSelected,
        flight,
        variantIndex
      }));
    }).flat();
  }, [visibleFlights, selectedFlight]);
*/
  // 辅助函数：生成直线路径（备用）
  const generateStraightRoute = (start, end) => {
    const steps = 60;
    const routes = [];
    const points = [];
    
    for (let i = 0; i <= steps; i++) {
      const t = i / steps;
      const lat = start.lat + (end.lat - start.lat) * t;
      const lng = start.lng + (end.lng - start.lng) * t;
      points.push([lat, lng]);
    }
    
    routes.push(points);
    routes.push(points.map(([lat, lng]) => [lat, lng - 360]));
    routes.push(points.map(([lat, lng]) => [lat, lng + 360]));
    
    return routes;
  };

  // 创建始末点图标
  const createOriginIcon = () => {
    return new L.Icon({
      iconUrl: 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(`
        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24">
          <circle cx="12" cy="12" r="8" fill="#ffd700" stroke="#333" stroke-width="2"/>
        </svg>
      `),
      iconSize: [14, 14],
      iconAnchor: [7, 7],
      popupAnchor: [0, -7]
    });
  };
  const createDestinationIcon = () => {
    return new L.Icon({
      iconUrl: 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(`
        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24">
          <circle cx="12" cy="12" r="8" fill="#ff9c6bff" stroke="#333" stroke-width="2"/>
        </svg>
      `),
      iconSize: [14, 14],
      iconAnchor: [7, 7],
      popupAnchor: [0, -7]
    });
  };
  const originIcon = createOriginIcon();
  const destinationIcon = createDestinationIcon();

  useEffect(() => {
    setTimeout(() => {
      setMapLoaded(true);
    }, 1000);
  }, []);

  // 监听isFiltersOpen变化，强制地图重新计算大小
  useEffect(() => {
    const timer = setTimeout(() => {
      window.dispatchEvent(new Event('resize'));
    }, 350); 
    
    return () => clearTimeout(timer);
  }, [isFiltersOpen]);

  return (
    <div style={{ 
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: '#000',
    }}>
      {/* 地图容器 */}
      <div style={{ 
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0
      }}>
        {mapLoaded && (
          <MapContainer
            center={[30, 0]}
            zoom={3}
            style={{ 
              width: '100%', 
              height: '100%' 
            }}
            minZoom={2}
            maxZoom={10}
            zoomControl={false}
            worldCopyJump={true}
            maxBounds={[[-85, -Infinity], [85, Infinity]]}
            maxBoundsViscosity={1.0}
          >
            {/* 使用深色地图瓦片 */}
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
              noWrap={false}
              bounds={[[-85, -Infinity], [85, Infinity]]}
            />

            {/* 绘制航线和起终点 */}
            {(showSearchResults ? searchResults : flightRoutes).map(flight => {
              const routeVariants = flight.origin && flight.destination ? 
                generateGreatCircleRoutes(flight.origin, flight.destination) : [];
              const isSelected = selectedFlight?.id === flight.id;
              
              return (
                <React.Fragment key={flight.id}>
                  {/* 航线创建 */}
                  {routeVariants.map((routePoints, variantIndex) => (
                    <React.Fragment key={`${flight.id}-${variantIndex}`}>
                      {/* 隐形的粗线条用于点击检测 */}
                      <Polyline
                        key={`click-${flight.id}-${variantIndex}`}
                        positions={routePoints}
                        pathOptions={{
                          color: "transparent",
                          weight: 15,
                          opacity: 0,
                          interactive: true
                        }}
                        eventHandlers={{
                          click: (e) => {
                            console.log('点击航线:', flight.flightNumber);
                            handleFlightSelect(flight);
                            e.originalEvent.stopPropagation();
                          },
                          mouseover: (e) => {
                            e.target.setStyle({ 
                              color: isSelected ? "#ff6b6b" : "#0084ff",
                              opacity: 0.3,
                              weight: 15
                            });
                            document.body.style.cursor = 'pointer';
                          },
                          mouseout: (e) => {
                            e.target.setStyle({ 
                              color: "transparent",
                              opacity: 0,
                              weight: 15
                            });
                            document.body.style.cursor = 'default';
                          }
                        }}
                      />

                      {/* 可见的航线 */}
                      <Polyline
                        key={`visible-${flight.id}-${variantIndex}`}
                        positions={routePoints}
                        pathOptions={{
                          color: isSelected ? "#0084ff" : "#ecececff",
                          weight: isSelected ? 3 : 2,
                          opacity: isSelected ? 0.8 : 0.5,
                          interactive: false
                        }}
                      />
                    </React.Fragment>
                  ))}
                  
                  {/* 起点标记 */}
                  {isSelected && [-360, 0, 360].map(lngOffset => (
                    <Marker 
                      key={`origin-${flight.id}-${lngOffset}`}
                      position={[flight.origin.lat, flight.origin.lng + lngOffset]}
                      icon={originIcon}
                      eventHandlers={{
                        click: (e) => {
                          console.log('点击起点标记:', flight.flightNumber);
                          handleFlightSelect(flight);
                        }
                      }}
                    >
                      <Popup>
                        <div style={{ minWidth: '200px' }}>
                          <h4 style={{ margin: '0 0 10px 0', color: '#0084ff' }}>
                            {flight.flightNumber} - Origin
                          </h4>
                          <p><strong>From:</strong> {flight.from}</p>
                          <p><strong>To:</strong> {flight.to}</p>
                          <p><strong>Date:</strong> {flight.date}</p>
                          <p><strong>Fatalities:</strong> {flight.fatalities}</p>
                          <p><strong>Cause:</strong> {flight.cause}</p>
                        </div>
                      </Popup>
                    </Marker>
                  ))}

                  {/* 终点标记*/}
                  {isSelected && [-360, 0, 360].map(lngOffset => (
                    <Marker 
                      key={`destination-${flight.id}-${lngOffset}`}
                      position={[flight.destination.lat, flight.destination.lng + lngOffset]}
                      icon={destinationIcon}
                      eventHandlers={{
                        click: (e) => {
                          console.log('点击终点标记:', flight.flightNumber);
                          handleFlightSelect(flight);
                        }
                      }}
                    >
                      <Popup>
                        <div style={{ minWidth: '200px' }}>
                          <h4 style={{ margin: '0 0 10px 0', color: '#0084ff' }}>
                            {flight.flightNumber} - Destination
                          </h4>
                          <p><strong>From:</strong> {flight.from}</p>
                          <p><strong>To:</strong> {flight.to}</p>
                          <p><strong>Date:</strong> {flight.date}</p>
                          <p><strong>Fatalities:</strong> {flight.fatalities}</p>
                          <p><strong>Cause:</strong> {flight.cause}</p>
                        </div>
                      </Popup>
                    </Marker>
                  ))}
                </React.Fragment>
              );
            })}
          </MapContainer>
        )}
      </div>

      {/* 搜索栏 */}
      <div style={{
        position: 'absolute',
        top: '20px',
        left: '50%',
        transform: `translateX(${isFiltersOpen ? '-28%' : '-50%'})`, 
        zIndex: 1000,
        transition: 'transform 0.3s ease',
        height: '48px'
      }}>
        <div style={{
          background: 'white',
          borderRadius: '25px',
          padding: '12px 24px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
          display: 'flex',
          alignItems: 'center',
          minWidth: '450px',
          height: '48px',
          boxSizing: 'border-box'
        }}>
          <span style={{ marginRight: '12px', fontSize: '16px', color: '#999' }}>🔍</span>
          <input 
            type="text" 
            placeholder="Search flights, airports, operators, narrative..."
            value={mapSearchQuery}
            onChange={handleSearchInputChange}
            style={{
              border: 'none',
              outline: 'none',
              flex: 1,
              fontSize: '14px',
              background: 'transparent',
              color: '#333',
              height: '100%'
            }}
          />
          {isSearching && (
            <div style={{ marginLeft: '8px', color: '#0084ff' }}>
              ⏳
            </div>
          )}
          {(mapSearchQuery  || showSearchResults) && (
            <button
              onClick={clearSearchAndFilters}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#999',
                cursor: 'pointer',
                marginLeft: '8px',
                fontSize: '18px'
              }}
            >
              ×
            </button>
          )}
        </div>

        {showSearchResults && (
          <div style={{
            marginTop: '8px',
            textAlign: 'center',
            background: 'rgba(0, 132, 255, 0.9)',
            color: 'white',
            padding: '4px 12px',
            borderRadius: '15px',
            fontSize: '12px'
          }}>
            <div>
              📊 Showing {searchResults.length}
              {searchPagination && searchPagination.totalRecords > searchResults.length && (
                <span> of {searchPagination.totalRecords.toLocaleString()}</span>
              )} results
            </div>
            {searchPagination && searchPagination.hasNextPage && (
              <button
                onClick={loadMoreResults}
                disabled={isLoadingMore}
                style={{
                  background: 'rgba(255, 255, 255, 0.2)',
                  border: '1px solid rgba(255, 255, 255, 0.3)',
                  color: 'white',
                  padding: '2px 8px',
                  borderRadius: '8px',
                  fontSize: '10px',
                  cursor: isLoadingMore ? 'not-allowed' : 'pointer',
                  marginTop: '4px',
                  transition: 'background 0.2s ease'
                }}
                onMouseEnter={(e) => {
                  if (!isLoadingMore) {
                    e.target.style.background = 'rgba(255, 255, 255, 0.3)'
                  }
                }}
                onMouseLeave={(e) => {
                  e.target.style.background = 'rgba(255, 255, 255, 0.2)'
                }}
              >
                Load More ({searchPagination.totalRecords - searchResults.length} remaining)
              </button>
            )}

          {isLoadingMore && (
            <div style={{
              marginTop: '6px',
              fontSize: '10px',
              color: '#ffd700'
            }}>
              ⏳ Loading more results...
            </div>
          )}            
          
          {filters && Object.values(filters).some(v => v !== 'all' && v !== '') && (
            <div style={{ 
              fontSize: '10px',
              opacity: 0.8,
              marginTop: '2px'
            }}>
              (filtered)
            </div>
          )}
          </div>
        )}
      </div>

      {/* 左上角Most Recent Accidents悬浮下拉面板 */}
      <div style={{
        position: 'absolute',
        top: '20px',
        left: '20px',
        zIndex: 1000
      }}>
        <div style={{
          width: '420px', 
          background: 'rgba(26, 26, 26, 0.95)',
          color: 'white',
          borderRadius: '8px',
          boxShadow: '0 4px 20px rgba(0,0,0,0.5)',
          border: '1px solid #333',
          backdropFilter: 'blur(10px)',
          overflow: 'hidden'
        }}>
          <div 
            onClick={() => {
              setShowRecentAccidents(!showRecentAccidents);
              if (!showRecentAccidents) setShowUnmapped(false);
            }}
            style={{
              padding: '18px 20px', 
              background: '#2c2c2c',
              borderBottom: showRecentAccidents ? '1px solid #333' : 'none',
              cursor: 'pointer',
              transition: 'all 0.2s ease'
            }}
            onMouseEnter={(e) => {
              e.target.style.background = '#333';
            }}
            onMouseLeave={(e) => {
              e.target.style.background = '#2c2c2c';
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{ fontSize: '18px' }}>📋</span> 
                <h3 style={{ 
                  margin: 0, 
                  color: '#ffd700',
                  fontSize: '18px', 
                  fontWeight: 'bold'
                }}>
                  Most Recent Accidents
                </h3>
                <div style={{
                  background: '#ffd700',
                  color: '#1a1a1a',
                  fontSize: '11px', 
                  padding: '3px 7px', 
                  borderRadius: '3px',
                  fontWeight: 'bold',
                  letterSpacing: '0.5px'
                }}>
                  DATA
                </div>
              </div>
              <div style={{ 
                fontSize: '18px', 
                color: '#999',
                transform: showRecentAccidents ? 'rotate(180deg)' : 'rotate(0deg)',
                transition: 'transform 0.2s ease'
              }}>
                ▼
              </div>
            </div>
          </div>
          
          <div style={{
            maxHeight: showRecentAccidents ? '650px' : '0', 
            overflow: 'hidden',
            transition: 'max-height 0.3s ease'
          }}>
            <div style={{ 
              maxHeight: '520px', 
              overflow: 'auto'
            }}>
              {recentIncidents.map((item, index) => (
                <div key={index} style={{
                  padding: '16px 20px', 
                  borderBottom: index < recentIncidents.length - 1 ? '1px solid #333' : 'none',
                  fontSize: '15px', 
                  background: index < 3 ? '#2a2a2a' : 'transparent',
                  cursor: 'pointer',
                  transition: 'background 0.2s ease'
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = '#333'}
                onMouseLeave={(e) => e.currentTarget.style.background = index < 3 ? '#2a2a2a' : 'transparent'}
                onClick={() => {
                  // 先尝试通过Registration匹配
                  let flight = flightRoutes.find(f => f.flightNumber === item.flight);
                  
                  // 如果没找到，通过日期+机场匹配
                  if (!flight && item.originalData) {
                    const originalData = item.originalData;
                    flight = flightRoutes.find(f => 
                      f.date === (originalData.Date ? new Date(originalData.Date).toISOString().split('T')[0] : 'Unknown') &&
                      f.from === (originalData['Departure airport'] || 'Unknown') &&
                      f.to === (originalData['Destination airport'] || 'Unknown')
                    );
                  }
                  
                  // 如果还是没找到，尝试通过操作员+飞机类型匹配
                  if (!flight && item.originalData) {
                    const originalData = item.originalData;
                    flight = flightRoutes.find(f => 
                      f.operator === (originalData['Owner/operator'] || 'Unknown') &&
                      f.aircraftType === (originalData.Type || 'Unknown') &&
                      f.fatalities === (originalData.Fatalities ? originalData.Fatalities.toString() : '0')
                    );
                  }
                  
                  // 如果找到匹配的航班，选中它
                  if (flight) {
                    console.log(' 找到匹配航班:', flight);
                    handleFlightSelect(flight);
                  } else {
                    // 如果没有找到对应的航班路线，创建一个临时的详情对象
                    console.log('! 未找到对应航班路线，创建临时详情');
                    const originalData = item.originalData;
                    const tempFlight = {
                      id: `temp-${Date.now()}`,
                      flightNumber: item.flight,
                      from: originalData['Departure airport'] || 'Unknown',
                      to: originalData['Destination airport'] || 'Unknown',
                      fromCode: originalData.dep_IATA || originalData.dep_ICAO || '',
                      toCode: originalData.arr_IATA || originalData.arr_ICAO || '',
                      status: 'accident',
                      date: originalData.Date ? new Date(originalData.Date).toISOString().split('T')[0] : 'Unknown',
                      location: originalData.Location || 'Unknown',
                      fatalities: originalData.Fatalities ? originalData.Fatalities.toString() : '0',
                      otherFatalities: originalData['Other fatalities'] ? originalData['Other fatalities'].toString() : '0',
                      occupants: originalData.Occupants ? originalData.Occupants.toString() : 'Unknown',
                      cause: originalData.Nature || 'Unknown cause',
                      phase: originalData.Phase || 'Unknown',
                      operator: originalData['Owner/operator'] || 'Unknown',
                      aircraftType: originalData.Type || 'Unknown',
                      damage: originalData['Aircraft damage'] || 'Unknown',
                      category: originalData.Category || 'Unknown',
                      narrative: originalData.Narrative || 'No route data available - accident location coordinates not found in database.',
                      sourceUrl: originalData.DetailURL || item.sourceUrl ||'',
                      // 没有坐标数据
                      origin: null,
                      destination: null
                    };
                    console.log(' 临时对象创建:', {
                      flightNumber: tempFlight.flightNumber,
                      sourceUrl: tempFlight.sourceUrl,
                      hasSourceUrl: !!tempFlight.sourceUrl,
                      from: tempFlight.from,
                      to: tempFlight.to
                    });

                    handleFlightSelect(tempFlight);
                  }
                }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
                    <span style={{ color: '#999', width: '22px', fontSize: '14px', fontWeight: 'bold' }}>{item.num}</span> 
                    <span style={{ color: '#0084ff', fontWeight: '700', marginRight: '10px', fontSize: '16px' }}> 
                      {item.flight}
                    </span>
                    <span style={{ color: '#999', fontSize: '12px', marginRight: '10px' }}> 
                      {item.code}
                    </span>
                    <span style={{ 
                      color: '#ffd700', 
                      marginLeft: 'auto', 
                      fontWeight: '700',
                      fontSize: '14px' 
                    }}>
                      {item.fatalities}
                    </span>
                  </div>
                  <div style={{ 
                    color: '#ccc', 
                    fontSize: '13px', 
                    paddingLeft: '22px',
                    marginBottom: '6px',
                    fontWeight: '500'
                  }}>
                    {item.route}
                  </div>
                  <div style={{ 
                    color: '#999', 
                    fontSize: '11px', 
                    paddingLeft: '22px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}>
                    <span style={{ fontWeight: '500' }}>{item.date}</span>
                    <span style={{ color: '#ccc', fontWeight: '500' }}>{item.cause}</span>
                  </div>
                </div>
              ))}
            </div>

            <div style={{
              padding: '20px 20px', 
              background: '#2c2c2c',
              borderTop: '1px solid #333'
            }}>
              <div style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '15px',
                fontSize: '13px' 
              }}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ color: '#ffd700', fontWeight: 'bold', fontSize: '20px' }}> 
                    {recentIncidents.length}
                  </div>
                  <div style={{ color: '#999', marginTop: '5px', fontSize: '12px' }}>Recent Accidents</div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ color: '#0084ff', fontWeight: 'bold', fontSize: '20px' }}> 
                    {recentIncidents.reduce((sum, item) => sum + parseInt(item.fatalities), 0)}
                  </div>
                  <div style={{ color: '#999', marginTop: '5px', fontSize: '12px' }}>Total Fatalities</div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        {/* 未在图上可视化航班列表（经纬度缺失） */}
        <div style={{
          width: '420px', 
          background: 'rgba(26, 26, 26, 0.95)',
          color: 'white',
          borderRadius: '8px',
          boxShadow: '0 4px 20px rgba(0,0,0,0.5)',
          border: '1px solid #333',
          backdropFilter: 'blur(10px)',
          overflow: 'hidden',
          marginTop: '16px'
        }}>
          <div 
            onClick={() => {
              setShowUnmapped(!showUnmapped);
              if (!showUnmapped) setShowRecentAccidents(false);
            }}
            style={{
              padding: '16px 20px', 
              background: '#2c2c2c',
              borderBottom: showUnmapped ? '1px solid #333' : 'none',
              cursor: 'pointer',
              transition: 'all 0.2s ease'
            }}
            onMouseEnter={e => e.target.style.background = '#333'}
            onMouseLeave={e => e.target.style.background = '#2c2c2c'}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontSize: '18px' }}>🗂️</span>
              <h3 style={{ margin: 0, color: '#ffd700', fontSize: '18px', fontWeight: 'bold' }}>
                 Unmapped Accidents
              </h3>
              <div style={{
                background: '#ffd700',
                color: '#1a1a1a',
                fontSize: '11px',
                padding: '2px 7px',
                borderRadius: '3px',
                fontWeight: 'bold',
                letterSpacing: '0.5px'
              }}>
                NO ROUTE
              </div>
              <div style={{ 
                fontSize: '18px',
                color: '#999',
                marginLeft: 'auto',
                transform: showUnmapped ? 'rotate(180deg)' : 'rotate(0deg)',
                transition: 'transform 0.2s ease'
              }}>
                ▼
              </div>
            </div>
          </div>
          <div style={{
            maxHeight: showUnmapped ? '650px' : '0', 
            overflow: 'hidden',
            transition: 'max-height 0.3s ease'
          }}>
            <div style={{ maxHeight: '520px', overflow: 'auto' }}>
              {unmappedAccidents.map((item, idx) => (
                <div key={idx} style={{
                  padding: '14px 20px',
                  borderBottom: idx < unmappedAccidents.length - 1 ? '1px solid #333' : 'none',
                  fontSize: '14px',
                  background: idx < 3 ? '#2a2a2a' : 'transparent'
                }}
                onClick={() => {
                  const tempFlight = {
                    id: `unmapped-${idx}`,
                    flightNumber: item.Registration || 'Unknown',
                    from: item['Departure airport'] || 'Unknown',
                    to: item['Destination airport'] || 'Unknown',
                    fromCode: item.dep_IATA || item.dep_ICAO || '',
                    toCode: item.arr_IATA || item.arr_ICAO || '',
                    status: 'accident',
                    date: item.Date ? new Date(item.Date).toISOString().split('T')[0] : 'Unknown',
                    location: item.Location || 'Unknown',
                    fatalities: item.Fatalities ? item.Fatalities.toString() : '0',
                    otherFatalities: item['Other fatalities'] ? item['Other fatalities'].toString() : '0',
                    occupants: item.Occupants ? item.Occupants.toString() : 'Unknown',
                    cause: item.Nature || 'Unknown cause',
                    phase: item.Phase || 'Unknown',
                    operator: item['Owner/operator'] || 'Unknown',
                    aircraftType: item.Type || 'Unknown',
                    damage: item['Aircraft damage'] || 'Unknown',
                    category: item.Category || 'Unknown',
                    narrative: item.Narrative || 'No route data available - accident location coordinates not found in database.',
                    sourceUrl: item.DetailURL || '',
                    origin: null,
                    destination: null
                  };
                  handleFlightSelect(tempFlight);
                }}
                onMouseEnter={e => e.currentTarget.style.background = '#333'}
                onMouseLeave={e => e.currentTarget.style.background = idx < 3 ? '#2a2a2a' : 'transparent'}
               >
                  <div style={{ display: 'flex', alignItems: 'center', marginBottom: '6px' }}>
                    <span style={{ color: '#999', width: '22px', fontSize: '13px', fontWeight: 'bold' }}>{idx + 1}.</span>
                    <span style={{ color: '#0084ff', fontWeight: '700', marginRight: '10px', fontSize: '15px' }}>
                      {item.Registration || 'Unknown'}
                    </span>
                    <span style={{ color: '#999', fontSize: '12px', marginRight: '10px' }}>
                      {item.Type || item.aircraftType || 'Unknown Type'}
                    </span>
                    <span style={{ color: '#ffd700', marginLeft: 'auto', fontWeight: '700', fontSize: '13px' }}>
                      {item.Fatalities}
                    </span>
                  </div>
                  <div style={{ color: '#ccc', fontSize: '12px', paddingLeft: '22px', marginBottom: '4px' }}>
                    {(item['Departure airport'] || 'Unknown') + ' → ' + (item['Destination airport'] || 'Unknown')}
                  </div>
                  <div style={{ color: '#999', fontSize: '11px', paddingLeft: '22px', display: 'flex', justifyContent: 'space-between' }}>
                    <span>{item.Date ? new Date(item.Date).toISOString().split('T')[0] : 'Unknown'}</span>
                    <span>{item.Nature || 'Unknown cause'}</span>
                  </div>
                  {item.Narrative && (
                    <div style={{
                      color: '#aaa',
                      fontSize: '11px',
                      marginTop: '6px',
                      paddingLeft: '22px'
                    }}>
                      {item.Narrative.length > 120 ? item.Narrative.slice(0, 120) + '...' : item.Narrative}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

      </div>
      

      {/* 选中航班详情信息面板 */}
      {selectedFlight && (
        <div style={{
          position: 'absolute',
          top: (showRecentAccidents || showUnmapped) ? '100px' : '180px',
          left: (showRecentAccidents || showUnmapped) ? '460px' : '20px',
          width: '350px',
          background: 'rgba(26, 26, 26, 0.95)',
          color: 'white',
          padding: '20px',
          borderRadius: '8px',
          zIndex: 1000,
          boxShadow: '0 4px 20px rgba(0,0,0,0.5)',
          border: '1px solid #333',
          backdropFilter: 'blur(10px)',
          transition: 'left 0.3s ease',
          maxHeight: '85vh',
          overflow: 'auto'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
            <h3 style={{ 
              margin: 0, 
              color: '#0084ff',
              fontSize: '20px',
              fontWeight: 'bold'
            }}>
              {selectedFlight.flightNumber}
              {!selectedFlight.origin && (
                <span style={{ 
                  fontSize: '12px', 
                  color: '#ffd700', 
                  marginLeft: '8px',
                  padding: '2px 6px',
                  background: 'rgba(255, 215, 0, 0.2)',
                  borderRadius: '3px'
                }}>
                  NO ROUTE
                </span>
              )}
            </h3>
            <button 
              onClick={() => setSelectedFlight(null)}
              style={{
                background: 'transparent',
                color: '#999',
                border: 'none',
                fontSize: '20px',
                cursor: 'pointer',
                padding: '0'
              }}
            >
              ×
            </button>
          </div>

          {!selectedFlight.origin && (
            <div style={{
              background: 'rgba(255, 215, 0, 0.1)',
              border: '1px solid rgba(255, 215, 0, 0.3)',
              borderRadius: '4px',
              padding: '10px',
              marginBottom: '15px',
              fontSize: '12px',
              color: '#ffd700'
            }}>
              ⚠️ Route visualization not available - missing coordinate data for departure/destination airports.
            </div>
          )}
    
          <div style={{ fontSize: '14px', lineHeight: '1.6' }}>
            <div style={{ marginBottom: '12px' }}>
              <strong style={{ color: '#ffd700' }}>Route:</strong> 
              <span style={{ marginLeft: '8px', color: '#fff' }}>{selectedFlight.from} → {selectedFlight.to}</span>
            </div>
            <div style={{ marginBottom: '12px' }}>
              <strong style={{ color: '#ffd700' }}>Date:</strong> 
              <span style={{ marginLeft: '8px', color: '#fff' }}>{selectedFlight.date}</span>
            </div>
            <div style={{ marginBottom: '12px' }}>
              <strong style={{ color: '#ffd700' }}>Fatalities:</strong> 
              <span style={{ marginLeft: '8px', color: '#fff' }}>{selectedFlight.fatalities}</span>
            </div>
            <div style={{ marginBottom: '12px' }}>
              <strong style={{ color: '#ffd700' }}>Aircraft Type:</strong> 
              <span style={{ marginLeft: '8px', color: '#fff' }}>{selectedFlight.aircraftType}</span>
            </div>
            <div style={{ marginBottom: '12px' }}>
              <strong style={{ color: '#ffd700' }}>Operator:</strong> 
              <span style={{ marginLeft: '8px', color: '#fff' }}>{selectedFlight.operator}</span>
            </div>
            <div style={{ marginBottom: '12px' }}>
              <strong style={{ color: '#ffd700' }}>Location:</strong> 
              <span style={{ marginLeft: '8px', color: '#fff' }}>{selectedFlight.location}</span>
            </div>

            {selectedFlight.narrative && selectedFlight.narrative.trim() !== '' && (
              <div style={{ marginBottom: '12px' }}>
                <strong style={{ color: '#ffd700' }}>Narrative:</strong>
                <div style={{ 
                  marginTop: '6px',
                  padding: '10px',
                  background: 'rgba(255, 255, 255, 0.05)',
                  borderRadius: '4px',
                  fontSize: '13px',
                  lineHeight: '1.5',
                  color: '#ccc',
                  maxHeight: '140px',
                  overflow: 'auto'
                }}>
                  {selectedFlight.narrative}
                </div>
              </div>
            )}

            <div style={{ 
              marginTop: '15px',
              paddingTop: '10px',
              borderTop: '1px solid #333'
            }}>
              <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center',
                fontSize: '12px'
              }}>

                {/* 原始 URL */}
                {selectedFlight.sourceUrl && selectedFlight.sourceUrl.trim() !== '' && (
                  <a 
                    href={selectedFlight.sourceUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{
                      color: '#0084ff',
                      textDecoration: 'none',
                      fontSize: '12px',
                      padding: '4px 8px',
                      border: '1px solid #0084ff',
                      borderRadius: '4px',
                      transition: 'all 0.2s ease'
                    }}
                    onMouseEnter={(e) => {
                      e.target.style.background = '#0084ff';
                      e.target.style.color = 'white';
                    }}
                    onMouseLeave={(e) => {
                      e.target.style.background = 'transparent';
                      e.target.style.color = '#0084ff';
                    }}
                  >
                    📄 Detailed Report
                  </a>
                )}
              </div>
            </div>

          </div>
        </div>
      )}

      {/* 加载状态 */}
      {!mapLoaded && (
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: '#000',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 2000
        }}>
          <div style={{ textAlign: 'center', color: 'white' }}>
            <div style={{ 
              fontSize: '48px', 
              marginBottom: '20px',
              color: '#0084ff'
            }}>
              ✈️
            </div>
            <div style={{ 
              fontSize: '18px', 
              marginBottom: '10px',
              color: '#0084ff',
              fontWeight: 'bold'
            }}>
              {loading ? 'Loading Real Aviation Data...' : 'Loading Aviation Accidents Map...'}
            </div>
            <div style={{ 
              fontSize: '14px', 
              color: '#999'
            }}>
              {loading ? 'Connecting to PostGIS database...' : 'Initializing map visualization...'}
            </div>
            {statistics && (
              <div style={{ 
                fontSize: '12px', 
                color: '#666',
                marginTop: '8px'
              }}>
                Found {statistics.totalAccidents} total accidents in database
              </div>
            )}
          </div>
        </div>
      )}
      {error && (
        <div style={{
          position: 'absolute',
          top: '80px',
          right: '20px',
          background: 'rgba(220, 53, 69, 0.9)',
          color: 'white',
          padding: '12px 16px',
          borderRadius: '8px',
          zIndex: 2000,
          maxWidth: '300px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <strong>⚠️ 数据库连接失败</strong>
            <button 
              onClick={fetchAccidentData}
              style={{
                background: 'rgba(255,255,255,0.2)',
                border: 'none',
                color: 'white',
                padding: '4px 8px',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '11px'
              }}
            >
              重试
            </button>
          </div>
          <div style={{ fontSize: '11px', marginTop: '4px', opacity: 0.9 }}>
            {error}
          </div>
        </div>
      )}

  {/* 在左下角添加数据库连接状态*/}
  {statistics && (
    <div style={{
      position: 'absolute',
      bottom: '20px',
      left: '20px',
      background: 'rgba(0, 132, 255, 0.9)',
      color: 'white',
      padding: '8px 12px',
      borderRadius: '6px',
      fontSize: '12px',
      zIndex: 1000
    }}>
      📊 PostGIS Connected 
    </div>
  )}
      
    </div>
  )
}

export default MapView