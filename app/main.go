package main

import (
  "fmt"
  "log"
  "math/rand"
  "net/http"
  "os"
  "strconv"
  "time"
)

func handler(w http.ResponseWriter, r *http.Request) {
  baseMs, _ := strconv.Atoi(getEnv("LATENCY_MS", "50"))
  jitter := rand.Intn(200)
  time.Sleep(time.Duration(baseMs+jitter) * time.Millisecond)

  errPct, _ := strconv.Atoi(getEnv("ERROR_PCT", "0"))
  if rand.Intn(100) < errPct {
    w.WriteHeader(500)
    fmt.Fprintf(w, "oops")
    return
  }
  fmt.Fprintf(w, "ok")
}

func main() {
  rand.Seed(time.Now().UnixNano())
  http.HandleFunc("/", handler)
  log.Println("listening :8080")
  log.Fatal(http.ListenAndServe(":8080", nil))
}

func getEnv(k, d string) string {
  if v := os.Getenv(k); v != "" { return v }
  return d
}
