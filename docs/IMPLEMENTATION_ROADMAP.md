# SPtrader Implementation Roadmap
*Data-First Approach - May 25, 2025*

## 🎯 Core Philosophy
**Profile your data limits first, then build UI to respect those limits**

This is how professional trading platforms like TradingView work - the chart behavior is shaped by data capabilities, not the other way around.

## 📊 Phase 1: Data Profiling (Current Phase)

### Immediate Actions
```bash
# 1. Fix known issue
./tools/fix_data_source_column.sh

# 2. Load test data (1 week EURUSD)
sptrader start
cd data_feeds
python dukascopy_importer.py

# 3. Profile performance
cd ../tools
python profile_data_limits.py
```

### Deliverables
- `data_contract.json` - Performance boundaries
- `data_contract.ts` - TypeScript interface
- Clear understanding of query limits

## 🚀 Phase 2: API Enhancement

### Option A: Enhance Python (Recommended Start)
```python
# Add to api/main.py
- Smart resolution selection
- Viewport-aware queries  
- Query explanation endpoint
- Metadata in responses
```

### Option B: Go Sidecar (If Needed)
```go
// Only if Python proves too slow
- Dedicated data service
- Type-safe contracts
- Superior concurrency
```

## 💹 Phase 3: Frontend Implementation

### Data-Aware Chart Manager
```javascript
class ChartDataManager {
    constructor(dataContract) {
        this.contract = dataContract;
        this.cache = new LRUCache();
    }
    
    async loadViewport(timeRange) {
        // Respects data contract limits
        const resolution = this.selectOptimalResolution(timeRange);
        const data = await this.fetchWithContract(timeRange, resolution);
        return this.prepareForChart(data);
    }
}
```

### Chart Integration
- Lightweight-charts for rendering
- Viewport-aware data loading
- Smooth pan/zoom within limits
- Preloading adjacent data

## 🧪 Phase 4: Testing & Optimization

### Progressive Testing
1. **1 week data** → Establish baseline
2. **1 month data** → Check scaling
3. **1 year data** → Find breaking points
4. **Multi-symbol** → Test concurrency

### Performance Metrics
- Query response times
- Cache hit rates
- Frontend FPS during pan/zoom
- Memory usage patterns

## 🏁 Phase 5: Production

### Prerequisites
- [ ] All viewport tables optimized
- [ ] API respects data contracts
- [ ] Frontend handles all edge cases
- [ ] Performance meets targets

### Deployment
- Systemd services
- Nginx reverse proxy
- SSL certificates
- Monitoring setup

## 📝 Key Decisions

### Language Choice
**Start with Python because:**
- Already implemented
- asyncpg is fast enough
- Simpler deployment
- Can add Go later if needed

### Data Contract Enforcement
**Backend-driven because:**
- Single source of truth
- Frontend can't make bad queries
- Performance guaranteed
- Easy to update limits

### Caching Strategy
**LRU with prefetch because:**
- Most queries are pan/zoom
- Adjacent data likely needed
- Memory efficient
- Good cache hit rates

## 🎯 Success Metrics

1. **Performance**
   - 95% of queries < 100ms
   - Cache hit rate > 70%
   - 60fps pan/zoom

2. **Scalability**
   - Handles 5 years of minute data
   - Supports 10+ concurrent charts
   - Memory usage < 1GB

3. **User Experience**
   - No loading spinners during pan
   - Instant timeframe switches
   - Smooth zoom transitions

## 🚨 Common Pitfalls to Avoid

1. **Building UI first** - Always profile data first
2. **Unlimited queries** - Enforce hard limits
3. **Ignoring viewport tables** - Use them!
4. **Over-engineering** - Start simple, optimize later
5. **Premature Go adoption** - Python might be enough

## 📚 Reference Implementation

Your Go approach is excellent for understanding the pattern:
- Profile tables first
- Build contracts from results
- Frontend respects contracts
- Monitor actual performance

Whether you implement in Python or Go, the pattern remains the same!

---

**Remember**: TradingView didn't build charts then figure out data. They figured out data, then built charts that work within those limits. Follow their lead!