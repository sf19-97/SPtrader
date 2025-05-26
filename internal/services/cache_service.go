package services

import (
	"crypto/md5"
	"encoding/hex"
	"fmt"
	"sync"
	"time"

	"github.com/rs/zerolog/log"
	"github.com/sptrader/sptrader/internal/config"
)

// CacheEntry represents a cached item
type CacheEntry struct {
	Data      interface{}
	ExpiresAt time.Time
	Size      int64
}

// CacheService provides in-memory caching
type CacheService struct {
	mu          sync.RWMutex
	items       map[string]*CacheEntry
	maxSize     int
	currentSize int
	stats       CacheStats
	config      config.CacheConfig
}

// CacheStats tracks cache performance
type CacheStats struct {
	Hits      int64
	Misses    int64
	Evictions int64
	Size      int
}

// NewCacheService creates a new cache service
func NewCacheService(cfg config.CacheConfig) *CacheService {
	return &CacheService{
		items:   make(map[string]*CacheEntry),
		maxSize: cfg.MaxSize,
		config:  cfg,
	}
}

// Get retrieves an item from cache
func (c *CacheService) Get(key string) (interface{}, bool) {
	c.mu.RLock()
	entry, exists := c.items[key]
	c.mu.RUnlock()

	if !exists {
		c.incrementMisses()
		return nil, false
	}

	// Check expiration
	if time.Now().After(entry.ExpiresAt) {
		c.Delete(key)
		c.incrementMisses()
		return nil, false
	}

	c.incrementHits()
	return entry.Data, true
}

// Set adds an item to cache
func (c *CacheService) Set(key string, data interface{}, ttl time.Duration) {
	entry := &CacheEntry{
		Data:      data,
		ExpiresAt: time.Now().Add(ttl),
		Size:      1, // Simplified size calculation
	}

	c.mu.Lock()
	defer c.mu.Unlock()

	// Check if we need to evict items
	if len(c.items) >= c.maxSize {
		c.evictOldest()
	}

	c.items[key] = entry
	c.currentSize = len(c.items)
	c.stats.Size = c.currentSize

	log.Debug().
		Str("key", key).
		Time("expires_at", entry.ExpiresAt).
		Msg("Added item to cache")
}

// Delete removes an item from cache
func (c *CacheService) Delete(key string) {
	c.mu.Lock()
	defer c.mu.Unlock()

	delete(c.items, key)
	c.currentSize = len(c.items)
	c.stats.Size = c.currentSize
}

// Clear removes all items from cache
func (c *CacheService) Clear() {
	c.mu.Lock()
	defer c.mu.Unlock()

	c.items = make(map[string]*CacheEntry)
	c.currentSize = 0
	c.stats.Size = 0
}

// GenerateKey creates a cache key from parameters
func (c *CacheService) GenerateKey(symbol, resolution string, start, end time.Time) string {
	key := fmt.Sprintf("%s:%s:%d:%d", symbol, resolution, start.Unix(), end.Unix())
	hash := md5.Sum([]byte(key))
	return hex.EncodeToString(hash[:])
}

// GetStats returns cache statistics
func (c *CacheService) GetStats() CacheStats {
	c.mu.RLock()
	defer c.mu.RUnlock()

	stats := c.stats
	stats.Size = len(c.items)
	
	// Calculate hit rate
	total := stats.Hits + stats.Misses
	if total > 0 {
		hitRate := float64(stats.Hits) / float64(total) * 100
		log.Debug().
			Int64("hits", stats.Hits).
			Int64("misses", stats.Misses).
			Float64("hit_rate", hitRate).
			Msg("Cache statistics")
	}

	return stats
}

// evictOldest removes the oldest cache entry
func (c *CacheService) evictOldest() {
	var oldestKey string
	var oldestTime time.Time

	// Find oldest entry
	for key, entry := range c.items {
		if oldestKey == "" || entry.ExpiresAt.Before(oldestTime) {
			oldestKey = key
			oldestTime = entry.ExpiresAt
		}
	}

	if oldestKey != "" {
		delete(c.items, oldestKey)
		c.stats.Evictions++
		log.Debug().
			Str("key", oldestKey).
			Msg("Evicted cache entry")
	}
}

// incrementHits safely increments hit counter
func (c *CacheService) incrementHits() {
	c.mu.Lock()
	c.stats.Hits++
	c.mu.Unlock()
}

// incrementMisses safely increments miss counter
func (c *CacheService) incrementMisses() {
	c.mu.Lock()
	c.stats.Misses++
	c.mu.Unlock()
}

// CleanupExpired removes expired entries
func (c *CacheService) CleanupExpired() {
	c.mu.Lock()
	defer c.mu.Unlock()

	now := time.Now()
	for key, entry := range c.items {
		if now.After(entry.ExpiresAt) {
			delete(c.items, key)
			log.Debug().
				Str("key", key).
				Msg("Removed expired cache entry")
		}
	}

	c.currentSize = len(c.items)
	c.stats.Size = c.currentSize
}

// StartCleanupRoutine starts a background cleanup goroutine
func (c *CacheService) StartCleanupRoutine() {
	go func() {
		ticker := time.NewTicker(1 * time.Minute)
		defer ticker.Stop()

		for range ticker.C {
			c.CleanupExpired()
		}
	}()
}