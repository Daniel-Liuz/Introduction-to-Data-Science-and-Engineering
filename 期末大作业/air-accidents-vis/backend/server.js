const express = require('express');
const { Pool } = require('pg');
const cors = require('cors');
const axios = require('axios');
require('dotenv').config();

const app = express();
const port = process.env.PORT || 3001;
const AI_SERVICE_URL = 'http://localhost:8000/chat';
app.use(cors());
app.use(express.json());

const pool = new Pool({
  user: process.env.DB_USER || 'your_username',
  host: process.env.DB_HOST || 'localhost',
  database: process.env.DB_NAME || 'your_database',
  password: process.env.DB_PASSWORD || 'your_password',
  port: process.env.DB_PORT || 5432,
});

pool.connect((err, client, release) => {
  if (err) {
    console.error('! 数据库连接失败:', err.stack);
  } else {
    console.log(' 数据库连接成功');
    release();
  }
});

// 获取所有航空事故数据（去除掉坐标缺失的数据）
app.get('/api/accidents', async (req, res) => {
  try {
    const query = `
      SELECT 
        "Date",
        "Departure airport",
        "Destination airport",
        "Fatalities",
        "Location",
        "Narrative",
        "Nature",
        "Other fatalities",
        "Owner/operator",
        "Phase",
        "Registration",
        "Type",
        "dep_IATA",
        "dep_ICAO", 
        "arr_IATA",
        "arr_ICAO",
        "dep_lat",
        "dep_lon",
        "arr_lat", 
        "arr_lon",
        "Occupants",
        "Category",
        "Aircraft damage",
        "Confidence Rating",
        "DetailURL"
      FROM asn_incidents 
      WHERE "dep_lat" IS NOT NULL 
        AND "dep_lon" IS NOT NULL 
        AND "arr_lat" IS NOT NULL 
        AND "arr_lon" IS NOT NULL
        AND "dep_lat" != 0 
        AND "dep_lon" != 0
        AND "arr_lat" != 0
        AND "arr_lon" != 0
      ORDER BY "Date" DESC
      LIMIT 1000
    `;
    
    const result = await pool.query(query);
    res.json(result.rows);
  } catch (err) {
    console.error('查询失败:', err);
    res.status(500).json({ error: '数据库查询失败', details: err.message });
  }
});

// 获取最近事故
app.get('/api/recent-accidents', async (req, res) => {
  try {
    const query = `
      SELECT 
        "Date",
        "Departure airport",
        "Destination airport", 
        "Fatalities",
        "Location",
        "Nature",
        "Owner/operator",
        "Registration",
        "Type",
        "dep_IATA",
        "arr_IATA",
        "DetailURL",
        "Narrative"
      FROM asn_incidents 
      WHERE "Fatalities" IS NOT NULL 
        AND "Fatalities" > 0
        AND "Date" IS NOT NULL
      ORDER BY "Date" DESC
      LIMIT 30
    `;
    
    const result = await pool.query(query);
    res.json(result.rows);
  } catch (err) {
    console.error('查询失败:', err);
    res.status(500).json({ error: '查询失败', details: err.message });
  }
});

