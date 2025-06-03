package api

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
)

// GetDataQualityV2 returns data quality information from the pre-computed table
func (h *Handlers) GetDataQualityV2(c *gin.Context) {
	symbol := c.Query("symbol")
	if symbol == "" {
		symbol = "EURUSD"
	}

	conn, err := h.dataService.GetConnection(c.Request.Context())
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Database connection failed"})
		return
	}
	defer conn.Release()

	// Get the latest good trading day
	latestGoodQuery := `
		SELECT 
			trading_date,
			tick_count,
			quality_rating,
			quality_score
		FROM data_quality
		WHERE symbol = $1
			AND is_complete = true
			AND quality_score >= 70
		ORDER BY trading_date DESC
		LIMIT 1
	`

	var latestGoodDate time.Time
	var tickCount int64
	var qualityRating string
	var qualityScore float64

	row := conn.QueryRow(c.Request.Context(), latestGoodQuery, symbol)
	err = row.Scan(&latestGoodDate, &tickCount, &qualityRating, &qualityScore)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "Failed to find good trading days",
			"details": err.Error(),
		})
		return
	}

	// Get quality distribution
	distributionQuery := `
		SELECT 
			quality_rating,
			COUNT(*) as count
		FROM data_quality
		WHERE symbol = $1
		GROUP BY quality_rating
	`

	rows, err := conn.Query(c.Request.Context(), distributionQuery, symbol)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to get distribution"})
		return
	}
	defer rows.Close()

	distribution := make(map[string]int64)
	for rows.Next() {
		var rating string
		var count int64
		if err := rows.Scan(&rating, &count); err == nil {
			distribution[rating] = count
		}
	}

	// Get suggested ranges for each timeframe
	ranges := h.getSuggestedRanges(c.Request.Context(), symbol, latestGoodDate)

	c.JSON(http.StatusOK, gin.H{
		"symbol": symbol,
		"latest_good_day": gin.H{
			"date":           latestGoodDate.Format("2006-01-02"),
			"tick_count":     tickCount,
			"quality_rating": qualityRating,
			"quality_score":  qualityScore,
		},
		"quality_distribution": distribution,
		"suggested_ranges":     ranges,
		"recommendation": gin.H{
			"use_end_date": latestGoodDate.Format("2006-01-02") + "T23:59:59Z",
			"reason":       fmt.Sprintf("Latest %s quality day with %.0f score", qualityRating, qualityScore),
		},
	})
}

// getSuggestedRanges returns optimal date ranges for each timeframe
func (h *Handlers) getSuggestedRanges(ctx context.Context, symbol string, endDate time.Time) map[string]interface{} {
	conn, err := h.dataService.GetConnection(ctx)
	if err != nil {
		return nil
	}
	defer conn.Release()

	ranges := make(map[string]interface{})
	
	timeframes := []struct {
		name string
		days int
	}{
		{"1m", 3},
		{"5m", 7},
		{"15m", 14},
		{"30m", 30},
		{"1h", 60},
		{"4h", 180},
		{"1d", 365},
	}

	for _, tf := range timeframes {
		// Find the optimal start date by looking for good quality days
		query := `
			SELECT 
				MIN(trading_date) as start_date,
				COUNT(*) as good_days
			FROM data_quality
			WHERE symbol = $1
				AND trading_date <= $2
				AND trading_date >= $3
				AND is_complete = true
				AND quality_score >= 50
		`

		targetStart := endDate.AddDate(0, 0, -tf.days)
		
		var startDate time.Time
		var goodDays int64

		row := conn.QueryRow(ctx, query, symbol, endDate, targetStart)
		if err := row.Scan(&startDate, &goodDays); err == nil && goodDays > 0 {
			ranges[tf.name] = gin.H{
				"start":      startDate.Format("2006-01-02") + "T00:00:00Z",
				"end":        endDate.Format("2006-01-02") + "T23:59:59Z",
				"good_days":  goodDays,
				"total_days": tf.days,
			}
		}
	}

	return ranges
}