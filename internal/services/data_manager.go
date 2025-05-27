package services

import (
	"context"
	"fmt"
	"log"
	"os"
	"os/exec"
	"sync"
	"time"

	"github.com/sptrader/sptrader/internal/db"
)

// DataManager handles on-demand data fetching and caching
type DataManager struct {
	pool         *db.Pool
	mu           sync.RWMutex
	fetching     map[string]bool // Track ongoing fetches to prevent duplicates
	pythonScript string          // Path to dukascopy_to_ilp.py
}

// DataAvailability represents what data we have for a symbol
type DataAvailability struct {
	Symbol      string    `json:"symbol"`
	FirstTick   time.Time `json:"first_tick"`
	LastTick    time.Time `json:"last_tick"`
	TickCount   int64     `json:"tick_count"`
	HasData     bool      `json:"has_data"`
	Gaps        []Gap     `json:"gaps,omitempty"`
}

// Gap represents a missing data range
type Gap struct {
	Start time.Time `json:"start"`
	End   time.Time `json:"end"`
	Hours int       `json:"hours"`
}

// NewDataManager creates a new data manager
func NewDataManager(pool *db.Pool) *DataManager {
	return &DataManager{
		pool:         pool,
		fetching:     make(map[string]bool),
		pythonScript: os.Getenv("SPTRADER_HOME") + "/data_feeds/dukascopy_to_ilp.py",
	}
}

// CheckDataAvailability checks what data we have for a symbol and time range
func (dm *DataManager) CheckDataAvailability(ctx context.Context, symbol string, start, end time.Time) (*DataAvailability, error) {
	query := `
		SELECT 
			MIN(timestamp) as first_tick,
			MAX(timestamp) as last_tick,
			COUNT(*) as tick_count
		FROM market_data_v2
		WHERE symbol = $1 
			AND timestamp >= $2 
			AND timestamp <= $3
	`

	var availability DataAvailability
	availability.Symbol = symbol

	err := dm.pool.QueryRow(ctx, query, symbol, start, end).Scan(
		&availability.FirstTick,
		&availability.LastTick,
		&availability.TickCount,
	)

	if err != nil || availability.TickCount == 0 {
		availability.HasData = false
		// If no data, the entire range is a gap
		availability.Gaps = []Gap{{
			Start: start,
			End:   end,
			Hours: int(end.Sub(start).Hours()),
		}}
		return &availability, nil
	}

	availability.HasData = true

	// Find gaps in the data
	gaps := dm.findDataGaps(ctx, symbol, start, end)
	availability.Gaps = gaps

	return &availability, nil
}

// findDataGaps identifies missing data ranges
func (dm *DataManager) findDataGaps(ctx context.Context, symbol string, start, end time.Time) []Gap {
	// Query to find hourly data coverage
	query := `
		SELECT 
			date_trunc('hour', timestamp) as hour,
			COUNT(*) as tick_count
		FROM market_data_v2
		WHERE symbol = $1 
			AND timestamp >= $2 
			AND timestamp <= $3
		GROUP BY hour
		ORDER BY hour
	`

	rows, err := dm.pool.Query(ctx, query, symbol, start, end)
	if err != nil {
		log.Printf("Error finding gaps: %v", err)
		return nil
	}
	defer rows.Close()

	// Build map of hours with data
	hoursWithData := make(map[time.Time]bool)
	for rows.Next() {
		var hour time.Time
		var count int
		if err := rows.Scan(&hour, &count); err == nil && count > 0 {
			hoursWithData[hour] = true
		}
	}

	// Find gaps
	var gaps []Gap
	current := start.Truncate(time.Hour)
	gapStart := time.Time{}

	for current.Before(end) {
		// Skip weekends (forex market closed)
		if current.Weekday() == time.Saturday || current.Weekday() == time.Sunday {
			current = current.Add(time.Hour)
			continue
		}

		if !hoursWithData[current] {
			if gapStart.IsZero() {
				gapStart = current
			}
		} else if !gapStart.IsZero() {
			// End of gap
			gaps = append(gaps, Gap{
				Start: gapStart,
				End:   current,
				Hours: int(current.Sub(gapStart).Hours()),
			})
			gapStart = time.Time{}
		}

		current = current.Add(time.Hour)
	}

	// Handle gap that extends to end
	if !gapStart.IsZero() {
		gaps = append(gaps, Gap{
			Start: gapStart,
			End:   end,
			Hours: int(end.Sub(gapStart).Hours()),
		})
	}

	return gaps
}

