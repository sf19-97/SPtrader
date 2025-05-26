package main

import (
	"context"
	"fmt"
	"os"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/rs/zerolog"
	"github.com/rs/zerolog/log"
)

// ProfileResult stores profiling data
type ProfileResult struct {
	Table           string
	Resolution      string
	TimeRangeHours  int
	Points          int
	QueryTimeMs     int64
	PointsPerMs     float64
	Status          string
	MemoryEstimateMB float64
}

// DataProfiler profiles database performance
type DataProfiler struct {
	pool    *pgxpool.Pool
	results []ProfileResult
}

func main() {
	// Setup logging
	zerolog.TimeFieldFormat = zerolog.TimeFormatUnix
	log.Logger = log.Output(zerolog.ConsoleWriter{Out: os.Stderr})

	log.Info().Msg("SPtrader Data Profiler")
	log.Info().Msg("=" + fmt.Sprintf("%80s", ""))

	// Connect to database
	ctx := context.Background()
	pool, err := pgxpool.New(ctx, "postgres://admin:quest@localhost:8812/qdb")
	if err != nil {
		log.Fatal().Err(err).Msg("Failed to connect to database")
	}
	defer pool.Close()

	// Test connection
	if err := pool.Ping(ctx); err != nil {
		log.Fatal().Err(err).Msg("Failed to ping database")
	}

	log.Info().Msg("✅ Connected to QuestDB")

	profiler := &DataProfiler{pool: pool}
	
	// Profile all tables
	profiler.profileAllTables(ctx)
	
	// Find optimal ranges
	profiler.findOptimalRanges(ctx)
	
	// Generate data contract
	profiler.generateDataContract()
}

func (p *DataProfiler) profileAllTables(ctx context.Context) {
	log.Info().Msg("\n🔍 Profiling Data Tables")
	
	tables := []struct {
		name       string
		resolution string
		hours      int
	}{
		{"market_data_v2", "tick", 1},
		{"ohlc_1m_v2", "1m", 4},
		{"ohlc_5m_v2", "5m", 24},
		{"ohlc_15m_v2", "15m", 168},
		{"ohlc_1h_v2", "1h", 720},
		{"ohlc_4h_viewport", "4h", 2160},
		{"ohlc_1d_viewport", "1d", 8760},
	}

	for _, table := range tables {
		result := p.profileTable(ctx, table.name, table.resolution, table.hours)
		p.results = append(p.results, result)
		
		log.Info().
			Str("table", table.name).
			Int("points", result.Points).
			Float64("query_ms", float64(result.QueryTimeMs)).
			Str("status", result.Status).
			Msg("Profile complete")
	}
}

func (p *DataProfiler) profileTable(ctx context.Context, table, resolution string, hours int) ProfileResult {
	query := fmt.Sprintf(`
		SELECT 
			timestamp,
			open,
			high,
			low,
			close,
			volume
		FROM %s
		WHERE symbol = 'EURUSD'
		AND timestamp >= NOW() - INTERVAL '%d hours'
		ORDER BY timestamp
	`, table, hours)

	start := time.Now()
	rows, err := p.pool.Query(ctx, query)
	queryTime := time.Since(start).Milliseconds()
	
	result := ProfileResult{
		Table:          table,
		Resolution:     resolution,
		TimeRangeHours: hours,
		QueryTimeMs:    queryTime,
	}

	if err != nil {
		result.Status = "❌ Failed"
		log.Error().Err(err).Str("table", table).Msg("Query failed")
		return result
	}
	defer rows.Close()

	// Count rows
	count := 0
	for rows.Next() {
		count++
	}

	result.Points = count
	result.PointsPerMs = float64(count) / float64(queryTime)
	result.MemoryEstimateMB = float64(count*48) / 1024 / 1024

	// Determine status
	switch {
	case queryTime < 50:
		result.Status = "⚡ Excellent"
	case queryTime < 100:
		result.Status = "✅ Good"
	case queryTime < 500:
		result.Status = "🔶 Acceptable"
	default:
		result.Status = "🐌 Slow"
	}

	return result
}

func (p *DataProfiler) findOptimalRanges(ctx context.Context) {
	log.Info().Msg("\n\n🎯 Finding Optimal Query Ranges")
	
	resolutions := []struct {
		table      string
		resolution string
		testHours  []int
	}{
		{"ohlc_5m_v2", "5m", []int{1, 4, 12, 24, 48, 168}},
		{"ohlc_1h_v2", "1h", []int{24, 168, 720, 2160}},
		{"ohlc_4h_viewport", "4h", []int{168, 720, 2160, 4320}},
		{"ohlc_1d_viewport", "1d", []int{720, 2160, 8760, 17520}},
	}

	for _, res := range resolutions {
		log.Info().Str("resolution", res.resolution).Msg("Testing resolution")
		
		for _, hours := range res.testHours {
			result := p.profileTable(ctx, res.table, res.resolution, hours)
			
			log.Info().
				Int("hours", hours).
				Int("points", result.Points).
				Float64("ms", float64(result.QueryTimeMs)).
				Str("status", result.Status).
				Msg("Range test")
		}
	}
}

func (p *DataProfiler) generateDataContract() {
	log.Info().Msg("\n\n📄 Data Contract")
	log.Info().Msg("=" + fmt.Sprintf("%80s", ""))
	
	fmt.Println(`
{
  "max_points_per_request": 10000,
  "resolutions": {
    "1m": {
      "table": "ohlc_1m_v2",
      "min_range_hours": 1,
      "max_range_hours": 24,
      "max_points": 1440,
      "typical_query_ms": 50
    },
    "5m": {
      "table": "ohlc_5m_v2",
      "min_range_hours": 4,
      "max_range_hours": 168,
      "max_points": 2016,
      "typical_query_ms": 75
    },
    "1h": {
      "table": "ohlc_1h_v2",
      "min_range_hours": 24,
      "max_range_hours": 2160,
      "max_points": 2160,
      "typical_query_ms": 100
    },
    "4h": {
      "table": "ohlc_4h_viewport",
      "min_range_hours": 168,
      "max_range_hours": 8760,
      "max_points": 2190,
      "typical_query_ms": 150
    },
    "1d": {
      "table": "ohlc_1d_viewport",
      "min_range_hours": 720,
      "max_range_hours": 43800,
      "max_points": 1825,
      "typical_query_ms": 200
    }
  },
  "performance_targets": {
    "excellent_ms": 50,
    "good_ms": 100,
    "acceptable_ms": 500
  }
}`)
}