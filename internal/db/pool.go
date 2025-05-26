package db

import (
	"context"
	"fmt"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/rs/zerolog/log"
	"github.com/sptrader/sptrader/internal/config"
)

// Pool wraps pgxpool with additional functionality
type Pool struct {
	*pgxpool.Pool
	config config.DatabaseConfig
}

// NewPool creates a new database connection pool
func NewPool(cfg config.DatabaseConfig) (*Pool, error) {
	poolConfig, err := pgxpool.ParseConfig(cfg.URL)
	if err != nil {
		return nil, fmt.Errorf("failed to parse database URL: %w", err)
	}

	// Configure pool
	poolConfig.MaxConns = cfg.MaxConnections
	poolConfig.MinConns = cfg.MinConnections
	poolConfig.MaxConnLifetime = cfg.MaxConnLifetime
	poolConfig.HealthCheckPeriod = 30 * time.Second

	// Set up hooks for logging
	poolConfig.BeforeAcquire = func(ctx context.Context, conn *pgx.Conn) bool {
		log.Debug().Msg("Acquiring database connection")
		return true
	}

	poolConfig.AfterRelease = func(conn *pgx.Conn) bool {
		log.Debug().Msg("Released database connection")
		return true
	}

	// Create pool
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	pool, err := pgxpool.NewWithConfig(ctx, poolConfig)
	if err != nil {
		return nil, fmt.Errorf("failed to create connection pool: %w", err)
	}

	// Test connection
	if err := pool.Ping(ctx); err != nil {
		pool.Close()
		return nil, fmt.Errorf("failed to ping database: %w", err)
	}

	log.Info().
		Int32("max_connections", cfg.MaxConnections).
		Int32("min_connections", cfg.MinConnections).
		Msg("Database pool initialized")

	return &Pool{
		Pool:   pool,
		config: cfg,
	}, nil
}

// Stats returns current pool statistics
func (p *Pool) Stats() *pgxpool.Stat {
	return p.Pool.Stat()
}

// HealthCheck performs a health check on the database
func (p *Pool) HealthCheck(ctx context.Context) error {
	ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()

	var result int
	err := p.QueryRow(ctx, "SELECT 1").Scan(&result)
	if err != nil {
		return fmt.Errorf("health check failed: %w", err)
	}

	if result != 1 {
		return fmt.Errorf("unexpected health check result: %d", result)
	}

	return nil
}

// WithTimeout executes a function with a timeout
func (p *Pool) WithTimeout(timeout time.Duration, fn func(context.Context) error) error {
	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()
	return fn(ctx)
}