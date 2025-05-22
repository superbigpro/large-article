import { check, sleep } from "k6";
import http from "k6/http";
import {
  randomString,
  randomIntBetween,
} from "https://jslib.k6.io/k6-utils/1.2.0/index.js";
import { Trend, Rate, Counter } from "k6/metrics";

// 메트릭 정의
const loginLatency = new Trend("login_latency");
const registerLatency = new Trend("register_latency");
const validateTokenLatency = new Trend("validate_token_latency");
const errorRate = new Rate("error_rate");
const requestCount = new Counter("request_count");

// 테스트 설정
export const options = {
  scenarios: {
    // 기본 시나리오: 일반적인 부하
    normal_load: {
      executor: "ramping-vus",
      startVUs: 1,
      stages: [
        { duration: "30s", target: 10 }, // 30초 동안 10명으로 증가
        { duration: "1m", target: 10 }, // 1분 동안 10명 유지
        { duration: "30s", target: 0 }, // 30초 동안 0명으로 감소
      ],
      gracefulRampDown: "10s",
    },
    // 스트레스 시나리오: 높은 부하
    stress_test: {
      executor: "ramping-vus",
      startVUs: 0,
      stages: [
        { duration: "20s", target: 20 }, // 20초 동안 20명으로 증가
        { duration: "1m", target: 50 }, // 1분 동안 50명으로 증가
        { duration: "20s", target: 0 }, // 20초 동안 0명으로 감소
      ],
      gracefulRampDown: "10s",
      startTime: "2m30s", // 기본 시나리오 이후 시작
    },
    // 스파이크 시나리오: 매우 갑작스러운 부하
    spike_test: {
      executor: "ramping-vus",
      startVUs: 0,
      stages: [
        { duration: "10s", target: 80 }, // 10초 동안 80명으로 증가
        { duration: "30s", target: 80 }, // 30초 동안 80명 유지
        { duration: "10s", target: 0 }, // 10초 동안 0명으로 감소
      ],
      gracefulRampDown: "10s",
      startTime: "4m30s", // 스트레스 시나리오 이후 시작
    },
  },
  thresholds: {
    login_latency: ["p(95)<500"], // 95%의 요청이 500ms 이하
    register_latency: ["p(95)<800"], // 95%의 요청이 800ms 이하
    validate_token_latency: ["p(95)<200"], // 95%의 요청이 200ms 이하
    error_rate: ["rate<0.1"], // 에러율 10% 이하
  },
};

// HTTP 요청 헤더 설정
const params = {
  headers: {
    "Content-Type": "application/json",
  },
};

// 기본 URL
const BASE_URL = "http://localhost:8000"; // REST API 게이트웨이를 통한 액세스 가정

// 테스트 사용자 DB
// 실제 테스트에서 생성 및 재사용할 사용자 정보를 저장
let testUsers = [];

// 로그인 테스트
function login(username = null, password = null) {
  const url = `${BASE_URL}/api/login`;

  // 이미 생성된 사용자가 있으면 재사용, 아니면 새로 생성
  if (!username && testUsers.length > 0) {
    const randomUser = testUsers[Math.floor(Math.random() * testUsers.length)];
    username = randomUser.username;
    password = randomUser.password;
  } else if (!username) {
    // 랜덤 사용자 생성
    username = `testuser_${randomString(8)}`;
    password = "password123";
  }

  const payload = JSON.stringify({
    username: username,
    password: password,
  });

  const startTime = new Date();
  const response = http.post(url, payload, params);
  const endTime = new Date();

  // 메트릭 기록
  loginLatency.add(endTime - startTime);
  requestCount.add(1);

  // 응답 확인
  const success = check(response, {
    "status is 200": (r) => r.status === 200,
    "has token": (r) => r.json("token") !== undefined,
    "has ok flag": (r) => r.json("ok") === true,
  });

  if (!success) {
    errorRate.add(1);
    console.log(
      `로그인 실패 - 상태 코드: ${response.status}, 내용: ${response.body}`
    );
    return null;
  }

  sleep(randomIntBetween(0.5, 1.5));
  return response.json("token");
}

// 회원가입 테스트
function register() {
  const url = `${BASE_URL}/api/register`;

  // 랜덤 사용자 생성
  const username = `testuser_${randomString(8)}`;
  const handle_name = `Test User ${randomString(4)}`;
  const password = "password123";

  const payload = JSON.stringify({
    username: username,
    handle_name: handle_name,
    password: password,
    re_pw: password,
  });

  const startTime = new Date();
  const response = http.post(url, payload, params);
  const endTime = new Date();

  // 메트릭 기록
  registerLatency.add(endTime - startTime);
  requestCount.add(1);

  // 응답 확인
  const success = check(response, {
    "status is 200": (r) => r.status === 200,
    "has ok flag": (r) => r.json("ok") === true,
  });

  if (success) {
    // 성공한 사용자 정보 저장
    testUsers.push({
      username: username,
      password: password,
      handle_name: handle_name,
    });
  } else {
    errorRate.add(1);
    console.log(
      `회원가입 실패 - 상태 코드: ${response.status}, 내용: ${response.body}`
    );
  }

  sleep(randomIntBetween(1, 2));
}

// 토큰 검증 테스트
function validateToken(token) {
  if (!token) {
    // 토큰이 없으면 로그인을 통해 얻기
    token = login();
    if (!token) return;
  }

  const url = `${BASE_URL}/api/authcheck`;

  const params = {
    headers: {
      "Content-Type": "application/json",
      token: token,
    },
  };

  const startTime = new Date();
  const response = http.post(url, "{}", params);
  const endTime = new Date();

  // 메트릭 기록
  validateTokenLatency.add(endTime - startTime);
  requestCount.add(1);

  // 응답 확인
  const success = check(response, {
    "status is 200": (r) => r.status === 200,
    "received token": (r) => r.json("received_token") !== undefined,
  });

  if (!success) {
    errorRate.add(1);
    console.log(
      `토큰 검증 실패 - 상태 코드: ${response.status}, 내용: ${response.body}`
    );
  }

  sleep(randomIntBetween(0.5, 1));
}

// 사전에 테스트 사용자 생성
export function setup() {
  // 초기에 2명의 테스트 사용자 생성
  for (let i = 0; i < 2; i++) {
    register();
  }

  console.log(`${testUsers.length}명의 테스트 사용자가 생성되었습니다.`);
}

// 메인 함수
export default function () {
  const choice = randomIntBetween(1, 10);
  let token = null;

  if (choice <= 6) {
    // 60% 확률로 로그인
    token = login();
  } else if (choice <= 8) {
    // 20% 확률로 회원가입
    register();
  } else {
    // 20% 확률로 토큰 검증
    validateToken(token);
  }
}
