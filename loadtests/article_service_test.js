import { check, sleep } from "k6";
import http from "k6/http";
import {
  randomIntBetween,
  randomString,
} from "https://jslib.k6.io/k6-utils/1.2.0/index.js";
import { Trend, Rate, Counter } from "k6/metrics";

// 메트릭 정의
const loginLatency = new Trend("login_latency");
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
    login_latency: ["p(95)<500"], // 95%의 요청이 500ms 이하
    get_post_latency: ["p(95)<300"], // 95%의 요청이 300ms 이하
    get_all_posts_latency: ["p(95)<800"], // 95%의 요청이 800ms 이하
    create_post_latency: ["p(95)<1000"], // 95%의 요청이 1000ms 이하
    error_rate: ["rate<0.1"], // 에러율 10% 이하
  },
};

// 기본 URL
const BASE_URL = "http://localhost:8000"; // API 게이트웨이를 통한 접근 가정

// 게시글 ID 범위 (1부터 100까지)
const POST_ID_MIN = 1;
const POST_ID_MAX = 100;

// 테스트 사용자 정보 - 등록된 사용자 정보를 보관
let testUsers = [];
let postIds = [];

// 로그인 및 토큰 가져오기
function login(username = null, password = null) {
  // 이미 만들어진 테스트 사용자가 있으면 사용
  if (!username && testUsers.length > 0) {
    const randomUser = testUsers[Math.floor(Math.random() * testUsers.length)];
    username = randomUser.username;
    password = randomUser.password;
  } else if (!username) {
    // 새 사용자 정보 생성
    username = `testuser_${randomString(8)}`;
    password = "password123";
  }

  const url = `${BASE_URL}/api/login`;

  const payload = JSON.stringify({
    username: username,
    password: password,
  });

  const params = {
    headers: {
      "Content-Type": "application/json",
    },
  };

  const startTime = new Date();
  const response = http.post(url, payload, params);
  const endTime = new Date();

  // 메트릭 기록
  loginLatency.add(endTime - startTime);
  requestCount.add(1);

  // 응답 확인
  const success = check(response, {
    "login status is 200": (r) => r.status === 200,
    "has token": (r) => r.json("token") !== undefined,
    "has ok flag": (r) => r.json("ok") === true,
  });

  if (!success) {
    errorRate.add(1);
    console.log(
      `로그인 실패 - 상태 코드: ${response.status}, 내용: ${response.body}`
    );

    // 로그인 실패 시 새 사용자 등록 시도
    registerUser(username, password);
    return null;
  }

  // 로그인 성공한 사용자 정보를 저장 (없는 경우)
  if (!testUsers.some((user) => user.username === username)) {
    testUsers.push({ username, password });
  }

  return {
    token: response.json("token"),
    username: username,
  };
}

// 새 사용자 등록
function registerUser(username, password) {
  const url = `${BASE_URL}/api/register`;

  const handle_name = `Test User ${randomString(5)}`;

  const payload = JSON.stringify({
    username: username,
    password: password,
    handle_name: handle_name,
    re_pw: password,
  });

  const params = {
    headers: {
      "Content-Type": "application/json",
    },
  };

  const response = http.post(url, payload, params);

  if (response.status === 200) {
    console.log(`새 사용자 등록 성공: ${username}`);
    testUsers.push({ username, password, handle_name });
    return true;
  } else {
    console.log(`새 사용자 등록 실패: ${response.body}`);
    return false;
  }
}

// 게시글 가져오기
function getPost(auth) {
  if (!auth) return;

  // 이미 생성된 게시글이 있으면 그 중 하나를 사용, 없으면 랜덤 ID
  const postId =
    postIds.length > 0
      ? postIds[Math.floor(Math.random() * postIds.length)]
      : randomIntBetween(POST_ID_MIN, POST_ID_MAX);

  const url = `${BASE_URL}/api/posts/${postId}`;

  const params = {
    headers: {
      "Content-Type": "application/json",
      token: auth.token,
    },
  };

  const startTime = new Date();
  const response = http.get(url, params);
  const endTime = new Date();

  // 메트릭 기록
  getPostLatency.add(endTime - startTime);
  requestCount.add(1);

  // 응답 확인
  const success = check(response, {
    "status is 200": (r) => r.status === 200,
    "has ok flag": (r) => r.json("ok") === "True",
  });

  if (!success) {
    errorRate.add(1);
    console.log(
      `게시글 조회 실패 - 상태 코드: ${response.status}, 내용: ${response.body}`
    );
  }

  sleep(randomIntBetween(0.5, 1.5));
  return response;
}