// 获取统计数据
app.get('/api/statistics', async (req, res) => {
  try {
    const queries = await Promise.all([
      // 总事故数
      pool.query('SELECT COUNT(*) as total_accidents FROM asn_incidents'),
      // 总死亡人数
      pool.query('SELECT SUM("Fatalities") as total_fatalities FROM asn_incidents WHERE "Fatalities" IS NOT NULL'),
      // 有坐标数据的事故数
      pool.query(`SELECT COUNT(*) as mapped_accidents FROM asn_incidents 
                  WHERE "dep_lat" IS NOT NULL AND "dep_lon" IS NOT NULL 
                  AND "arr_lat" IS NOT NULL AND "arr_lon" IS NOT NULL`),
      // 按年份统计
      pool.query(`
                  SELECT 
                    EXTRACT(YEAR FROM "Date"::date) as year, 
                    COUNT(*) as count,
                    SUM("Fatalities") as fatalities
                  FROM asn_incidents 
                  WHERE "Date" IS NOT NULL 
                  GROUP BY EXTRACT(YEAR FROM "Date"::date) 
                  ORDER BY year DESC LIMIT 10
                `),
      // 事故类型分布
      pool.query(`SELECT "Category" as type, COUNT(*) as count 
                  FROM asn_incidents 
                  WHERE "Category" IS NOT NULL AND "Category" != ''
                  GROUP BY "Category"
                  ORDER BY count DESC`),
      // 机型Top20
      pool.query(`SELECT "Type" as aircraft, COUNT(*) as count 
                  FROM asn_incidents 
                  WHERE "Type" IS NOT NULL AND "Type" != ''
                  GROUP BY "Type"
                  ORDER BY count DESC
                  LIMIT 20`),
      // 飞行阶段
      pool.query(`SELECT "Phase" as phase, COUNT(*) as count 
                  FROM asn_incidents 
                  WHERE "Phase" IS NOT NULL AND "Phase" != ''
                  GROUP BY "Phase"
                  ORDER BY count DESC`),
      // 运营商Top20
      pool.query(`SELECT "Owner/operator" as operator, COUNT(*) as count 
                  FROM asn_incidents 
                  WHERE "Owner/operator" IS NOT NULL AND "Owner/operator" != ''
                  GROUP BY "Owner/operator"
                  ORDER BY count DESC
                  LIMIT 20`),

    ]);

    res.json({
      totalAccidents: parseInt(queries[0].rows[0].total_accidents),
      totalFatalities: parseInt(queries[1].rows[0].total_fatalities) || 0,
      mappedAccidents: parseInt(queries[2].rows[0].mapped_accidents),
      yearlyStats: queries[3].rows,
      typeStats: queries[4].rows,
      aircraftTop: queries[5].rows,
      phaseStats: queries[6].rows,
      operatorTop: queries[7].rows
    });
  } catch (err) {
    console.error('统计查询失败:', err);
    res.status(500).json({ error: '统计查询失败', details: err.message });
  }
});

// 搜索
app.get('/api/search', async (req, res) => {
  try {
    const { 
      q,           
      startDate,
      endDate,        
      minFatalities, 
      maxFatalities, 
      operator,    
      aircraftType,       
      category,    
      hasRoute,
      page = 1,
      limit = 500    
    } = req.query;

    let conditions = [];
    let params = [];
    let paramCount = 0;

    // 基础搜索关键词
    if (q && q.trim()) {
      paramCount++;
      conditions.push(`(
        "Departure airport" ILIKE $${paramCount} OR
        "Destination airport" ILIKE $${paramCount} OR
        "Registration" ILIKE $${paramCount} OR
        "Owner/operator" ILIKE $${paramCount} OR
        "Type" ILIKE $${paramCount} OR
        "Location" ILIKE $${paramCount} OR
        "Nature" ILIKE $${paramCount} OR
        "Narrative" ILIKE $${paramCount}
      )`);
      params.push(`%${q.trim()}%`);
    }

    // 时间筛选
    if (startDate) {
      paramCount++;
      conditions.push(`"Date"::date >= $${paramCount}`);
      params.push(startDate);
    }
    if (endDate) {
      paramCount++;
      conditions.push(`"Date"::date <= $${paramCount}`);
      params.push(endDate);
    }

    // 死亡人数范围
    if (minFatalities && minFatalities !== '') {
      paramCount++;
      conditions.push(`"Fatalities" >= $${paramCount}`);
      params.push(parseInt(minFatalities));
    }
    if (maxFatalities && maxFatalities !== '') {
      paramCount++;
      conditions.push(`"Fatalities" <= $${paramCount}`);
      params.push(parseInt(maxFatalities));
    }

    // 运营商筛选
    
    if (operator && operator !== 'all') {
      paramCount++;
      conditions.push(`"Owner/operator" ILIKE $${paramCount}`);
      params.push(`%${operator}%`);
    }

    // 飞机类型筛选
    if (aircraftType && aircraftType !== 'all') {
      paramCount++;
      conditions.push(`"Type" ILIKE $${paramCount}`);
      params.push(`%${aircraftType}%`);
    }

    // 事故类型筛选
    if (category && category !== 'all') {
      paramCount++;
      conditions.push(`"Category" ILIKE $${paramCount}`);
      params.push(`%${category}%`);
    }

    // 是否有航线数据筛选
    if (hasRoute === 'true') {
      conditions.push(`"dep_lat" IS NOT NULL AND "dep_lon" IS NOT NULL AND "arr_lat" IS NOT NULL AND "arr_lon" IS NOT NULL AND "dep_lat" != 0 AND "dep_lon" != 0 AND "arr_lat" != 0 AND "arr_lon" != 0`);
    } else if (hasRoute === 'false') {
      conditions.push(`("dep_lat" IS NULL OR "dep_lon" IS NULL OR "arr_lat" IS NULL OR "arr_lon" IS NULL OR "dep_lat" = 0 OR "dep_lon" = 0 OR "arr_lat" = 0 OR "arr_lon" = 0)`);
    }

    const whereClause = conditions.length > 0 ? `WHERE ${conditions.join(' AND ')}` : '';
    
    //分页参数
    const pageNum = Math.max(1, parseInt(page));
    const limitNum = Math.min(1000, Math.max(100, parseInt(limit))); // 限制在100-1000之间
    const offset = (pageNum - 1) * limitNum;
    
    const countQuery = `
      SELECT COUNT(*) as total
      FROM asn_incidents
      ${whereClause}
    `;

    const countResult = await pool.query(countQuery, params);
    const totalRecords = parseInt(countResult.rows[0].total);
    const query = `
      SELECT 
        "Date",
        "Departure airport",
        "Destination airport",
        "Fatalities",
        "Location",
        "Narrative",
        "Nature",
        "Other fatalities",
        "Owner/operator",
        "Phase",
        "Registration",
        "Type",
        "dep_IATA",
        "dep_ICAO", 
        "arr_IATA",
        "arr_ICAO",
        "dep_lat",
        "dep_lon",
        "arr_lat", 
        "arr_lon",
        "Occupants",
        "Category",
        "Aircraft damage",
        "Confidence Rating",
        "DetailURL"
      FROM asn_incidents
      ${whereClause}
      ORDER BY "Date" DESC
      LIMIT ${limitNum} OFFSET ${offset}
    `;
    
    console.log('搜索查询:', { 
      query: query.substring(0, 200) + '...', 
      params, 
      page: pageNum, 
      limit: limitNum,
      totalRecords
    });
    
    const result = await pool.query(query, params);
    
    console.log(`搜索结果: 第${pageNum}页，${result.rows.length}/${totalRecords} 条记录`);
    
    res.json({
      data: result.rows,
      pagination: {
        currentPage: pageNum,
        totalPages: Math.ceil(totalRecords / limitNum),
        totalRecords: totalRecords,
        recordsPerPage: limitNum,
        hasNextPage: pageNum < Math.ceil(totalRecords / limitNum),
        hasPrevPage: pageNum > 1
      }
    });
  } catch (err) {
    console.error('搜索失败:', err);
    res.status(500).json({ error: '搜索失败', details: err.message });
  }
});

