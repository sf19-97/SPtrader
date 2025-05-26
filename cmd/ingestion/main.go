package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"net/http"
	"os"
	"time"

	qdb "github.com/questdb/go-questdb-client/v3"
)

// Tick represents a single market data tick
type Tick struct {
	Timestamp      time.Time `json:"timestamp"`
	Symbol         string    `json:"symbol"`
	Bid            float64   `json:"bid"`
	Ask            float64   `json:"ask"`
	Price          float64   `json:"price"`
	Spread         float64   `json:"spread"`
	Volume         float64   `json:"volume"`
	BidVolume      float64   `json:"bid_volume"`
	AskVolume      float64   `json:"ask_volume"`
	HourOfDay      int       `json:"hour_of_day"`
	DayOfWeek      int       `json:"day_of_week"`
	TradingSession string    `json:"trading_session"`
	MarketOpen     bool      `json:"market_open"`
}

func main() {
	var (
		ilpAddr    = flag.String("ilp", "localhost:9009", "QuestDB ILP address")
		httpAddr   = flag.String("http", "localhost:9000", "QuestDB HTTP address")
		jsonFile   = flag.String("file", "", "JSON file with tick data to import")
		pythonMode = flag.Bool("python", false, "Accept data from Python script via stdin")
		testMode   = flag.Bool("test", false, "Generate and insert test data")
	)
	flag.Parse()

	log.Printf("Starting ILP ingestion service...")
	log.Printf("ILP endpoint: %s", *ilpAddr)

	// Create ILP sender with TCP
	ctx := context.Background()
	sender, err := qdb.NewLineSender(ctx, qdb.WithTcp(), qdb.WithAddress(*ilpAddr))
	if err != nil {
		log.Fatalf("Failed to create ILP sender: %v", err)
	}
	defer sender.Close(ctx)

	log.Printf("Connected to QuestDB ILP at %s", *ilpAddr)

	// Choose mode
	if *testMode {
		if err := generateTestData(ctx, sender); err != nil {
			log.Fatalf("Failed to generate test data: %v", err)
		}
	} else if *jsonFile != "" {
		if err := importFromFile(ctx, sender, *jsonFile); err != nil {
			log.Fatalf("Failed to import from file: %v", err)
		}
	} else if *pythonMode {
		if err := importFromStdin(ctx, sender); err != nil {
			log.Fatalf("Failed to import from stdin: %v", err)
		}
	} else {
		log.Fatal("Please specify -test, -file, or -python mode")
	}

	// Verify data was inserted
	if err := verifyData(*httpAddr); err != nil {
		log.Printf("Warning: Failed to verify data: %v", err)
	}
}

func generateTestData(ctx context.Context, sender qdb.LineSender) error {
	log.Println("Generating test data...")
	
	// Generate 1 hour of test data
	baseTime := time.Date(2024, 1, 19, 10, 0, 0, 0, time.UTC)
	basePrice := 1.08825
	tickCount := 0
	
	for i := 0; i < 3600; i += 1 { // One tick per second for an hour
		timestamp := baseTime.Add(time.Duration(i) * time.Second)
		
		// Simulate realistic price movement
		spread := 0.00002 + (float64(i%10) * 0.000001)
		bid := basePrice + (float64(i%60-30) * 0.00001)
		ask := bid + spread
		price := (bid + ask) / 2
		volume := 1.0 + float64(i%5)
		
		err := sender.
			Table("market_data_v2").
			Symbol("symbol", "EURUSD").
			Float64Column("bid", bid).
			Float64Column("ask", ask).
			Float64Column("price", price).
			Float64Column("spread", spread).
			Float64Column("volume", volume).
			Float64Column("bid_volume", volume*0.6).
			Float64Column("ask_volume", volume*0.4).
			Int64Column("hour_of_day", int64(timestamp.Hour())).
			Int64Column("day_of_week", int64(timestamp.Weekday())).
			StringColumn("trading_session", "LONDON").
			BoolColumn("market_open", true).
			At(ctx, timestamp)
		
		if err != nil {
			return fmt.Errorf("failed to send tick %d: %w", i, err)
		}
		
		tickCount++
		
		// Flush every 1000 ticks
		if tickCount%1000 == 0 {
			if err := sender.Flush(ctx); err != nil {
				return fmt.Errorf("failed to flush at tick %d: %w", tickCount, err)
			}
			log.Printf("Inserted %d ticks...", tickCount)
		}
	}
	
	// Final flush
	if err := sender.Flush(ctx); err != nil {
		return fmt.Errorf("failed to final flush: %w", err)
	}
	
	log.Printf("Successfully generated and inserted %d test ticks", tickCount)
	return nil
}

