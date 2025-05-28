package main

import (
	"context"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/rs/zerolog"
	"github.com/rs/zerolog/log"
	"github.com/sptrader/sptrader/internal/api"
	"github.com/sptrader/sptrader/internal/config"
	"github.com/sptrader/sptrader/internal/db"
	"github.com/sptrader/sptrader/internal/services"
)

func main() {
	// Setup logging
	zerolog.TimeFieldFormat = zerolog.TimeFormatUnix
	log.Logger = log.Output(zerolog.ConsoleWriter{Out: os.Stderr})

	// Load configuration
	cfg, err := config.Load()
	if err != nil {
		log.Fatal().Err(err).Msg("Failed to load config")
	}

	// Initialize database
	dbPool, err := db.NewPool(cfg.Database)
	if err != nil {
		log.Fatal().Err(err).Msg("Failed to connect to database")
	}
	defer dbPool.Close()

	// Initialize services
	dataService := services.NewDataService(dbPool)
	cacheService := services.NewCacheService(cfg.Cache)
	viewportService := services.NewViewportService(dbPool, cacheService)
	dataManager := services.NewDataManager(dbPool)

	// Setup Gin
	if cfg.Server.Mode == "production" {
		gin.SetMode(gin.ReleaseMode)
	}

	router := gin.New()
	router.Use(gin.Recovery())
	router.Use(api.LoggerMiddleware())
	router.Use(api.CORSMiddleware())

	// Initialize handlers
	handlers := api.NewHandlers(dataService, viewportService, dataManager)

	// Routes
	v1 := router.Group("/api/v1")
	{
		// Health check
		v1.GET("/health", handlers.Health)
		
		// Data endpoints
		v1.GET("/candles", handlers.GetCandles)
		v1.GET("/candles/smart", handlers.GetSmartCandles)
		v1.GET("/candles/explain", handlers.ExplainQuery)
		
		// Market data
		v1.GET("/symbols", handlers.GetSymbols)
		v1.GET("/timeframes", handlers.GetTimeframes)
		v1.GET("/data/range", handlers.GetDataRange)
		
		// Stats
		v1.GET("/stats", handlers.GetStats)
		v1.GET("/stats/cache", handlers.GetCacheStats)
		
		// Data contract
		v1.GET("/contract", handlers.GetDataContract)
		
		// Lazy loading endpoints
		v1.GET("/data/check", handlers.CheckDataAvailability)
		v1.POST("/data/ensure", handlers.EnsureData)
		v1.GET("/data/status", handlers.GetDataStatus)
		v1.GET("/candles/lazy", handlers.GetCandlesWithLazyLoad)
	}

	// Setup server
	srv := &http.Server{
		Addr:         cfg.Server.Address,
		Handler:      router,
		ReadTimeout:  cfg.Server.ReadTimeout,
		WriteTimeout: cfg.Server.WriteTimeout,
	}

	// Start server
	go func() {
		log.Info().Str("address", cfg.Server.Address).Msg("Starting server")
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatal().Err(err).Msg("Failed to start server")
		}
	}()

	// Wait for interrupt signal
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Info().Msg("Shutting down server...")

	// Graceful shutdown
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := srv.Shutdown(ctx); err != nil {
		log.Fatal().Err(err).Msg("Server forced to shutdown")
	}

	log.Info().Msg("Server exited")
}