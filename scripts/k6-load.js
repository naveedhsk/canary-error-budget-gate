import http from 'k6/http';
import { sleep } from 'k6';

export const options = { vus: 5, duration: '2m' };
export default function () {
  http.get('http://localhost:8080');
  sleep(0.2);
}