// 모든 게시글 가져오기
function getAllPosts(auth) {
  if (!auth) return;

  const url = `${BASE_URL}/api/get_posts/0`; // cursor_id 0부터 시작

  const params = {
    headers: {
      "Content-Type": "application/json",
      token: auth.token,
    },
  };

  const startTime = new Date();
  const response = http.get(url, params);
  const endTime = new Date();

  // 메트릭 기록
  getAllPostsLatency.add(endTime - startTime);
  requestCount.add(1);

  // 응답 확인
  const success = check(response, {
    "status is 200": (r) => r.status === 200,
    "has posts": (r) => r.json("posts") !== undefined,
    "has ok flag": (r) => r.json("ok") === "True",
  });

  if (!success) {
    errorRate.add(1);
    console.log(
      `모든 게시글 조회 실패 - 상태 코드: ${response.status}, 내용: ${response.body}`
    );
  }

  sleep(randomIntBetween(1, 2));
  return response;
}

// 게시글 작성하기
function createPost(auth) {
  if (!auth) return;

  const url = `${BASE_URL}/api/create`;

  const title = `테스트 게시글 ${randomString(8)}`;
  const content = `이것은 부하 테스트로 생성된 게시글입니다. 작성자: ${
    auth.username
  }, 시간: ${new Date().toISOString()}`;

  const payload = JSON.stringify({
    title: title,
    content: content,
    picture: null,
  });

  const params = {
    headers: {
      "Content-Type": "application/json",
      token: auth.token,
    },
  };

  const startTime = new Date();
  const response = http.post(url, payload, params);
  const endTime = new Date();

  // 메트릭 기록
  createPostLatency.add(endTime - startTime);
  requestCount.add(1);

  // 응답 확인
  const success = check(response, {
    "status is 200": (r) => r.status === 200,
    "has ok flag": (r) => r.json("ok") === true,
  });

  if (success) {
    // 여기서 새 게시글 ID를 저장할 수 있지만, 현재 API는 ID를 반환하지 않음
    // 만약 API가 ID를 반환한다면: postIds.push(response.json("id"));
    console.log(`게시글 생성 성공: ${title}`);
  } else {
    errorRate.add(1);
    console.log(
      `게시글 작성 실패 - 상태 코드: ${response.status}, 내용: ${response.body}`
    );
  }

  sleep(randomIntBetween(1.5, 3));
  return response;
}

// 테스트 준비 - 사용자 생성 및 기본 게시글 등록
export function setup() {
  // 초기에 3명의 테스트 사용자 생성
  for (let i = 0; i < 3; i++) {
    const username = `loadtest_user_${randomString(6)}`;
    const password = "password123";
    registerUser(username, password);
  }

  console.log(`${testUsers.length}명의 테스트 사용자가 생성되었습니다.`);

  // 테스트 사용자 중 한 명으로 로그인하여 기본 게시글 생성
  if (testUsers.length > 0) {
    const user = testUsers[0];
    const auth = login(user.username, user.password);

    if (auth) {
      for (let i = 0; i < 3; i++) {
        createPost(auth);
      }
    }
  }
}

// 메인 함수
export default function () {
  // 먼저 로그인하여 토큰 획득
  const auth = login();
  if (!auth) return; // 로그인 실패시 테스트 중단

  // 테스트 시나리오 시뮬레이션
  const choice = randomIntBetween(1, 10);

  if (choice <= 5) {
    // 50% 확률로 단일 게시글 조회
    getPost(auth);
  } else if (choice <= 8) {
    // 30% 확률로 모든 게시글 조회
    getAllPosts(auth);
  } else {
    // 20% 확률로 게시글 작성
    createPost(auth);
  }
}