// 获取筛选选项数据
app.get('/api/filter-options', async (req, res) => {
  try {
    const queries = await Promise.all([
      // 获取年份列表
      pool.query(`
        SELECT DISTINCT EXTRACT(YEAR FROM "Date") as year 
        FROM asn_incidents 
        WHERE "Date" IS NOT NULL 
        ORDER BY year DESC
      `).catch(err => {
        console.error('年份查询失败:', err);
        return { rows: [] };
      }),

      // 获取主要运营商
      pool.query(`
        SELECT "Owner/operator", COUNT(*) as count 
        FROM asn_incidents 
        WHERE "Owner/operator" IS NOT NULL 
          AND "Owner/operator" != ''
          AND LENGTH("Owner/operator") > 1
        GROUP BY "Owner/operator" 
        ORDER BY count DESC 
      `).catch(err => {
        console.error('运营商查询失败:', err);
        return { rows: [] };
      }),
      // 获取主要飞机类型
      pool.query(`
        SELECT "Type", COUNT(*) as count 
        FROM asn_incidents 
        WHERE "Type" IS NOT NULL 
          AND "Type" != ''
          AND LENGTH("Type") > 1
        GROUP BY "Type" 
        ORDER BY count DESC 
      `).catch(err => {
        console.error('飞机型号查询失败:', err);
        return { rows: [] };
      }),
      // 获取事故类型
      pool.query(`
        SELECT "Category", COUNT(*) as count 
        FROM asn_incidents 
        WHERE "Category" IS NOT NULL 
          AND "Category" != ''
          AND LENGTH("Category") > 1
        GROUP BY "Category" 
        ORDER BY count DESC
      `).catch(err => {
        console.error('事故类型查询失败:', err);
        return { rows: [] };
      })
    ]);

    res.json({
      years: queries[0].rows.map(row => parseInt(row.year)).filter(year => !isNaN(year)),
      operators: queries[1].rows,
      aircraftTypes: queries[2].rows,
      categories: queries[3].rows
    });
  } catch (err) {
    console.error('获取筛选选项失败:', err);
    res.status(500).json({ error: '获取筛选选项失败', details: err.message });
  }
});

