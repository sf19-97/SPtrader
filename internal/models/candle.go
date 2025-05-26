package models

import (
	"time"
)

// Candle represents OHLC data
type Candle struct {
	Timestamp time.Time `json:"timestamp"`
	Open      float64   `json:"open"`
	High      float64   `json:"high"`
	Low       float64   `json:"low"`
	Close     float64   `json:"close"`
	Volume    float64   `json:"volume"`
}

// CandleRequest represents a request for candle data
type CandleRequest struct {
	Symbol     string    `form:"symbol" binding:"required"`
	Timeframe  string    `form:"tf"`
	Start      time.Time `form:"start" binding:"required" time_format:"2006-01-02T15:04:05Z"`
	End        time.Time `form:"end" binding:"required" time_format:"2006-01-02T15:04:05Z"`
	Resolution string    `form:"resolution"`
	Source     string    `form:"source"` // "v1" or "v2", default "v2"
}

// CandleResponse represents the response containing candles
type CandleResponse struct {
	Symbol     string    `json:"symbol"`
	Timeframe  string    `json:"timeframe"`
	Resolution string    `json:"resolution"`
	Start      time.Time `json:"start"`
	End        time.Time `json:"end"`
	Count      int       `json:"count"`
	Candles    []Candle  `json:"candles"`
	Metadata   Metadata  `json:"metadata"`
}

// Metadata provides additional information about the query
type Metadata struct {
	TableUsed      string        `json:"table_used"`
	QueryTimeMs    int64         `json:"query_time_ms"`
	CacheHit       bool          `json:"cache_hit"`
	PointsReturned int           `json:"points_returned"`
	MaxPoints      int           `json:"max_points"`
	DataComplete   bool          `json:"data_complete"`
	NextURL        string        `json:"next_url,omitempty"`
	DataSource     string        `json:"data_source"`
	ServerTime     time.Time     `json:"server_time"`
	TimeRange      time.Duration `json:"time_range"`
}

// ExplainResponse explains query planning
type ExplainResponse struct {
	Symbol       string                 `json:"symbol"`
	TimeRange    time.Duration          `json:"time_range"`
	Resolution   string                 `json:"resolution"`
	TableUsed    string                 `json:"table_used"`
	EstimatedPoints int                 `json:"estimated_points"`
	MaxAllowed   int                    `json:"max_allowed"`
	Reason       string                 `json:"reason"`
	Alternatives []ResolutionAlternative `json:"alternatives"`
}

// ResolutionAlternative provides other resolution options
type ResolutionAlternative struct {
	Resolution      string `json:"resolution"`
	EstimatedPoints int    `json:"estimated_points"`
	Recommended     bool   `json:"recommended"`
}

// Symbol represents a trading pair
type Symbol struct {
	Symbol      string    `json:"symbol"`
	Description string    `json:"description"`
	BaseCurrency string   `json:"base_currency"`
	QuoteCurrency string  `json:"quote_currency"`
	MinSize     float64   `json:"min_size"`
	TickSize    float64   `json:"tick_size"`
	LastUpdate  time.Time `json:"last_update"`
}

// DataContract represents the performance contract
type DataContract struct {
	MaxPointsPerRequest int                          `json:"max_points_per_request"`
	Resolutions         map[string]ResolutionContract `json:"resolutions"`
	PerformanceTargets  PerformanceTargets           `json:"performance_targets"`
	Version             string                       `json:"version"`
	Generated           time.Time                    `json:"generated"`
}

// ResolutionContract defines limits for a specific resolution
type ResolutionContract struct {
	Resolution   string `json:"resolution"`
	MinRangeMs   int64  `json:"min_range_ms"`
	MaxRangeMs   int64  `json:"max_range_ms"`
	MaxPoints    int    `json:"max_points"`
	Table        string `json:"table"`
	Description  string `json:"description"`
	Recommended  string `json:"recommended_for"`
}

// PerformanceTargets defines performance goals
type PerformanceTargets struct {
	ExcellentMs  int `json:"excellent_ms"`
	GoodMs       int `json:"good_ms"`
	AcceptableMs int `json:"acceptable_ms"`
}

// Stats represents API statistics
type Stats struct {
	Uptime          time.Duration     `json:"uptime"`
	TotalRequests   int64             `json:"total_requests"`
	AverageLatency  float64           `json:"average_latency_ms"`
	ActiveQueries   int               `json:"active_queries"`
	DatabasePool    DatabasePoolStats `json:"database_pool"`
	Cache           CacheStats        `json:"cache"`
	LastError       *ErrorInfo        `json:"last_error,omitempty"`
}

// DatabasePoolStats shows database connection pool status
type DatabasePoolStats struct {
	TotalConnections   int32 `json:"total_connections"`
	IdleConnections    int32 `json:"idle_connections"`
	ActiveConnections  int32 `json:"active_connections"`
	MaxConnections     int32 `json:"max_connections"`
	WaitCount          int64 `json:"wait_count"`
	WaitDuration       int64 `json:"wait_duration_ms"`
}

// CacheStats shows cache performance
type CacheStats struct {
	Size        int     `json:"size"`
	MaxSize     int     `json:"max_size"`
	Hits        int64   `json:"hits"`
	Misses      int64   `json:"misses"`
	HitRate     float64 `json:"hit_rate"`
	Evictions   int64   `json:"evictions"`
	MemoryUsage int64   `json:"memory_bytes"`
}

// ErrorInfo provides error details
type ErrorInfo struct {
	Code      string    `json:"code"`
	Message   string    `json:"message"`
	Timestamp time.Time `json:"timestamp"`
	Count     int       `json:"count"`
}