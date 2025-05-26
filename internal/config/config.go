package config

import (
	"os"
	"time"

	"github.com/joho/godotenv"
)

type Config struct {
	Server   ServerConfig
	Database DatabaseConfig
	Cache    CacheConfig
	Data     DataConfig
}

type ServerConfig struct {
	Address      string
	Mode         string // "debug" or "production"
	ReadTimeout  time.Duration
	WriteTimeout time.Duration
}

type DatabaseConfig struct {
	URL             string
	MaxConnections  int32
	MinConnections  int32
	MaxConnLifetime time.Duration
}

type CacheConfig struct {
	MaxSize      int
	TTL          time.Duration
	HistoricalTTL time.Duration
	RecentTTL    time.Duration
}

type DataConfig struct {
	MaxPointsPerRequest int
	Resolutions         map[string]ResolutionConfig
}

type ResolutionConfig struct {
	Table        string
	MinRange     time.Duration
	MaxRange     time.Duration
	MaxPoints    int
	Description  string
}

func Load() (*Config, error) {
	// Load .env file if it exists
	_ = godotenv.Load()

	cfg := &Config{
		Server: ServerConfig{
			Address:      getEnv("SERVER_ADDRESS", ":8080"),
			Mode:         getEnv("GIN_MODE", "debug"),
			ReadTimeout:  getDuration("SERVER_READ_TIMEOUT", 10*time.Second),
			WriteTimeout: getDuration("SERVER_WRITE_TIMEOUT", 10*time.Second),
		},
		Database: DatabaseConfig{
			URL:             getEnv("DATABASE_URL", "postgres://admin:quest@localhost:8812/qdb"),
			MaxConnections:  getInt32("DB_MAX_CONNECTIONS", 20),
			MinConnections:  getInt32("DB_MIN_CONNECTIONS", 5),
			MaxConnLifetime: getDuration("DB_MAX_CONN_LIFETIME", 1*time.Hour),
		},
		Cache: CacheConfig{
			MaxSize:       getInt("CACHE_MAX_SIZE", 1000),
			TTL:           getDuration("CACHE_TTL", 5*time.Minute),
			HistoricalTTL: getDuration("CACHE_HISTORICAL_TTL", 5*time.Minute),
			RecentTTL:     getDuration("CACHE_RECENT_TTL", 10*time.Second),
		},
		Data: DataConfig{
			MaxPointsPerRequest: getInt("MAX_POINTS_PER_REQUEST", 10000),
			Resolutions: map[string]ResolutionConfig{
				"1m": {
					Table:       "ohlc_1m_v2",
					MinRange:    1 * time.Hour,
					MaxRange:    24 * time.Hour,
					MaxPoints:   1440,
					Description: "1-minute bars for intraday analysis",
				},
				"5m": {
					Table:       "ohlc_5m_v2",
					MinRange:    4 * time.Hour,
					MaxRange:    7 * 24 * time.Hour,
					MaxPoints:   2016,
					Description: "5-minute bars for short-term trading",
				},
				"15m": {
					Table:       "ohlc_15m_v2",
					MinRange:    12 * time.Hour,
					MaxRange:    30 * 24 * time.Hour,
					MaxPoints:   2880,
					Description: "15-minute bars for day trading",
				},
				"30m": {
					Table:       "ohlc_30m_v2",
					MinRange:    24 * time.Hour,
					MaxRange:    60 * 24 * time.Hour,
					MaxPoints:   2880,
					Description: "30-minute bars for swing trading",
				},
				"1h": {
					Table:       "ohlc_1h_v2",
					MinRange:    2 * 24 * time.Hour,
					MaxRange:    90 * 24 * time.Hour,
					MaxPoints:   2160,
					Description: "Hourly bars for position trading",
				},
				"4h": {
					Table:       "ohlc_4h_viewport",
					MinRange:    7 * 24 * time.Hour,
					MaxRange:    365 * 24 * time.Hour,
					MaxPoints:   2190,
					Description: "4-hour bars for trend analysis",
				},
				"1d": {
					Table:       "ohlc_1d_viewport",
					MinRange:    30 * 24 * time.Hour,
					MaxRange:    5 * 365 * 24 * time.Hour,
					MaxPoints:   1825,
					Description: "Daily bars for long-term analysis",
				},
			},
		},
	}

	return cfg, nil
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func getInt(key string, defaultValue int) int {
	// Implementation would parse env var to int
	return defaultValue
}

func getInt32(key string, defaultValue int32) int32 {
	// Implementation would parse env var to int32
	return defaultValue
}

func getDuration(key string, defaultValue time.Duration) time.Duration {
	// Implementation would parse env var to duration
	return defaultValue
}