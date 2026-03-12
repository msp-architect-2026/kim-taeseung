import http from 'k6/http';

export let options = {
  stages: [
    { duration: '30s', target: 200 },
    { duration: '30s', target: 500 },
    { duration: '10s', target: 0 },
  ],
};

export default function () {
  http.post(
    'http://kube-fortune.local:30768/api/login',
    JSON.stringify({ nickname: '테스트유저' }),
    { headers: { 'Content-Type': 'application/json' } }
  );
}