func importFromFile(ctx context.Context, sender qdb.LineSender, filename string) error {
	log.Printf("Importing from file: %s", filename)
	
	data, err := os.ReadFile(filename)
	if err != nil {
		return fmt.Errorf("failed to read file: %w", err)
	}
	
	var ticks []Tick
	if err := json.Unmarshal(data, &ticks); err != nil {
		return fmt.Errorf("failed to parse JSON: %w", err)
	}
	
	return insertTicks(ctx, sender, ticks)
}

func importFromStdin(ctx context.Context, sender qdb.LineSender) error {
	log.Println("Reading tick data from stdin...")
	
	decoder := json.NewDecoder(os.Stdin)
	var ticks []Tick
	
	if err := decoder.Decode(&ticks); err != nil {
		return fmt.Errorf("failed to decode JSON from stdin: %w", err)
	}
	
	return insertTicks(ctx, sender, ticks)
}

func insertTicks(ctx context.Context, sender qdb.LineSender, ticks []Tick) error {
	log.Printf("Inserting %d ticks via ILP...", len(ticks))
	
	for i, tick := range ticks {
		err := sender.
			Table("market_data_v2").
			Symbol("symbol", tick.Symbol).
			Float64Column("bid", tick.Bid).
			Float64Column("ask", tick.Ask).
			Float64Column("price", tick.Price).
			Float64Column("spread", tick.Spread).
			Float64Column("volume", tick.Volume).
			Float64Column("bid_volume", tick.BidVolume).
			Float64Column("ask_volume", tick.AskVolume).
			Int64Column("hour_of_day", int64(tick.HourOfDay)).
			Int64Column("day_of_week", int64(tick.DayOfWeek)).
			StringColumn("trading_session", tick.TradingSession).
			BoolColumn("market_open", tick.MarketOpen).
			At(ctx, tick.Timestamp)
		
		if err != nil {
			return fmt.Errorf("failed to send tick %d: %w", i, err)
		}
		
		// Flush every 1000 ticks
		if (i+1)%1000 == 0 {
			if err := sender.Flush(ctx); err != nil {
				return fmt.Errorf("failed to flush at tick %d: %w", i+1, err)
			}
			log.Printf("Inserted %d/%d ticks...", i+1, len(ticks))
		}
	}
	
	// Final flush
	if err := sender.Flush(ctx); err != nil {
		return fmt.Errorf("failed to final flush: %w", err)
	}
	
	log.Printf("Successfully inserted %d ticks", len(ticks))
	return nil
}

func verifyData(httpAddr string) error {
	// Query QuestDB to verify data was inserted
	url := fmt.Sprintf("http://%s/exec?query=SELECT%%20count(*)%%20FROM%%20market_data_v2", httpAddr)
	
	resp, err := http.Get(url)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	
	var result struct {
		Dataset [][]interface{} `json:"dataset"`
	}
	
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return err
	}
	
	if len(result.Dataset) > 0 && len(result.Dataset[0]) > 0 {
		count := result.Dataset[0][0]
		log.Printf("✅ Verification: %v records in market_data_v2", count)
	}
	
	return nil
}