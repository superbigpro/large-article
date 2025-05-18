import { check, sleep } from "k6";
import http from "k6/http";
import { randomIntBetween } from "https://jslib.k6.io/k6-utils/1.2.0/index.js";
import { Trend, Rate, Counter } from "k6/metrics";

// 메트릭 정의
const getTrendingLatency = new Trend("get_trending_latency");
const getPostLatency = new Trend("get_post_latency");
const getAllPostsLatency = new Trend("get_all_posts_latency");
const createPostLatency = new Trend("create_post_latency");
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
        { duration: "10s", target: 100 }, // 10초 동안 100명으로 증가
        { duration: "30s", target: 100 }, // 30초 동안 100명 유지
        { duration: "10s", target: 0 }, // 10초 동안 0명으로 감소
      ],
      gracefulRampDown: "10s",
      startTime: "4m30s", // 스트레스 시나리오 이후 시작
    },
  },
  thresholds: {
    get_trending_latency: ["p(95)<500"], // 95%의 요청이 500ms 이하
    get_post_latency: ["p(95)<300"], // 95%의 요청이 300ms 이하
    get_all_posts_latency: ["p(95)<800"], // 95%의 요청이 800ms 이하
    create_post_latency: ["p(95)<1000"], // 95%의 요청이 1000ms 이하
    error_rate: ["rate<0.1"], // 에러율 10% 이하
  },
};

// HTTP 요청 헤더 설정
const params = {
  headers: {
    "Content-Type": "application/json",
    Authorization: "Bearer fake-jwt-token",
  },
};

// 게시글 ID 범위 (1부터 100까지)
const POST_ID_MIN = 1;
const POST_ID_MAX = 100;

// 사용자 ID 범위 (1부터 20까지)
const USER_ID_MIN = 1;
const USER_ID_MAX = 20;

// 기본 URL
const BASE_URL = "http://localhost:8000/article"; // REST API 게이트웨이를 통한 액세스 가정

// 게시글 가져오기
function getPost() {
  const postId = randomIntBetween(POST_ID_MIN, POST_ID_MAX);
  const url = `${BASE_URL}/posts/${postId}`;

  const startTime = new Date();
  const response = http.get(url, params);
  const endTime = new Date();

  // 메트릭 기록
  getPostLatency.add(endTime - startTime);
  requestCount.add(1);

  // 응답 확인
  const success = check(response, {
    get_post_status_200: (r) => r.status === 200,
    get_post_has_title: (r) => r.json("post.title") !== undefined,
  });

  if (!success) {
    errorRate.add(1);
    console.log(
      `게시글 조회 실패 - 상태 코드: ${response.status}, 내용: ${response.body}`
    );
  }

  sleep(randomIntBetween(1, 3));
}

// 모든 게시글 가져오기
function getAllPosts() {
  const url = `${BASE_URL}/posts`;

  const startTime = new Date();
  const response = http.get(url, params);
  const endTime = new Date();

  // 메트릭 기록
  getAllPostsLatency.add(endTime - startTime);
  requestCount.add(1);

  // 응답 확인
  const success = check(response, {
    get_all_posts_status_200: (r) => r.status === 200,
    get_all_posts_has_posts: (r) => Array.isArray(r.json("posts")),
  });

  if (!success) {
    errorRate.add(1);
    console.log(
      `모든 게시글 조회 실패 - 상태 코드: ${response.status}, 내용: ${response.body}`
    );
  }

  sleep(randomIntBetween(2, 5));
}

// 인기 게시글 가져오기
function getTrendingPosts() {
  const url = `${BASE_URL}/trending`;

  const startTime = new Date();
  const response = http.get(url, params);
  const endTime = new Date();

  // 메트릭 기록
  getTrendingLatency.add(endTime - startTime);
  requestCount.add(1);

  // 응답 확인
  const success = check(response, {
    get_trending_status_200: (r) => r.status === 200,
    get_trending_has_posts: (r) => Array.isArray(r.json("posts")),
  });

  if (!success) {
    errorRate.add(1);
    console.log(
      `인기 게시글 조회 실패 - 상태 코드: ${response.status}, 내용: ${response.body}`
    );
  }

  sleep(randomIntBetween(1, 3));
}

// 게시글 작성하기
function createPost() {
  const url = `${BASE_URL}/posts`;
  const userId = randomIntBetween(USER_ID_MIN, USER_ID_MAX);

  const payload = JSON.stringify({
    title: `테스트 게시글 ${new Date().toISOString()}`,
    content: `이것은 부하 테스트로 생성된 게시글입니다. 사용자 ID: ${userId}`,
    author: userId,
  });

  const startTime = new Date();
  const response = http.post(url, payload, params);
  const endTime = new Date();

  // 메트릭 기록
  createPostLatency.add(endTime - startTime);
  requestCount.add(1);

  // 응답 확인
  const success = check(response, {
    create_post_status_201: (r) => r.status === 201,
    create_post_has_id: (r) => r.json("id") !== undefined,
  });

  if (!success) {
    errorRate.add(1);
    console.log(
      `게시글 작성 실패 - 상태 코드: ${response.status}, 내용: ${response.body}`
    );
  }

  sleep(randomIntBetween(3, 8));
}

// 웹소켓 연결 시뮬레이션 (실제 구현은 WebSocket 확장이 필요)
function simulateWSConnection() {
  // WebSocket 연결 시뮬레이션
  sleep(randomIntBetween(30, 60));
}

// 메인 함수
export default function () {
  // 테스트 시나리오 시뮬레이션
  const choice = randomIntBetween(1, 10);

  if (choice <= 4) {
    // 40% 확률로 단일 게시글 조회
    getPost();
  } else if (choice <= 7) {
    // 30% 확률로 모든 게시글 조회
    getAllPosts();
  } else if (choice <= 9) {
    // 20% 확률로 인기 게시글 조회
    getTrendingPosts();
  } else {
    // 10% 확률로 게시글 작성
    createPost();
  }
}
