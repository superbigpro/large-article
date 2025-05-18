# k6 부하 테스트 가이드

이 디렉토리에는 Article 및 Auth 서비스에 대한 부하 테스트 스크립트가 포함되어 있습니다.

## 설치 방법

### k6 설치

MacOS:

```bash
brew install k6
```

Linux:

```bash
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6
```

Windows:

```
choco install k6
```

### gRPC 지원 설치 (gRPC 테스트용)

k6는 기본적으로 gRPC를 지원하지 않으므로, [xk6-grpc](https://github.com/grafana/xk6-grpc) 확장이 필요합니다.

1. Go 설치 (1.17 이상)
2. xk6 설치:

```bash
go install go.k6.io/xk6/cmd/xk6@latest
```

3. gRPC 확장이 포함된 k6 빌드:

```bash
xk6 build --with github.com/grafana/xk6-grpc@latest
```

4. 빌드된 바이너리를 적절한 위치에 이동

## 테스트 실행 방법

### REST API 테스트 (게이트웨이 필요)

```bash
# Article 서비스 테스트 실행
k6 run loadtests/article_service_test.js

# Auth 서비스 테스트 실행
k6 run loadtests/auth_service_test.js
```

### gRPC 직접 테스트 (xk6-grpc 필요)

1. 먼저 proto 파일을 복사:

```bash
cp ArticleService/protos/article.proto loadtests/
```

2. 확장된 k6로 테스트 실행:

```bash
# gRPC Article 서비스 테스트
./k6 run loadtests/grpc_article_test.js
```

## 테스트 설정 변경

모든 테스트 스크립트는 다음 시나리오를 포함합니다:

1. **normal_load** - 정상적인 부하 테스트 (10명의 동시 사용자)
2. **stress_test** - 스트레스 테스트 (최대 50명의 동시 사용자)
3. **spike_test** - 스파이크 테스트 (갑작스러운 100명의 동시 사용자)

테스트 파라미터는 각 스크립트의 `options` 객체에서 조정할 수 있습니다:

```javascript
export const options = {
  scenarios: {
    normal_load: { ... },
    stress_test: { ... },
    spike_test: { ... }
  },
  thresholds: { ... }
};
```

## 특정 시나리오만 실행

특정 시나리오만 실행하려면:

```bash
k6 run --tag scenario=normal_load loadtests/article_service_test.js
```

## 결과 시각화

Grafana와 InfluxDB로 결과 시각화하기:

1. InfluxDB 및 Grafana 설치
2. InfluxDB로 결과 내보내기:

```bash
k6 run --out influxdb=http://localhost:8086/k6 loadtests/article_service_test.js
```

3. Grafana에서 k6 대시보드 설정

## 분산 부하 테스트

여러 서버에서 부하를 분산하려면 k6 Cloud 또는 k6 Operator를 사용할 수 있습니다.

### k6 Operator로 Kubernetes에서 분산 테스트

1. k6-operator 설치:

```bash
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
helm install k6-operator grafana/k6-operator
```

2. 테스트 구성 파일 생성 (k6-test.yaml):

```yaml
apiVersion: k6.io/v1alpha1
kind: K6
metadata:
  name: distributed-test
spec:
  parallelism: 4
  script:
    configMap:
      name: article-test
      file: article_service_test.js
```

3. 테스트 스크립트를 ConfigMap으로 생성:

```bash
kubectl create configmap article-test --from-file=article_service_test.js=./loadtests/article_service_test.js
```

4. 분산 테스트 실행:

```bash
kubectl apply -f k6-test.yaml
```