app.get('/api/unmapped-accidents', async (req, res) => {
  try {
    const query = `
      SELECT 
        "Date",
        "Departure airport",
        "Destination airport", 
        "Fatalities",
        "Location",
        "Nature",
        "Owner/operator",
        "Registration",
        "Type",
        "dep_IATA",
        "arr_IATA",
        "DetailURL",
        "Narrative"
      FROM asn_incidents 
      WHERE (
        "dep_lat" IS NULL OR "dep_lon" IS NULL OR
        "arr_lat" IS NULL OR "arr_lon" IS NULL OR
        "dep_lat" = 0 OR "dep_lon" = 0 OR
        "arr_lat" = 0 OR "arr_lon" = 0
      )
      AND "Date" IS NOT NULL
      ORDER BY "Date" DESC
      LIMIT 40
    `;
    const result = await pool.query(query);
    res.json(result.rows);
  } catch (err) {
    console.error('查询unmapped事故失败:', err);
    res.status(500).json({ error: '查询unmapped事故失败', details: err.message });
  }
});

app.get('/api/country-accident-stats', async (req, res) => {
  try {
    // 提取Location最后的国家名（假设用'-'分隔，最后一个trim即可）
    const query = `
      SELECT 
        TRIM(SPLIT_PART("Location", '-', array_length(string_to_array("Location", '-'), 1))) AS country,
        COUNT(*) AS count
      FROM asn_incidents
      WHERE "Location" IS NOT NULL AND "Location" LIKE '%-%'
      GROUP BY country
      ORDER BY count DESC
      LIMIT 30
    `;
    const result = await pool.query(query);
    res.json(result.rows);
  } catch (err) {
    console.error('国家事故统计失败:', err);
    res.status(500).json({ error: '国家事故统计失败', details: err.message });
  }
});

app.get('/api/monthly-accidents', async (req, res) => {
  try {
    const query = `
      SELECT 
        EXTRACT(MONTH FROM "Date"::DATE) AS month,
        COUNT(*) AS count,
        SUM("Fatalities") AS fatalities
      FROM asn_incidents
      WHERE "Date" IS NOT NULL
        AND EXTRACT(YEAR FROM "Date"::DATE) BETWEEN 2020 AND 2024
      GROUP BY month
      ORDER BY month
    `;
    const result = await pool.query(query);
    res.json(result.rows);
  } catch (err) {
    console.error('月份累计事故统计失败:', err);
    res.status(500).json({ error: '月份累计事故统计失败', details: err.message });
  }
});

app.get('/api/age-accident-stats', async (req, res) => {
  try {
    // 计算机龄（事故发生年份 - 出厂年份），统计每个机龄的事故数和总伤亡
    const query = `
      SELECT 
        (EXTRACT(YEAR FROM "Date"::DATE) - "Year of manufacture") AS age,
        COUNT(*) AS accident_count,
        SUM("Fatalities") AS total_fatalities
      FROM asn_incidents
      WHERE "Date" IS NOT NULL 
        AND "Year of manufacture" IS NOT NULL
        AND "Year of manufacture" > 1900
        AND "Year of manufacture" <= EXTRACT(YEAR FROM "Date"::DATE)
      GROUP BY (EXTRACT(YEAR FROM "Date"::DATE) - "Year of manufacture")
      HAVING (EXTRACT(YEAR FROM "Date"::DATE) - "Year of manufacture") >= 0 
         AND (EXTRACT(YEAR FROM "Date"::DATE) - "Year of manufacture") <= 80
      ORDER BY age
    `;
    const result = await pool.query(query);
    res.json(result.rows);
  } catch (err) {
    console.error('机龄统计失败:', err);
    res.status(500).json({ error: '机龄统计失败', details: err.message });
  }
});

