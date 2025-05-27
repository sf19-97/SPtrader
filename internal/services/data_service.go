package services

import (
	"context"
	"fmt"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/rs/zerolog/log"
	"github.com/sptrader/sptrader/internal/db"
	"github.com/sptrader/sptrader/internal/models"
)

// DataService handles data retrieval from QuestDB
type DataService struct {
	pool *db.Pool
}

// NewDataService creates a new data service
func NewDataService(pool *db.Pool) *DataService {
	return &DataService{pool: pool}
}

// GetCandles retrieves OHLC data for the specified parameters
func (s *DataService) GetCandles(ctx context.Context, req models.CandleRequest, table string, limit int) ([]models.Candle, error) {
	// Check if we're querying an OHLC table or need to aggregate
	var query string
	
	// If the table name contains "ohlc", assume it's pre-aggregated
	if len(table) > 4 && table[:4] == "ohlc" {
		// Query pre-aggregated table
		query = fmt.Sprintf(`
			SELECT 
				timestamp,
				open,
				high,
				low,
				close,
				volume
			FROM %s
			WHERE symbol = $1
				AND timestamp >= $2
				AND timestamp <= $3
			ORDER BY timestamp
			LIMIT $4
		`, table)
	} else {
		// Generate SAMPLE BY query based on timeframe
		sampleInterval := s.getTimeframeInterval(req.Timeframe)
		if sampleInterval == "" {
			// Fallback to raw data if timeframe not recognized
			query = fmt.Sprintf(`
				SELECT 
					timestamp,
					bid as open,
					bid as high,
					bid as low,
					bid as close,
					volume
				FROM %s
				WHERE symbol = $1
					AND timestamp >= $2
					AND timestamp <= $3
				ORDER BY timestamp
				LIMIT $4
			`, table)
		} else {
			// Use SAMPLE BY to aggregate tick data into OHLC candles
			query = fmt.Sprintf(`
				SELECT 
					timestamp,
					first(bid) as open,
					max(bid) as high,
					min(bid) as low,
					last(bid) as close,
					sum(volume) as volume
				FROM %s
				WHERE symbol = $1
					AND timestamp >= $2
					AND timestamp <= $3
				SAMPLE BY %s ALIGN TO CALENDAR
				ORDER BY timestamp
				LIMIT $4
			`, table, sampleInterval)
		}
	}

	start := time.Now()
	rows, err := s.pool.Query(ctx, query, req.Symbol, req.Start, req.End, limit)
	if err != nil {
		return nil, fmt.Errorf("failed to query candles: %w", err)
	}
	defer rows.Close()

	queryTime := time.Since(start)
	log.Debug().
		Str("table", table).
		Str("symbol", req.Symbol).
		Dur("query_time", queryTime).
		Msg("Executed candle query")

	candles := make([]models.Candle, 0, limit)
	for rows.Next() {
		var c models.Candle
		err := rows.Scan(
			&c.Timestamp,
			&c.Open,
			&c.High,
			&c.Low,
			&c.Close,
			&c.Volume,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan candle: %w", err)
		}
		candles = append(candles, c)
	}

	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating rows: %w", err)
	}

	return candles, nil
}

// GetSymbols retrieves available trading symbols
func (s *DataService) GetSymbols(ctx context.Context) ([]models.Symbol, error) {
	query := `
		SELECT DISTINCT 
			symbol,
			max(timestamp) as last_update
		FROM market_data_v2
		GROUP BY symbol
		ORDER BY symbol
	`

	rows, err := s.pool.Query(ctx, query)
	if err != nil {
		return nil, fmt.Errorf("failed to query symbols: %w", err)
	}
	defer rows.Close()

	symbols := make([]models.Symbol, 0)
	for rows.Next() {
		var sym models.Symbol
		var symbolStr string
		err := rows.Scan(&symbolStr, &sym.LastUpdate)
		if err != nil {
			return nil, fmt.Errorf("failed to scan symbol: %w", err)
		}

		// Parse symbol (e.g., "EURUSD" -> EUR/USD)
		if len(symbolStr) >= 6 {
			sym.Symbol = symbolStr
			sym.BaseCurrency = symbolStr[:3]
			sym.QuoteCurrency = symbolStr[3:6]
			sym.Description = fmt.Sprintf("%s/%s", sym.BaseCurrency, sym.QuoteCurrency)
			sym.MinSize = 0.01    // Default values
			sym.TickSize = 0.0001 // Default for forex
		}

		symbols = append(symbols, sym)
	}

	return symbols, nil
}

// getTimeframeInterval converts timeframe string to QuestDB SAMPLE BY interval
func (s *DataService) getTimeframeInterval(timeframe string) string {
	switch timeframe {
	case "1m":
		return "1m"
	case "5m":
		return "5m"
	case "15m":
		return "15m"
	case "30m":
		return "30m"
	case "1h":
		return "1h"
	case "4h":
		return "4h"
	case "1d":
		return "1d"
	case "1w":
		return "1w"
	default:
		return ""
	}
}

// GetTableStats retrieves statistics about a table
func (s *DataService) GetTableStats(ctx context.Context, table string) (map[string]interface{}, error) {
	query := fmt.Sprintf(`
		SELECT 
			count(*) as row_count,
			min(timestamp) as first_timestamp,
			max(timestamp) as last_timestamp
		FROM %s
	`, table)

	var rowCount int64
	var firstTime, lastTime *time.Time

	err := s.pool.QueryRow(ctx, query).Scan(&rowCount, &firstTime, &lastTime)
	if err != nil {
		if err == pgx.ErrNoRows {
			return map[string]interface{}{
				"row_count": 0,
				"empty":     true,
			}, nil
		}
		return nil, fmt.Errorf("failed to get table stats: %w", err)
	}

	stats := map[string]interface{}{
		"table":      table,
		"row_count":  rowCount,
		"empty":      false,
	}

	if firstTime != nil {
		stats["first_timestamp"] = firstTime
		stats["last_timestamp"] = lastTime
		stats["time_range"] = lastTime.Sub(*firstTime)
	}

	return stats, nil
}

// EstimatePoints estimates the number of points for a query
func (s *DataService) EstimatePoints(ctx context.Context, table string, symbol string, start, end time.Time) (int, error) {
	// Use a more efficient count query
	query := fmt.Sprintf(`
		SELECT count(*) 
		FROM %s
		WHERE symbol = $1
			AND timestamp >= $2
			AND timestamp <= $3
	`, table)

	var count int
	err := s.pool.QueryRow(ctx, query, symbol, start, end).Scan(&count)
	if err != nil {
		return 0, fmt.Errorf("failed to estimate points: %w", err)
	}

	return count, nil
}

// CheckTableExists verifies if a table exists
func (s *DataService) CheckTableExists(ctx context.Context, table string) (bool, error) {
	query := `
		SELECT EXISTS (
			SELECT 1 
			FROM information_schema.tables 
			WHERE table_name = $1
		)
	`

	var exists bool
	err := s.pool.QueryRow(ctx, query, table).Scan(&exists)
	if err != nil {
		// QuestDB might not support information_schema, try alternative
		testQuery := fmt.Sprintf("SELECT 1 FROM %s LIMIT 1", table)
		err = s.pool.QueryRow(ctx, testQuery).Scan(&exists)
		if err != nil {
			if err == pgx.ErrNoRows {
				return true, nil // Table exists but is empty
			}
			return false, nil // Table doesn't exist
		}
		return true, nil
	}

	return exists, nil
}