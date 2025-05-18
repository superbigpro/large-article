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
const getUserLatency = new Trend("get_user_latency");
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
    get_user_latency: ["p(95)<300"], // 95%의 요청이 300ms 이하
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
const BASE_URL = "http://localhost:8000/auth"; // REST API 게이트웨이를 통한 액세스 가정

// 사용자 ID 범위 (1부터 20까지 - 테스트 전에 이미 등록된 사용자로 가정)
const USER_ID_MIN = 1;
const USER_ID_MAX = 20;

// 로그인 테스트
function login() {
  const url = `${BASE_URL}/login`;

  const randomUserId = randomIntBetween(USER_ID_MIN, USER_ID_MAX);
  const payload = JSON.stringify({
    username: `user${randomUserId}`,
    password: "password", // 모든 테스트 사용자는 단순화를 위해 같은 비밀번호 사용
  });

  const startTime = new Date();
  const response = http.post(url, payload, params);
  const endTime = new Date();

  // 메트릭 기록
  loginLatency.add(endTime - startTime);
  requestCount.add(1);

  // 응답 확인
  const success = check(response, {
    login_status_200: (r) => r.status === 200,
    login_has_token: (r) => r.json("token") !== undefined,
    login_has_user_id: (r) => r.json("user_id") !== undefined,
  });

  if (!success) {
    errorRate.add(1);
    console.log(
      `로그인 실패 - 상태 코드: ${response.status}, 내용: ${response.body}`
    );
    return null;
  }

  sleep(randomIntBetween(1, 3));
  return response.json("token");
}

// 회원가입 테스트
function register() {
  const url = `${BASE_URL}/register`;

  // 랜덤 사용자 생성
  const username = `testuser_${randomString(8)}`;
  const email = `${username}@example.com`;

  const payload = JSON.stringify({
    username: username,
    email: email,
    password: "password123", // 테스트용 단순 비밀번호
  });

  const startTime = new Date();
  const response = http.post(url, payload, params);
  const endTime = new Date();

  // 메트릭 기록
  registerLatency.add(endTime - startTime);
  requestCount.add(1);

  // 응답 확인
  const success = check(response, {
    register_status_201: (r) => r.status === 201,
    register_has_user_id: (r) => r.json("id") !== undefined,
  });

  if (!success) {
    errorRate.add(1);
    console.log(
      `회원가입 실패 - 상태 코드: ${response.status}, 내용: ${response.body}`
    );
  }

  sleep(randomIntBetween(2, 5));
}

// 토큰 검증 테스트
function validateToken(token) {
  if (!token) {
    // 토큰이 없으면 로그인을 통해 얻기
    token = login();
    if (!token) return;
  }

  const url = `${BASE_URL}/validate`;

  // Authorization 헤더에 토큰 추가
  const tokenParams = {
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
  };

  const startTime = new Date();
  const response = http.post(url, "{}", tokenParams);
  const endTime = new Date();

  // 메트릭 기록
  validateTokenLatency.add(endTime - startTime);
  requestCount.add(1);

  // 응답 확인
  const success = check(response, {
    validate_token_status_200: (r) => r.status === 200,
    validate_token_is_valid: (r) => r.json("valid") === true,
  });

  if (!success) {
    errorRate.add(1);
    console.log(
      `토큰 검증 실패 - 상태 코드: ${response.status}, 내용: ${response.body}`
    );
  }

  sleep(randomIntBetween(1, 2));
}

// 사용자 정보 조회 테스트
function getUser(token) {
  if (!token) {
    // 토큰이 없으면 로그인을 통해 얻기
    token = login();
    if (!token) return;
  }

  const userId = randomIntBetween(USER_ID_MIN, USER_ID_MAX);
  const url = `${BASE_URL}/users/${userId}`;

  // Authorization 헤더에 토큰 추가
  const tokenParams = {
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
  };

  const startTime = new Date();
  const response = http.get(url, tokenParams);
  const endTime = new Date();

  // 메트릭 기록
  getUserLatency.add(endTime - startTime);
  requestCount.add(1);

  // 응답 확인
  const success = check(response, {
    get_user_status_200: (r) => r.status === 200,
    get_user_has_username: (r) => r.json("user.username") !== undefined,
  });

  if (!success) {
    errorRate.add(1);
    console.log(
      `사용자 정보 조회 실패 - 상태 코드: ${response.status}, 내용: ${response.body}`
    );
  }

  sleep(randomIntBetween(1, 3));
}

// 메인 함수
export default function () {
  // 테스트 시나리오 시뮬레이션
  const choice = randomIntBetween(1, 10);

  // 사용자별로 고유한 토큰을 가지도록 설정
  // 실제로는 적절한 저장소에 토큰을 보관해야 함
  let token = null;

  if (choice <= 4) {
    // 40% 확률로 로그인
    token = login();
  } else if (choice <= 5) {
    // 10% 확률로 회원가입
    register();
  } else if (choice <= 8) {
    // 30% 확률로 토큰 검증
    token = login();
    if (token) validateToken(token);
  } else {
    // 20% 확률로 사용자 정보 조회
    token = login();
    if (token) getUser(token);
  }
}
