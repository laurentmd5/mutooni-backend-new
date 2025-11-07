pipeline {
    agent any

    environment {
        GH_REPO = 'laurentmd5/mutooni-backend-new'
        GITHUB_CREDENTIALS_ID = 'my-token-jenkins'
        IMAGE_NAME = "mon-app-django"
        DOCKER_REGISTRY = "docker.io/laurentmd5"
        DOCKER_REGISTRY_CREDENTIALS_ID = 'docker-hub-creds'

        TEST_DB_CONTAINER_NAME = "test-db-django-${BUILD_NUMBER}"
        TEST_IMAGE_TAG = "${env.DOCKER_REGISTRY}/${env.IMAGE_NAME}:${BUILD_NUMBER}"
        DAST_NAMESPACE = "dast-test-${BUILD_NUMBER}"
        DAST_APP_NAME = "django-app-dast"
        DAST_DB_NAME = "postgres-dast"
        DAST_SERVICE_PORT = "8000"
        DAST_NODE_PORT = "30080"
        DAST_TIMEOUT = "180"
    }

    options {
        skipDefaultCheckout()
        timestamps()
        timeout(time: 1, unit: 'HOURS')
    }

    stages {
        stage('Checkout Code Source') {
            steps {
                echo '📦 Cloning repository...'
                cleanWs()
                git branch: 'main', credentialsId: env.GITHUB_CREDENTIALS_ID, url: "https://github.com/${env.GH_REPO}.git"

                script {
                    def commitHash = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                    def commitAuthor = sh(script: 'git log -1 --pretty=format:%an', returnStdout: true).trim()
                    def commitMessage = sh(script: 'git log -1 --pretty=format:%s', returnStdout: true).trim()

                    echo "✅ Commit: ${commitHash} par ${commitAuthor}"
                    echo "   Message: ${commitMessage}"
                }
            }
        }

        stage('Inject Firebase Key') {
            steps {
                echo '🔑 Injecting Firebase Service Account Key...'
                withCredentials([file(credentialsId: 'FIREBASE_SERVICE_ACCOUNT_KEY', variable: 'FIREBASE_KEY')]) {
                    sh '''
                        mkdir -p mysite/core/firebase
                        cp "$FIREBASE_KEY" mysite/core/firebase/serviceAccountKey.json
                        chmod 644 mysite/core/firebase/serviceAccountKey.json
                    '''
                }
                echo '✅ Firebase key injected successfully'
            }
        }

        stage('Analyse Qualité & Sécurité en parallèle') {
            parallel {
                stage('Linting & Qualité du Code (Flake8)') {
                    steps {
                        script {
                            echo '🔍 Checking code style with flake8 (inside Docker)...'
                            sh """
                                docker run --rm --user root -v \$(pwd):/workspace -w /workspace python:3.11-slim bash -c '
                                    pip install --upgrade pip --quiet && \
                                    pip install flake8 flake8-html --quiet && \
                                    flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics || echo "⚠️  Erreurs critiques détectées" && \
                                    flake8 . --count --exit-zero --max-complexity=10 --max-line-length=120 --statistics --format=html --htmldir=flake8-report
                                '
                            """
                            echo '✅ Linting completed'
                        }
                    }
                    post {
                        always { archiveArtifacts artifacts: 'flake8-report/**', allowEmptyArchive: true }
                    }
                }

                stage('Sécurité Statique du Code (SAST - Python)') {
                    steps {
                        script {
                            echo '🛡️  Running SAST with Bandit and Semgrep (inside Docker)...'
                            sh """
                                docker run --rm --user root -v \$(pwd):/workspace -w /workspace python:3.11-slim bash -c '
                                    pip install --upgrade pip --quiet && \
                                    pip install bandit semgrep --quiet && \
                                    bandit -r . -o bandit_report.json -f json --exit-zero && \
                                    bandit -r . -o bandit_report.html -f html --exit-zero && \
                                    semgrep --config="p/python" --config="p/django" --json -o semgrep_report.json . --error || echo "⚠️  Semgrep a trouvé des problèmes"
                                '
                            """
                            echo '✅ SAST analysis completed'
                        }
                    }
                    post {
                        always {
                            archiveArtifacts artifacts: 'bandit_report.*', allowEmptyArchive: true
                            archiveArtifacts artifacts: 'semgrep_report.json', allowEmptyArchive: true
                        }
                    }
                }
            }
        }

        stage('Analyse des Dépendances (SCA - Trivy)') {
            steps {
                echo '📦 Scanning dependencies (requirements.txt) with Trivy...'
                script {
                    def trivyScaResult = sh(
                        script: """
                            docker run --rm -v \$(pwd):/src aquasec/trivy fs \
                                --exit-code 1 --severity HIGH,CRITICAL --ignore-unfixed \
                                --format json -o /src/trivy_sca_report.json .
                        """, returnStatus: true
                    )
                    archiveArtifacts artifacts: 'trivy_sca_report.json', allowEmptyArchive: true
                    if (trivyScaResult != 0) {
                        currentBuild.result = 'UNSTABLE'
                        echo '⚠️  Trivy a trouvé des vulnérabilités critiques/élevées dans les dépendances !'
                    } else {
                        echo '✅ Aucune vulnérabilité SCA critique ou élevée trouvée.'
                    }
                }
            }
        }

        stage('Build Image Docker') {
            steps {
                echo "🐳 Building Docker image: ${env.TEST_IMAGE_TAG}"
                script {
                    withCredentials([usernamePassword(credentialsId: env.DOCKER_REGISTRY_CREDENTIALS_ID, usernameVariable: 'DOCKER_USERNAME', passwordVariable: 'DOCKER_PASSWORD')]) {
                        sh "echo \$DOCKER_PASSWORD | docker login -u \$DOCKER_USERNAME --password-stdin ${env.DOCKER_REGISTRY}"
                        sh """
                            docker build --build-arg BUILD_DATE=\$(date -u +"%Y-%m-%dT%H:%M:%SZ") \
                                         --build-arg VCS_REF=\$(git rev-parse --short HEAD) \
                                         --build-arg BUILD_NUMBER=${BUILD_NUMBER} \
                                         --tag ${env.TEST_IMAGE_TAG} .
                        """
                        sh "docker push ${env.TEST_IMAGE_TAG}"
                        echo "✅ Image built and pushed: ${env.TEST_IMAGE_TAG}"
                    }
                }
            }
        }

        stage('Scan Image Docker (Trivy)') {
            steps {
                echo "🔍 Scanning Docker image: ${env.TEST_IMAGE_TAG}"
                script {
                    def trivyImageResult = sh(
                        script: """
                            docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
                                -v /var/lib/jenkins/trivy-cache:/root/.cache/ \
                                -e TRIVY_DB_REPOSITORY=public.ecr.aws/aquasecurity/trivy-db \
                                aquasec/trivy:latest image --timeout 10m --exit-code 1 --severity CRITICAL --ignore-unfixed --no-progress ${env.TEST_IMAGE_TAG}
                        """, returnStatus: true
                    )
                    if (trivyImageResult != 0) {
                        error '❌ Trivy a trouvé des vulnérabilités CRITIQUES dans l\'image Docker.'
                    } else {
                        echo '✅ Aucune vulnérabilité CRITIQUE trouvée dans l\'image.'
                    }
                    sh """
                        docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
                            -v /var/lib/jenkins/trivy-cache:/root/.cache/ \
                            -v \$(pwd):/scan \
                            -e TRIVY_DB_REPOSITORY=public.ecr.aws/aquasecurity/trivy-db \
                            aquasec/trivy:latest image --timeout 10m --format json --no-progress --severity HIGH,CRITICAL \
                            -o /scan/trivy_image_report.json ${env.TEST_IMAGE_TAG}
                    """
                    archiveArtifacts artifacts: 'trivy_image_report.json', allowEmptyArchive: true
                }
            }
        }

        stage('Tests Unitaires & Fonctionnels') {
            steps {
                echo '🧪 Running Django unit tests with a temporary database...'
                script {
                    try {
                        echo "🗄️  Starting temporary test database: ${env.TEST_DB_CONTAINER_NAME}"
                        sh """
                            docker run -d --name ${env.TEST_DB_CONTAINER_NAME} \
                                -e POSTGRES_DB=mysite_test \
                                -e POSTGRES_USER=postgres \
                                -e POSTGRES_PASSWORD=postgres \
                                --health-cmd='pg_isready -U postgres' \
                                --health-interval=5s \
                                --health-timeout=3s \
                                --health-retries=5 \
                                docker.io/library/postgres:13
                        """
                        echo '⏳ Waiting for database to be healthy...'
                        sh "timeout 30s bash -c 'until docker inspect --format=\"{{.State.Health.Status}}\" ${env.TEST_DB_CONTAINER_NAME} | grep -q \"healthy\"; do sleep 1; done'"
                        echo '✅ Database is healthy.'

                        sh 'mkdir -p test-reports'
                        sh """
                            docker run --rm --link ${env.TEST_DB_CONTAINER_NAME}:db \
                                -v \$(pwd)/mysite/core/firebase/serviceAccountKey.json:/app/core/firebase/serviceAccountKey.json:ro \
                                -v \$(pwd)/test-reports:/app/test-reports \
                                -e DB_NAME=mysite_test \
                                -e DB_USER=postgres \
                                -e DB_PASSWORD=postgres \
                                -e DB_HOST=db \
                                -e DB_PORT=5432 \
                                -e DJANGO_SETTINGS_MODULE=mysite.settings \
                                ${env.TEST_IMAGE_TAG} \
                                sh -c "python manage.py test --noinput --verbosity=2"
                        """
                        echo '✅ All tests passed successfully!'
                    } catch (e) {
                        currentBuild.result = 'FAILURE'
                        echo "❌ Tests failed: ${e.message}"
                        throw e
                    } finally {
                        echo '🧹 Stopping and removing test database...'
                        sh "docker stop ${env.TEST_DB_CONTAINER_NAME} || true"
                        sh "docker rm ${env.TEST_DB_CONTAINER_NAME} || true"
                    }
                }
            }
            post {
                always { junit testResults: 'test-reports/**/*.xml', allowEmptyResults: true }
            }
        }

        stage('Déploiement Temporaire pour DAST') {
            steps {
                echo '🚀 Deploying application to Kubernetes for DAST testing...'
                script {
                    try {
                        echo '🔍 Checking Kubernetes cluster connectivity...'
                        sh "kubectl cluster-info || exit 1; kubectl get nodes || exit 1"
                        echo "✅ Kubernetes cluster is reachable"

                        echo "📦 Creating temporary namespace: ${env.DAST_NAMESPACE}"
                        sh "kubectl create namespace ${env.DAST_NAMESPACE} || true; kubectl label namespace ${env.DAST_NAMESPACE} jenkins-build=${BUILD_NUMBER} || true"

                        echo "📥 Ensure Docker image is available for Kubernetes"
                        sh "docker save ${env.TEST_IMAGE_TAG} | docker load"

                        // Déploiement PostgreSQL
                        echo '🗄️  Deploying PostgreSQL database...'
                        sh """
                            cat <<EOF | kubectl apply -n ${env.DAST_NAMESPACE} -f -
apiVersion: v1
kind: Secret
metadata:
  name: postgres-secret
type: Opaque
stringData:
  POSTGRES_DB: mysite_dast
  POSTGRES_USER: postgres
  POSTGRES_PASSWORD: postgres_dast_secure
---
apiVersion: v1
kind: Service
metadata:
  name: ${env.DAST_DB_NAME}
  labels:
    app: postgres
spec:
  ports:
    - port: 5432
      targetPort: 5432
  selector:
    app: postgres
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${env.DAST_DB_NAME}
  labels:
    app: postgres
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
        - name: postgres
          image: postgres:13
          ports:
            - containerPort: 5432
          envFrom:
            - secretRef:
                name: postgres-secret
          readinessProbe:
            exec:
              command: ["pg_isready", "-U", "postgres"]
            initialDelaySeconds: 10
            periodSeconds: 5
            timeoutSeconds: 3
          livenessProbe:
            exec:
              command: ["pg_isready", "-U", "postgres"]
            initialDelaySeconds: 30
            periodSeconds: 10
            timeoutSeconds: 3
          resources:
            requests:
              memory: "256Mi"
              cpu: "250m"
            limits:
              memory: "512Mi"
              cpu: "500m"
EOF
                        """

                        echo '⏳ Waiting for PostgreSQL to be ready...'
                        sh "kubectl wait --for=condition=available --timeout=${env.DAST_TIMEOUT}s deployment/${env.DAST_DB_NAME} -n ${env.DAST_NAMESPACE}"

                        // Déploiement Django
                        echo '🐍 Deploying Django application...'
                        withCredentials([string(credentialsId: 'DJANGO_SECRET_KEY', variable: 'DJANGO_SECRET')]) {
                            sh """
cat <<EOF | kubectl apply -n ${env.DAST_NAMESPACE} -f -
apiVersion: v1
kind: Secret
metadata:
  name: django-secret
type: Opaque
stringData:
  SECRET_KEY: \${DJANGO_SECRET}
  DB_NAME: mysite_dast
  DB_USER: postgres
  DB_PASSWORD: postgres_dast_secure
  DB_HOST: ${env.DAST_DB_NAME}
  DB_PORT: "5432"
---
apiVersion: v1
kind: Service
metadata:
  name: ${env.DAST_APP_NAME}
  labels:
    app: django
spec:
  type: NodePort
  ports:
    - port: ${env.DAST_SERVICE_PORT}
      targetPort: 8000
      nodePort: ${env.DAST_NODE_PORT}
      protocol: TCP
  selector:
    app: django
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${env.DAST_APP_NAME}
  labels:
    app: django
spec:
  replicas: 1
  selector:
    matchLabels:
      app: django
  template:
    metadata:
      labels:
        app: django
    spec:
      initContainers:
        - name: wait-for-db
          image: busybox:1.36
          command: ["sh", "-c", "until nc -z ${env.DAST_DB_NAME} 5432; do echo 'Waiting for database...'; sleep 2; done; echo 'Database is ready!'"]
        - name: django-migrate
          image: ${env.TEST_IMAGE_TAG}
          command: ["/bin/sh", "-c"]
          args:
            - python manage.py migrate --noinput
          envFrom:
            - secretRef:
                name: django-secret
          env:
            - name: DJANGO_SETTINGS_MODULE
              value: "mysite.settings"
      containers:
        - name: django
          image: ${env.TEST_IMAGE_TAG}
          imagePullPolicy: Never
          ports:
            - containerPort: 8000
          envFrom:
            - secretRef:
                name: django-secret
          env:
            - name: DJANGO_SETTINGS_MODULE
              value: "mysite.settings"
          readinessProbe:
            httpGet:
              path: /
              port: 8000
            initialDelaySeconds: 15
            periodSeconds: 5
            timeoutSeconds: 3
            failureThreshold: 3
          livenessProbe:
            httpGet:
              path: /
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 3
          resources:
            requests:
              memory: "512Mi"
              cpu: "500m"
            limits:
              memory: "1Gi"
              cpu: "1000m"
EOF
                            """
                        }

                        echo '⏳ Waiting for Django application to be ready...'
                        sh "kubectl wait --for=condition=available --timeout=${env.DAST_TIMEOUT}s deployment/${env.DAST_APP_NAME} -n ${env.DAST_NAMESPACE}"

                        def nodePort = sh(script: "kubectl get svc ${env.DAST_APP_NAME} -n ${env.DAST_NAMESPACE} -o jsonpath='{.spec.ports[0].nodePort}'", returnStdout: true).trim()
                        env.DAST_APP_URL = "http://127.0.0.1:${nodePort}"
                        echo "✅ Application deployed and accessible at: ${env.DAST_APP_URL}"

                        echo '✅ DAST deployment completed successfully!'
                    } catch (Exception e) {
                        currentBuild.result = 'FAILURE'
                        echo "❌ DAST deployment failed: ${e.message}"
                        throw e
                    }
                }
            }
            post {
                failure {
                    echo '🧹 Cleaning up failed DAST deployment...'
                    sh "kubectl delete namespace ${env.DAST_NAMESPACE} --wait=false || true"
                }
            }
        }
    }

    post {
        always {
            echo 'Pipeline finished.'
            sh "docker logout ${env.DOCKER_REGISTRY} || true"
            sh "docker stop ${env.TEST_DB_CONTAINER_NAME} || true"
            sh "docker rm ${env.TEST_DB_CONTAINER_NAME} || true"
            cleanWs()
        }
        success { echo '✅ Pipeline a réussi !' }
        failure { echo '❌ Pipeline a échoué !' }
        unstable { echo '⚠️ Pipeline instable (problèmes de qualité/sécurité trouvés).' }
    }
}
