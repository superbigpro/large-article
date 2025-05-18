# large-article

gRPC 기반의 마이크로서비스 아키텍처를 사용한 아티클 시스템입니다. 이 프로젝트는 각 서비스 간의 고성능 통신을 위해 gRPC를 채택했으며, 성능 최적화와 부하 테스트를 위한 다양한 도구를 포함합니다.

## 서비스 구조

- **ArticleService**: 게시글 CRUD 및 통계 관리(조회수, 좋아요)
- **AuthService**: 사용자 인증 및 토큰 관리
- **DashboardService**: 시스템 메트릭 모니터링 및 통계

## 기술 스택

- **언어**: Python
- **통신 프로토콜**: gRPC
- **데이터베이스**: MySQL
- **캐싱**: Redis
- **부하 테스트**: k6
- **컨테이너화**: Docker, Docker Compose

## 주요 기능

### ArticleService

- 게시글 CRUD 작업
- 조회수/좋아요 증감 처리 및 통계 관리
- Redis 캐싱을 통한 성능 최적화
- 배치 업데이트를 통한 DB 부하 분산

### AuthService

- 사용자 등록 및 로그인
- 토큰 기반 인증
- 권한 관리

### 성능 최적화

- Redis SCAN 명령어를 사용한 대용량 키 조회 최적화
- 파이프라인과 청크 단위 처리로 메모리 효율성 개선
- 로컬 백로그 처리를 통한 일시적 장애 대응

## 설치 및 실행

### 요구 사항

- Docker 및 Docker Compose
- Python 3.8 이상

### 실행 방법

1. 저장소 클론:

```bash
git clone <repository-url>
cd RpcArticle
```

2. Docker Compose로 서비스 실행:

```bash
docker-compose up -d
```

3. 각 서비스는 다음 포트에서 실행됩니다:
   - AuthService: 50001
   - ArticleService: 50002

## 부하 테스트

k6를 사용한 부하 테스트 스크립트가 `loadtests` 디렉토리에 포함되어 있습니다.

### 설치

```bash
# macOS
brew install k6

# Linux
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6
```

### gRPC 테스트 준비 (선택사항)

```bash
go install go.k6.io/xk6/cmd/xk6@latest
xk6 build --with github.com/grafana/xk6-grpc@latest
```

### 테스트 실행

REST API 테스트:

```bash
k6 run loadtests/article_service_test.js
k6 run loadtests/auth_service_test.js
```

gRPC 직접 테스트:

```bash
cp ArticleService/protos/article.proto loadtests/
./k6 run loadtests/grpc_article_test.js
```

## 개발 환경 설정

각 서비스 디렉토리에는 `requirements.txt` 파일이 있으며, 다음 명령으로 설치할 수 있습니다:

```bash
pip install -r ArticleService/app/requirements.txt
pip install -r AuthService/app/requirements.txt
```
