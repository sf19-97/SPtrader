package api

import (
	"time"

	"github.com/gin-gonic/gin"
	"github.com/rs/zerolog/log"
)

// LoggerMiddleware logs HTTP requests
func LoggerMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		start := time.Now()
		path := c.Request.URL.Path
		raw := c.Request.URL.RawQuery

		// Process request
		c.Next()

		// Log request details
		latency := time.Since(start)
		clientIP := c.ClientIP()
		method := c.Request.Method
		statusCode := c.Writer.Status()

		if raw != "" {
			path = path + "?" + raw
		}

		switch {
		case statusCode >= 500:
			log.Error().
				Str("method", method).
				Str("path", path).
				Int("status", statusCode).
				Str("ip", clientIP).
				Dur("latency", latency).
				Msg("Server error")
		case statusCode >= 400:
			log.Warn().
				Str("method", method).
				Str("path", path).
				Int("status", statusCode).
				Str("ip", clientIP).
				Dur("latency", latency).
				Msg("Client error")
		default:
			log.Info().
				Str("method", method).
				Str("path", path).
				Int("status", statusCode).
				Str("ip", clientIP).
				Dur("latency", latency).
				Msg("Request processed")
		}
	}
}

// CORSMiddleware handles CORS headers
func CORSMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		c.Writer.Header().Set("Access-Control-Allow-Origin", "*")
		c.Writer.Header().Set("Access-Control-Allow-Credentials", "true")
		c.Writer.Header().Set("Access-Control-Allow-Headers", "Content-Type, Content-Length, Accept-Encoding, X-CSRF-Token, Authorization, accept, origin, Cache-Control, X-Requested-With")
		c.Writer.Header().Set("Access-Control-Allow-Methods", "POST, OPTIONS, GET, PUT, DELETE")

		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(204)
			return
		}

		c.Next()
	}
}

// RateLimitMiddleware implements rate limiting
func RateLimitMiddleware(requestsPerMinute int) gin.HandlerFunc {
	// This would implement actual rate limiting
	// For now, just pass through
	return func(c *gin.Context) {
		c.Next()
	}
}

// MetricsMiddleware collects request metrics
func MetricsMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		start := time.Now()
		
		c.Next()
		
		// Would update metrics here
		duration := time.Since(start)
		_ = duration // Use this for metrics
	}
}