app.get('/api/manufacturer-accident-stats', async (req, res) => {
  try {
    const query = `
      WITH manu_normalized AS (
        SELECT
          CASE
            WHEN "Type" ILIKE 'de Havilland %'  THEN 'de Havilland'
            WHEN "Type" ILIKE 'Air Tractor %'   THEN 'Air Tractor'
            WHEN "Type" ILIKE 'Air Creation %'  THEN 'Air Creation'
            WHEN "Type" ILIKE 'Air Camper %'    THEN 'Air Camper'
            WHEN "Type" ILIKE 'Air Command %'   THEN 'Air Command'
            WHEN "Type" ILIKE 'McDonnell Douglas %' 
              OR "Type" ILIKE 'Mc Donnell Douglas %'
              OR "Type" ILIKE 'McDonnel Douglas %'
            THEN 'McDonnell Douglas'
            WHEN "Type" ILIKE $$Van's %$$
              OR "Type" ILIKE $$Vans %$$
              OR "Type" ILIKE $$Van’s %$$
            THEN 'Vans'
            ELSE split_part("Type", ' ', 1)
          END AS manufacturer
        FROM asn_incidents
        WHERE "Type" IS NOT NULL
      )
      SELECT
        manufacturer,
        COUNT(*) AS incident_count
      FROM manu_normalized
      GROUP BY manufacturer
      ORDER BY incident_count DESC
      LIMIT 20;
    `;
    const result = await pool.query(query);
    res.json(result.rows);
  } catch (err) {
    console.error('制造商事故统计失败:', err);
    res.status(500).json({ error: '制造商事故统计失败', details: err.message });
  }
});

app.get('/api/manufacturer-fatality-stats', async (req, res) => {
  try {
    const query = `
      WITH manu_normalized AS (
        SELECT
          CASE
            WHEN "Type" ILIKE 'de Havilland %'  THEN 'de Havilland'
            WHEN "Type" ILIKE 'Air Tractor %'   THEN 'Air Tractor'
            WHEN "Type" ILIKE 'Air Creation %'  THEN 'Air Creation'
            WHEN "Type" ILIKE 'Air Camper %'    THEN 'Air Camper'
            WHEN "Type" ILIKE 'Air Command %'   THEN 'Air Command'
            WHEN "Type" ILIKE 'McDonnell Douglas %' 
              OR "Type" ILIKE 'Mc Donnell Douglas %'
              OR "Type" ILIKE 'McDonnel Douglas %'
            THEN 'McDonnell Douglas'
            WHEN "Type" ILIKE $$Van's %$$
              OR "Type" ILIKE $$Vans %$$
              OR "Type" ILIKE $$Van’s %$$
            THEN 'Vans'
            ELSE split_part("Type", ' ', 1)
          END AS manufacturer,
          "Fatalities"
        FROM asn_incidents
        WHERE "Type" IS NOT NULL AND "Fatalities" IS NOT NULL
      )
      SELECT
        manufacturer,
        SUM("Fatalities") AS total_fatalities
      FROM manu_normalized
      GROUP BY manufacturer
      ORDER BY total_fatalities DESC
      LIMIT 20;
    `;
    const result = await pool.query(query);
    res.json(result.rows);
  } catch (err) {
    console.error('制造商累计死亡人数统计失败:', err);
    res.status(500).json({ error: '制造商累计死亡人数统计失败', details: err.message });
  }
});


app.listen(port, () => {
  console.log(` 后端服务运行在 http://localhost:${port}`);
});

app.post('/api/chat', async (req, res) => {
  const { message } = req.body;

  if (!message) {
    return res.status(400).json({ error: '消息内容不能为空' });
  }

  try {
    console.log(`[Proxy] 正在转发问题到 AI 微服务: "${message}"`);

    // 2. 转发请求到 Python FastAPI
    const response = await axios.post(AI_SERVICE_URL, {
      message: message
    }, {
      timeout: 60000 // AI 生成可能较慢，设置 60 秒超时
    });

    // 3. 将 AI 的回答和参考上下文返回给前端
    res.json({
      answer: response.data.answer,
      context: response.data.context // 这是我们在 app.py 中定义的参考记录
    });

  } catch (err) {
    console.error('AI 微服务调用失败:', err.message);
    
    // 错误处理：如果 Python 服务没开，给前端一个友好的提示
    if (err.code === 'ECONNREFUSED') {
      return res.status(503).json({ 
        error: 'AI 引擎离线', 
        details: '请确保 Python 端的 app.py 已经成功运行。' 
      });
    }

    res.status(500).json({ 
      error: 'AI 回答生成失败', 
      details: err.message 
    });
  }
});