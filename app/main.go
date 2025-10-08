package main

import (
  "fmt"
  "log"
  "math/rand"
  "net/http"
  "os"
  "strconv"
  "time"

  "github.com/prometheus/client_golang/prometheus"
  "github.com/prometheus/client_golang/prometheus/promhttp"
)

var (
  reqDur = prometheus.NewHistogramVec(
    prometheus.HistogramOpts{
      Name:    "http_server_request_duration_seconds",
      Help:    "Request duration",
      Buckets: prometheus.DefBuckets,
    },
    []string{"method", "path", "code"},
  )
  reqCnt = prometheus.NewCounterVec(
    prometheus.CounterOpts{
      Name: "http_server_requests_total",
      Help: "Request count",
    },
    []string{"method", "path", "code"},
  )
)

func handler(w http.ResponseWriter, r *http.Request) {
  start := time.Now()
  code := 200

  baseMs, _ := strconv.Atoi(getEnv("LATENCY_MS", "50"))
  jitter := rand.Intn(200)
  time.Sleep(time.Duration(baseMs+jitter) * time.Millisecond)

  errPct, _ := strconv.Atoi(getEnv("ERROR_PCT", "0"))
  if rand.Intn(100) < errPct {
    code = 500
    w.WriteHeader(code)
    fmt.Fprintf(w, "oops")
  } else {
    fmt.Fprintf(w, "ok")
  }

  dur := time.Since(start).Seconds()
  labels := prometheus.Labels{"method": r.Method, "path": "/", "code": fmt.Sprintf("%d", code)}
  reqDur.With(labels).Observe(dur)
  reqCnt.With(labels).Inc()
}

func main() {
  rand.Seed(time.Now().UnixNano())

  // register metrics and handlers
  prometheus.MustRegister(reqDur, reqCnt)
  http.HandleFunc("/", handler)
  http.Handle("/metrics", promhttp.Handler())

  log.Println("listening :8080")
  log.Fatal(http.ListenAndServe(":8080", nil))
}

func getEnv(k, d string) string {
  if v := os.Getenv(k); v != "" {
    return v
  }
  return d
}
