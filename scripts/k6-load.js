import http from 'k6/http';
import { sleep } from 'k6';

const HOST = __ENV.HOST || 'http://localhost:8080';  // ← use env or default

export const options = { vus: 5, duration: '2m' };
export default function () {
  http.get(HOST);
  sleep(0.2);
}
