package services

import (
	"context"
	"fmt"
	"time"

	"github.com/rs/zerolog/log"
	"github.com/sptrader/sptrader/internal/config"
	"github.com/sptrader/sptrader/internal/db"
	"github.com/sptrader/sptrader/internal/models"
)

// ViewportService manages intelligent data loading based on viewport
type ViewportService struct {
	pool     *db.Pool
	cache    *CacheService
	config   config.DataConfig
}

// NewViewportService creates a new viewport service
func NewViewportService(pool *db.Pool, cache *CacheService) *ViewportService {
	// Default configuration - would normally come from config
	defaultConfig := config.DataConfig{
		MaxPointsPerRequest: 10000,
		Resolutions: map[string]config.ResolutionConfig{
			"1m": {
				Table:       "ohlc_1m_v2",
				MinRange:    1 * time.Hour,
				MaxRange:    24 * time.Hour,
				MaxPoints:   1440,
				Description: "1-minute bars for intraday",
			},
			"5m": {
				Table:       "ohlc_5m_v2", 
				MinRange:    4 * time.Hour,
				MaxRange:    7 * 24 * time.Hour,
				MaxPoints:   2016,
				Description: "5-minute bars",
			},
			"1h": {
				Table:       "ohlc_1h_v2",
				MinRange:    24 * time.Hour,
				MaxRange:    90 * 24 * time.Hour,
				MaxPoints:   2160,
				Description: "Hourly bars",
			},
			"4h": {
				Table:       "ohlc_4h_viewport",
				MinRange:    7 * 24 * time.Hour,
				MaxRange:    365 * 24 * time.Hour,
				MaxPoints:   2190,
				Description: "4-hour bars",
			},
			"1d": {
				Table:       "ohlc_1d_viewport",
				MinRange:    30 * 24 * time.Hour,
				MaxRange:    5 * 365 * 24 * time.Hour,
				MaxPoints:   1825,
				Description: "Daily bars",
			},
		},
	}

	return &ViewportService{
		pool:   pool,
		cache:  cache,
		config: defaultConfig,
	}
}

// SelectOptimalResolution picks the best resolution for a time range
func (v *ViewportService) SelectOptimalResolution(start, end time.Time) (string, config.ResolutionConfig) {
	duration := end.Sub(start)

	// Order matters - check from finest to coarsest
	resolutionOrder := []string{"1m", "5m", "1h", "4h", "1d"}

	for _, res := range resolutionOrder {
		cfg := v.config.Resolutions[res]
		if duration >= cfg.MinRange && duration <= cfg.MaxRange {
			log.Debug().
				Str("resolution", res).
				Dur("duration", duration).
				Str("table", cfg.Table).
				Msg("Selected optimal resolution")
			return res, cfg
		}
	}

	// Default to daily for very long ranges
	return "1d", v.config.Resolutions["1d"]
}

// GetSmartCandles retrieves candles with automatic resolution selection
func (v *ViewportService) GetSmartCandles(ctx context.Context, req models.CandleRequest) (*models.CandleResponse, error) {
	start := time.Now()

	// Select optimal resolution if not specified
	resolution := req.Resolution
	var resConfig config.ResolutionConfig
	
	if resolution == "" {
		resolution, resConfig = v.SelectOptimalResolution(req.Start, req.End)
	} else {
		var ok bool
		resConfig, ok = v.config.Resolutions[resolution]
		if !ok {
			return nil, fmt.Errorf("invalid resolution: %s", resolution)
		}
	}

	// Check cache first
	cacheKey := v.cache.GenerateKey(req.Symbol, resolution, req.Start, req.End)
	if cached, found := v.cache.Get(cacheKey); found {
		log.Debug().Str("cache_key", cacheKey).Msg("Cache hit")
		response := cached.(*models.CandleResponse)
		response.Metadata.CacheHit = true
		response.Metadata.QueryTimeMs = time.Since(start).Milliseconds()
		return response, nil
	}

	// Create data service to fetch candles
	dataService := NewDataService(v.pool)
	
	// Fetch candles with limit
	candles, err := dataService.GetCandles(ctx, req, resConfig.Table, resConfig.MaxPoints)
	if err != nil {
		return nil, fmt.Errorf("failed to get candles: %w", err)
	}

	// Build response
	response := &models.CandleResponse{
		Symbol:     req.Symbol,
		Timeframe:  req.Timeframe,
		Resolution: resolution,
		Start:      req.Start,
		End:        req.End,
		Count:      len(candles),
		Candles:    candles,
		Metadata: models.Metadata{
			TableUsed:      resConfig.Table,
			QueryTimeMs:    time.Since(start).Milliseconds(),
			CacheHit:       false,
			PointsReturned: len(candles),
			MaxPoints:      resConfig.MaxPoints,
			DataComplete:   len(candles) < resConfig.MaxPoints,
			DataSource:     "v2", // or from req.Source
			ServerTime:     time.Now().UTC(),
			TimeRange:      req.End.Sub(req.Start),
		},
	}

	// Generate next URL if data is incomplete
	if !response.Metadata.DataComplete && len(candles) > 0 {
		lastTime := candles[len(candles)-1].Timestamp
		response.Metadata.NextURL = fmt.Sprintf(
			"/api/v1/candles?symbol=%s&start=%s&end=%s&resolution=%s",
			req.Symbol,
			lastTime.Add(time.Second).Format(time.RFC3339),
			req.End.Format(time.RFC3339),
			resolution,
		)
	}

	// Cache the response
	v.cache.Set(cacheKey, response, v.getCacheTTL(req.End))

	return response, nil
}

