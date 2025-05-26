package api

import (
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
)

// CheckDataAvailability checks what data is available for a symbol/timerange
func (h *Handlers) CheckDataAvailability(c *gin.Context) {
	symbol := c.Query("symbol")
	if symbol == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "symbol parameter required"})
		return
	}

	// Parse time range
	start, err := time.Parse(time.RFC3339, c.Query("start"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid start time"})
		return
	}

	end, err := time.Parse(time.RFC3339, c.Query("end"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid end time"})
		return
	}

	// Check availability
	availability, err := h.dataManager.CheckDataAvailability(c.Request.Context(), symbol, start, end)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, availability)
}

// EnsureData fetches missing data if needed
func (h *Handlers) EnsureData(c *gin.Context) {
	var request struct {
		Symbol string    `json:"symbol" binding:"required"`
		Start  time.Time `json:"start" binding:"required"`
		End    time.Time `json:"end" binding:"required"`
	}

	if err := c.ShouldBindJSON(&request); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Start background fetch
	go func() {
		ctx := c.Request.Context()
		if err := h.dataManager.EnsureData(ctx, request.Symbol, request.Start, request.End); err != nil {
			// Log error (in production, send to monitoring)
			println("Data fetch error:", err.Error())
		}
	}()

	c.JSON(http.StatusAccepted, gin.H{
		"status": "fetching",
		"message": "Data fetch initiated in background",
		"check_url": "/api/v1/data/status?symbol=" + request.Symbol,
	})
}

// GetDataStatus returns overall data availability
func (h *Handlers) GetDataStatus(c *gin.Context) {
	status, err := h.dataManager.GetDataStatus(c.Request.Context())
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, status)
}

// GetCandlesWithLazyLoad is an enhanced version that fetches missing data
func (h *Handlers) GetCandlesWithLazyLoad(c *gin.Context) {
	symbol := c.Query("symbol")
	if symbol == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "symbol parameter required"})
		return
	}

	timeframe := c.Query("tf")
	if timeframe == "" {
		timeframe = c.Query("timeframe")
	}
	if timeframe == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "timeframe parameter required"})
		return
	}

	start, err := time.Parse(time.RFC3339, c.Query("start"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid start time"})
		return
	}

	end, err := time.Parse(time.RFC3339, c.Query("end"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid end time"})
		return
	}

	// Check if we need to fetch data
	availability, err := h.dataManager.CheckDataAvailability(c.Request.Context(), symbol, start, end)
	if err == nil && !availability.HasData {
		// No data available, trigger fetch
		c.JSON(http.StatusAccepted, gin.H{
			"status": "no_data",
			"message": "No data available for this range. Use /api/v1/data/ensure to fetch it.",
			"availability": availability,
		})
		return
	}

	// If we have partial data, return what we have and indicate gaps
	if len(availability.Gaps) > 0 {
		// Get candles for available data
		candles, metadata, err := h.candleService.GetCandles(
			c.Request.Context(),
			symbol,
			timeframe,
			start,
			end,
			"v2",
		)

		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}

		c.JSON(http.StatusPartialContent, gin.H{
			"symbol":    symbol,
			"timeframe": timeframe,
			"start":     start,
			"end":       end,
			"count":     len(candles),
			"candles":   candles,
			"metadata":  metadata,
			"gaps":      availability.Gaps,
			"partial":   true,
		})
		return
	}

	// Full data available, return normally
	h.GetCandles(c)
}