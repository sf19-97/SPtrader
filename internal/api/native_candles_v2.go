package api

import (
	"fmt"
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
)

// GetNativeCandlesV2 generates candles only for periods with actual data
func (h *Handlers) GetNativeCandlesV2(c *gin.Context) {
	symbol := c.Query("symbol")
	timeframe := c.Query("tf")
	startStr := c.Query("start")
	endStr := c.Query("end")

	if symbol == "" || timeframe == "" || startStr == "" || endStr == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Missing required parameters"})
		return
	}

	// Parse timestamps
	start, err := time.Parse(time.RFC3339, startStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid start time"})
		return
	}

	end, err := time.Parse(time.RFC3339, endStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid end time"})
		return
	}

	// Get connection
	conn, err := h.dataService.GetConnection(c.Request.Context())
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Database connection failed"})
		return
	}
	defer conn.Release()

	// Build query that only returns candles where data exists
	// This avoids empty candles during weekends/holidays
	query := fmt.Sprintf(`
		SELECT 
			timestamp,
			FIRST(bid) as open,
			MAX(bid) as high,
			MIN(bid) as low,
			LAST(bid) as close,
			SUM(COALESCE(bid_volume, 0) + COALESCE(ask_volume, 0)) as volume,
			COUNT(*) as tick_count
		FROM market_data_v2
		WHERE symbol = $1
			AND timestamp >= $2
			AND timestamp < $3
		SAMPLE BY %s FILL(NONE)
		ORDER BY timestamp
	`, timeframe)

	// Execute query
	rows, err := conn.Query(c.Request.Context(), query, symbol, start, end)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "Query failed",
			"details": err.Error(),
		})
		return
	}
	defer rows.Close()

	// Collect results
	type Candle struct {
		Timestamp string  `json:"timestamp"`
		Open      float64 `json:"open"`
		High      float64 `json:"high"`
		Low       float64 `json:"low"`
		Close     float64 `json:"close"`
		Volume    float64 `json:"volume"`
		TickCount int64   `json:"tick_count,omitempty"`
	}

	var candles []Candle
	for rows.Next() {
		var timestamp time.Time
		var open, high, low, close, volume float64
		var tickCount int64
		
		if err := rows.Scan(&timestamp, &open, &high, &low, &close, &volume, &tickCount); err != nil {
			continue
		}

		// Skip candles with no data
		if tickCount == 0 {
			continue
		}

		candles = append(candles, Candle{
			Timestamp: timestamp.Format(time.RFC3339),
			Open:      open,
			High:      high,
			Low:       low,
			Close:     close,
			Volume:    volume,
			TickCount: tickCount,
		})
	}

	c.JSON(http.StatusOK, gin.H{
		"candles":   candles,
		"count":     len(candles),
		"symbol":    symbol,
		"timeframe": timeframe,
		"method":    "native_aggregation_v2",
	})
}