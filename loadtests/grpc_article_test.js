import grpc from "k6/net/grpc";
import { check, sleep } from "k6";
import { randomString } from "https://jslib.k6.io/k6-utils/1.2.0/index.js";
import { Trend, Rate, Counter } from "k6/metrics";

// 메트릭 정의
const authorizeLatency = new Trend("grpc_authorize_latency");
const errorRate = new Rate("grpc_error_rate");
const requestCount = new Counter("grpc_request_count");

// gRPC 클라이언트 설정
const client = new grpc.Client();
client.load(["proto"], "auth.proto");

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
  },
  thresholds: {
    grpc_authorize_latency: ["p(95)<200"], // 95%의 요청이 200ms 이하
    grpc_error_rate: ["rate<0.1"], // 에러율 10% 이하
  },
};

// gRPC 연결 설정
export function setup() {
  client.connect("localhost:50001", {
    plaintext: true,
  });

  // REST API로 테스트 사용자 생성 및 토큰 발급
  const tokens = createTestTokens(3);
  return { tokens };
}

// REST API를 통해 사용자 생성 및 토큰 발급
function createTestTokens(count) {
  const http = require("k6/http");
  const tokens = [];

  for (let i = 0; i < count; i++) {
    // 테스트 사용자 등록
    const username = `grpc_test_user_${randomString(8)}`;
    const password = "password123";
    const handle_name = `GRPC Test User ${i}`;

    const registerResponse = http.post(
      "http://localhost:8000/api/register",
      JSON.stringify({
        username: username,
        password: password,
        handle_name: handle_name,
        re_pw: password,
      }),
      {
        headers: { "Content-Type": "application/json" },
      }
    );

    if (registerResponse.status === 200) {
      // 로그인하여 토큰 획득
      const loginResponse = http.post(
        "http://localhost:8000/api/login",
        JSON.stringify({
          username: username,
          password: password,
        }),
        {
          headers: { "Content-Type": "application/json" },
        }
      );

      if (loginResponse.status === 200) {
        tokens.push(loginResponse.json("token"));
      }
    }
  }

  console.log(`${tokens.length}개의 테스트 토큰이 생성되었습니다.`);
  return tokens;
}

// gRPC 연결 종료
export function teardown() {
  client.close();
}

// 토큰 유효성 검증
function authorize(token) {
  const payload = {
    token: token,
  };

  const startTime = new Date();
  const response = client.invoke("auth.AuthService/Authorize", payload);
  const endTime = new Date();

  // 메트릭 기록
  authorizeLatency.add(endTime - startTime);
  requestCount.add(1);

  // 응답 확인
  const success = check(response, {
    "status is OK": (r) => r.status === grpc.StatusOK,
    "is successful": (r) => r.message.success === true,
    "has user id": (r) =>
      r.message.userid !== undefined && r.message.userid > 0,
  });

  if (!success) {
    errorRate.add(1);
    console.log(
      `토큰 검증 실패 - 상태: ${response.status}, 메시지: ${JSON.stringify(
        response.message || response.error
      )}`
    );
  }

  sleep(randomIntBetween(0.3, 0.8));
  return response.message;
}

// 랜덤 정수 생성 함수
function randomIntBetween(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

// 메인 함수
export default function (data) {
  // 사용 가능한 토큰이 없으면 고정 테스트 토큰 사용
  const tokens =
    data?.tokens?.length > 0
      ? data.tokens
      : ["sample_token_1", "sample_token_2", "sample_token_3"];

  // 랜덤하게 토큰 선택
  const token = tokens[randomIntBetween(0, tokens.length - 1)];

  // 토큰 유효성 검증 테스트
  authorize(token);
}
