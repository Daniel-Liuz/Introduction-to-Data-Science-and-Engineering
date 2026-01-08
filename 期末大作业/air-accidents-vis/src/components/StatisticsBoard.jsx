import React, { useEffect, useState } from 'react'
import ReactECharts from 'echarts-for-react'

function StatisticsBoard({onClose}) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [countryStats, setCountryStats] = useState([]);
  const [ageStats, setAgeStats] = useState([]);
  const [monthlyStats, setMonthlyStats] = useState([]);
  const [manufacturerStats, setManufacturerStats] = useState([]);
  const [manufacturerFatalityStats, setManufacturerFatalityStats] = useState([]);

  useEffect(() => {
    fetch('/api/statistics')
      .then(res => res.json())
      .then(data => {
        setStats(data)
        setLoading(false)
      })
      .catch(err => {
        setError('加载统计数据失败')
        setLoading(false)
      })

    fetch('/api/age-accident-stats')
      .then(res => res.json())
      .then(data => setAgeStats(data || []))
      .catch(err => {
        setError('加载机龄数据失败')
      });

    fetch('/api/monthly-accidents')
      .then(res => res.json())
      .then(data => setMonthlyStats(data || []));

    fetch('/api/country-accident-stats')
      .then(res => res.json())
      .then(data => setCountryStats(data || []));

    fetch('/api/manufacturer-accident-stats')
      .then(res => res.json())
      .then(data => setManufacturerStats(data || []));

    fetch('/api/manufacturer-fatality-stats')
      .then(res => res.json())
      .then(data => setManufacturerFatalityStats(data || []));
  }, [])

  if (loading) return (
    <div style={{ 
      color: '#999', 
      padding: 30,
      minHeight: '92vh',
      maxHeight: '92vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }}>
      Loading...
    </div>
  )
  if (error) return <div style={{ color: 'red', padding: 30 }}>{error}</div>
  if (!stats) return null

  const maxYearCount = Math.max(...stats.yearlyStats.map(y => y.count))

  return (
    <div style={{
      //background: '#1a1a1a',
      color: 'white',
      //borderRadius: '8px',
      //boxShadow: '0 4px 20px rgba(0,0,0,0.5)',
      //border: '1px solid #333',
      padding: '0 24px 24px 24px',
      fontFamily: '-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif'
    }}>
      <div
        style={{
          position: 'sticky',
          top: 0,
          zIndex: 10,
          background: '#1a1a1a',
          display: 'flex',
          alignItems: 'center',
          gap: 10
          //paddingBottom: 10,
          //marginBottom: 18
        }}
      >
        <span style={{ fontSize: 18 }}>📊</span>
        <span style={{
          color: '#ffd700',
          fontSize: 18,
          fontWeight: 'bold',
          letterSpacing: '0.5px'
        }}>
          Dashboard
        </span>
        <div style={{
          background: '#ffd700',
          color: '#1a1a1a',
          fontSize: 11,
          padding: '3px 7px',
          borderRadius: 3,
          fontWeight: 'bold',
          letterSpacing: '0.5px',
          marginLeft: 8
        }}>
          DATA
        </div>
        <button
          onClick={onClose}
          style={{
            fontSize: 22,
            color: '#ffd700',
            marginLeft: 'auto',
            background: 'none',
            border: 'none',
            cursor: 'pointer'
          }}
          title="Fold"
        >▼</button>
      </div>

      {/* KPI Cards */}
      <div style={{ display: 'flex', gap: 18, marginBottom: 28, marginTop: 12 }}>
        <div style={{
            flex: 1,
            background: '#23272f',
            borderRadius: 8,
            padding: '18px 12px',
            textAlign: 'center',
            border: '1px solid #2a2a2a',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 6
        }}>
            <span style={{ fontSize: 26, marginBottom: 2 }}>✈️</span>
            <div style={{ fontSize: 13, color: '#8ea2c6', marginBottom: 2 }}>Total Accidents</div>
            <div style={{ fontSize: 26, color: '#3fa7ff', fontWeight: 700 }}>{stats.totalAccidents.toLocaleString()}</div>
        </div>
        <div style={{
            flex: 1,
            background: '#23272f',
            borderRadius: 8,
            padding: '18px 12px',
            textAlign: 'center',
            border: '1px solid #2a2a2a',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 6
        }}>
            <span style={{ fontSize: 26, marginBottom: 2 }}>☠️</span>
            <div style={{ fontSize: 13, color: '#8ea2c6', marginBottom: 2 }}>Total Fatalities</div>
            <div style={{ fontSize: 26, color: '#ff6b6b', fontWeight: 700 }}>{stats.totalFatalities.toLocaleString()}</div>
        </div>
        <div style={{
            flex: 1,
            background: '#23272f',
            borderRadius: 8,
            padding: '18px 12px',
            textAlign: 'center',
            border: '1px solid #2a2a2a',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 6
        }}>
            <span style={{ fontSize: 26, marginBottom: 2 }}>🗺️</span>
            <div style={{ fontSize: 13, color: '#8ea2c6', marginBottom: 2 }}>Mapped Accidents</div>
            <div style={{ fontSize: 26, color: '#00c2b2', fontWeight: 700 }}>{stats.mappedAccidents.toLocaleString()}</div>
        </div>
      </div>

      {/* 年度事故趋势柱状图 */}
      <div>
        <div style={{
            background: '#23272f',
            borderRadius: 8,
            padding: '18px 10px',
            marginBottom: 12
        }}>
            <ReactECharts
            style={{ height: 340 }}
            option={{
                title: { text: 'Yearly Accident & Fatality Trend', left: 'center', textStyle: { color: '#d3dcedff', fontSize: 18 } },
                tooltip: { trigger: 'axis' },
                legend: { data: ['Accidents', 'Fatalities'], top: 40, textStyle: { color: '#ccc' } },
                grid: { left: 60, right: 60, bottom: 40, top: 80 },
                xAxis: {
                type: 'category',
                data: stats.yearlyStats.slice().reverse().map(y => y.year),
                axisLabel: { color: '#ccc', fontSize: 13 }
                },
                yAxis: [
                {
                    type: 'value',
                    name: 'Accidents',
                    axisLabel: { color: '#3fa7ff' },
                    splitLine: { lineStyle: { color: '#222' } }
                },
                {
                    type: 'value',
                    name: 'Fatalities',
                    axisLabel: { color: '#ff6b6b' }
                }
                ],
                series: [
                {
                    name: 'Accidents',
                    type: 'bar',
                    data: stats.yearlyStats.slice().reverse().map(y => y.count),
                    itemStyle: {
                    color: {
                        type: 'linear',
                        x: 0, y: 0, x2: 0, y2: 1,
                        colorStops: [
                        { offset: 0, color: '#3fa7ff' },
                        { offset: 1, color: '#8ea2c6' }
                        ]
                    }
                    },
                    barWidth: 64
                },
                {
                    name: 'Fatalities',
                    type: 'line',
                    yAxisIndex: 1,
                    data: stats.yearlyStats.slice().reverse().map(y => y.fatalities || 0),
                    itemStyle: { color: '#ff6b6b' },
                    lineStyle: { width: 3 }
                }
                ]
            }}
            />
        </div>
      </div>
    
      {/* 月度事故总数柱状图 */}
      <div style={{
        background: '#23272f',
        borderRadius: 8,
        padding: 18,
        marginTop: 32
        }}>
        <ReactECharts
            style={{ height: 340 }}
            option={{
            title: { text: 'Monthly Accident & Fatality Total (2020-2024)', left: 'center', textStyle: { color: '#d3dcedff', fontSize: 18 } },
            tooltip: { trigger: 'axis' },
            legend: { data: ['Accidents', 'Fatalities'], top: 40, textStyle: { color: '#ccc' } },
            grid: { left: 60, right: 60, bottom: 40, top: 80 },
            xAxis: {
                type: 'category',
                data: ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],
                axisLabel: { color: '#ccc', fontSize: 13 }
            },
            yAxis: [
                {
                type: 'value',
                name: 'Accidents',
                axisLabel: { color: '#3fa7ff' },
                splitLine: { lineStyle: { color: '#222' } }
                },
                {
                type: 'value',
                name: 'Fatalities',
                axisLabel: { color: '#ff6b6b' }
                }
            ],
            series: [
                {
                name: 'Accidents',
                type: 'bar',
                data: Array.from({length:12}, (_,i) => {
                    const found = (monthlyStats || []).find(m => Number(m.month) === i+1);
                    return found ? Number(found.count) : 0;
                }),
                itemStyle: {
                    color: {
                    type: 'linear',
                    x: 0, y: 0, x2: 0, y2: 1,
                    colorStops: [
                        { offset: 0, color: '#3fa7ff' },
                        { offset: 1, color: '#8ea2c6' }
                    ]
                    }
                },
                barWidth: 32
                },
                {
                name: 'Fatalities',
                type: 'line',
                yAxisIndex: 1,
                data: Array.from({length:12}, (_,i) => {
                    const found = (monthlyStats || []).find(m => Number(m.month) === i+1);
                    return found ? Number(found.fatalities) : 0;
                }),
                itemStyle: { color: '#ff6b6b' },
                lineStyle: { width: 3 }
                }
            ]
            }}
        />
      </div>

      {/* 发生地国家统计条形图 */}
      <ReactECharts
        style={{ height: 730, marginTop: 32 }}
        option={{
          title: { text: 'Top 30 Countries by Accident Count', left: 'center', textStyle: { color: '#d3dcedff', fontSize: 18 } },
          tooltip: { trigger: 'axis' },
          grid: { left: 240, right: 30, bottom: 40, top: 50 },
          xAxis: {
            type: 'log',
            axisLabel: { color: '#ccc' },
            splitLine: { lineStyle: { color: '#222' } }
          },
          yAxis: {
            type: 'category',
            data: (countryStats || []).map(item => item.country),
            axisLabel: {
              color: '#8ea2c6',
              fontSize: 13,
              width: 220,
              overflow: 'break',
              formatter: function(value) {
                return value.length > 30 ? value.replace(/(.{30})/g, '$1\n') : value;
              }
            }
          },
          series: [{
            type: 'bar',
            data: (countryStats || []).map(item => item.count),
            itemStyle: {
              color: {
                type: 'linear',
                x: 1, y: 0, x2: 0, y2: 0,
                colorStops: [
                  { offset: 0, color: '#ffd700' },
                  { offset: 1, color: '#8ea2c6' }
                ]
              }
            },
            barWidth: 18
          }]
        }}
      />

      {/* 事故类型分布饼图 */}
      <div style={{ display: 'flex', gap: 32, marginTop: 32, marginBottom: 8 }}>
        <div style={{ flex: 1, background: '#23272f', borderRadius: 8, padding: 12, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            <ReactECharts
            style={{ height: 420 }}
            option={{
                title: { 
                text: 'Accident Type Distribution', 
                left: 'center', 
                top: 15,
                textStyle: { color: '#d3dcedff', fontSize: 18 } 
                },
                tooltip: { trigger: 'item' },
                legend: { 
                bottom: 8, 
                left: 'center', 
                textStyle: { color: '#ccc', fontSize: 12 } 
                },
                series: [{
                type: 'pie',
                radius: ['38%', '60%'],
                center: ['50%', '50%'],
                data: (stats.typeStats || []).map(item => ({ value: item.count, name: item.type })),
                label: { color: '#ccc', fontSize: 12 }
                }]
            }}
            />
        </div>
        {/* 事故发生阶段饼图 */}
        <div style={{ flex: 1, background: '#23272f', borderRadius: 8, padding: 12, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            <ReactECharts
            style={{ height: 420 }}
            option={{
                title: { 
                text: 'Accident Phase Distribution', 
                left: 'center', 
                top: 15,
                textStyle: { color: '#d3dcedff', fontSize: 18 } 
                },
                tooltip: { trigger: 'item' },
                legend: { 
                bottom: 8, 
                left: 'center', 
                textStyle: { color: '#ccc', fontSize: 12 } 
                },
                series: [{
                type: 'pie',
                radius: ['38%', '60%'],
                center: ['50%', '50%'],
                data: (stats.phaseStats || []).map(item => ({ value: item.count, name: item.phase })),
                label: { color: '#ccc', fontSize: 12 }
                }]
            }}
            />
        </div>
      </div>

      {/* 飞机类型条形图 */}
      <ReactECharts
        style={{ height: 520, marginTop: 32 }}
        option={{
            title: { text: 'Top 20 Aircraft Types by Accident Count', left: 'center', textStyle: { color: '#d3dcedff', fontSize: 18 } },
            tooltip: { trigger: 'axis' },
            grid: { left: 240, right: 30, bottom: 40, top: 50 }, 
            xAxis: {
            type: 'value',
            axisLabel: { color: '#ccc' },
            splitLine: { lineStyle: { color: '#222' } }
            },
            yAxis: {
            type: 'category',
            data: (stats.aircraftTop || []).map(item => item.aircraft),
            axisLabel: { 
                color: '#8ea2c6', 
                fontSize: 13,
                width: 220, 
                overflow: 'break',
                formatter: function(value) {
                return value.length > 28 ? value.replace(/(.{28})/g, '$1\n') : value;
                }
            }
            },
            series: [{
            type: 'bar',
            data: (stats.aircraftTop || []).map(item => item.count),
            itemStyle: {
                color: {
                type: 'linear',
                x: 1, y: 0, x2: 0, y2: 0,
                colorStops: [
                    { offset: 0, color: '#3fa7ff' },
                    { offset: 1, color: '#8ea2c6' }
                ]
                }
            },
            barWidth: 18
            }]
        }}
      />

      {/* 运营商Top20条形图 */}
      <ReactECharts
        style={{ height: 520, marginTop: 32 }}
        option={{
            title: { text: 'Top 20 Operators by Accident Count', left: 'center', textStyle: { color: '#d3dcedff', fontSize: 18 } },
            tooltip: { trigger: 'axis' },
            grid: { left: 240, right: 30, bottom: 40, top: 50 },
            xAxis: {
            type: 'log',
            axisLabel: { color: '#ccc' },
            splitLine: { lineStyle: { color: '#222' } }
            },
            yAxis: {
            type: 'category',
            data: (stats.operatorTop || []).map(item => item.operator),
            axisLabel: {
                color: '#8ea2c6',
                fontSize: 13,
                width: 220,
                overflow: 'break',
                formatter: function(value) {
                return value.length > 30 ? value.replace(/(.{30})/g, '$1\n') : value;
                }
            }
            },
            series: [{
            type: 'bar',
            data: (stats.operatorTop || []).map(item => item.count),
            itemStyle: {
                color: {
                type: 'linear',
                x: 1, y: 0, x2: 0, y2: 0,
                colorStops: [
                    { offset: 0, color: '#ffd700' },
                    { offset: 1, color: '#8ea2c6' }
                ]
                }
            },
            barWidth: 18
            }]
        }}
      />

      {/* 制造商累计事故数条形图 */}
      <ReactECharts
        style={{ height: 520, marginTop: 32 }}
        option={{
          title: { text: 'Top 20 Manufacturers by Accident Count', left: 'center', textStyle: { color: '#d3dcedff', fontSize: 18 } },
          tooltip: { trigger: 'axis' },
          grid: { left: 180, right: 30, bottom: 40, top: 50 },
          xAxis: {
            type: 'value',
            axisLabel: { color: '#ccc' },
            splitLine: { lineStyle: { color: '#222' } }
          },
          yAxis: {
            type: 'category',
            data: (manufacturerStats || []).map(item => item.manufacturer),
            axisLabel: { color: '#8ea2c6', fontSize: 13 }
          },
          series: [{
            type: 'bar',
            data: (manufacturerStats || []).map(item => item.incident_count),
            itemStyle: {
              color: {
                type: 'linear',
                x: 1, y: 0, x2: 0, y2: 0,
                colorStops: [
                  { offset: 0, color: '#ffb347' },
                  { offset: 1, color: '#8ea2c6' }
                ]
              }
            },
            barWidth: 18
          }]
        }}
      />

      {/* 制造商累计死亡人数条形图 */}
      <ReactECharts
        style={{ height: 520, marginTop: 32 }}
        option={{
          title: { text: 'Top 20 Manufacturers by Total Fatalities', left: 'center', textStyle: { color: '#d3dcedff', fontSize: 18 } },
          tooltip: { trigger: 'axis' },
          grid: { left: 180, right: 30, bottom: 40, top: 50 },
          xAxis: {
            type: 'value',
            axisLabel: { color: '#ccc' },
            splitLine: { lineStyle: { color: '#222' } }
          },
          yAxis: {
            type: 'category',
            data: (manufacturerFatalityStats || []).map(item => item.manufacturer),
            axisLabel: { color: '#8ea2c6', fontSize: 13 }
          },
          series: [{
            type: 'bar',
            data: (manufacturerFatalityStats || []).map(item => item.total_fatalities),
            itemStyle: {
              color: {
                type: 'linear',
                x: 1, y: 0, x2: 0, y2: 0,
                colorStops: [
                  { offset: 0, color: '#ff6b6b' },
                  { offset: 1, color: '#8ea2c6' }
                ]
              }
            },
            barWidth: 18
          }]
        }}
      />

      {/* 机龄vs事故/伤亡数 散点图 */}
      <div style={{
        background: '#23272f',
        borderRadius: 8,
        padding: 8,
        marginTop: 32
        }}>
        <ReactECharts
            style={{ height: 420, marginTop: 32 }}
            option={{
                title: { text: 'Aircraft Age vs Accident Count / Fatalities', left: 'center', textStyle: { color: '#d3dcedff', fontSize: 18 } },
                tooltip: { trigger: 'item', formatter: p => `Aircraft Age: ${p.value[0]} <br/>Accident: ${p.value[1]}<br/>Fatalities: ${p.value[2]}` },
                legend: { data: ['Accidents', 'Fatalities'], top: 42, textStyle: { color: '#ccc' } },
                grid: { left: 90, right: 90, bottom: 40, top: 90 },
                xAxis: { name: 'Age (years)', type: 'value', min: 0, max: 80, axisLabel: { color: '#ccc' } },
                yAxis: { name: 'Count', type: 'value', axisLabel: { color: '#ccc' } },
                series: [
                {
                    name: 'Accidents',
                    type: 'scatter',
                    data: ageStats.map(item => [Number(item.age), Number(item.accident_count), Number(item.total_fatalities)]),
                    symbolSize: 10,
                    itemStyle: { color: '#3fa7ff' }
                },
                {
                    name: 'Fatalities',
                    type: 'scatter',
                    data: ageStats.map(item => [Number(item.age), Number(item.total_fatalities), Number(item.accident_count)]),
                    symbolSize: 10,
                    itemStyle: { color: '#ff6b6b' }
                }
                ]
            }}
        />
      </div>
    </div>
  )
}

export default StatisticsBoard