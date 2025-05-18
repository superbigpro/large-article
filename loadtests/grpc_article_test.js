import grpc from "k6/net/grpc";
import { check, sleep } from "k6";
import { randomIntBetween } from "https://jslib.k6.io/k6-utils/1.2.0/index.js";
import { Trend, Rate, Counter } from "k6/metrics";

// 메트릭 정의
const getPostLatency = new Trend("grpc_get_post_latency");
const getAllPostsLatency = new Trend("grpc_get_all_posts_latency");
const getPostViewsLatency = new Trend("grpc_get_post_views_latency");
const getPostHeartsLatency = new Trend("grpc_get_post_hearts_latency");
const incrementViewsLatency = new Trend("grpc_increment_views_latency");
const incrementHeartsLatency = new Trend("grpc_increment_hearts_latency");
const decrementHeartsLatency = new Trend("grpc_decrement_hearts_latency");
const errorRate = new Rate("grpc_error_rate");
const requestCount = new Counter("grpc_request_count");

// 게시글 ID 범위 (1부터 100까지)
const POST_ID_MIN = 1;
const POST_ID_MAX = 100;

// 사용자 ID 범위 (1부터 20까지)
const USER_ID_MIN = 1;
const USER_ID_MAX = 20;

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
    grpc_get_post_latency: ["p(95)<300"], // 95%의 요청이 300ms 이하
    grpc_get_all_posts_latency: ["p(95)<800"], // 95%의 요청이 800ms 이하
    grpc_get_post_views_latency: ["p(95)<200"], // 95%의 요청이 200ms 이하
    grpc_get_post_hearts_latency: ["p(95)<200"], // 95%의 요청이 200ms 이하
    grpc_increment_views_latency: ["p(95)<300"], // 95%의 요청이 300ms 이하
    grpc_increment_hearts_latency: ["p(95)<300"], // 95%의 요청이 300ms 이하
    grpc_decrement_hearts_latency: ["p(95)<300"], // 95%의 요청이 300ms 이하
    grpc_error_rate: ["rate<0.1"], // 에러율 10% 이하
  },
};

// gRPC 클라이언트 초기화 함수
function setupClient() {
  const client = new grpc.Client();
  // proto 파일 로드 (k6 실행 시 -e PROTO_PATH=... 옵션으로 경로 지정 필요)
  client.load([], "article.proto");

  // 서버 연결
  client.connect("localhost:50051", { plaintext: true });

  return client;
}

// GetPost 요청
function getPost(client) {
  const postId = randomIntBetween(POST_ID_MIN, POST_ID_MAX);

  const startTime = new Date();
  const response = client.invoke("article.ArticleService/GetPost", {
    id: postId,
  });
  const endTime = new Date();

  // 메트릭 기록
  getPostLatency.add(endTime - startTime);
  requestCount.add(1);

  // 응답 확인
  const success = check(response, {
    "status is OK": (r) => r.status === grpc.StatusOK,
    "has post": (r) => r && r.post && r.post.id === postId,
  });

  if (!success) {
    errorRate.add(1);
    console.log(
      `GetPost 실패 - 상태: ${response.status}, 메시지: ${response.error.message}`
    );
  }

  sleep(randomIntBetween(1, 3));
  return response;
}

// GetAllPosts 요청
function getAllPosts(client) {
  const startTime = new Date();
  const response = client.invoke("article.ArticleService/GetAllPosts", {});
  const endTime = new Date();

  // 메트릭 기록
  getAllPostsLatency.add(endTime - startTime);
  requestCount.add(1);

  // 응답 확인
  const success = check(response, {
    "status is OK": (r) => r.status === grpc.StatusOK,
    "has posts": (r) => r && r.posts && Array.isArray(r.posts),
  });

  if (!success) {
    errorRate.add(1);
    console.log(
      `GetAllPosts 실패 - 상태: ${response.status}, 메시지: ${
        response.error ? response.error.message : "알 수 없는 오류"
      }`
    );
  }

  sleep(randomIntBetween(2, 5));
  return response;
}

// GetPostViews 요청
function getPostViews(client) {
  const postId = randomIntBetween(POST_ID_MIN, POST_ID_MAX);

  const startTime = new Date();
  const response = client.invoke("article.ArticleService/GetPostViews", {
    post_id: postId,
  });
  const endTime = new Date();

  // 메트릭 기록
  getPostViewsLatency.add(endTime - startTime);
  requestCount.add(1);

  // 응답 확인
  const success = check(response, {
    "status is OK": (r) => r.status === grpc.StatusOK,
    "has views": (r) => r && r.views !== undefined,
  });

  if (!success) {
    errorRate.add(1);
    console.log(
      `GetPostViews 실패 - 상태: ${response.status}, 메시지: ${
        response.error ? response.error.message : "알 수 없는 오류"
      }`
    );
  }

  sleep(randomIntBetween(1, 2));
  return response;
}