// EnsureData checks if data exists and fetches if missing
func (dm *DataManager) EnsureData(ctx context.Context, symbol string, start, end time.Time) error {
	availability, err := dm.CheckDataAvailability(ctx, symbol, start, end)
	if err != nil {
		return fmt.Errorf("failed to check availability: %w", err)
	}

	// If no gaps, we have all the data
	if len(availability.Gaps) == 0 {
		log.Printf("Data already available for %s from %s to %s", symbol, start.Format("2006-01-02"), end.Format("2006-01-02"))
		return nil
	}

	// Fetch data for each gap
	for _, gap := range availability.Gaps {
		if err := dm.fetchDataRange(ctx, symbol, gap.Start, gap.End); err != nil {
			return fmt.Errorf("failed to fetch data for gap: %w", err)
		}
	}

	return nil
}

// fetchDataRange fetches missing data using the Python script
func (dm *DataManager) fetchDataRange(ctx context.Context, symbol string, start, end time.Time) error {
	// Prevent duplicate fetches
	key := fmt.Sprintf("%s_%s_%s", symbol, start.Format("20060102"), end.Format("20060102"))
	
	dm.mu.Lock()
	if dm.fetching[key] {
		dm.mu.Unlock()
		log.Printf("Already fetching %s", key)
		return nil
	}
	dm.fetching[key] = true
	dm.mu.Unlock()

	defer func() {
		dm.mu.Lock()
		delete(dm.fetching, key)
		dm.mu.Unlock()
	}()

	log.Printf("Fetching %s data from %s to %s", symbol, start.Format("2006-01-02"), end.Format("2006-01-02"))

	// Run Python script
	cmd := exec.CommandContext(ctx, "python3", dm.pythonScript,
		symbol,
		start.Format("2006-01-02"),
		end.Format("2006-01-02"),
	)
	cmd.Dir = os.Getenv("SPTRADER_HOME") + "/data_feeds"

	output, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("fetch failed: %w\nOutput: %s", err, string(output))
	}

	log.Printf("Successfully fetched %s data", symbol)
	
	// Generate OHLC data after fetching
	return dm.generateOHLC(ctx)
}

// generateOHLC triggers OHLC generation
func (dm *DataManager) generateOHLC(ctx context.Context) error {
	cmd := exec.CommandContext(ctx, "python3", "-c",
		`from dukascopy_importer import DukascopyDownloader; d=DukascopyDownloader(); d.generate_ohlcv()`,
	)
	cmd.Dir = os.Getenv("SPTRADER_HOME") + "/data_feeds"

	if output, err := cmd.CombinedOutput(); err != nil {
		return fmt.Errorf("OHLC generation failed: %w\nOutput: %s", err, string(output))
	}

	log.Println("OHLC data generated successfully")
	return nil
}

// GetDataStatus returns the overall data status for monitoring
func (dm *DataManager) GetDataStatus(ctx context.Context) (map[string]interface{}, error) {
	query := `
		SELECT 
			symbol,
			COUNT(*) as tick_count,
			MIN(timestamp) as first_tick,
			MAX(timestamp) as last_tick
		FROM market_data_v2
		GROUP BY symbol
		ORDER BY symbol
	`

	rows, err := dm.pool.Query(ctx, query)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	symbols := make([]map[string]interface{}, 0)
	totalTicks := int64(0)

	for rows.Next() {
		var symbol string
		var count int64
		var first, last time.Time

		if err := rows.Scan(&symbol, &count, &first, &last); err != nil {
			continue
		}

		symbols = append(symbols, map[string]interface{}{
			"symbol":     symbol,
			"tick_count": count,
			"first_tick": first,
			"last_tick":  last,
			"days":       int(last.Sub(first).Hours() / 24),
		})
		totalTicks += count
	}

	return map[string]interface{}{
		"total_ticks": totalTicks,
		"symbols":     symbols,
		"updated_at":  time.Now(),
	}, nil
}