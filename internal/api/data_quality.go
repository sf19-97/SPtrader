package api

import (
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
)

// GetDataQuality returns information about data quality for intelligent range selection
func (h *Handlers) GetDataQuality(c *gin.Context) {
	symbol := c.Query("symbol")
	if symbol == "" {
		symbol = "EURUSD"
	}

	// Get connection
	conn, err := h.dataService.GetConnection(c.Request.Context())
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Database connection failed"})
		return
	}
	defer conn.Release()

	// Query to find days with good data (>10k ticks)
	// QuestDB specific: use simpler date filtering
	query := `
		SELECT 
			DATE_TRUNC('day', timestamp) as trading_day,
			COUNT(*) as tick_count,
			MIN(timestamp) as first_tick,
			MAX(timestamp) as last_tick
		FROM market_data_v2
		WHERE symbol = $1
			AND timestamp >= '2024-01-01'
		GROUP BY trading_day
		ORDER BY trading_day DESC
	`

	rows, err := conn.Query(c.Request.Context(), query, symbol)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "Query failed",
			"details": err.Error(),
		})
		return
	}
	defer rows.Close()

	type TradingDay struct {
		Date      string `json:"date"`
		TickCount int64  `json:"tick_count"`
		Quality   string `json:"quality"`
		FirstTick string `json:"first_tick"`
		LastTick  string `json:"last_tick"`
	}

	var goodDays []TradingDay
	var latestGoodDay time.Time

	for rows.Next() {
		var day time.Time
		var tickCount int64
		var firstTick, lastTick time.Time

		if err := rows.Scan(&day, &tickCount, &firstTick, &lastTick); err != nil {
			continue
		}

		// Only include days with substantial data
		if tickCount < 10000 {
			continue
		}

		quality := "GOOD"
		if tickCount > 50000 {
			quality = "EXCELLENT"
		}

		goodDays = append(goodDays, TradingDay{
			Date:      day.Format("2006-01-02"),
			TickCount: tickCount,
			Quality:   quality,
			FirstTick: firstTick.Format(time.RFC3339),
			LastTick:  lastTick.Format(time.RFC3339),
		})

		// Track the latest good day
		if len(goodDays) == 1 {
			latestGoodDay = day
		}
	}

	// Also get overall stats
	statsQuery := `
		SELECT 
			MIN(timestamp) as earliest,
			MAX(timestamp) as latest,
			COUNT(*) as total_ticks
		FROM market_data_v2
		WHERE symbol = $1
	`

	var earliest, latest time.Time
	var totalTicks int64

	row := conn.QueryRow(c.Request.Context(), statsQuery, symbol)
	row.Scan(&earliest, &latest, &totalTicks)

	c.JSON(http.StatusOK, gin.H{
		"symbol":          symbol,
		"latest_good_day": latestGoodDay.Format("2006-01-02"),
		"good_days":       goodDays,
		"overall_range": gin.H{
			"start":       earliest.Format(time.RFC3339),
			"end":         latest.Format(time.RFC3339),
			"total_ticks": totalTicks,
		},
		"recommendation": gin.H{
			"use_end_date": latestGoodDay.Format("2006-01-02T23:59:59Z"),
			"reason":       "Latest day with substantial trading data",
		},
	})
}