// GetPostHearts 요청
function getPostHearts(client) {
  const postId = randomIntBetween(POST_ID_MIN, POST_ID_MAX);

  const startTime = new Date();
  const response = client.invoke("article.ArticleService/GetPostHearts", {
    post_id: postId,
  });
  const endTime = new Date();

  // 메트릭 기록
  getPostHeartsLatency.add(endTime - startTime);
  requestCount.add(1);

  // 응답 확인
  const success = check(response, {
    "status is OK": (r) => r.status === grpc.StatusOK,
    "has hearts": (r) => r && r.hearts !== undefined,
  });

  if (!success) {
    errorRate.add(1);
    console.log(
      `GetPostHearts 실패 - 상태: ${response.status}, 메시지: ${
        response.error ? response.error.message : "알 수 없는 오류"
      }`
    );
  }

  sleep(randomIntBetween(1, 2));
  return response;
}

// IncrementViews 요청
function incrementViews(client) {
  const postId = randomIntBetween(POST_ID_MIN, POST_ID_MAX);

  const startTime = new Date();
  const response = client.invoke("article.ArticleService/IncrementViews", {
    post_id: postId,
  });
  const endTime = new Date();

  // 메트릭 기록
  incrementViewsLatency.add(endTime - startTime);
  requestCount.add(1);

  // 응답 확인
  const success = check(response, {
    "status is OK": (r) => r.status === grpc.StatusOK,
    "has views": (r) => r && r.views !== undefined,
  });

  if (!success) {
    errorRate.add(1);
    console.log(
      `IncrementViews 실패 - 상태: ${response.status}, 메시지: ${
        response.error ? response.error.message : "알 수 없는 오류"
      }`
    );
  }

  sleep(randomIntBetween(1, 2));
  return response;
}

// IncrementHearts 요청
function incrementHearts(client) {
  const postId = randomIntBetween(POST_ID_MIN, POST_ID_MAX);
  const userId = randomIntBetween(USER_ID_MIN, USER_ID_MAX);

  const startTime = new Date();
  const response = client.invoke("article.ArticleService/IncrementHearts", {
    post_id: postId,
    user_id: userId,
  });
  const endTime = new Date();

  // 메트릭 기록
  incrementHeartsLatency.add(endTime - startTime);
  requestCount.add(1);

  // 응답 확인
  const success = check(response, {
    "status is OK": (r) => r.status === grpc.StatusOK,
    "has hearts": (r) => r && r.hearts !== undefined,
  });

  if (!success) {
    errorRate.add(1);
    console.log(
      `IncrementHearts 실패 - 상태: ${response.status}, 메시지: ${
        response.error ? response.error.message : "알 수 없는 오류"
      }`
    );
  }

  sleep(randomIntBetween(1, 2));
  return response;
}

// DecrementHearts 요청
function decrementHearts(client) {
  const postId = randomIntBetween(POST_ID_MIN, POST_ID_MAX);
  const userId = randomIntBetween(USER_ID_MIN, USER_ID_MAX);

  const startTime = new Date();
  const response = client.invoke("article.ArticleService/DecrementHearts", {
    post_id: postId,
    user_id: userId,
  });
  const endTime = new Date();

  // 메트릭 기록
  decrementHeartsLatency.add(endTime - startTime);
  requestCount.add(1);

  // 응답 확인
  const success = check(response, {
    "status is OK": (r) => r.status === grpc.StatusOK,
    "has hearts": (r) => r && r.hearts !== undefined,
  });

  if (!success) {
    errorRate.add(1);
    console.log(
      `DecrementHearts 실패 - 상태: ${response.status}, 메시지: ${
        response.error ? response.error.message : "알 수 없는 오류"
      }`
    );
  }

  sleep(randomIntBetween(1, 2));
  return response;
}

// 메인 함수
export default function () {
  // gRPC 클라이언트 초기화
  const client = setupClient();

  try {
    // 테스트 시나리오 시뮬레이션
    const choice = randomIntBetween(1, 10);

    if (choice <= 2) {
      // 20% 확률로 단일 게시글 조회
      getPost(client);
    } else if (choice <= 3) {
      // 10% 확률로 모든 게시글 조회
      getAllPosts(client);
    } else if (choice <= 5) {
      // 20% 확률로 조회수 증가
      incrementViews(client);
    } else if (choice <= 7) {
      // 20% 확률로 좋아요 증가
      incrementHearts(client);
    } else if (choice <= 8) {
      // 10% 확률로 좋아요 감소
      decrementHearts(client);
    } else if (choice <= 9) {
      // 10% 확률로 조회수 조회
      getPostViews(client);
    } else {
      // 10% 확률로 좋아요 수 조회
      getPostHearts(client);
    }
  } finally {
    // 클라이언트 연결 종료
    client.close();
  }
}
