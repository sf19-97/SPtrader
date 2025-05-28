package api

import (
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/sptrader/sptrader/internal/models"
	"github.com/sptrader/sptrader/internal/services"
)

// Handlers contains all HTTP handlers
type Handlers struct {
	dataService     *services.DataService
	viewportService *services.ViewportService
	candleService   *services.DataService  // alias for backward compatibility
	dataManager     *services.DataManager
	startTime       time.Time
}

// NewHandlers creates new handlers instance
func NewHandlers(dataService *services.DataService, viewportService *services.ViewportService, dataManager *services.DataManager) *Handlers {
	return &Handlers{
		dataService:     dataService,
		viewportService: viewportService,
		candleService:   dataService,
		dataManager:     dataManager,
		startTime:       time.Now(),
	}
}

// Health handles health check requests
func (h *Handlers) Health(c *gin.Context) {
	// Simple health check for now
	// TODO: Add database health check using ctx := c.Request.Context()
	
	c.JSON(http.StatusOK, gin.H{
		"status":  "healthy",
		"service": "sptrader-api",
		"version": "1.0.0",
		"uptime":  time.Since(h.startTime).String(),
	})
}

// GetCandles handles standard candle requests
func (h *Handlers) GetCandles(c *gin.Context) {
	var req models.CandleRequest
	if err := c.ShouldBindQuery(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "Invalid request parameters",
			"details": err.Error(),
		})
		return
	}

	// Default to v2 if not specified
	if req.Source == "" {
		req.Source = "v2"
	}

	// Use viewport service to get candles
	response, err := h.viewportService.GetSmartCandles(c.Request.Context(), req)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "Failed to retrieve candles",
			"details": err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, response)
}

// GetSmartCandles handles viewport-aware candle requests
func (h *Handlers) GetSmartCandles(c *gin.Context) {
	var req models.CandleRequest
	if err := c.ShouldBindQuery(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "Invalid request parameters",
			"details": err.Error(),
		})
		return
	}

	// Let viewport service handle resolution selection
	response, err := h.viewportService.GetSmartCandles(c.Request.Context(), req)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "Failed to retrieve candles",
			"details": err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, response)
}

// ExplainQuery explains how a query would be executed
func (h *Handlers) ExplainQuery(c *gin.Context) {
	var req models.CandleRequest
	if err := c.ShouldBindQuery(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "Invalid request parameters",
			"details": err.Error(),
		})
		return
	}

	explanation := h.viewportService.ExplainQuery(req)
	c.JSON(http.StatusOK, explanation)
}

// GetSymbols returns available trading symbols
func (h *Handlers) GetSymbols(c *gin.Context) {
	symbols, err := h.dataService.GetSymbols(c.Request.Context())
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "Failed to retrieve symbols",
			"details": err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"count": len(symbols),
		"symbols": symbols,
	})
}

// GetDataRange returns the available date range for a symbol
func (h *Handlers) GetDataRange(c *gin.Context) {
	symbol := c.Query("symbol")
	if symbol == "" {
		symbol = "EURUSD"
	}

	dataRange, err := h.dataService.GetDataRange(c.Request.Context(), symbol)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "Failed to retrieve data range",
			"details": err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, dataRange)
}

// GetTimeframes returns supported timeframes
func (h *Handlers) GetTimeframes(c *gin.Context) {
	timeframes := []gin.H{
		{"name": "1m", "label": "1 Minute", "seconds": 60},
		{"name": "5m", "label": "5 Minutes", "seconds": 300},
		{"name": "15m", "label": "15 Minutes", "seconds": 900},
		{"name": "30m", "label": "30 Minutes", "seconds": 1800},
		{"name": "1h", "label": "1 Hour", "seconds": 3600},
		{"name": "4h", "label": "4 Hours", "seconds": 14400},
		{"name": "1d", "label": "1 Day", "seconds": 86400},
	}

	c.JSON(http.StatusOK, gin.H{
		"timeframes": timeframes,
	})
}

// GetStats returns API statistics
func (h *Handlers) GetStats(c *gin.Context) {
	// This would be enhanced with actual metrics
	stats := models.Stats{
		Uptime:         time.Since(h.startTime),
		TotalRequests:  0, // Would track this
		AverageLatency: 0, // Would calculate this
		ActiveQueries:  0, // Would track this
	}

	c.JSON(http.StatusOK, stats)
}

// GetCacheStats returns cache statistics
func (h *Handlers) GetCacheStats(c *gin.Context) {
	// This would get actual cache stats from the cache service
	c.JSON(http.StatusOK, gin.H{
		"message": "Cache stats endpoint",
		// Would include actual stats
	})
}

// GetDataContract returns the current data contract
func (h *Handlers) GetDataContract(c *gin.Context) {
	contract := h.viewportService.GetDataContract()
	c.JSON(http.StatusOK, contract)
}