// ExplainQuery explains what table and resolution would be used
func (v *ViewportService) ExplainQuery(req models.CandleRequest) *models.ExplainResponse {
	resolution, resConfig := v.SelectOptimalResolution(req.Start, req.End)
	
	// Calculate estimated points
	duration := req.End.Sub(req.Start)
	var estimatedPoints int
	
	switch resolution {
	case "1m":
		estimatedPoints = int(duration.Minutes())
	case "5m":
		estimatedPoints = int(duration.Minutes() / 5)
	case "1h":
		estimatedPoints = int(duration.Hours())
	case "4h":
		estimatedPoints = int(duration.Hours() / 4)
	case "1d":
		estimatedPoints = int(duration.Hours() / 24)
	}

	// Build alternatives
	alternatives := make([]models.ResolutionAlternative, 0)
	for res, cfg := range v.config.Resolutions {
		if res != resolution {
			alt := models.ResolutionAlternative{
				Resolution: res,
			}
			
			// Calculate points for this resolution
			switch res {
			case "1m":
				alt.EstimatedPoints = int(duration.Minutes())
			case "5m":
				alt.EstimatedPoints = int(duration.Minutes() / 5)
			case "1h":
				alt.EstimatedPoints = int(duration.Hours())
			case "4h":
				alt.EstimatedPoints = int(duration.Hours() / 4)
			case "1d":
				alt.EstimatedPoints = int(duration.Hours() / 24)
			}
			
			// Check if it's within range
			if duration >= cfg.MinRange && duration <= cfg.MaxRange {
				alt.Recommended = true
			}
			
			alternatives = append(alternatives, alt)
		}
	}

	return &models.ExplainResponse{
		Symbol:          req.Symbol,
		TimeRange:       duration,
		Resolution:      resolution,
		TableUsed:       resConfig.Table,
		EstimatedPoints: estimatedPoints,
		MaxAllowed:      resConfig.MaxPoints,
		Reason:          fmt.Sprintf("Selected %s resolution for %.0f hour range", resolution, duration.Hours()),
		Alternatives:    alternatives,
	}
}

// GetDataContract returns the current data contract
func (v *ViewportService) GetDataContract() *models.DataContract {
	resolutions := make(map[string]models.ResolutionContract)
	
	for res, cfg := range v.config.Resolutions {
		resolutions[res] = models.ResolutionContract{
			Resolution:  res,
			MinRangeMs:  cfg.MinRange.Milliseconds(),
			MaxRangeMs:  cfg.MaxRange.Milliseconds(),
			MaxPoints:   cfg.MaxPoints,
			Table:       cfg.Table,
			Description: cfg.Description,
			Recommended: v.getRecommendation(res),
		}
	}

	return &models.DataContract{
		MaxPointsPerRequest: v.config.MaxPointsPerRequest,
		Resolutions:         resolutions,
		PerformanceTargets: models.PerformanceTargets{
			ExcellentMs:  50,
			GoodMs:       100,
			AcceptableMs: 500,
		},
		Version:   "1.0.0",
		Generated: time.Now().UTC(),
	}
}

// getCacheTTL determines cache duration based on data recency
func (v *ViewportService) getCacheTTL(endTime time.Time) time.Duration {
	age := time.Since(endTime)
	
	if age < 1*time.Hour {
		return 10 * time.Second // Recent data
	} else if age < 24*time.Hour {
		return 1 * time.Minute // Today's data
	} else {
		return 5 * time.Minute // Historical data
	}
}

// getRecommendation provides usage recommendation for resolution
func (v *ViewportService) getRecommendation(resolution string) string {
	switch resolution {
	case "1m":
		return "Scalping and micro-movements"
	case "5m":
		return "Intraday trading"
	case "1h":
		return "Day trading and short-term analysis"
	case "4h":
		return "Swing trading"
	case "1d":
		return "Position trading and long-term trends"
	default:
		return "General analysis"
	}
}